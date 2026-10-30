/* ==========================================================================
   SpectraPlume 2.0 — Mission Console Application Controller (ES6)
   Connects Native Editorial Light UI to Python FastAPI + PyTorch 3D-CNN Backend
   Zero Emojis • Real-Time Leaflet GIS • Live 40-Band Pixel Spectroscopy
   ========================================================================== */

const AppState = {
  passes: [],
  liveHotspots: [],
  liveScannedItems: [],
  totalNasaHits: 0,
  totalScopeHits: 0,
  yearFilter: 'all',         // 'all' | 'recent' | '2024' | '2023' | '2022'
  yearCounts: { all: 0, recent: 0, '2024': 0, '2023': 0, '2022': 0 },
  feedMode: 'live',          // 'live' | 'benchmarks'
  radarScope: 'egypt',       // 'egypt' | 'mena' | 'global'
  scanMapMode: false,
  activePassId: 'deadsea',
  activeView: 'radar',       // 'radar' | 'lab' | 'dispatch'
  mapLayerMode: 'ai',        // 'ai' | 'nasa' | 'both'
  retrievalMode: 'spectraplume',
  windMode: 'era5',          // 'era5' | 'custom'
  customWindSpeed: 4.2,
  customWindDir: 240,
  maskThreshold: 0.50,
  showSwathBounds: true,
  showWindVector: true,
  currentPayload: null,
  activePreset: 'primary',
  leafletMap: null,
  hotspotClusterLayer: null,
  layers: {
    aiOverlay: null,
    nasaOverlay: null,
    swathRect: null,
    nasaPolygon: null,
    epicenterMarker: null,
    probeMarker: null,
    windLine: null,
  },
  debounceTimer: null,
};

/* ==================== INITIALIZATION ==================== */
document.addEventListener('DOMContentLoaded', async () => {
  initDropdownDismiss();
  initUploadDragDrop();
  initMapEngine();
  initResponsiveObservers();
  await loadPassesAndBoot();
});

function initResponsiveObservers() {
  let rafId = null;
  const handleLayoutChange = () => {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(() => {
      if (AppState.leafletMap) {
        AppState.leafletMap.invalidateSize({ pan: false });
      }
      if (AppState.currentPayload && AppState.currentPayload.active_spectrum) {
        renderAllCharts(AppState.currentPayload.active_spectrum);
      }
    });
  };

  window.addEventListener('resize', handleLayoutChange);

  if (typeof ResizeObserver !== 'undefined') {
    const ro = new ResizeObserver(handleLayoutChange);
    const mapStage = document.querySelector('.leaflet-stage');
    const mainEl = document.querySelector('.sp-main');
    if (mapStage) ro.observe(mapStage);
    if (mainEl) ro.observe(mainEl);
  }
}

async function loadPassesAndBoot() {
  try {
    const qs = new URLSearchParams(window.location.search);
    const reqPass = qs.get('pass');
    const reqView = qs.get('view');
    const reqModal = qs.get('modal');
    const reqScope = qs.get('scope');

    const res = await fetch('/api/passes');
    const data = await res.json();
    AppState.passes = data.passes || [];
    updateConnectionBadge(data.earthdata_connected, data.earthdata_auth);

    // If URL explicitly asked for one of the 4 benchmark passes, open Benchmarks mode directly
    if (reqPass && AppState.passes.some(p => p.pass_id === reqPass)) {
      AppState.feedMode = 'benchmarks';
      AppState.activePassId = reqPass;
      syncFeedTabUI();
      renderPassFeed();
      await runAnalysis(AppState.activePassId, true);
      // Still load live red dots onto the world map in the background!
      loadLiveHotspots(reqScope || 'egypt', false, false);
    } else {
      // Default Boot: Live NASA Satellite Hotspot Radar across Egypt (48 real red dots!)
      const liveOk = await loadLiveHotspots(reqScope || 'egypt', true, true);
      if (!liveOk || !AppState.currentPayload) {
        // Offline / Token-Free Guaranteed Fallback so telemetry & charts are NEVER uninitialized
        if (!liveOk) {
          AppState.feedMode = 'benchmarks';
          syncFeedTabUI();
          renderPassFeed();
        }
        AppState.activePassId = 'deadsea';
        await runAnalysis('deadsea', !liveOk);
      }
    }

    if (reqView === 'lab') switchView('lab', document.getElementById('tabBtnLab'));
    else if (reqView === 'dispatch') switchView('dispatch', document.getElementById('tabBtnDispatch'));
    if (reqModal === 'upload') openUploadModal();
  } catch (err) {
    showToast('Unable to reach local SpectraPlume engine. Keep run_demo.py open in the background.');
  }
}

function updateConnectionBadge(hasLiveToken, authObj) {
  const txt = document.getElementById('connBadgeText');
  if (!txt) return;
  if (hasLiveToken && authObj && authObj.account) {
    txt.textContent = `NASA Live • @${authObj.account}`;
  } else if (hasLiveToken) {
    txt.textContent = 'NASA LP DAAC • Live Connected';
  } else if (AppState.liveHotspots && AppState.liveHotspots.length > 0) {
    txt.textContent = 'NASA CMR • Public Live';
  } else {
    txt.textContent = 'ISS EMIT Suite • Active';
  }
}

function setMapLoading(visible, msg) {
  const box = document.getElementById('mapLiveLoading');
  const txt = document.getElementById('mapLiveLoadingText');
  if (!box) return;
  if (msg && txt) txt.textContent = msg;
  box.style.display = visible ? 'inline-flex' : 'none';
}

/* ==================== LIVE NASA HOTSPOT RADAR & POINT SCANNER ==================== */
function syncYearFilterUI() {
  const counts = AppState.yearCounts || {};
  const scannedRecent = AppState.liveScannedItems.filter(
    s => s.is_new || s.is_recent || (String(s.year || '').match(/^\d+$/) && Number(s.year) >= 2025)
  ).length;

  const labels = {
    all: { id: 'yrBtnAll', base: 'All', count: counts.all },
    recent: { id: 'yrBtnRecent', base: '2025–26', count: (counts.recent || 0) + scannedRecent },
    '2024': { id: 'yrBtn2024', base: '2024', count: counts['2024'] },
    '2023': { id: 'yrBtn2023', base: '2023', count: counts['2023'] },
    '2022': { id: 'yrBtn2022', base: '2022', count: counts['2022'] },
  };

  Object.keys(labels).forEach(k => {
    const cfg = labels[k];
    const btn = document.getElementById(cfg.id);
    if (!btn) return;
    btn.classList.toggle('active', AppState.yearFilter === k);
    if (typeof cfg.count === 'number') {
      btn.innerHTML = `${cfg.base} <span class="year-pill-count">(${cfg.count})</span>`;
    } else {
      btn.textContent = cfg.base;
    }
  });
}

async function switchYearFilter(yearKey) {
  AppState.yearFilter = yearKey;
  AppState.feedMode = 'live';
  syncFeedTabUI();
  syncYearFilterUI();
  await loadLiveHotspots(AppState.radarScope, false, false, yearKey);
}

async function loadLiveHotspots(scope, setRegionalCamera = true, autoAnalyzeTop = false, yearOverride = null) {
  AppState.radarScope = scope;
  const activeYear = yearOverride || AppState.yearFilter || 'all';
  AppState.yearFilter = activeYear;

  document.querySelectorAll('#nasaScopeSwitcher .scope-pill[data-scope]').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-scope') === scope);
  });

  const yrDesc = activeYear === 'all' ? 'All Years' : (activeYear === 'recent' ? '2025–2026' : activeYear);
  setMapLoading(true, `Fetching Live NASA EMIT Methane Hotspots (${scope.toUpperCase()} • ${yrDesc})...`);
  try {
    const res = await fetch(
      `/api/nasa/hotspots?scope=${encodeURIComponent(scope)}&year=${encodeURIComponent(activeYear)}`
    );
    if (!res.ok) throw new Error('CMR offline');
    const data = await res.json();
    AppState.liveHotspots = data.hotspots || [];
    AppState.totalNasaHits = typeof data.total_nasa_hits === 'number' ? data.total_nasa_hits : AppState.liveHotspots.length;
    AppState.totalScopeHits = typeof data.total_scope_hits === 'number' ? data.total_scope_hits : AppState.totalNasaHits;
    if (data.year_counts) {
      AppState.yearCounts = data.year_counts;
    }

    if (data.earthdata_auth) {
      updateConnectionBadge(data.earthdata_auth.connected, data.earthdata_auth);
    }

    const liveBtnTxt = document.getElementById('feedLiveBtnText');
    if (liveBtnTxt) {
      liveBtnTxt.textContent = `Live NASA (${AppState.totalScopeHits})`;
    }

    syncYearFilterUI();
    renderHotspotMarkersOnMap();
    if (AppState.feedMode === 'live') {
      renderPassFeed();
    }

    if (setRegionalCamera && AppState.leafletMap && data.map_center) {
      AppState.leafletMap.flyTo(data.map_center, data.map_zoom || 6, { duration: 0.85 });
    }

    if (autoAnalyzeTop && AppState.liveHotspots.length > 0) {
      // Quantify the latest real NASA plume without zooming away from the regional red-dot overview!
      await selectLiveHotspot(AppState.liveHotspots[0].granule_ur, false);
    }
    setMapLoading(false);
    return true;
  } catch (_) {
    setMapLoading(false);
    return false;
  }
}

