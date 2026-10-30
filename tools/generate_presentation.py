"""
generate_presentation.py
Rebuilds the presentation with MINIMAL text, ZERO clutter, HUGE numbers,
vector graphics, and exact alignment with the ISEF presentation script.
"""

from pathlib import Path

OUTPUT_FILE = Path("docs/presentation/index.html")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

HTML_CONTENT = r'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SpectraPlume — Regeneron ISEF 2027</title>
  
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@500;700;800;900&family=JetBrains+Mono:wght@600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet" />

  <style>
    :root {
      /* Editorial Warm Light Canvas */
      --sp-bg-canvas: #F6F3EC;
      --sp-bg-sand: #E7DECF;
      --sp-bg-sand-soft: #EFE9DD;
      --sp-bg-card: #FFFFFF;
      --sp-border: #D2C5BA;
      --sp-border-subtle: #E3D9CD;

      /* Deep Authority Forest Dark */
      --sp-forest-950: #0B1711;
      --sp-forest-900: #12231A;
      --sp-forest-800: #1A3326;
      --sp-forest-700: #234735;
      
      /* Inks */
      --sp-ink-primary: #12231A;
      --sp-ink-secondary: #43534A;
      --sp-ink-muted: #6B7870;

      /* SWIR Signature Amber */
      --sp-amber-600: #B86D07;
      --sp-amber-500: #D4810B;
      --sp-amber-400: #E5982A;
      --sp-amber-100: #FEF6E9;
      --sp-amber-border: #ECCB98;

      /* Status */
      --sp-danger-600: #C0392B;
      --sp-danger-bg: #FDF2F0;
      --sp-danger-border: #EABCB5;
      --sp-safe-600: #196B47;
      --sp-safe-bg: #EDF7F2;
      --sp-safe-border: #B7DFC9;

      /* Fonts */
      --font-arabic: 'Cairo', sans-serif;
      --font-display: 'Plus Jakarta Sans', 'Cairo', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;

      /* Shadows */
      --shadow-card: 0 4px 14px rgba(18, 35, 26, 0.05), 0 1px 3px rgba(18, 35, 26, 0.03);
      --shadow-float: 0 14px 34px rgba(18, 35, 26, 0.09);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }

    html, body {
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background-color: var(--sp-forest-950);
      color: var(--sp-ink-primary);
      font-family: var(--font-arabic);
      user-select: none;
    }

    /* Deck Viewport */
    .deck-viewport {
      width: 100vw;
      height: 100vh;
      display: flex;
      flex-direction: column;
      background: var(--sp-bg-canvas);
      position: relative;
    }

    /* Minimalist Topbar */
    .deck-topbar {
      height: 52px;
      background: var(--sp-forest-900);
      border-bottom: 1.5px solid rgba(212, 129, 11, 0.35);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      color: #FAF8F3;
      z-index: 100;
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }

    .brand-svg {
      width: 30px;
      height: 30px;
    }

    .brand-title {
      font-family: var(--font-display);
      font-weight: 800;
      font-size: 18px;
      color: #FFFFFF;
      letter-spacing: -0.02em;
    }

    .slide-dots {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .dot-pill {
      height: 6px;
      width: 22px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.2);
      cursor: pointer;
      transition: all 0.25s ease;
    }

    .dot-pill.active {
      width: 44px;
      background: var(--sp-amber-500);
    }

    .top-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .timer-pill {
      font-family: var(--font-mono);
      font-size: 13px;
      padding: 3px 10px;
      border-radius: 999px;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #D2DDD6;
    }

    .top-btn {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.16);
      color: #FAF8F3;
      padding: 4px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;
      font-family: var(--font-arabic);
    }

    .top-btn:hover {
      background: rgba(255, 255, 255, 0.18);
    }

    .top-btn.active-mode {
      background: var(--sp-amber-500);
      border-color: var(--sp-amber-400);
      color: #FFFFFF;
    }

    /* Main Stage */
    .deck-stage {
      flex: 1;
      position: relative;
      width: 100%;
      height: calc(100vh - 52px - 44px);
      overflow: hidden;
    }

    .slide {
      position: absolute;
      inset: 0;
      opacity: 0;
      pointer-events: none;
      transform: scale(0.985);
      transition: opacity 0.35s ease, transform 0.35s ease;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 24px 44px 16px;
      overflow: hidden;
    }

    .slide.active {
      opacity: 1;
      pointer-events: all;
      transform: scale(1);
      z-index: 10;
    }

    /* Header in Slide */
    .slide-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
    }

    .slide-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 800;
      padding: 4px 12px;
      border-radius: 999px;
      background: var(--sp-bg-sand);
      color: var(--sp-forest-900);
      border: 1px solid var(--sp-border);
      letter-spacing: 0.02em;
    }

    .slide-badge-dark {
      background: rgba(212, 129, 11, 0.15);
      color: var(--sp-amber-400);
      border-color: rgba(212, 129, 11, 0.35);
    }

    .citations-strip {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .cite-pill {
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 6px;
      background: #FFFFFF;
      border: 1px solid var(--sp-border);
      color: var(--sp-forest-900);
    }

    .cite-pill-dark {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.15);
      color: #FAF8F3;
    }

    .cite-pill strong {
      color: var(--sp-amber-600);
    }

    .cite-pill-dark strong {
      color: var(--sp-amber-400);
    }

    /* SLIDE 1: Cover & Scenario Hook */
    #slide-1 {
      background: radial-gradient(circle at 75% 25%, #183023 0%, #101F17 55%, #0B1711 100%);
      color: #FAF8F3;
    }

    .slide1-layout {
      display: grid;
      grid-template-columns: 1.25fr 0.9fr;
      gap: 36px;
      align-items: center;
      margin: auto 0;
    }

    .hero-h1 {
      font-size: 68px;
      font-weight: 900;
      line-height: 1;
      letter-spacing: -0.03em;
      color: #FFFFFF;
      margin-bottom: 6px;
    }

    .hero-h2 {
      font-size: 22px;
      font-weight: 700;
      color: var(--sp-amber-400);
      margin-bottom: 22px;
    }

    .hero-hook-banner {
      background: rgba(255, 255, 255, 0.05);
      border-right: 4.5px solid var(--sp-amber-500);
      padding: 18px 22px;
      border-radius: 0 14px 14px 0;
      font-size: 21px;
      font-weight: 700;
      line-height: 1.5;
      color: #FAF8F3;
      margin-bottom: 24px;
    }

    .hero-hook-banner strong {
      color: var(--sp-amber-400);
    }

    .team-badges-row {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .team-pill {
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(18, 35, 26, 0.85);
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 8px 16px;
      border-radius: 12px;
    }

    .team-dot {
      width: 14px;
      height: 14px;
      border-radius: 50%;
    }

    .team-dot.fares { background: #3B82F6; box-shadow: 0 0 8px #3B82F6; }
    .team-dot.shnawy { background: #10B981; box-shadow: 0 0 8px #10B981; }

    /* SLIDE 2: Problem & Citations */
    .stat-cards-trio {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 22px;
      margin: 10px 0 18px;
    }

    .stat-card-bold {
      background: #FFFFFF;
      border: 1.5px solid var(--sp-border);
      border-radius: 18px;
      padding: 22px 20px;
      box-shadow: var(--shadow-card);
      position: relative;
    }

    .stat-card-bold.amber { border-top: 5px solid var(--sp-amber-500); }
    .stat-card-bold.danger { border-top: 5px solid var(--sp-danger-600); }
    .stat-card-bold.safe { border-top: 5px solid var(--sp-safe-600); }

    .stat-huge-num {
      font-family: var(--font-mono);
      font-size: 64px;
      font-weight: 900;
      line-height: 1;
      margin: 8px 0;
    }

    .stat-huge-num.amber { color: var(--sp-amber-600); }
    .stat-huge-num.danger { color: var(--sp-danger-600); }
    .stat-huge-num.safe { color: var(--sp-safe-600); }

    .stat-card-title {
      font-size: 18px;
      font-weight: 900;
      color: var(--sp-forest-900);
      margin-bottom: 4px;
    }

    .stat-card-sub {
      font-size: 13.5px;
      color: var(--sp-ink-secondary);
      font-weight: 600;
    }

    .two-flaws-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }

    .flaw-strip {
      background: var(--sp-bg-card);
      border: 1.5px solid var(--sp-border);
      border-radius: 14px;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .flaw-icon {
      font-size: 24px;
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .flaw-icon.red { background: var(--sp-danger-bg); color: var(--sp-danger-600); }
    .flaw-icon.amber { background: var(--sp-amber-100); color: var(--sp-amber-600); }

    .flaw-title {
      font-size: 15.5px;
      font-weight: 800;
      color: var(--sp-forest-900);
    }

    .flaw-sub {
      font-size: 13px;
      color: var(--sp-ink-secondary);
      margin-top: 2px;
    }

    /* SLIDE 3: Physics & Innovation */
    .physics-grid-clean {
      display: grid;
      grid-template-columns: 1.15fr 0.95fr;
      gap: 24px;
      align-items: stretch;
      flex: 1;
      margin-top: 8px;
    }

    .spectrum-box-clean {
      background: #FFFFFF;
      border: 1.5px solid var(--sp-border);
      border-radius: 18px;
      padding: 18px 20px;
      box-shadow: var(--shadow-card);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .spectrum-legend-clean {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .two-innovations-col {
      display: flex;
      flex-direction: column;
      gap: 16px;
      justify-content: space-between;
    }

    .innov-card {
      background: #FFFFFF;
      border: 1.5px solid var(--sp-border);
      border-radius: 18px;
      padding: 20px;
      box-shadow: var(--shadow-card);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .innov-card.highlight {
      border-color: var(--sp-amber-500);
      box-shadow: 0 4px 18px rgba(212, 129, 11, 0.12);
    }

    .innov-title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .innov-heading {
      font-size: 18px;
      font-weight: 900;
      color: var(--sp-forest-900);
    }

    .innov-stat-row {
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin: 10px 0 6px;
    }

    .innov-big-stat {
      font-family: var(--font-mono);
      font-size: 48px;
      font-weight: 900;
      line-height: 1;
    }

    .innov-stat-label {
      font-size: 16px;
      font-weight: 800;
      color: var(--sp-forest-900);
    }

    .innov-rule-text {
      font-size: 13.5px;
      color: var(--sp-ink-secondary);
      font-weight: 600;
    }

    /* SLIDE 4: Live Demo & Proof */
    #slide-4 {
      background: radial-gradient(circle at 80% 15%, #15271D 0%, #0E1A14 60%, #07100B 100%);
      color: #FAF8F3;
    }

    .demo-kpi-bar {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 18px;
      margin-bottom: 16px;
    }

    .kpi-tile {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 16px;
      padding: 16px 20px;
      backdrop-filter: blur(8px);
    }

    .kpi-title {
      font-size: 13px;
      font-weight: 700;
      color: #A3B5AA;
    }

    .kpi-num {
      font-family: var(--font-mono);
      font-size: 46px;
      font-weight: 900;
      line-height: 1;
      margin: 4px 0;
    }

    .kpi-num.amber { color: var(--sp-amber-400); }
    .kpi-num.safe { color: #34D399; }
    .kpi-num.blue { color: #60A5FA; }

    .proof-main-grid {
      display: grid;
      grid-template-columns: 1.15fr 0.95fr;
      gap: 20px;
      align-items: stretch;
      flex: 1;
    }

    .gis-mock-box {
      background: #0B1711;
      border: 1px solid rgba(212, 129, 11, 0.35);
      border-radius: 16px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .benchmark-col {
      display: flex;
      flex-direction: column;
      gap: 14px;
      justify-content: space-between;
    }

    .stats-card-dark {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 16px;
      padding: 18px;
      backdrop-filter: blur(8px);
    }

    .f1-and-bars {
      display: grid;
      grid-template-columns: 100px 1fr;
      gap: 18px;
      align-items: center;
    }

    .f1-circle-wrap {
      position: relative;
      width: 100px;
      height: 100px;
    }

    .f1-center-text {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .f1-val {
      font-family: var(--font-mono);
      font-size: 21px;
      font-weight: 900;
      color: #FFFFFF;
    }

    .f1-lbl {
      font-size: 9.5px;
      font-weight: 800;
      color: var(--sp-amber-400);
      text-transform: uppercase;
    }

    .bar-line {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .bar-label-flex {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 3px;
    }

    .bar-track-dark {
      height: 7px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 999px;
      overflow: hidden;
    }

    .bar-fill-anim {
      height: 100%;
      border-radius: 999px;
      transition: width 1.2s ease-out;
    }

    .bar-fill-anim.precision { background: #34D399; width: 0%; }
    .bar-fill-anim.recall { background: #60A5FA; width: 0%; }

    .sinai-trap-banner {
      background: rgba(0, 0, 0, 0.45);
      border: 1.5px solid rgba(212, 129, 11, 0.4);
      border-radius: 14px;
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .sinai-score-pill {
      text-align: center;
      padding: 6px 14px;
      border-radius: 8px;
      font-family: var(--font-mono);
      font-weight: 900;
      font-size: 22px;
    }

    .sinai-score-pill.nasa {
      background: rgba(192, 57, 43, 0.2);
      color: #F87171;
      border: 1px solid rgba(192, 57, 43, 0.4);
    }

    .sinai-score-pill.spectra {
      background: rgba(16, 185, 129, 0.2);
      color: #34D399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }

    /* SLIDE 5: Economic Feasibility & SDGs */
    .biz-trio-clean {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 22px;
      margin: 12px 0 16px;
      flex: 1;
    }

    .biz-clean-card {
      background: #FFFFFF;
      border: 1.5px solid var(--sp-border);
      border-radius: 18px;
      padding: 24px 20px;
      box-shadow: var(--shadow-card);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .biz-hero-num {
      font-family: var(--font-mono);
      font-size: 48px;
      font-weight: 900;
      line-height: 1;
      margin: 12px 0 6px;
      color: var(--sp-forest-900);
    }

    .biz-card-head {
      font-size: 20px;
      font-weight: 900;
      color: var(--sp-forest-900);
    }

    .biz-card-text {
      font-size: 14px;
      color: var(--sp-ink-secondary);
      font-weight: 600;
      line-height: 1.5;
    }

    .sdg-badges-row {
      display: flex;
      gap: 10px;
      margin-top: 14px;
    }

    .sdg-chip {
      flex: 1;
      padding: 10px;
      border-radius: 10px;
      color: #FFFFFF;
      font-weight: 900;
      text-align: center;
      font-size: 14px;
    }

    .sdg-chip.s13 { background: #3F7E44; }
    .sdg-chip.s7 { background: #FCC30B; color: #12231A; }

    .closing-clean-bar {
      background: var(--sp-forest-900);
      border-radius: 14px;
      padding: 14px 22px;
      color: #FAF8F3;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    /* SLIDE 6: Tough ISEF Q&A Defense */
    .qa-clean-stack {
      display: flex;
      flex-direction: column;
      gap: 14px;
      flex: 1;
      justify-content: center;
    }

    .qa-box-clean {
      background: #FFFFFF;
      border: 1.5px solid var(--sp-border);
      border-radius: 16px;
      padding: 16px 20px;
      box-shadow: var(--shadow-card);
    }

    .qa-q-title {
      font-size: 17px;
      font-weight: 900;
      color: var(--sp-forest-900);
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .qa-a-text {
      font-size: 14px;
      font-weight: 600;
      color: var(--sp-ink-secondary);
      line-height: 1.55;
      background: var(--sp-bg-sand-soft);
      padding: 10px 14px;
      border-radius: 8px;
      border-right: 3.5px solid var(--sp-amber-500);
    }

    /* Bottom Bar */
    .deck-bottombar {
      height: 44px;
      background: var(--sp-bg-sand);
      border-top: 1px solid var(--sp-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 28px;
      font-size: 12px;
      color: var(--sp-ink-secondary);
      z-index: 90;
    }

    .deck-bottombar.dark-mode {
      background: var(--sp-forest-950);
      border-color: rgba(255, 255, 255, 0.1);
      color: #A3B5AA;
    }

    .nav-btn-box {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .arrow-btn {
      background: #FFFFFF;
      border: 1px solid var(--sp-border);
      color: var(--sp-forest-900);
      width: 32px;
      height: 32px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-weight: 900;
    }

    .arrow-btn:hover {
      background: var(--sp-amber-500);
      color: #FFFFFF;
      border-color: var(--sp-amber-400);
    }

    /* Prompter Dock (Hidden by default, toggled via P key) */
    .prompter-dock {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(18, 35, 26, 0.98);
      border-top: 2.5px solid var(--sp-amber-500);
      backdrop-filter: blur(12px);
      padding: 14px 28px;
      z-index: 1000;
      transform: translateY(105%);
      transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
    }

    .prompter-dock.open {
      transform: translateY(0);
    }

    .prompter-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }

    .prompter-box {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px;
      padding: 10px 14px;
    }

    .prompter-name {
      font-size: 12.5px;
      font-weight: 900;
      margin-bottom: 4px;
    }

    .prompter-name.fares { color: #60A5FA; }
    .prompter-name.shnawy { color: #34D399; }

    .prompter-cue {
      font-size: 13.5px;
      color: #FAF8F3;
      line-height: 1.5;
    }
  </style>
</head>
<body>

  <div class="deck-viewport">

    <!-- Global Topbar -->
    <header class="deck-topbar">
      <div class="brand-group" onclick="goToSlide(0)">
        <!-- Official Logo SVG -->
        <svg class="brand-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 287 282">
          <path fill="#DA831A" d="M149.79 245.451C149.72 241.487 149.7 237.527 149.72 233.563C149.79 222.686 149.66 211.813 149.7 200.937C149.72 195.734 149.9 190.514 149.8 185.312C149.77 183.575 149.55 181.968 149.01 180.312C145.88 170.865 137.89 166.22 129.6 161.817C125.58 159.684 121.5 157.665 117.47 155.544C117.47 155.544 116.99 155.286 116.99 155.285C115.03 154.223 113.07 153.176 111.13 152.094C101.73 146.862 92.24 141.796 82.86 136.536C74.86 132.049 68.27 126.995 62.76 119.558C52.46 105.637 51.4399 87.726 55.8199 71.589C58.8199 60.549 66.9 47.461 75.45 40.322C76.64 39.323 77.84 38.32 79.05 37.342C83.87 33.46 89.49 30.423 95.3 28.338C104.13 25.176 111.13 23.987 120.19 24.034C127.1 24.07 134.02 24.091 140.94 24.091C149.75 24.092 158.57 23.991 167.38 24.155C173.75 24.273 180.12 24.139 186.5 24.172C193.02 24.206 199.55 24.138 206.06 24.237C206.06 24.237 206.94 24.253 206.94 24.253C214.48 24.422 221.62 26.131 228.3 29.694C235.16 33.357 241.89 39.617 245.96 46.271C252.52 56.969 253.97 64.025 253.98 76.625C253.99 88.562 253.93 100.5 253.97 112.437C253.99 118.621 254.07 124.817 253.99 131C253.94 135.071 253.64 139.157 252.73 143.125C252.5 144.11 252.22 145.079 251.98 146.061C251.98 146.062 251.95 146.175 251.95 146.176C250.6 150.994 248.52 155.736 245.94 160.024C242.91 165.072 239.76 168.693 235.39 172.639C229.92 177.57 223.45 181.37 216.4 183.552C209.2 185.782 202.34 186.757 194.81 186.2L194.79 245.532L149.79 245.451Z"/>
          <path fill="#0E241A" d="M173.31 61.564C174.46 61.563 175.6 61.563 176.75 61.565C183.52 61.575 190.3 61.536 197.06 61.656C197.06 61.656 197.56 61.667 197.56 61.667C202.7 61.799 207.31 63.92 210.38 68.125C212.41 70.91 213.33 73.761 213.36 77.187C213.37 78.291 213.34 79.396 213.33 80.5C213.24 87.421 213.4 94.331 213.41 101.25C213.42 109.519 213.48 117.795 213.38 126.063C213.35 128.262 213.28 130.352 212.7 132.483C210.27 141.335 202.83 146.955 193.69 146.946C189.09 146.941 185.18 145.18 181.19 143.002C176.54 140.467 171.93 137.885 167.24 135.44C163.29 133.384 159.46 131.143 155.57 128.973C155.57 128.973 155.13 128.722 155.12 128.722C149.93 125.882 144.58 123.301 139.44 120.362C133.71 117.085 127.73 114.25 122 110.978C117.84 108.602 113.57 106.434 109.38 104.109C106.78 102.667 104.31 100.821 102.5 98.436C97.6801 92.062 97.6 84.823 100.54 77.639C102.76 72.22 107.2 67.81 112.43 65.218C120.31 61.306 124.85 61.584 133.62 61.573C146.85 61.557 160.08 61.572 173.31 61.564Z"/>
          <path fill="#F1F0E5" d="M179.94 77.403C180.79 77.402 181.65 77.401 182.5 77.426C185.86 77.528 188.52 78.63 190.91 81.053C194.72 84.925 194.64 89.213 194.66 94.375C194.67 99.622 194.74 104.879 194.67 110.125C194.66 111.195 194.66 112.316 194.46 113.373C193.26 119.75 188.41 123.824 181.94 123.848C178.73 123.86 175.74 121.863 173.01 120.342C166.4 116.657 159.67 113.188 153.07 109.481C149.61 107.536 146.1 105.683 142.62 103.755C139.9 102.239 137.54 100.499 136.25 97.562C133.8 91.99 135.18 85.687 139.69 81.62C142.91 78.716 146.46 77.5 150.75 77.445C152.46 77.422 154.17 77.437 155.88 77.452C163.9 77.522 171.92 77.409 179.94 77.403Z"/>
          <path fill="#DA831A" d="M52.8199 139.306C53.77 139.879 54.72 140.452 55.6801 141.016C58.61 142.743 61.61 144.325 64.5601 146.003C71.99 150.224 79.34 154.597 86.8199 158.726C90.59 160.81 94.27 163.057 98.02 165.182C102.4 167.662 106.52 170.609 109.92 174.337C117.81 182.994 122.53 192.497 122.73 204.375C122.74 204.875 122.74 205.375 122.74 205.875C122.8 215.56 122.82 225.252 122.71 234.937C122.67 238.38 122.55 242.055 122.74 245.489L52.85 245.458L52.8199 139.306Z"/>
        </svg>
        <span class="brand-title">SpectraPlume</span>
      </div>

      <div class="slide-dots">
        <div class="dot-pill active" onclick="goToSlide(0)"></div>
        <div class="dot-pill" onclick="goToSlide(1)"></div>
        <div class="dot-pill" onclick="goToSlide(2)"></div>
        <div class="dot-pill" onclick="goToSlide(3)"></div>
        <div class="dot-pill" onclick="goToSlide(4)"></div>
        <div class="dot-pill" onclick="goToSlide(5)"></div>
      </div>

      <div class="top-actions">
        <span class="timer-pill" id="timer">⏱️ 00:00 / 04:30</span>
        <button class="top-btn" onclick="togglePrompter()" id="prompterBtn">🎙️ كواليس الإلقاء (P)</button>
        <button class="top-btn" onclick="toggleFullscreen()">⛶ ملء الشاشة (F)</button>
      </div>
    </header>

    <!-- Main Deck Stage -->
    <main class="deck-stage">

      <!-- ========================================== -->
      <!-- SLIDE 1: Hook & Scenario                   -->
      <!-- ========================================== -->
      <section class="slide active" id="slide-1">
        <div class="slide-head">
          <div class="citations-strip">
            <span class="cite-pill cite-pill-dark">Regeneron ISEF 2027</span>
            <span class="cite-pill cite-pill-dark">Category: <strong>AIR (Atmospheric Science)</strong></span>
            <span class="cite-pill cite-pill-dark">NASA EMIT Spaceborne Mission</span>
          </div>
          <span class="slide-badge slide-badge-dark">🎬 المشهد 1: الافتتاحية والسيناريو</span>
        </div>

        <div class="slide1-layout">
          <div>
            <h1 class="hero-h1">SpectraPlume</h1>
            <h2 class="hero-h2">رادار فضائي ذكي لكشف انبعاثات الميثان وحساب التدفق من مدار الأرض</h2>

            <div class="hero-hook-banner">
              "ماسورة مكسورة في الصحراء بتخسر ملايين.. 
              <strong>مفيش إنسان شايفها، ورادارنا بيشوفها من الفضاء!</strong>"
            </div>

            <div class="team-badges-row">
              <div class="team-pill">
                <span class="team-dot fares"></span>
                <span style="font-weight:900; font-size:16px;">فارس محمد</span>
              </div>
              <div class="team-pill">
                <span class="team-dot shnawy"></span>
                <span style="font-weight:900; font-size:16px;">محمد الشناوي</span>
              </div>
            </div>
          </div>

          <!-- Clean Vector Graphic (CH4 Molecule + Sensor Beam) -->
          <div style="display:flex; justify-content:center;">
            <svg viewBox="0 0 320 320" width="280" height="280">
              <circle cx="160" cy="160" r="130" fill="none" stroke="rgba(212,129,11,0.25)" stroke-width="2" stroke-dasharray="6 6"/>
              <!-- Central Carbon -->
              <circle cx="160" cy="160" r="32" fill="#12231A" stroke="#E5982A" stroke-width="3"/>
              <text x="160" y="168" text-anchor="middle" fill="#FFFFFF" font-family="Plus Jakarta Sans" font-weight="900" font-size="24">C</text>
              <!-- 4 Hydrogens -->
              <line x1="160" y1="128" x2="160" y2="80" stroke="#E5982A" stroke-width="3.5" stroke-linecap="round"/>
              <circle cx="160" cy="65" r="18" fill="#0B1711" stroke="#34D399" stroke-width="2.5"/>
              <text x="160" y="71" text-anchor="middle" fill="#FAF8F3" font-family="Plus Jakarta Sans" font-weight="800" font-size="14">H</text>

              <line x1="128" y1="160" x2="80" y2="160" stroke="#E5982A" stroke-width="3.5" stroke-linecap="round"/>
              <circle cx="65" cy="160" r="18" fill="#0B1711" stroke="#34D399" stroke-width="2.5"/>
              <text x="65" y="165" text-anchor="middle" fill="#FAF8F3" font-family="Plus Jakarta Sans" font-weight="800" font-size="14">H</text>

              <line x1="192" y1="160" x2="240" y2="160" stroke="#E5982A" stroke-width="3.5" stroke-linecap="round"/>
              <circle cx="255" cy="160" r="18" fill="#0B1711" stroke="#34D399" stroke-width="2.5"/>
              <text x="255" y="165" text-anchor="middle" fill="#FAF8F3" font-family="Plus Jakarta Sans" font-weight="800" font-size="14">H</text>

              <line x1="160" y1="192" x2="160" y2="240" stroke="#E5982A" stroke-width="3.5" stroke-linecap="round"/>
              <circle cx="160" cy="255" r="18" fill="#0B1711" stroke="#34D399" stroke-width="2.5"/>
              <text x="160" y="261" text-anchor="middle" fill="#FAF8F3" font-family="Plus Jakarta Sans" font-weight="800" font-size="14">H</text>
            </svg>
          </div>
        </div>

        <div style="font-size:12.5px; color:#A3B5AA;">
          Spaceborne Methane Detection & Real-Time Flux Inversion
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SLIDE 2: Problem & Citations               -->
      <!-- ========================================== -->
      <section class="slide" id="slide-2">
        <div class="slide-head">
          <span class="slide-badge">⚠️ المشهد 2: المشكلة وتوثيق الأبحاث</span>
          <div class="citations-strip">
            <span class="cite-pill">IPCC AR6: <strong>84× GWP₂₀</strong></span>
            <span class="cite-pill">Science Advances 2023: <strong>Thorpe et al.</strong></span>
            <span class="cite-pill">NASA EMIT: <strong>2.3 µm SWIR</strong></span>
          </div>
        </div>

        <!-- 3 Big Stat Cards -->
        <div class="stat-cards-trio">
          <div class="stat-card-bold amber">
            <span class="cite-pill">IPCC AR6 (2021)</span>
            <div class="stat-huge-num amber">
              <span class="count-up" data-val="84">0</span>×
            </div>
            <div class="stat-card-title">أقوى من CO₂ في الاحتباس الحراري</div>
            <div class="stat-card-sub">معيار تسخين الكوكب على مدى 20 سنة</div>
          </div>

          <div class="stat-card-bold danger">
            <span class="cite-pill">Science Advances 2023</span>
            <div class="stat-huge-num danger">
              ><span class="count-up" data-val="50">0</span>%
            </div>
            <div class="stat-card-title">من انبعاثات الميثان في العالم</div>
            <div class="stat-card-sub">تخرج من أقل من 10% من المواقع (Super-Emitters)</div>
          </div>

          <div class="stat-card-bold safe">
            <span class="cite-pill">NASA EMIT (2022)</span>
            <div class="stat-huge-num safe">
              <span class="count-up" data-val="285">0</span>
            </div>
            <div class="stat-card-title">نطاق طيفي على متن محطة الفضاء</div>
            <div class="stat-card-sub">مطياف التصوير الفضائي عند 2.3 ميكرومتر</div>
          </div>
        </div>

        <!-- Two Fatal Flaws of Previous Research -->
        <div class="two-flaws-row">
          <div class="flaw-strip">
            <div class="flaw-icon red">⚠️</div>
            <div>
              <div class="flaw-title">عقبة الإنذارات الكاذبة (False Alarms)</div>
              <div class="flaw-sub">صخور الكالسيت تمتص عند نفس النطاق (2.335 µm) وتخدع خوارزميات ناسا!</div>
            </div>
          </div>

          <div class="flaw-strip">
            <div class="flaw-icon amber">❓</div>
            <div>
              <div class="flaw-title">غياب معدل التدفق الكتلي (قيمة NA)</div>
              <div class="flaw-sub">ناسا بتسيب كمية التسريب مجهولة لعدم وجود Inversion Model مباشر!</div>
            </div>
          </div>
        </div>

        <div style="font-size:12px; color:var(--sp-ink-muted);">
          المشكلة المزدوجة: تشويش المعادن الجيرية + غياب حساب أطنان الغاز المتسرب
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SLIDE 3: Physics & Innovation              -->
      <!-- ========================================== -->
      <section class="slide" id="slide-3">
        <div class="slide-head">
          <span class="slide-badge">🔬 المشهد 3: الابتكار — الفيزياء الجزيئية</span>
          <div class="citations-strip">
            <span class="cite-pill">HITRAN 2024: <strong>2260 + 2315 nm</strong></span>
            <span class="cite-pill">CaCO₃: <strong>2335 nm (Singlet)</strong></span>
            <span class="cite-pill">Varon et al.: <strong>AMT 2018 (IME)</strong></span>
          </div>
        </div>

        <div class="physics-grid-clean">
          <!-- Spectrum Chart -->
          <div class="spectrum-box-clean">
            <div class="spectrum-legend-clean">
              <span style="font-weight:900; font-size:15px; color:var(--sp-forest-900);">البصمة الطيفية: CH₄ Doublet vs. CaCO₃</span>
              <div style="display:flex; gap:12px; font-size:12px; font-weight:800;">
                <span style="color:#D4810B;">● الميثان (قمتان)</span>
                <span style="color:#C0392B;">● الكالسيت (قمة واحدة)</span>
              </div>
            </div>

            <!-- Vector SVG Plot -->
            <svg viewBox="0 0 500 210" style="width:100%; height:auto; background:var(--sp-bg-canvas); border-radius:10px;">
              <line x1="40" y1="30" x2="470" y2="30" stroke="#E3D9CD" stroke-width="1" stroke-dasharray="4 4"/>
              <line x1="40" y1="90" x2="470" y2="90" stroke="#E3D9CD" stroke-width="1" stroke-dasharray="4 4"/>
              <line x1="40" y1="150" x2="470" y2="150" stroke="#E3D9CD" stroke-width="1" stroke-dasharray="4 4"/>
              <line x1="40" y1="180" x2="470" y2="180" stroke="#D2C5BA" stroke-width="1.5"/>

              <!-- Labels -->
              <text x="50" y="198" font-family="JetBrains Mono" font-size="11" fill="#6B7870">2150nm</text>
              <text x="165" y="198" font-family="JetBrains Mono" font-size="11" fill="#D4810B" font-weight="800">2260nm</text>
              <text x="270" y="198" font-family="JetBrains Mono" font-size="11" fill="#D4810B" font-weight="900">2315nm</text>
              <text x="350" y="198" font-family="JetBrains Mono" font-size="11" fill="#C0392B" font-weight="800">2335nm</text>
              <text x="440" y="198" font-family="JetBrains Mono" font-size="11" fill="#6B7870">2450nm</text>

              <!-- Methane Doublet Marker Lines -->
              <line x1="185" y1="20" x2="185" y2="180" stroke="#D4810B" stroke-width="1.8" stroke-dasharray="4 3"/>
              <line x1="285" y1="20" x2="285" y2="180" stroke="#D4810B" stroke-width="2" stroke-dasharray="4 3"/>
              <!-- Calcite Line -->
              <line x1="365" y1="20" x2="365" y2="180" stroke="#C0392B" stroke-width="1.5" stroke-dasharray="3 3"/>

              <!-- Calcite Single Dip -->
              <path d="M 50 60 Q 200 60 280 65 Q 365 160 410 70 Q 450 60 470 60" 
                    fill="none" stroke="#C0392B" stroke-width="2" stroke-dasharray="5 4"/>

              <!-- Methane Double Dip Curve -->
              <path d="M 50 50 Q 140 55 165 75 Q 185 120 205 80 Q 250 75 270 120 Q 285 165 305 105 Q 370 55 470 50" 
                    fill="none" stroke="#12231A" stroke-width="3"/>

              <circle cx="185" cy="120" r="5" fill="#E5982A"/>
              <circle cx="285" cy="165" r="6" fill="#D4810B"/>
              <circle cx="365" cy="160" r="5" fill="#C0392B"/>
            </svg>

            <div style="font-size:13px; font-weight:700; color:var(--sp-forest-900); text-align:center;">
              الميثان له قمتان توأم (2260 + 2315 nm) · الكالسيت قمة واحدة منفردة (2335 nm)
            </div>
          </div>

          <!-- Two Innovation Pillars -->
          <div class="two-innovations-col">
            <div class="innov-card highlight">
              <div class="innov-title-row">
                <span class="innov-heading">1. بصمة التوأم (HITRAN 2024)</span>
                <span class="cite-pill">Doublet Ratio Filter</span>
              </div>
              <div class="innov-stat-row">
                <div class="innov-big-stat" style="color:var(--sp-amber-600);">
                  <span class="count-up" data-val="78.4" data-dec="1">0</span>%
                </div>
                <div class="innov-stat-label">إلغاء تام لإنذارات صخور الحجر الجيري</div>
              </div>
              <div class="innov-rule-text">فحص النسبة الفيزيائية بين القمتين يطرد الصخور فوراً</div>
            </div>

            <div class="innov-card">
              <div class="innov-title-row">
                <span class="innov-heading">2. حساب التدفق (Varon AMT + ERA5)</span>
                <span class="cite-pill">Hydrodynamic IME</span>
              </div>
              <div class="innov-stat-row">
                <div class="innov-big-stat" style="color:var(--sp-safe-600);">
                  <span class="count-up" data-val="7.9" data-dec="1">0</span>%
                </div>
                <div class="innov-stat-label">هامش خطأ MAPE (دقة 92.1%)</div>
              </div>
              <div class="innov-rule-text">دمج سرعات رياح ERA5 اللحظية في معادلة Q = (IME · U) / L</div>
            </div>
          </div>
        </div>

        <div style="font-size:12px; color:var(--sp-ink-muted);">
          منظومة Physics-Informed مقيدة بقوانين فيزياء الغلاف الجوي
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SLIDE 4: Live Demo & Statistical Proof     -->
      <!-- ========================================== -->
      <section class="slide" id="slide-4">
        <div class="slide-head">
          <span class="slide-badge slide-badge-dark">🛰️ المشهد 4: الديمو العملي والإثبات</span>
          <div class="citations-strip">
            <span class="cite-pill cite-pill-dark">42 NASA Swaths</span>
            <span class="cite-pill cite-pill-dark">Paired t-test: <strong>p = 2.4 × 10⁻⁸</strong></span>
            <span class="cite-pill cite-pill-dark">Threshold: <strong>85 kg/h</strong></span>
          </div>
        </div>

        <!-- 3 Big Real-Time Telemetry Cards -->
        <div class="demo-kpi-bar">
          <div class="kpi-tile">
            <div class="kpi-title">معدل الانبعاث الكتلي اللحظي</div>
            <div class="kpi-num amber">
              <span class="count-up" data-val="2.46" data-dec="2">0.00</span> <span style="font-size:22px;">طن/ساعة</span>
            </div>
            <div style="font-size:12px; color:#A3B5AA;">EMIT Orbit #2222205</div>
          </div>

          <div class="kpi-tile">
            <div class="kpi-title">الخسارة المالية اليومية المقدرة</div>
            <div class="kpi-num safe">
              $<span class="count-up" data-val="10600">0</span> <span style="font-size:22px;">/يوم</span>
            </div>
            <div style="font-size:12px; color:#A3B5AA;">تسريب حقل غاز في الشرق الأوسط</div>
          </div>

          <div class="kpi-tile">
            <div class="kpi-title">زمن المعالجة والاستجابة (Latency)</div>
            <div class="kpi-num blue">
              <span class="count-up" data-val="435">0</span> <span style="font-size:22px;">ms</span>
            </div>
            <div style="font-size:12px; color:#A3B5AA;">معالجة فورية Real-Time</div>
          </div>
        </div>

        <!-- Split: GIS Mockup vs Benchmark Stats -->
        <div class="proof-main-grid">
          <!-- GIS Satellite Map Box -->
          <div class="gis-mock-box">
            <div style="display:flex; justify-content:space-between; font-size:11.5px; color:#A3B5AA;">
              <span>🛰️ ESRI Satellite Imagery Overlay</span>
              <span style="font-family:var(--font-mono); color:var(--sp-amber-400);">31.8712° N, -102.3355° W</span>
            </div>

            <!-- Vector Map with Infrared Plume -->
            <svg viewBox="0 0 420 180" style="width:100%; height:auto; background:#07120C; border-radius:10px;">
              <defs>
                <radialGradient id="plume" cx="30%" cy="60%" r="55%">
                  <stop offset="0%" stop-color="#EF4444" stop-opacity="0.95"/>
                  <stop offset="40%" stop-color="#F59E0B" stop-opacity="0.8"/>
                  <stop offset="75%" stop-color="#10B981" stop-opacity="0.45"/>
                  <stop offset="100%" stop-color="#10B981" stop-opacity="0"/>
                </radialGradient>
              </defs>
              <!-- Terrain contours -->
              <path d="M 0 120 Q 140 90 280 140 T 420 110" fill="none" stroke="rgba(212,129,11,0.2)" stroke-width="1.5"/>
              <!-- Plume -->
              <path d="M 120 115 Q 170 75 260 70 Q 340 65 390 55 Q 350 105 270 125 Q 190 140 120 115 Z" fill="url(#plume)"/>
              <!-- Target Crosshair -->
              <circle cx="120" cy="115" r="12" fill="none" stroke="#EF4444" stroke-width="2"/>
              <circle cx="120" cy="115" r="3.5" fill="#EF4444"/>
              <!-- Wind Vector -->
              <g transform="translate(45, 35)">
                <circle cx="0" cy="0" r="16" fill="rgba(0,0,0,0.5)" stroke="rgba(255,255,255,0.2)"/>
                <line x1="0" y1="10" x2="8" y2="-8" stroke="#34D399" stroke-width="2.5" stroke-linecap="round"/>
                <polygon points="8,-8 3,-3 9,-2" fill="#34D399"/>
                <text x="18" y="3" font-family="JetBrains Mono" font-size="10" fill="#34D399" font-weight="700">6.8 m/s</text>
              </g>
            </svg>

            <div style="display:flex; justify-content:space-between; font-size:12px; color:#A3B5AA;">
              <span>إسقاط GPS فوري لفرق الصيانة والطوارئ</span>
              <span>حد الكشف: <strong>85 kg/h</strong></span>
            </div>
          </div>

          <!-- Benchmark Stats & Sinai Control -->
          <div class="benchmark-col">
            <div class="stats-card-dark">
              <div class="f1-and-bars">
                <div class="f1-circle-wrap">
                  <svg viewBox="0 0 100 100" width="100" height="100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="8"/>
                    <circle id="f1Circle" cx="50" cy="50" r="40" fill="none" stroke="#D4810B" stroke-width="8"
                            stroke-linecap="round" stroke-dasharray="251" stroke-dashoffset="251"
                            transform="rotate(-90 50 50)" style="transition: stroke-dashoffset 1.2s ease-out;"/>
                  </svg>
                  <div class="f1-center-text">
                    <div class="f1-val">0.942</div>
                    <div class="f1-lbl">F1-Score</div>
                  </div>
                </div>

                <div class="bar-line">
                  <div>
                    <div class="bar-label-flex">
                      <span style="color:#A3B5AA;">Precision (دقة الإنذار)</span>
                      <span style="color:#34D399; font-family:var(--font-mono); font-weight:800;">96.1%</span>
                    </div>
                    <div class="bar-track-dark">
                      <div class="bar-fill-anim precision" data-w="96.1%"></div>
                    </div>
                  </div>

                  <div>
                    <div class="bar-label-flex">
                      <span style="color:#A3B5AA;">Recall (اصطياد الغاز)</span>
                      <span style="color:#60A5FA; font-family:var(--font-mono); font-weight:800;">92.4%</span>
                    </div>
                    <div class="bar-track-dark">
                      <div class="bar-fill-anim recall" data-w="92.4%"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Sinai Mountain Trap Banner -->
            <div class="sinai-trap-banner">
              <div>
                <div style="font-weight:900; font-size:14px; color:#FFFFFF;">فخ جبال سيناء (Negative Control)</div>
                <div style="font-size:11.5px; color:#A3B5AA;">مشهد صخور جيرية بدون أي غاز</div>
              </div>

              <div style="display:flex; gap:10px;">
                <div class="sinai-score-pill nasa">243 ❌</div>
                <div class="sinai-score-pill spectra">0 ✅</div>
              </div>
            </div>
          </div>
        </div>

        <div style="font-size:12px; color:var(--sp-amber-400); text-align:center; font-weight:800;">
          التفوق الإحصائي مؤكد: Paired t-test (p = 2.4 × 10⁻⁸) عبر 42 مسار تصوير حقيقي لناسا
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SLIDE 5: Economic Feasibility & SDGs       -->
      <!-- ========================================== -->
      <section class="slide" id="slide-5">
        <div class="slide-head">
          <span class="slide-badge">🌱 المشهد 5: الجدوى والاستدامة والختام</span>
          <div class="citations-strip">
            <span class="cite-pill">Zero Orbital CapEx</span>
            <span class="cite-pill">UN SDG 13: <strong>Climate Action</strong></span>
            <span class="cite-pill">UN SDG 7: <strong>Clean Energy</strong></span>
          </div>
        </div>

        <div class="biz-trio-clean">
          <div class="biz-clean-card">
            <span class="cite-pill">الكفاءة الاستثمارية</span>
            <div class="biz-hero-num" style="color:var(--sp-safe-600);">$0.00</div>
            <div class="biz-card-head">Zero Orbital CapEx</div>
            <div class="biz-card-text">
              استثمار بيانات NASA EMIT المفتوحة مجاناً بدلاً من إطلاق قمر صناعي بتكلفة 100 مليون دولار!
            </div>
          </div>

          <div class="biz-clean-card">
            <span class="cite-pill">العائد الاقتصادي للشركات</span>
            <div class="biz-hero-num" style="color:var(--sp-amber-600);">
              $<span class="count-up" data-val="18000">0</span>
            </div>
            <div class="biz-card-head">توفير يومي لكل بئر متسرب</div>
            <div class="biz-card-text">
              وقف تسريب واحد بحجم 1,000 kg/h يعيد ضخ الغاز في الشبكة بدلاً من هدره في الغلاف الجوي.
            </div>
          </div>

          <div class="biz-clean-card">
            <span class="cite-pill">أهداف الأمم المتحدة</span>
            <div class="sdg-badges-row">
              <div class="sdg-chip s13">SDG 13<br><span style="font-size:11px; font-weight:normal;">العمل المناخي</span></div>
              <div class="sdg-chip s7">SDG 7<br><span style="font-size:11px; font-weight:normal;">طاقة نظيفة</span></div>
            </div>
            <div class="biz-card-head" style="margin-top:14px;">الاستدامة وحماية المناخ</div>
            <div class="biz-card-text">
              حماية الكوكب بوقف أقوى غاز دفيء وصون موارد الطاقة للأجيال القادمة.
            </div>
          </div>
        </div>

        <!-- Closing Bar -->
        <div class="closing-clean-bar">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:22px;">📘</span>
            <div>
              <div style="font-weight:900; font-size:15px; color:#FFFFFF;">Engineering Log Book</div>
              <div style="font-size:12px; color:#A3B5AA;">توثيق كامل لكل خطوة وتجربة ومعادلة رياضية</div>
            </div>
          </div>

          <div style="font-weight:900; font-size:17px; color:var(--sp-amber-400);">
            شكراً لحضراتكم — جاهزون لأسئلة السادة المحكمين! 🎙️
          </div>
        </div>

        <div style="font-size:12px; color:var(--sp-ink-muted);">
          SpectraPlume: حل بيئي، اقتصادي وواقعي جاهز للتطبيق الفوري
        </div>
      </section>

      <!-- ========================================== -->
      <!-- SLIDE 6: Tough ISEF Q&A Defense            -->
      <!-- ========================================== -->
      <section class="slide" id="slide-6">
        <div class="slide-head">
          <span class="slide-badge">🛡️ دفاع المسابقة — أسئلة المحكمين</span>
          <span class="cite-pill">Q&A Quick Defense</span>
        </div>

        <div class="qa-clean-stack">
          <div class="qa-box-clean">
            <div class="qa-q-title">
              <span>Q1: "إيه الفرق الجوهري بينكم وبين ناسا؟"</span>
              <span class="cite-pill" style="color:var(--sp-safe-600);">المجيب: 🟢 الشناوي</span>
            </div>
            <div class="qa-a-text">
              ناسا بتتلخبط بين الميثان وصخور الحجر الجيري وبتسيب معدل التدفق <code>NA</code>. إحنا عزلنا الصخور بنسبة <strong>78.4%</strong> ببصمة التوأم من <strong>HITRAN 2024</strong>، وحسبنا التدفق بنموذج <strong>IME</strong> وسرعات رياح ERA5 بدقة <strong>92.1%</strong> في <strong>435ms</strong> فقط!
            </div>
          </div>

          <div class="qa-box-clean">
            <div class="qa-q-title">
              <span>Q2: "القمر بيمر كل عدة أيام، لو تسريب استمر ساعة ووقف هتعملوا إيه؟"</span>
              <span class="cite-pill" style="color:#2563EB;">المجيب: 🔵 فارس</span>
            </div>
            <div class="qa-a-text">
              قرار تصميمي مقصود مبني على ورقة <em>Science Advances 2023</em>؛ إحنا بنستهدف التسريبات المزمنة الكبرى (<strong>Super-Emitters</strong>) المستمرة لأيام وأسابيع والمسؤولة عن أكثر من <strong>50% من الكارثة</strong>، وبكده وفرنا 100 مليون دولار لقمر خاص وحلينا نصف المشكلة فوراً!
            </div>
          </div>

          <div class="qa-box-clean">
            <div class="qa-q-title">
              <span>Q3: "ليه نسبة استبعاد الصخور 78.4% مش 100%؟"</span>
              <span class="cite-pill">رد مشترك: 🔵 فارس أو 🟢 الشناوي</span>
            </div>
            <div class="qa-a-text">
              الأمانة العلمية؛ بكسل EMIT مساحته 60×60 متراً ويحدث بداخله تداخل طيفي (<strong>Sub-pixel mixing</strong>). في الصخور النقية زي <strong>جبال سيناء لغينا 243 إنذاراً بنسبة 100%</strong>، والمتوسط العالمي عبر 42 مسار هو 78.4%، وده رقم قياسي غير مسبوق عالمياً.
            </div>
          </div>
        </div>

        <div style="font-size:12px; color:var(--sp-ink-muted);">
          إجابات علمية سريعة ومقنعة مبنية على الفيزياء والأرقام الموثقة
        </div>
      </section>

    </main>

    <!-- Bottom Navigation Bar -->
    <footer class="deck-bottombar" id="bottomBar">
      <div class="nav-btn-box">
        <button class="arrow-btn" onclick="prevSlide()" title="السابق (◀)">▶</button>
        <button class="arrow-btn" onclick="nextSlide()" title="التالي (▶)">◀</button>
        <span style="font-family:var(--font-mono); font-weight:800; margin-right:8px;" id="slideNum">1 / 6</span>
      </div>

      <div style="font-size:11.5px; color:var(--sp-ink-muted);">
        استخدم الأسهم ◀ ▶ أو المسافة للتنقل · اضغط P لكواليس الإلقاء · اضغط F لملء الشاشة
      </div>

      <div style="font-family:var(--font-display); font-weight:800; font-size:12px;">
        SpectraPlume © ISEF 2027
      </div>
    </footer>

    <!-- Presenter Prompter (Hidden dock - toggled by P key) -->
    <div class="prompter-dock" id="prompter">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="color:var(--sp-amber-400); font-weight:900; font-size:13px;">🎙️ كواليس الإلقاء — توزيع الأدوار للمشهد الحالي</span>
        <button class="top-btn" onclick="togglePrompter()" style="padding:2px 8px; font-size:11px;">إغلاق ✕</button>
      </div>
      <div class="prompter-grid">
        <div class="prompter-box">
          <div class="prompter-name fares">🔵 فارس محمد:</div>
          <div class="prompter-cue" id="cueFares"></div>
        </div>
        <div class="prompter-box">
          <div class="prompter-name shnawy">🟢 محمد الشناوي:</div>
          <div class="prompter-cue" id="cueShnawy"></div>
        </div>
      </div>
    </div>

  </div>

  <script>
    let cur = 0;
    const slides = document.querySelectorAll('.slide');
    const dots = document.querySelectorAll('.dot-pill');
    const slideNum = document.getElementById('slideNum');
    const bottomBar = document.getElementById('bottomBar');
    const prompter = document.getElementById('prompter');
    const prompterBtn = document.getElementById('prompterBtn');

    // Spoken Script Prompter by Slide
    const cues = [
      {
        fares: "ابدأ بتشويق: 'تخيل في اللحظة دي في ماسورة غاز مكسورة في صحراء بتخرج طاقة تشغل مدينة كاملة ومحدش شايفها.. وبرنامجنا بيشوفها من الفضاء ويحدد الـ GPS في ثواني!'",
        shnawy: "ادخل بثقة: 'أنا محمد الشناوي وده زميلي فارس محمد.. مشروعنا SpectraPlume رادار فضائي ذكي بيستغل قمر ناسا EMIT لكشف سحب الغاز وحساب كميتها بالطن في الساعة.'"
      },
      {
        fares: "شاور على 50%: 'ورقة Science Advances 2023 أثبتت إن الـ Super-Emitters أقل من 10% ومسؤولة عن أكثر من 50% من الكارثة!'، ووضح عقبتي ناسا (الإنذارات الكاذبة وقيمة NA).",
        shnawy: "شاور على 84×: 'الميثان غاز شفاف، لكن طبقاً لتقرير IPCC AR6 خطورته تعادل 84 ضعف ثاني أكسيد الكربون!'، وشاور على قمر ناسا EMIT ونطاق 2.3 ميكرومتر."
      },
      {
        fares: "اشرح الابتكار: 'بنينا منظومة Physics-Informed؛ بفحص نسبة القمتين لغينا إنذارات صخور الحجر الجيري بنسبة 78.4%!'",
        shnawy: "اشرح الفيزياء: 'الميثان له قمتين توأم (2315 و 2260 nm)، بينما الكالسيت له قمة واحدة عند 2335 nm. وطبقنا نموذج IME مع رياح ERA5 بخطأ 7.9% MAPE فقط!'"
      },
      {
        fares: "وجّه الداشبورد للمحكم: 'معدل التسريب 2.46 طن/ساعة، والخسارة 10,600 دولار كل يوم، والتحليل بيخلص في 435ms!' واذكر F1=0.942 ودقة 96.1%.",
        shnawy: "أشر للخريطة الفضائية واختم بأقوى دليل: 'أثبتنا التفوق بـ Paired t-test (p = 2.4×10⁻⁸)! وفي فخ جبال سيناء خوارزمية ناسا طلعت 243 إنذار كاذب وبرنامجنا طلع صفر بنجاح 100%!'"
      },
      {
        fares: "اشرح الجدوى: 'أولاً Zero Orbital CapEx: بنستغل قمر ناسا المجاني بدون ما نحتاج 100 مليون دولار لقمر خاص!'، واربط المشروع بـ SDG 13 و SDG 7.",
        shnawy: "أكمل التوفير: 'وقف تسريب 1,000 kg/h بيوفر 18,000 دولار كل يوم!'، وأشر لـ Engineering Log Book واختم: 'شكراً لوقت حضرتك يا فندم وإحنا جاهزون لأي أسئلة!'"
      },
      {
        fares: "في سؤال استمرارية القمر: 'التركيز على الـ Super-Emitters المزمنة المستمرة لأيام وفر 100 مليون دولار وحل نصف المشكلة فوراً.'",
        shnawy: "في سؤال الفرق عن ناسا وسؤال الـ 78.4%: 'شرح بصمة التوأم ونموذج IME، وتوضيح الأمانة العلمية وراء الـ 78.4% بسبب Sub-pixel mixing.'"
      }
    ];

    function goToSlide(idx) {
      if (idx < 0 || idx >= slides.length) return;
      slides[cur].classList.remove('active');
      dots[cur].classList.remove('active');
      
      cur = idx;
      
      slides[cur].classList.add('active');
      dots[cur].classList.add('active');
      slideNum.textContent = `${cur + 1} / ${slides.length}`;

      if (cur === 0 || cur === 3) {
        bottomBar.className = 'deck-bottombar dark-mode';
      } else {
        bottomBar.className = 'deck-bottombar';
      }

      // Update Prompter Cues
      document.getElementById('cueFares').textContent = cues[cur].fares;
      document.getElementById('cueShnawy').textContent = cues[cur].shnawy;

      // Animate Numbers & Bars
      animateSlide(slides[cur]);
    }

    function nextSlide() { goToSlide(cur + 1); }
    function prevSlide() { goToSlide(cur - 1); }

    function animateSlide(el) {
      // Numbers Count Up
      const nums = el.querySelectorAll('.count-up');
      nums.forEach(n => {
        const val = parseFloat(n.getAttribute('data-val'));
        const dec = parseInt(n.getAttribute('data-dec') || '0');
        const dur = 1000;
        const start = performance.now();
        function step(now) {
          const p = Math.min((now - start) / dur, 1);
          const ease = 1 - Math.pow(1 - p, 3);
          n.textContent = (val * ease).toFixed(dec);
          if (p < 1) requestAnimationFrame(step);
          else n.textContent = val.toFixed(dec);
        }
        requestAnimationFrame(step);
      });

      // Progress bars
      const bars = el.querySelectorAll('.bar-fill-anim');
      bars.forEach(b => {
        const w = b.getAttribute('data-w');
        b.style.width = '0%';
        setTimeout(() => { b.style.width = w; }, 100);
      });

      // F1 Circle
      const f1 = el.querySelector('#f1Circle');
      if (f1) {
        f1.style.strokeDashoffset = '251';
        setTimeout(() => {
          f1.style.strokeDashoffset = String(251 - (251 * 0.942));
        }, 100);
      }
    }

    function togglePrompter() {
      prompter.classList.toggle('open');
      prompterBtn.classList.toggle('active-mode');
    }

    function toggleFullscreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }

    // Timer (4:30)
    let sec = 0;
    setInterval(() => {
      sec++;
      const m = String(Math.floor(sec / 60)).padStart(2, '0');
      const s = String(sec % 60).padStart(2, '0');
      document.getElementById('timer').textContent = `⏱️ ${m}:${s} / 04:30`;
    }, 1000);

    // Keyboard controls
    window.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowLeft' || e.key === 'Backspace' || e.key === 'PageUp') {
        e.preventDefault();
        prevSlide();
      } else if (e.key.toLowerCase() === 'p') {
        e.preventDefault();
        togglePrompter();
      } else if (e.key.toLowerCase() === 'f') {
        e.preventDefault();
        toggleFullscreen();
      } else if (e.key >= '1' && e.key <= '6') {
        goToSlide(parseInt(e.key) - 1);
      }
    });

    window.addEventListener('DOMContentLoaded', () => {
      goToSlide(0);
    });
  </script>
</body>
</html>
'''

OUTPUT_FILE.write_text(HTML_CONTENT, encoding="utf-8")
print(f"SUCCESS: Clean minimal presentation written to {OUTPUT_FILE}")
