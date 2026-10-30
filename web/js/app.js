/* ==========================================================================
   SpectraPlume 2.0 — Mission Console Application Controller (ES6)
   Connects Native Editorial Light UI to Python FastAPI + PyTorch 3D-CNN Backend
   Zero Emojis • Real-Time Leaflet GIS • Live 40-Band Pixel Spectroscopy
   ========================================================================== */

const AppState = {
  passes: [],
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
  layers: {
    aiOverlay: null,
    nasaOverlay: null,
    swathRect: null,
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
  await loadPassesAndBoot();
  window.addEventListener('resize', () => {
    if (AppState.currentPayload && AppState.currentPayload.active_spectrum) {
      renderAllCharts(AppState.currentPayload.active_spectrum);
    }
    if (AppState.leafletMap) {
      AppState.leafletMap.invalidateSize();
    }
  });
});

async function loadPassesAndBoot() {
  try {
    const res = await fetch('/api/passes');
    const data = await res.json();
    AppState.passes = data.passes || [];
    updateConnectionBadge(data.earthdata_connected);
    renderPassFeed();
    await runAnalysis(AppState.activePassId, true);
  } catch (err) {
    showToast('Unable to reach local SpectraPlume engine. Retrying...');
  }
}

function updateConnectionBadge(hasLiveToken) {
  const txt = document.getElementById('connBadgeText');
  if (!txt) return;
  txt.textContent = hasLiveToken
    ? 'NASA LP DAAC • Live Connected'
    : 'ISS EMIT Suite • Active';
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
function renderPassFeed() {
  const container = document.getElementById('passFeedList');
  if (!container) return;
  const countEl = document.getElementById('passCountLabel');
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
      <div class="pass-card ${isActive ? 'active' : ''}" onclick="selectOrbitalPass('${p.pass_id}')">
        <div class="pass-card-top">
          <span class="pass-orbit-tag">ISS Orbit #${escapeHtml(p.orbit)}</span>
          <span class="status-pill ${pillClass}">${escapeHtml(p.badge_label)}</span>
        </div>
        <div class="pass-title">${escapeHtml(p.name)}</div>
        <div class="pass-facility">${escapeHtml(p.facility)}</div>
        <div class="pass-telemetry-row">
          <span>Flux: ${fluxText}</span>
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
  const body = {
    pass_id: passId || AppState.activePassId,
    mask_threshold: AppState.maskThreshold,
    retrieval_mode: AppState.retrievalMode,
    wind_speed: AppState.windMode === 'custom' ? AppState.customWindSpeed : null,
    wind_direction: AppState.windMode === 'custom' ? AppState.customWindDir : null,
  };

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error('Analysis request failed');
    const payload = await res.json();
    AppState.currentPayload = payload;
    applyPayloadToUI(payload, flyCamera);
  } catch (err) {
    showToast('Error analyzing granule. Please verify server connection.');
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

  // 3. Map Telemetry Chips
  const latDir = geography.source_lat >= 0 ? 'N' : 'S';
  const lonDir = geography.source_lon >= 0 ? 'E' : 'W';
  document.getElementById('mapCoordText').textContent =
    `${Math.abs(geography.source_lat).toFixed(4)}° ${latDir}, ${Math.abs(geography.source_lon).toFixed(4)}° ${lonDir}`;
  document.getElementById('mapWindText').textContent =
    `${kpis.wind_speed_m_s} m/s @ ${kpis.wind_direction_deg}°`;

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

  // Click anywhere inside the swath to inspect that pixel's 40-band spectrum live!
  map.on('click', async (e) => {
    if (!AppState.currentPayload) return;
    const b = AppState.currentPayload.geography.swath_bounds;
    const { lat, lng } = e.latlng;
    if (lat >= b[0][0] && lat <= b[1][0] && lng >= b[0][1] && lng <= b[1][1]) {
      await fetchPixelSpectrum({ lat, lon: lng });
    }
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

  // 3. Epicenter / Verified Mineral Marker
  const markerLat = geography.is_zero_gas_trap ? geography.center_lat : geography.source_lat;
  const markerLon = geography.is_zero_gas_trap ? geography.center_lon : geography.source_lon;

  if (geography.is_zero_gas_trap) {
    const cleanIcon = L_lib.divIcon({
      className: '',
      html: '<div class="sp-map-marker-clean"><div class="sp-map-marker-clean-core"></div></div>',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    });
    AppState.layers.epicenterMarker = L_lib.marker([markerLat, markerLon], { icon: cleanIcon })
      .bindPopup(`
        <div style="font-family:'Plus Jakarta Sans',sans-serif;min-width:210px;color:#12231A;">
          <div style="font-weight:800;color:#196B47;margin-bottom:4px;">Verified Zero Gas (Limestone)</div>
          <div style="font-size:12.5px;"><b>Target:</b> ${escapeHtml(pass_info.name)}</div>
          <div style="font-size:12.5px;"><b>NASA Raw Echoes:</b> ${kpis.nasa_flagged_pixels} false pixels</div>
          <div style="font-size:12.5px;"><b>SpectraPlume Verdict:</b> 0.00 kg/h (100% Rejected)</div>
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
        <div style="font-family:'Plus Jakarta Sans',sans-serif;min-width:220px;color:#12231A;">
          <div style="font-weight:800;color:#C0392B;margin-bottom:4px;">Confirmed Super-Emitter Source</div>
          <div style="font-size:12.5px;"><b>Facility:</b> ${escapeHtml(pass_info.facility)}</div>
          <div style="font-size:12.5px;"><b>Flux Rate:</b> ${Math.round(kpis.flux_kg_hr).toLocaleString()} kg/h (${kpis.flux_ton_hr} t/h)</div>
          <div style="font-size:12.5px;"><b>95% CI:</b> [${kpis.ci95_low_ton_hr}, ${kpis.ci95_high_ton_hr}] t/h</div>
          <div style="font-size:12.5px;"><b>Daily Loss:</b> $${Math.round(kpis.daily_loss_usd).toLocaleString()}/day</div>
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
  document.getElementById('labPxXY').textContent = `X = ${spec.x}, Y = ${spec.y}`;
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
  if (!canvas) return null;
  const dpr = window.devicePixelRatio || 1;
  const cssWidth = Math.max(260, canvas.parentElement.clientWidth - 20);
  canvas.style.width = cssWidth + 'px';
  canvas.style.height = cssHeight + 'px';
  canvas.width = Math.floor(cssWidth * dpr);
  canvas.height = Math.floor(cssHeight * dpr);
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
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
  document.getElementById('repMass').textContent = `${kpis.ime_kg} kg across ${kpis.plume_area_km2} km²`;
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