async function switchRadarScope(scope, btnEl) {
  AppState.feedMode = 'live';
  syncFeedTabUI();
  await loadLiveHotspots(scope, true, false, AppState.yearFilter);
}

function zoomToActiveSwath() {
  if (!AppState.leafletMap || !AppState.currentPayload) return;
  const g = AppState.currentPayload.geography;
  const z = (AppState.currentPayload.pass_info && AppState.currentPayload.pass_info.zoom) || 13;
  AppState.leafletMap.flyTo([g.center_lat, g.center_lon], z, { duration: 0.9 });
}

function renderHotspotMarkersOnMap() {
  if (!AppState.leafletMap || typeof window.L === 'undefined') return;
  const L_lib = window.L;
  if (!AppState.hotspotClusterLayer) {
    AppState.hotspotClusterLayer = L_lib.layerGroup().addTo(AppState.leafletMap);
  }
  AppState.hotspotClusterLayer.clearLayers();

  AppState.liveHotspots.forEach(hs => {
    const isSel = AppState.activePassId === hs.pass_id;
    const ageTxt = hs.age_label ? ` (${escapeHtml(hs.age_label)})` : '';
    const yrBadge = hs.recency_badge || hs.year || 'NASA';
    const icon = L_lib.divIcon({
      className: '',
      html: `<div class="sp-live-hotspot ${isSel ? 'selected' : ''}" title="${escapeHtml(hs.name)} • ${escapeHtml(hs.utc_time)}"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });
    const m = L_lib.marker([hs.lat, hs.lon], { icon });
    m.bindTooltip(
      `<div style="font-family:'Plus Jakarta Sans',sans-serif;line-height:1.38;">` +
      `<b>Live NASA Plume #${escapeHtml(hs.plume_id)}</b> ` +
      `<span style="background:#12231A;color:#FDE68A;padding:1px 5px;border-radius:4px;font-size:10px;font-weight:700;">${escapeHtml(yrBadge)}</span><br>` +
      `${escapeHtml(hs.name)}<br>` +
      `<span style="color:#B45309;font-weight:700;">Captured: ${escapeHtml(hs.utc_time)}</span>${ageTxt}<br>` +
      `<span style="font-size:10.5px;color:#526058;">Click red dot to quantify flux (kg/h)</span>` +
      `</div>`,
      { direction: 'top', offset: [0, -6] }
    );
    m.on('click', (ev) => {
      L_lib.DomEvent.stopPropagation(ev);
      selectLiveHotspot(hs.granule_ur, true);
    });
    AppState.hotspotClusterLayer.addLayer(m);
  });
}

async function selectLiveHotspot(granuleUr, flyToTarget = true) {
  setMapLoading(true, `Quantifying Live NASA Granule ${granuleUr} + ERA5 Wind...`);
  let res;
  try {
    res = await fetch('/api/nasa/analyze-plume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        granule_ur: granuleUr,
        mask_threshold: AppState.maskThreshold,
        retrieval_mode: AppState.retrievalMode,
        wind_speed: AppState.windMode === 'custom' ? AppState.customWindSpeed : null,
        wind_direction: AppState.windMode === 'custom' ? AppState.customWindDir : null,
      }),
    });
  } catch (_) {
    setMapLoading(false);
    showToast('Local Python server stopped — double-click run_demo.bat (or run python run_demo.py) to reconnect.');
    return;
  }

  try {
    const payload = await res.json();
    setMapLoading(false);
    if (!res.ok) {
      showToast(payload.error_message || 'Could not retrieve live NASA plume granule.');
      return;
    }
    AppState.activePassId = payload.pass_info.pass_id;
    AppState.currentPayload = payload;
    // Record quantified flux on the hotspot item so the sidebar shows the live kg/h value!
    const hsItem = AppState.liveHotspots.find(h => h.granule_ur === granuleUr);
    if (hsItem) {
      hsItem.quantified_flux_kg_hr = Math.round(payload.kpis.flux_kg_hr);
    }
    renderHotspotMarkersOnMap();
    renderPassFeed();
    applyPayloadToUI(payload, flyToTarget);
  } catch (_) {
    setMapLoading(false);
    showToast('Unexpected response while quantifying NASA granule.');
  }
}

function toggleScanMapMode() {
  AppState.scanMapMode = !AppState.scanMapMode;
  const btn = document.getElementById('btnScanMapMode');
  const txt = document.getElementById('btnScanMapText');
  const stage = document.getElementById('leafletStageWrap');
  if (btn) btn.classList.toggle('active', AppState.scanMapMode);
  if (stage) stage.classList.toggle('scan-active', AppState.scanMapMode);
  if (txt) {
    txt.textContent = AppState.scanMapMode ? 'Click Any Spot Now...' : 'Click Map to Scan';
  }
  if (AppState.scanMapMode) {
    showToast('Point-Scan Active: Click anywhere on Earth to scan latest NASA EMIT satellite swath.');
  }
}

async function scanTypedCoordinates() {
  const inp = document.getElementById('coordSearchInput');
  if (!inp || !inp.value.trim()) {
    showToast('Enter GPS coordinates as: Lat, Lon (e.g. 30.82, 29.55)');
    return;
  }
  const parts = inp.value.split(/[\s,;]+/).filter(Boolean);
  if (parts.length < 2) {
    showToast('Enter both Latitude and Longitude separated by a comma (e.g. 30.82, 29.55).');
    return;
  }
  const lat = parseFloat(parts[0]);
  const lon = parseFloat(parts[1]);
  if (Number.isNaN(lat) || Number.isNaN(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) {
    showToast('Invalid GPS coordinates. Example: 30.82, 29.55');
    return;
  }
  await scanCoordinatesOnNASA(lat, lon);
}

function normalizeLon(rawLon) {
  return ((((Number(rawLon) + 180.0) % 360.0) + 360.0) % 360.0) - 180.0;
}

async function scanCoordinatesOnNASA(lat, rawLon) {
  const lon = normalizeLon(rawLon);
  setMapLoading(true, `Scanning Live NASA ISS EMIT Swath at (${lat.toFixed(3)}°, ${lon.toFixed(3)}°)...`);
  let res;
  try {
    res = await fetch('/api/nasa/scan-point', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lat,
        lon,
        mask_threshold: AppState.maskThreshold,
        retrieval_mode: AppState.retrievalMode,
        wind_speed: AppState.windMode === 'custom' ? AppState.customWindSpeed : null,
        wind_direction: AppState.windMode === 'custom' ? AppState.customWindDir : null,
      }),
    });
  } catch (_) {
    setMapLoading(false);
    if (AppState.scanMapMode) toggleScanMapMode();
    showToast('Local Python server stopped — double-click run_demo.bat (or run python run_demo.py) to reconnect.');
    return;
  }

  try {
    const payload = await res.json();
    setMapLoading(false);

    // Turn off one-shot crosshair toggle after click completes
    if (AppState.scanMapMode) {
      toggleScanMapMode();
    }

    if (!res.ok) {
      const errTitle = payload.error_title || 'NASA Scan';
      const rawDetail = Array.isArray(payload.detail)
        ? (payload.detail[0] && payload.detail[0].msg)
        : payload.detail;
      const errMsg = payload.error_message || rawDetail || 'No overpass at this coordinate.';
      showToast(`${errTitle}: ${errMsg}`);
      if (AppState.leafletMap && typeof window.L !== 'undefined') {
        window.L.popup()
          .setLatLng([lat, rawLon])
          .setContent(
            `<div style="font-family:'Plus Jakarta Sans',sans-serif;max-width:240px;color:#12231A;">
              <div style="font-weight:800;color:#D4810B;margin-bottom:3px;">${escapeHtml(errTitle)}</div>
              <div style="font-size:12px;">${escapeHtml(String(errMsg))}</div>
            </div>`
          )
          .openOn(AppState.leafletMap);
      }
      return;
    }

    AppState.activePassId = payload.pass_info.pass_id;
    AppState.currentPayload = payload;

    // Add scanned sector to top of Live NASA Feed with full temporal metadata
    const existingIdx = AppState.liveScannedItems.findIndex(s => s.pass_info ? false : s.pass_id === payload.pass_info.pass_id);
    const scanCard = {
      pass_id: payload.pass_info.pass_id,
      orbit: payload.pass_info.orbit,
      name: payload.pass_info.name,
      facility: payload.pass_info.facility,
      utc_time: payload.pass_info.utc_time,
      year: payload.pass_info.year || '2026',
      age_label: payload.pass_info.age_label || 'Live Scan',
      recency_badge: payload.pass_info.recency_badge || 'RECENT',
      is_new: Boolean(payload.pass_info.is_new),
      is_recent: Boolean(payload.pass_info.is_recent),
      lat: payload.geography.center_lat,
      lon: payload.geography.center_lon,
      is_clean: payload.geography.is_zero_gas_trap || !payload.geography.has_active_plume,
      flux_kg_hr: Math.round(payload.kpis.flux_kg_hr),
    };
    if (existingIdx >= 0) AppState.liveScannedItems.splice(existingIdx, 1);
    AppState.liveScannedItems.unshift(scanCard);

    AppState.feedMode = 'live';
    syncFeedTabUI();
    syncYearFilterUI();
    renderHotspotMarkersOnMap();
    renderPassFeed();
    applyPayloadToUI(payload, true);
    showToast(`Scanned NASA Swath ${payload.pass_info.daac_granule} (Captured ${payload.pass_info.utc_time}).`);
  } catch (_) {
    setMapLoading(false);
    if (AppState.scanMapMode) toggleScanMapMode();
    showToast('Unexpected response while scanning NASA LP DAAC archive.');
  }
}

function switchFeedMode(mode) {
  AppState.feedMode = mode;
  syncFeedTabUI();
  renderPassFeed();
}

function syncFeedTabUI() {
  const tLive = document.getElementById('feedTabLive');
  const tBench = document.getElementById('feedTabBench');
  if (tLive) tLive.classList.toggle('active', AppState.feedMode === 'live');
  if (tBench) tBench.classList.toggle('active', AppState.feedMode === 'benchmarks');
}

/* ==================== VIEW NAVIGATION ==================== */
function switchView(viewName, btnEl) {
  AppState.activeView = viewName;
  document.querySelectorAll('.sp-nav-tab').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  document.querySelectorAll('.sp-view-pane').forEach(p => p.classList.remove('active'));
  const target = document.getElementById('view-' + viewName);
  if (target) target.classList.add('active');

  if (viewName === 'radar' && AppState.leafletMap) {
    setTimeout(() => AppState.leafletMap.invalidateSize(), 60);
  }
  if (AppState.currentPayload && AppState.currentPayload.active_spectrum) {
    setTimeout(() => renderAllCharts(AppState.currentPayload.active_spectrum), 40);
  }
}

/* ==================== ORBITAL SCAN FEED (LEFT RAIL) ==================== */
function _formatAgeBadgeHtml(item) {
  const txt = item.age_label || item.year || '';
  if (!txt) return '';
  const cls = item.is_new ? 'is-new' : (item.is_recent ? 'is-recent' : '');
  return `<span class="time-age-badge ${cls}">${escapeHtml(txt)}</span>`;
}

function renderPassFeed() {
  const container = document.getElementById('passFeedList');
  if (!container) return;
  const countEl = document.getElementById('passCountLabel');

  if (AppState.feedMode === 'live') {
    const yr = AppState.yearFilter || 'all';
    const filteredScans = AppState.liveScannedItems.filter(s => {
      if (yr === 'all') return true;
      if (yr === 'recent') {
        return s.is_new || s.is_recent || (String(s.year || '').match(/^\d+$/) && Number(s.year) >= 2025);
      }
      return String(s.year) === yr;
    });

    const totalShown = filteredScans.length + AppState.totalNasaHits;
    if (countEl) {
      const yrTag = yr === 'all' ? 'Live' : (yr === 'recent' ? '2025–26' : yr);
      countEl.textContent = `${totalShown} • ${yrTag}`;
    }

    const scannedHtml = filteredScans.map(s => {
      const isActive = s.pass_id === AppState.activePassId;
      const pillClass = s.is_clean ? 'pill-safe' : 'pill-leak';
      const badge = s.is_clean ? `Scan • ${s.year || 'Live'}` : `Leak • ${s.year || 'Live'}`;
      const fluxTxt = s.is_clean
        ? '<span style="color:var(--sp-safe-600);font-weight:700;">0 kg/h (Clean)</span>'
        : `<strong>${Number(s.flux_kg_hr).toLocaleString()} kg/h</strong>`;
      const latDir = s.lat >= 0 ? 'N' : 'S';
      const lonDir = s.lon >= 0 ? 'E' : 'W';
      const coordStr = `${Math.abs(s.lat).toFixed(2)}°${latDir}, ${Math.abs(s.lon).toFixed(2)}°${lonDir}`;
      return `
        <div class="pass-card ${isActive ? 'active' : ''}" onclick="selectOrbitalPass('${s.pass_id}')" title="${escapeHtml(s.name)} — Captured ${escapeHtml(s.utc_time)}">
          <div class="pass-card-top">
            <span class="pass-orbit-tag">Orbit #${escapeHtml(s.orbit)}</span>
            <span class="status-pill ${pillClass}">${escapeHtml(badge)}</span>
          </div>
          <div class="pass-title">${escapeHtml(s.name)}</div>
          <div class="pass-time-row">
            <span class="pass-time-left"><svg><use href="#ic-clock"/></svg><span>${escapeHtml(s.utc_time)}</span></span>
            ${_formatAgeBadgeHtml(s)}
          </div>
          <div class="pass-telemetry-row">
            <span>${fluxTxt}</span>
            <span>${coordStr}</span>
          </div>
        </div>
      `;
    }).join('');

    const hotspotsHtml = AppState.liveHotspots.slice(0, 100).map(hs => {
      const isActive = hs.pass_id === AppState.activePassId;
      const latDir = hs.lat >= 0 ? 'N' : 'S';
      const lonDir = hs.lon >= 0 ? 'E' : 'W';
      const coordStr = `${Math.abs(hs.lat).toFixed(2)}°${latDir}, ${Math.abs(hs.lon).toFixed(2)}°${lonDir}`;
      const qFlux = hs.quantified_flux_kg_hr
        ? `<strong>${Number(hs.quantified_flux_kg_hr).toLocaleString()} kg/h</strong>`
        : `<span style="color:var(--sp-danger-600);font-weight:700;">Plume #${escapeHtml(hs.plume_id)}</span>`;
      const yrPill = hs.is_new ? 'NEW • LIVE' : `NASA • ${hs.year || 'L2B'}`;
      return `
        <div class="pass-card ${isActive ? 'active' : ''}" onclick="selectLiveHotspot('${hs.granule_ur}', true)" title="${escapeHtml(hs.name)} — Captured ${escapeHtml(hs.utc_time)}">
          <div class="pass-card-top">
            <span class="pass-orbit-tag">Orbit #${escapeHtml(hs.orbit)}</span>
            <span class="status-pill pill-leak">${escapeHtml(yrPill)}</span>
          </div>
          <div class="pass-title">${escapeHtml(hs.name)}</div>
          <div class="pass-time-row">
            <span class="pass-time-left"><svg><use href="#ic-clock"/></svg><span>${escapeHtml(hs.utc_time)}</span></span>
            ${_formatAgeBadgeHtml(hs)}
          </div>
          <div class="pass-telemetry-row">
            <span>${qFlux}</span>
            <span>${coordStr}</span>
          </div>
        </div>
      `;
    }).join('');

    if (!scannedHtml && !hotspotsHtml) {
      if (yr === 'recent') {
        container.innerHTML = `
          <div style="background:#FFFFFF;border:1px solid var(--sp-border);border-radius:10px;padding:11px;font-size:11.75px;color:var(--sp-ink-secondary);line-height:1.48;">
            <strong style="display:block;color:var(--sp-forest-900);margin-bottom:4px;">0 Curated 2025–2026 Plumes in This Region</strong>
            NASA JPL's manual <code>CH4PLM</code> plume catalog currently ends at late 2024 in this sector. Use <b>Click Map to Scan</b> to inspect raw <b>2025–2026 ISS EMIT</b> swaths live!
            <button type="button" class="sp-btn sp-btn-amber" style="width:100%;margin-top:8px;justify-content:center;" onclick="if(!AppState.scanMapMode) toggleScanMapMode();">
              <svg><use href="#ic-crosshair"/></svg>
              <span>Scan 2026 Live Swath on Map</span>
            </button>
          </div>
        `;
      } else {
        container.innerHTML =
          '<div style="font-size:12px;color:var(--sp-ink-muted);padding:8px;">No NASA plumes recorded for this year filter in the selected region.</div>';
      }
      return;
    }

    container.innerHTML = scannedHtml + hotspotsHtml;
    return;
  }

  if (countEl) countEl.textContent = `${AppState.passes.length} Passes`;

  container.innerHTML = AppState.passes.map(p => {
    const isActive = p.pass_id === AppState.activePassId;
    const pillClass = p.is_zero_gas_trap ? 'pill-safe' : (p.flux_kg_hr >= 85 ? 'pill-leak' : 'pill-amber');
    const fluxText = p.is_zero_gas_trap
      ? '<span style="color:var(--sp-safe-600);font-weight:700;">0 kg/h (Rock)</span>'
      : `<strong>${Number(p.flux_kg_hr).toLocaleString()} kg/h</strong>`;
    const latDir = p.center_lat >= 0 ? 'N' : 'S';
    const lonDir = p.center_lon >= 0 ? 'E' : 'W';
    const coordStr = `${Math.abs(p.center_lat).toFixed(2)}°${latDir}, ${Math.abs(p.center_lon).toFixed(2)}°${lonDir}`;

    return `
      <div class="pass-card ${isActive ? 'active' : ''}" onclick="selectOrbitalPass('${p.pass_id}')" title="${escapeHtml(p.name)} — ${escapeHtml(p.facility)}">
        <div class="pass-card-top">
          <span class="pass-orbit-tag">Orbit #${escapeHtml(p.orbit)}</span>
          <span class="status-pill ${pillClass}">${escapeHtml(p.badge_label)}</span>
        </div>
        <div class="pass-title">${escapeHtml(p.name)}</div>
        <div class="pass-facility">${escapeHtml(p.facility)}</div>
        <div class="pass-time-row">
          <span class="pass-time-left"><svg><use href="#ic-clock"/></svg><span>${escapeHtml(p.utc_time || '')}</span></span>
          ${_formatAgeBadgeHtml(p)}
        </div>
        <div class="pass-telemetry-row">
          <span>${fluxText}</span>
          <span>${coordStr}</span>
        </div>
      </div>
    `;
  }).join('');
}

async function selectOrbitalPass(passId) {
  AppState.activePassId = passId;
  AppState.activePreset = 'primary';
  renderPassFeed();
  await runAnalysis(passId, true);
}

/* ==================== ANALYSIS EXECUTION ==================== */
async function runAnalysis(passId, flyCamera = false) {
  const targetId = passId || AppState.activePassId || 'deadsea';
  const body = {
    pass_id: targetId,
    mask_threshold: AppState.maskThreshold,
    retrieval_mode: AppState.retrievalMode,
    wind_speed: AppState.windMode === 'custom' ? AppState.customWindSpeed : null,
    wind_direction: AppState.windMode === 'custom' ? AppState.customWindDir : null,
  };

  let res;
  try {
    res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch (_) {
    showToast('Local Python server stopped — keep the terminal (run_demo.py) window open in the background.');
    return;
  }

  try {
    const payload = await res.json();
    if (!res.ok) {
      const reason = payload.error_message || payload.detail || `HTTP ${res.status}`;
      showToast(`Analysis Warning: ${reason}`);
      return;
    }
    AppState.currentPayload = payload;
    applyPayloadToUI(payload, flyCamera);
  } catch (_) {
    showToast('Server returned an unexpected response — restart run_demo.py after git pull.');
  }
}

function scheduleReanalysis() {
  clearTimeout(AppState.debounceTimer);
  AppState.debounceTimer = setTimeout(() => runAnalysis(AppState.activePassId, false), 140);
}

/* ==================== APPLY PAYLOAD ACROSS ALL 3 VIEWS ==================== */
function applyPayloadToUI(data, flyCamera) {
  const { pass_info, verdict, kpis, geography, visuals, active_spectrum } = data;

  // 1. Verdict Banner
  const banner = document.getElementById('verdictBanner');
  banner.className = `verdict-banner state-${verdict.state}`;

  const iconEl = document.getElementById('verdictIconBox');
  if (verdict.state === 'confirmed_leak') {
    iconEl.innerHTML = '<svg><use href="#ic-beacon"/></svg>';
  } else if (verdict.state === 'false_alarm_blocked') {
    iconEl.innerHTML = '<svg><use href="#ic-shield-check"/></svg>';
  } else {
    iconEl.innerHTML = '<svg><use href="#ic-orbit"/></svg>';
  }

  const pillEl = document.getElementById('verdictStatePill');
  pillEl.className = 'status-pill ' + (
    verdict.state === 'confirmed_leak' ? 'pill-leak' :
    verdict.state === 'false_alarm_blocked' ? 'pill-safe' : 'pill-amber'
  );
  pillEl.textContent = verdict.pill;

  document.getElementById('verdictOrbitTag').textContent =
    `Orbit #${pass_info.orbit} • ${pass_info.utc_time} • ${kpis.processing_time_ms} ms`;
  document.getElementById('verdictHeadline').textContent = verdict.headline;
  document.getElementById('verdictSummary').textContent = verdict.summary;

  const proofStrip = document.getElementById('falseAlarmProofStrip');
  if (verdict.proof_cards && verdict.proof_cards.length > 0) {
    proofStrip.style.display = 'grid';
    proofStrip.innerHTML = verdict.proof_cards.map(c => `
      <div class="proof-reason-card">
        <strong>${escapeHtml(c.title)}</strong>
        <span>${escapeHtml(c.body)}</span>
      </div>
    `).join('');
  } else {
    proofStrip.style.display = 'none';
  }

  // 2. Four Crisp KPI Cards
  document.getElementById('kpiFluxVal').textContent =
    geography.is_zero_gas_trap ? '0 kg/h' : `${Math.round(kpis.flux_kg_hr).toLocaleString()} kg/h`;
  document.getElementById('kpiFluxSub').textContent =
    geography.is_zero_gas_trap
      ? '0.00 Tons/hr (Verified Zero Gas)'
      : `${kpis.flux_ton_hr.toFixed(2)} ± ${kpis.flux_uncertainty_ton_hr.toFixed(2)} t/h (95% CI)`;

  document.getElementById('kpiMassVal').textContent = `${Math.round(kpis.ime_kg).toLocaleString()} kg`;
  document.getElementById('kpiMassSub').textContent =
    geography.is_zero_gas_trap
      ? '0 Active Plume Pixels'
      : `Area: ${kpis.plume_area_km2.toFixed(2)} km² • Length: ${Math.round(kpis.plume_length_m)} m`;

  document.getElementById('kpiRejectVal').textContent = `${kpis.false_alarm_reduction_pct.toFixed(1)}%`;
  document.getElementById('kpiRejectSub').textContent =
    `${kpis.rejected_clutter_pixels} spurious NASA pixels blocked`;

  document.getElementById('kpiLossVal').textContent = `$${Math.round(kpis.daily_loss_usd).toLocaleString()}/d`;
  document.getElementById('kpiLossSub').textContent =
    `$${Math.round(kpis.annual_loss_usd).toLocaleString()}/yr • Wind ${kpis.wind_speed_m_s} m/s @ ${kpis.wind_direction_deg}°`;

  // 3. Map Telemetry Chips + Active Capture Timestamp Badges
  const latDir = geography.source_lat >= 0 ? 'N' : 'S';
  const lonDir = geography.source_lon >= 0 ? 'E' : 'W';
  document.getElementById('mapCoordText').textContent =
    `${Math.abs(geography.source_lat).toFixed(4)}° ${latDir}, ${Math.abs(geography.source_lon).toFixed(4)}° ${lonDir}`;
  document.getElementById('mapWindText').textContent =
    `${kpis.wind_speed_m_s} m/s @ ${kpis.wind_direction_deg}°`;

  const ageSuffix = pass_info.age_label ? ` (${pass_info.age_label})` : '';
  const mapTimeEl = document.getElementById('mapTimeText');
  if (mapTimeEl) {
    mapTimeEl.textContent = `${pass_info.utc_time}${ageSuffix}`;
  }
  const activeCapEl = document.getElementById('activeCaptureText');
  if (activeCapEl) {
    activeCapEl.textContent = `Captured: ${pass_info.utc_time}${ageSuffix}`;
  }

  // Sync default wind sliders when in ERA5 mode
  if (AppState.windMode === 'era5') {
    AppState.customWindSpeed = kpis.wind_speed_m_s;
    AppState.customWindDir = kpis.wind_direction_deg;
    const wsEl = document.getElementById('windSpeedSlider');
    const wdEl = document.getElementById('windDirSlider');
    if (wsEl) { wsEl.value = kpis.wind_speed_m_s; updateRangeFill(wsEl); }
    if (wdEl) { wdEl.value = kpis.wind_direction_deg; updateRangeFill(wdEl); }
    document.getElementById('windSpeedLabel').textContent = `${kpis.wind_speed_m_s} m/s`;
    document.getElementById('windDirLabel').textContent = `${kpis.wind_direction_deg}°`;
  }

  // 4. Update Interactive Map Overlays
  updateMapOverlays(data, flyCamera);

  // 5. Update View 2 (3-Stage Visual Tiles)
  document.getElementById('imgStageSwir').src = visuals.tile_swir_rgb;
  document.getElementById('imgStageAmf').src = visuals.tile_nasa_amf;
  document.getElementById('imgStageAi').src = visuals.tile_ai_clean;
  document.getElementById('stageAmfCaption').textContent =
    `Raw AMF flagged ${kpis.nasa_flagged_pixels} pixels (including stationary carbonate rock clutter).`;
  document.getElementById('stageAiCaption').textContent =
    geography.is_zero_gas_trap
      ? '100% of limestone rock echoes suppressed — clean background confirmed.'
      : `Isolated ${kpis.ai_plume_pixels} true fluid plume pixels (${kpis.false_alarm_reduction_pct}% clutter reduction).`;

  // 6. Update Active Pixel Spectrum & Lab Telemetry
  applySpectrumToUI(active_spectrum);

  // 7. Update View 3 (Official Incident Dispatch Certificate)
  populateDispatchReport(data);
}

/* ==================== LEAFLET SATELLITE GIS ENGINE (+ OFFLINE FALLBACK) ==================== */
function initMapEngine() {
  const mapDiv = document.getElementById('leafletMap');
  if (!mapDiv) return;

  if (typeof window.L === 'undefined') {
    // Graceful Offline Mode if venue has zero internet for Leaflet CDN
    mapDiv.innerHTML = `
      <div id="offlineMapStage" style="width:100%;height:100%;position:relative;background:#18261E;display:flex;align-items:center;justify-content:center;">
        <img id="offlineBaseImg" style="width:100%;height:100%;object-fit:contain;opacity:0.65;image-rendering:pixelated;" alt="SWIR Base" />
        <img id="offlineOverlayImg" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;image-rendering:pixelated;" alt="AI Overlay" />
      </div>
    `;
    return;
  }

  const map = L.map('leafletMap', {
    center: [31.1279, 35.2028],
    zoom: 13,
    zoomControl: true,
    attributionControl: true,
  });

  const esriSat = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 18, attribution: 'Esri World Imagery | NASA EMIT' }
  );

  const cartoLight = L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    { maxZoom: 19, attribution: 'CartoDB Editorial Light | OpenStreetMap' }
  );

  esriSat.addTo(map);
  L.control.layers({ 'Esri Optical Satellite': esriSat, 'Editorial Light Map': cartoLight }, null, {
    position: 'bottomright'
  }).addTo(map);

  // Predictable Map Click Behavior (ZERO accidental camera hijacking!):
  //   1. When "Click Map to Scan" crosshair mode is explicitly ON -> scan that GPS coordinate on NASA!
  //   2. When clicking inside the active 7.7x7.7 km swath rectangle -> probe 40-band pixel spectrum!
  //   3. Normal map clicks outside the swath (panning, double-click zoom, closing popups) do NOT move the camera.
  //   4. Right-click anywhere on the map offers a 1-click "Scan This Location on NASA (2026 Archive)" context popup!
  map.on('click', async (e) => {
    const { lat, lng } = e.latlng;
    const lon = normalizeLon(lng);
    if (AppState.scanMapMode) {
      await scanCoordinatesOnNASA(lat, lng);
      return;
    }
    if (AppState.currentPayload) {
      const b = AppState.currentPayload.geography.swath_bounds;
      if (lat >= b[0][0] && lat <= b[1][0] && lon >= b[0][1] && lon <= b[1][1]) {
        await fetchPixelSpectrum({ lat, lon });
      }
    }
  });

  map.on('contextmenu', (e) => {
    const { lat, lng } = e.latlng;
    const lon = normalizeLon(lng);
    L.popup()
      .setLatLng([lat, lng])
      .setContent(`
        <div style="font-family:'Plus Jakarta Sans',sans-serif;min-width:205px;color:#12231A;">
          <div style="font-weight:800;font-size:12.5px;margin-bottom:4px;">GPS (${lat.toFixed(4)}°, ${lon.toFixed(4)}°)</div>
          <div style="font-size:11.5px;color:#526058;margin-bottom:7px;">Query latest 2025–2026 NASA ISS EMIT orbital swath over this coordinate:</div>
          <button type="button" onclick="scanCoordinatesOnNASA(${lat.toFixed(5)}, ${lng.toFixed(5)})"
            style="width:100%;background:#12231A;color:#FAF8F3;border:none;border-radius:6px;padding:6px 10px;font-weight:700;font-size:11.5px;cursor:pointer;">
            Scan This Spot on NASA Live
          </button>
        </div>
      `)
      .openOn(map);
  });

  AppState.leafletMap = map;
}

function updateMapOverlays(data, flyCamera) {
  const { geography, visuals, kpis, pass_info } = data;
  const bounds = geography.swath_bounds;

  // Offline Fallback Handling
  if (!AppState.leafletMap) {
    const baseImg = document.getElementById('offlineBaseImg');
    const overImg = document.getElementById('offlineOverlayImg');
    if (baseImg) baseImg.src = visuals.tile_swir_rgb;
    if (overImg) {
      overImg.src = AppState.mapLayerMode === 'nasa' ? visuals.map_nasa_overlay : visuals.map_ai_overlay;
    }
    updateMapFooterCaption(geography, kpis);
    return;
  }

  const map = AppState.leafletMap;
  const L_lib = window.L;

  // Clear previous dynamic layers
  Object.keys(AppState.layers).forEach(k => {
    if (AppState.layers[k]) {
      map.removeLayer(AppState.layers[k]);
      AppState.layers[k] = null;
    }
  });

  // 1. EMIT Swath Footprint Rectangle
  if (AppState.showSwathBounds) {
    AppState.layers.swathRect = L_lib.rectangle(bounds, {
      color: '#E7DECF',
      weight: 1.6,
      fill: false,
      dashArray: '6, 5',
    }).bindTooltip(`NASA EMIT Sensor Swath (Orbit #${pass_info.orbit}) — Click inside to probe pixel spectrum`).addTo(map);
  }

  // 1b. Authentic NASA JPL Plume Polygon Perimeter (when viewing a live NASA LP DAAC granule)
  if (data.live_nasa && Array.isArray(data.live_nasa.polygon) && data.live_nasa.polygon.length >= 3) {
    AppState.layers.nasaPolygon = L_lib.polygon(data.live_nasa.polygon, {
      color: '#38BDF8',
      weight: 1.8,
      dashArray: '4, 4',
      fillColor: '#38BDF8',
      fillOpacity: 0.06,
      interactive: false,
    }).addTo(map);
  }

  // 2. Georeferenced Overlays based on Active Layer Pill ('ai' | 'nasa' | 'both')
  if (AppState.mapLayerMode === 'nasa' || AppState.mapLayerMode === 'both') {
    AppState.layers.nasaOverlay = L_lib.imageOverlay(visuals.map_nasa_overlay, bounds, {
      opacity: 0.88,
      interactive: false,
    }).addTo(map);
  }

  if (AppState.mapLayerMode === 'ai' || AppState.mapLayerMode === 'both') {
    AppState.layers.aiOverlay = L_lib.imageOverlay(visuals.map_ai_overlay, bounds, {
      opacity: 0.90,
      interactive: false,
    }).addTo(map);
  }

  // 3. Epicenter / Verified Mineral Marker (with full Capture Date, UTC Time & Recency Status)
  const markerLat = geography.is_zero_gas_trap ? geography.center_lat : geography.source_lat;
  const markerLon = geography.is_zero_gas_trap ? geography.center_lon : geography.source_lon;
  const recBadgeTxt = pass_info.recency_badge || pass_info.year || 'ISS';
  const recBadgeBg = pass_info.is_new ? '#DC2626' : (pass_info.is_recent ? '#D4810B' : '#12231A');
  const ageNote = pass_info.age_label ? ` (${escapeHtml(pass_info.age_label)})` : '';
  const feedSrcLabel = (data.live_nasa && data.live_nasa.capture_source_label)
    ? data.live_nasa.capture_source_label
    : 'Calibrated EMIT Benchmark Granule';

  if (geography.is_zero_gas_trap) {
    const cleanIcon = L_lib.divIcon({
      className: '',
      html: '<div class="sp-map-marker-clean"><div class="sp-map-marker-clean-core"></div></div>',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    });
    AppState.layers.epicenterMarker = L_lib.marker([markerLat, markerLon], { icon: cleanIcon })
      .bindPopup(`
        <div style="font-family:'Plus Jakarta Sans',sans-serif;min-width:235px;color:#12231A;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:3px;">
            <span style="font-weight:800;color:#196B47;">Verified Zero Gas</span>
            <span style="background:${recBadgeBg};color:#FAF8F3;font-size:10px;font-weight:800;padding:1.5px 6px;border-radius:4px;">${escapeHtml(recBadgeTxt)}</span>
          </div>
          <div class="sp-popup-time-box">
            <div><b>Captured:</b> ${escapeHtml(pass_info.utc_time)}${ageNote}</div>
            <div style="font-size:11px;color:#526058;"><b>Source:</b> ${escapeHtml(feedSrcLabel)}</div>
          </div>
          <div style="font-size:12.25px;"><b>Target:</b> ${escapeHtml(pass_info.name)}</div>
          <div style="font-size:12.25px;"><b>NASA Raw Echoes:</b> ${kpis.nasa_flagged_pixels} false pixels</div>
          <div style="font-size:12.25px;"><b>SpectraPlume Verdict:</b> 0.00 kg/h (100% Rejected)</div>
        </div>
      `).addTo(map);
  } else if (geography.has_active_plume) {
    const leakIcon = L_lib.divIcon({
      className: '',
      html: '<div class="sp-map-marker-leak"><div class="sp-map-marker-leak-core"></div></div>',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    AppState.layers.epicenterMarker = L_lib.marker([markerLat, markerLon], { icon: leakIcon })
      .bindPopup(`
        <div style="font-family:'Plus Jakarta Sans',sans-serif;min-width:242px;color:#12231A;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:3px;">
            <span style="font-weight:800;color:#C0392B;">Confirmed Super-Emitter Source</span>
            <span style="background:${recBadgeBg};color:#FAF8F3;font-size:10px;font-weight:800;padding:1.5px 6px;border-radius:4px;">${escapeHtml(recBadgeTxt)}</span>
          </div>
          <div class="sp-popup-time-box">
            <div><b>Captured:</b> ${escapeHtml(pass_info.utc_time)}${ageNote}</div>
            <div style="font-size:11px;color:#526058;"><b>Source:</b> ${escapeHtml(feedSrcLabel)}</div>
          </div>
          <div style="font-size:12.25px;"><b>Facility:</b> ${escapeHtml(pass_info.facility)}</div>
          <div style="font-size:12.25px;"><b>Flux Rate:</b> ${Math.round(kpis.flux_kg_hr).toLocaleString()} kg/h (${kpis.flux_ton_hr} t/h)</div>
          <div style="font-size:12.25px;"><b>95% CI:</b> [${kpis.ci95_low_ton_hr}, ${kpis.ci95_high_ton_hr}] t/h</div>
          <div style="font-size:12.25px;"><b>Daily Loss:</b> $${Math.round(kpis.daily_loss_usd).toLocaleString()}/day</div>
        </div>
      `).addTo(map);
  }

  // 4. Wind Transport Vector Line
  if (AppState.showWindVector && geography.has_active_plume) {
    // Wind direction is meteorological FROM azimuth; transport blows TOWARD (dir + 180)
    const advectRad = (((kpis.wind_direction_deg + 180) % 360) * Math.PI) / 180.0;
    const dLat = Math.cos(advectRad) * 0.018;
    const dLon = Math.sin(advectRad) * 0.021;
    AppState.layers.windLine = L_lib.polyline(
      [[markerLat, markerLon], [markerLat + dLat, markerLon + dLon]],
      { color: '#FDE047', weight: 2.4, dashArray: '5, 5' }
    ).bindTooltip(`Wind Transport Axis (${kpis.wind_speed_m_s} m/s)`).addTo(map);
  }

  if (flyCamera) {
    map.flyTo([geography.center_lat, geography.center_lon], pass_info.zoom || 13, {
      duration: 0.95,
    });
    if (AppState.layers.epicenterMarker) {
      setTimeout(() => {
        if (AppState.layers.epicenterMarker) {
          AppState.layers.epicenterMarker.openPopup();
        }
      }, 980);
    }
  }

  updateMapFooterCaption(geography, kpis);
}

function setMapLayerMode(mode, btnEl) {
  AppState.mapLayerMode = mode;
  document.querySelectorAll('#mapLayerSwitcher .seg-pill').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
  if (AppState.currentPayload) {
    updateMapOverlays(AppState.currentPayload, false);
  }
}

function updateMapFooterCaption(geography, kpis) {
  const el = document.getElementById('mapLayerStatusText');
  if (!el) return;
  if (AppState.mapLayerMode === 'ai') {
    el.textContent = geography.is_zero_gas_trap
      ? 'SpectraPlume AI Layer: 0 Gas — Stationary Limestone Confirmed (Click swath to inspect pixel)'
      : 'SpectraPlume AI Layer: Clean Segmented Methane Plume (Click swath to inspect pixel)';
  } else if (AppState.mapLayerMode === 'nasa') {
    el.textContent = `NASA Raw Filter Layer: Showing ${kpis.rejected_clutter_pixels} False-Positive Carbonate Rock Pixels (Violet)`;
  } else {
    el.textContent = 'Dual Comparison: Amber/Red = True Gas Plume | Violet = Rejected NASA Mineral False Alarms';
  }
}

/* ==================== LIVE 40-BAND PIXEL SPECTROSCOPY ==================== */
async function selectDiagnosticPreset(presetKey, btnEl) {
  if (!AppState.currentPayload) return;
  AppState.activePreset = presetKey;
  document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  const coords = AppState.currentPayload.presets[presetKey];
  if (coords) {
    await fetchPixelSpectrum({ x: coords.x, y: coords.y });
  }
}

async function handleSwirCubeClick(event) {
  if (!AppState.currentPayload) return;
  const wrap = event.currentTarget;
  const rect = wrap.getBoundingClientRect();
  const relX = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
  const relY = Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height));

  const W = AppState.currentPayload.geography.grid_width || 128;
  const H = AppState.currentPayload.geography.grid_height || 128;
  const px = Math.min(W - 1, Math.floor(relX * W));
  const py = Math.min(H - 1, Math.floor(relY * H));

  document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
  await fetchPixelSpectrum({ x: px, y: py });
}

async function fetchPixelSpectrum(params) {
  const qs = new URLSearchParams({ pass_id: AppState.activePassId });
  if (params.x !== undefined && params.y !== undefined) {
    qs.set('x', params.x);
    qs.set('y', params.y);
  } else if (params.lat !== undefined && params.lon !== undefined) {
    qs.set('lat', params.lat);
    qs.set('lon', params.lon);
  }

  try {
    const res = await fetch(`/api/pixel-spectrum?${qs.toString()}`);
    if (!res.ok) return;
    const spec = await res.json();
    AppState.currentPayload.active_spectrum = spec;
    applySpectrumToUI(spec);
  } catch (_) {}
}

function applySpectrumToUI(spec) {
  if (!spec) return;
  const pillClass =
    spec.classification_type === 'methane_plume' ? 'pill-leak' :
    spec.classification_type === 'mineral_false_alarm' ? 'pill-safe' : 'pill-amber';

  // View 1 Right Proof Card
  const b1 = document.getElementById('miniProofBadge');
  b1.className = `status-pill ${pillClass}`;
  b1.textContent = spec.badge;
  document.getElementById('miniProofTitle').textContent = spec.title;
  document.getElementById('miniProofExplain').textContent = spec.explanation;
  document.getElementById('miniPixelCoords').textContent =
    `Pixel (${spec.x}, ${spec.y}) • ${spec.alpha_ppm_m} ppm·m • AI Conf: ${spec.ai_confidence_pct}%`;

  // View 2 Lab Telemetry Card & Crosshair Pin
  const b2 = document.getElementById('labClassBadge');
  b2.className = `status-pill ${pillClass}`;
  b2.textContent = spec.badge;
  document.getElementById('labClassTitle').textContent = spec.title;
  document.getElementById('labClassExplain').textContent = spec.explanation;
  document.getElementById('labPxXY').textContent = `(${spec.x}, ${spec.y})`;
  document.getElementById('labPxGPS').textContent = `${spec.lat.toFixed(4)}°, ${spec.lon.toFixed(4)}°`;
  document.getElementById('labPxAlpha').textContent = `${spec.alpha_ppm_m} ppm·m`;
  document.getElementById('labPxSnr').textContent = `${spec.snr}`;
  document.getElementById('labPxConf').textContent = `${spec.ai_confidence_pct}%`;

  const pin = document.getElementById('swirCrosshairPin');
  if (pin && AppState.currentPayload) {
    const W = AppState.currentPayload.geography.grid_width || 128;
    const H = AppState.currentPayload.geography.grid_height || 128;
    pin.style.left = `${((spec.x + 0.5) / W) * 100}%`;
    pin.style.top = `${((spec.y + 0.5) / H) * 100}%`;
  }

  // Sync live spectrometer probe ring on the Leaflet satellite map
  if (AppState.leafletMap && window.L && spec.lat && spec.lon) {
    if (AppState.layers.probeMarker) {
      AppState.leafletMap.removeLayer(AppState.layers.probeMarker);
      AppState.layers.probeMarker = null;
    }
    const ringColor =
      spec.classification_type === 'methane_plume' ? '#D4810B' :
      spec.classification_type === 'mineral_false_alarm' ? '#196B47' : '#12231A';
    AppState.layers.probeMarker = window.L.circleMarker([spec.lat, spec.lon], {
      radius: 8,
      color: '#FFFFFF',
      weight: 2.2,
      fillColor: ringColor,
      fillOpacity: 0.88,
    }).bindTooltip(`Spectrometer Probe (${spec.x}, ${spec.y}) • ${spec.badge}`).addTo(AppState.leafletMap);
  }

  renderAllCharts(spec);
}

/* ==================== HIGH-DPI HTML5 CANVAS SPECTRAL CHARTS ==================== */
function renderAllCharts(spec) {
  drawDeficitChart('miniSpectrumCanvas', spec, 175);
  drawReflectanceChart('labReflectanceCanvas', spec, 195);
  drawDeficitChart('labDeficitCanvas', spec, 205);
}

function setupHiDPICanvas(canvasId, cssHeight) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !canvas.parentElement) return null;
  const dpr = window.devicePixelRatio || 1;
  // Never lock canvas.style.width to a fixed pixel string — keep 100% fluid so CSS Grid shrinks cleanly!
  canvas.style.width = '100%';
  canvas.style.height = cssHeight + 'px';
  const measured = canvas.getBoundingClientRect().width || (canvas.parentElement.clientWidth - 18);
  const cssWidth = Math.max(180, Math.floor(measured));
  canvas.width = Math.floor(cssWidth * dpr);
  canvas.height = Math.floor(cssHeight * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, w: cssWidth, h: cssHeight };
}

function drawDeficitChart(canvasId, spec, heightPx) {
  const setup = setupHiDPICanvas(canvasId, heightPx);
  if (!setup) return;
  const { ctx, w, h } = setup;
  const pad = { l: 44, r: 14, t: 16, b: 26 };
  const pw = w - pad.l - pad.r;
  const ph = h - pad.t - pad.b;

  ctx.clearRect(0, 0, w, h);

  const wl = spec.wavelengths;
  const def = spec.absorption_deficit;
  const ch4 = spec.hitran_ch4_reference;
  const cal = spec.calcite_caco3_reference;

  const minWl = wl[0];
  const maxWl = wl[wl.length - 1];
  const allVals = [...def, ...ch4, ...cal, 0];
  const minY = Math.min(-0.004, ...allVals) * 1.12;
  const maxY = Math.max(0.016, ...allVals) * 1.15;

  const xOf = (val) => pad.l + ((val - minWl) / (maxWl - minWl)) * pw;
  const yOf = (val) => pad.t + ph - ((val - minY) / (maxY - minY + 1e-9)) * ph;

  // Shaded diagnostic wavelength bands (2260 nm, 2315 nm, 2335 nm)
  const bands = [
    { wl: 2260, color: 'rgba(212, 129, 11, 0.12)', line: '#D4810B', label: '2260 CH4' },
    { wl: 2315, color: 'rgba(192, 57, 43, 0.12)', line: '#C0392B', label: '2315 CH4' },
    { wl: 2335, color: 'rgba(25, 107, 71, 0.10)', line: '#53625A', label: '2335 CaCO3' },
  ];

  bands.forEach(b => {
    const bx = xOf(b.wl);
    ctx.fillStyle = b.color;
    ctx.fillRect(bx - 7, pad.t, 14, ph);
    ctx.save();
    ctx.strokeStyle = b.line;
    ctx.setLineDash([3, 3]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(bx, pad.t);
    ctx.lineTo(bx, pad.t + ph);
    ctx.stroke();
    ctx.restore();

    ctx.fillStyle = b.line;
    ctx.font = '600 10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(b.wl + 'nm', bx, h - 7);
  });

  // Zero baseline
  ctx.strokeStyle = '#D2C5BA';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad.l, yOf(0));
  ctx.lineTo(pad.l + pw, yOf(0));
  ctx.stroke();

  // Helper to plot series
  const plotSeries = (arr, color, width, dash = []) => {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.setLineDash(dash);
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();
    arr.forEach((v, i) => {
      const px = xOf(wl[i]);
      const py = yOf(v);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    ctx.restore();
  };

  // 1. Calcite Reference (dashed muted)
  plotSeries(cal, '#8A7E72', 1.6, [4, 4]);
  // 2. HITRAN CH4 Reference (dotted forest)
  plotSeries(ch4, '#1E3F2F', 1.8, [2, 3]);
  // 3. Measured Pixel Absorption Depth (bold primary curve)
  const mainColor =
    spec.classification_type === 'methane_plume' ? '#D4810B' :
    spec.classification_type === 'mineral_false_alarm' ? '#196B47' : '#12231A';
  plotSeries(def, mainColor, 2.7, []);

  // Y-axis labels
  ctx.fillStyle = '#6A776F';
  ctx.font = '500 10px "JetBrains Mono", monospace';
  ctx.textAlign = 'right';
  ctx.fillText(maxY.toFixed(3), pad.l - 6, pad.t + 9);
  ctx.fillText('0.000', pad.l - 6, yOf(0) + 3);
}

function drawReflectanceChart(canvasId, spec, heightPx) {
  const setup = setupHiDPICanvas(canvasId, heightPx);
  if (!setup) return;
  const { ctx, w, h } = setup;
  const pad = { l: 44, r: 14, t: 16, b: 24 };
  const pw = w - pad.l - pad.r;
  const ph = h - pad.t - pad.b;

  ctx.clearRect(0, 0, w, h);

  const wl = spec.wavelengths;
  const pxArr = spec.pixel_reflectance;
  const bgArr = spec.scene_mean_reflectance;
  const minWl = wl[0];
  const maxWl = wl[wl.length - 1];
  const all = [...pxArr, ...bgArr];
  const minY = Math.min(...all) * 0.94;
  const maxY = Math.max(...all) * 1.04;

  const xOf = (val) => pad.l + ((val - minWl) / (maxWl - minWl)) * pw;
  const yOf = (val) => pad.t + ph - ((val - minY) / (maxY - minY + 1e-9)) * ph;

  // Grid lines
  ctx.strokeStyle = '#E4DBCF';
  ctx.lineWidth = 1;
  [0.25, 0.5, 0.75].forEach(f => {
    const gy = pad.t + ph * f;
    ctx.beginPath();
    ctx.moveTo(pad.l, gy);
    ctx.lineTo(pad.l + pw, gy);
    ctx.stroke();
  });

  // Scene Mean Continuum (Dashed)
  ctx.save();
  ctx.strokeStyle = '#7A867E';
  ctx.lineWidth = 1.8;
  ctx.setLineDash([5, 4]);
  ctx.beginPath();
  bgArr.forEach((v, i) => {
    const x = xOf(wl[i]), y = yOf(v);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.restore();

  // Measured Pixel Reflectance (Solid Forest)
  ctx.strokeStyle = '#12231A';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  pxArr.forEach((v, i) => {
    const x = xOf(wl[i]), y = yOf(v);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = '#6A776F';
  ctx.font = '500 10px "JetBrains Mono", monospace';
  ctx.textAlign = 'right';
  ctx.fillText(maxY.toFixed(2), pad.l - 6, pad.t + 9);
  ctx.fillText(minY.toFixed(2), pad.l - 6, pad.t + ph);

  ctx.textAlign = 'center';
  [2150, 2250, 2315, 2400, 2450].forEach(tick => {
    ctx.fillText(tick + 'nm', xOf(tick), h - 6);
  });
}

/* ==================== CUSTOM DROPDOWNS, SLIDERS & SWITCHES ==================== */
function toggleDropdown(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const open = el.classList.contains('open');
  document.querySelectorAll('.sp-dropdown').forEach(d => d.classList.remove('open'));
  if (!open) el.classList.add('open');
}

function initDropdownDismiss() {
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.sp-dropdown')) {
      document.querySelectorAll('.sp-dropdown').forEach(d => d.classList.remove('open'));
    }
  });
}

function selectRetrievalMode(mode, label, optEl) {
  AppState.retrievalMode = mode;
  document.getElementById('ddRetrievalLabel').textContent = label;
  const dd = document.getElementById('ddRetrieval');
  dd.querySelectorAll('.sp-dropdown-option').forEach(o => o.classList.remove('selected'));
  if (optEl) optEl.classList.add('selected');
  dd.classList.remove('open');
  runAnalysis(AppState.activePassId, false);
}

function selectWindMode(mode, label, optEl) {
  AppState.windMode = mode;
  document.getElementById('ddWindLabel').textContent = label;
  const dd = document.getElementById('ddWind');
  dd.querySelectorAll('.sp-dropdown-option').forEach(o => o.classList.remove('selected'));
  if (optEl) optEl.classList.add('selected');
  dd.classList.remove('open');

  document.getElementById('customWindControls').style.display = mode === 'custom' ? 'block' : 'none';
  runAnalysis(AppState.activePassId, false);
}

function onThresholdSlide(slider) {
  const val = parseFloat(slider.value) / 100.0;
  AppState.maskThreshold = val;
  updateRangeFill(slider);
  let tag = 'Balanced';
  if (val < 0.42) tag = 'High Sensitivity';
  else if (val > 0.68) tag = 'Strict Core';
  document.getElementById('threshLabelVal').textContent = `${val.toFixed(2)} (${tag})`;
  scheduleReanalysis();
}

function onCustomWindSlide() {
  const ws = document.getElementById('windSpeedSlider');
  const wd = document.getElementById('windDirSlider');
  AppState.customWindSpeed = parseFloat(ws.value);
  AppState.customWindDir = parseFloat(wd.value);
  updateRangeFill(ws);
  updateRangeFill(wd);
  document.getElementById('windSpeedLabel').textContent = `${AppState.customWindSpeed.toFixed(1)} m/s`;
  document.getElementById('windDirLabel').textContent = `${Math.round(AppState.customWindDir)}°`;
  scheduleReanalysis();
}

function updateRangeFill(slider) {
  const pct = ((slider.value - slider.min) / (slider.max - slider.min)) * 100;
  slider.style.background = `linear-gradient(to right, var(--sp-amber-500) 0%, var(--sp-amber-500) ${pct}%, var(--sp-bg-sand) ${pct}%, var(--sp-bg-sand) 100%)`;
}

function toggleMapOption(optionKey, rowEl) {
  rowEl.classList.toggle('checked');
  AppState[optionKey] = rowEl.classList.contains('checked');
  if (AppState.currentPayload) {
    updateMapOverlays(AppState.currentPayload, false);
  }
}

/* ==================== DISPATCH REPORT & EXPORT ==================== */
function populateDispatchReport(data) {
  const { pass_info, kpis, geography } = data;
  const isLeak = !geography.is_zero_gas_trap && kpis.flux_kg_hr >= 85;

  const badge = document.getElementById('repStatusPill');
  badge.className = 'status-pill ' + (isLeak ? 'pill-leak' : 'pill-safe');
  badge.textContent = isLeak ? 'Immediate Mitigation Required' : 'In Compliance • Zero Leak';

  document.getElementById('repFacility').textContent = `${pass_info.name} — ${pass_info.facility}`;
  document.getElementById('repOrbit').textContent = `ISS EMIT Orbit #${pass_info.orbit} (${pass_info.utc_time})`;
  document.getElementById('repCoords').textContent = `${geography.source_lat.toFixed(5)}°, ${geography.source_lon.toFixed(5)}°`;
  document.getElementById('repFlux').textContent =
    geography.is_zero_gas_trap
      ? '0.0 kg/h (0.00 Tons/hr)'
      : `${kpis.flux_kg_hr.toLocaleString()} kg/h (${kpis.flux_ton_hr} ± ${kpis.flux_uncertainty_ton_hr} t/h)`;
  document.getElementById('repCI').textContent = `[${kpis.ci95_low_ton_hr}, ${kpis.ci95_high_ton_hr}] Tons/hr (95% CI)`;
  document.getElementById('repMass').textContent =
    geography.is_zero_gas_trap
      ? '0.0 kg (0.000 km²)'
      : `${kpis.ime_kg} kg • L = ${Math.round(kpis.plume_length_m)} m (${kpis.plume_area_km2} km²)`;

  const kinEl = document.getElementById('repKinematics');
  if (kinEl) {
    kinEl.textContent = geography.is_zero_gas_trap
      ? 'Stationary Strata (0.00 m/s advection)'
      : `U_eff = ${kpis.effective_wind_speed_m_s} m/s • Azimuth ${kpis.plume_azimuth_deg}° (${kpis.wind_alignment_pct}% wind match)`;
  }

  const climEl = document.getElementById('repClimate');
  if (climEl) {
    climEl.textContent = geography.is_zero_gas_trap
      ? '0.0 tCO2e / hr (IPCC AR6)'
      : `${kpis.co2e_ton_hr} tCO2e / hr (IPCC AR6 20-Yr)`;
  }

  document.getElementById('repFalseAlarm').textContent =
    `${kpis.false_alarm_reduction_pct}% (${kpis.rejected_clutter_pixels} rock pixels rejected)`;
  document.getElementById('repLoss').textContent =
    `$${kpis.daily_loss_usd.toLocaleString()} / day ($${kpis.annual_loss_usd.toLocaleString()} / yr)`;
}

async function downloadOfficialJSON() {
  try {
    const res = await fetch(`/api/report/${AppState.activePassId}`);
    const report = await res.json();
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `SpectraPlume_Dispatch_${AppState.activePassId}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Official Regulatory JSON Report downloaded.');
  } catch (_) {
    showToast('Could not generate JSON report.');
  }
}

/* ==================== UPLOAD MODAL & HUMAN-FRIENDLY ERROR RECOVERY ==================== */
function openUploadModal() {
  document.getElementById('uploadErrorCard').style.display = 'none';
  document.getElementById('uploadProgressText').style.display = 'none';
  document.getElementById('uploadModalBackdrop').classList.add('open');
}

function closeUploadModal() {
  document.getElementById('uploadModalBackdrop').classList.remove('open');
}

function initUploadDragDrop() {
  const dz = document.getElementById('modalDropzone');
  if (!dz) return;
  dz.addEventListener('dragover', (e) => {
    e.preventDefault();
    dz.classList.add('dragover');
  });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', async (e) => {
    e.preventDefault();
    dz.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadGranuleFile(e.dataTransfer.files[0]);
    }
  });
}

async function onGranuleFileSelected(input) {
  if (input.files && input.files[0]) {
    await uploadGranuleFile(input.files[0]);
    input.value = '';
  }
}

async function uploadGranuleFile(fileObj) {
  const errBox = document.getElementById('uploadErrorCard');
  const prog = document.getElementById('uploadProgressText');
  errBox.style.display = 'none';
  prog.style.display = 'block';
  prog.textContent = `Analyzing '${fileObj.name}' via Spatial-Spectral 3D-CNN...`;

  const formData = new FormData();
  formData.append('file', fileObj);

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const payload = await res.json();
    prog.style.display = 'none';

    if (!res.ok) {
      errBox.style.display = 'block';
      document.getElementById('uploadErrTitle').textContent = payload.error_title || 'Invalid Granule File';
      document.getElementById('uploadErrMsg').textContent = payload.error_message || 'Unable to parse hyperspectral cube.';
      document.getElementById('uploadErrHint').textContent = payload.suggestion || '';
      return;
    }

    // Valid granule ingested! Refresh pass feed & display immediately
    closeUploadModal();
    const passesRes = await fetch('/api/passes');
    const passesData = await passesRes.json();
    AppState.passes = passesData.passes || [];
    AppState.feedMode = 'benchmarks';
    syncFeedTabUI();
    AppState.activePassId = payload.pass_info.pass_id;
    AppState.currentPayload = payload;
    renderPassFeed();
    applyPayloadToUI(payload, true);
    showToast(`Granule '${fileObj.name}' analyzed successfully.`);
  } catch (_) {
    prog.style.display = 'none';
    errBox.style.display = 'block';
    document.getElementById('uploadErrTitle').textContent = 'Upload Interrupted';
    document.getElementById('uploadErrMsg').textContent = 'Could not transmit file to local processing engine.';
    document.getElementById('uploadErrHint').textContent = 'Check that the local server is running and file size is under 200 MB.';
  }
}

/* ==================== UTILITIES ==================== */
function showToast(msg) {
  const t = document.getElementById('spToast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(window._spToastTimer);
  window._spToastTimer = setTimeout(() => t.classList.remove('show'), 2600);
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
