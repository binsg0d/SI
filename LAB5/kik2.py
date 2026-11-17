import json
import math
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

HTML_PAGE = """<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TIC // TAC // TOE</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    :root {
      --bg: #f5f2eb;
      --surface: rgba(255,255,255,0.72);
      --tile: #faf7f2;
      --border: rgba(17,24,39,0.08);
      --border-strong: rgba(17,24,39,0.14);
      --accent: #7c5cff;
      --accent-2: #5b87ff;
      --x: #1f6feb;
      --o: #d85a7a;
      --win: #2ab67d;
      --text: #111827;
      --muted: #667085;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      width: 100%;
      height: 100%;
      font-family: 'Inter', sans-serif;
      background:
        radial-gradient(circle at top, rgba(124,92,255,0.08), transparent 34%),
        linear-gradient(180deg, #f7f3ee 0%, #f1efe9 100%);
      color: var(--text);
    }

    body {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 18px;
      overflow-x: hidden;
    }

    .container {
      width: min(92vw, 430px);
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .screen {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 16px;
      animation: fadeUp 0.28s ease;
    }

    .hidden { display: none !important; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(12px) scale(0.985); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 4px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .dot-live {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--win);
      box-shadow: 0 0 12px var(--win);
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.55; transform: scale(0.85); }
    }

    .title {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      letter-spacing: 1px;
      font-size: 0.9rem;
    }

    .title span { color: var(--muted); }

    .icon-btn {
      border: 1px solid var(--border);
      border-radius: 10px;
      background: rgba(255,255,255,0.7);
      padding: 8px 10px;
      cursor: pointer;
      font-size: 0.85rem;
    }

    .menu-card {
      background: rgba(255,255,255,0.74);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 26px 22px;
      box-shadow: 0 20px 50px rgba(17, 24, 39, 0.08);
      display: flex;
      flex-direction: column;
      gap: 20px;
      backdrop-filter: blur(12px);
    }

    .hero {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 8px;
    }

    .hero-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.64rem;
      letter-spacing: 1.2px;
      text-transform: uppercase;
      font-weight: 700;
      color: var(--accent);
      background: rgba(124,92,255,0.08);
      border: 1px solid rgba(124,92,255,0.12);
      padding: 5px 10px;
      border-radius: 999px;
    }

    .hero h1 {
      font-size: clamp(1.35rem, 2vw, 1.7rem);
      font-weight: 800;
      letter-spacing: -0.5px;
    }

    .hero p {
      font-size: 0.84rem;
      line-height: 1.5;
      color: var(--muted);
      max-width: 300px;
    }

    .section {
      display: flex;
      flex-direction: column;
      gap: 9px;
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }

    .section-label {
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: #94a3b8;
    }

    .section-hint {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      color: var(--accent);
      white-space: nowrap;
    }

    .size-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }

    .option-pill {
      background: rgba(17,24,39,0.02);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      cursor: pointer;
      transition: transform 0.15s ease, border-color 0.2s ease, background 0.2s ease;
      user-select: none;
    }

    .option-pill:hover {
      border-color: var(--border-strong);
      transform: translateY(-1px);
    }

    .option-pill.active {
      background: rgba(124,92,255,0.07);
      border-color: rgba(124,92,255,0.25);
      box-shadow: 0 8px 18px rgba(124,92,255,0.08);
    }

    .option-pill strong {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.95rem;
    }

    .option-pill span {
      font-size: 0.65rem;
      color: var(--muted);
    }

    .depth-box {
      background: rgba(17,24,39,0.02);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    input[type='range'] {
      width: 100%;
      appearance: none;
      -webkit-appearance: none;
      height: 6px;
      border-radius: 999px;
      background: rgba(17,24,39,0.08);
      outline: none;
    }

    input[type='range']::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: var(--accent);
      border: 2px solid #fff;
      box-shadow: 0 4px 10px rgba(124,92,255,0.28);
      cursor: pointer;
    }

    .depth-ticks {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.66rem;
      color: var(--muted);
    }

    .starter-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0,1fr));
      gap: 10px;
    }

    .starter-card {
      background: rgba(17,24,39,0.02);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 12px 14px;
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      transition: all 0.2s ease;
      min-height: 70px;
    }

    .starter-card:hover {
      border-color: var(--border-strong);
    }

    .starter-card.active.user-opt {
      background: rgba(31,111,235,0.06);
      border-color: rgba(31,111,235,0.22);
    }

    .starter-card.active.ai-opt {
      background: rgba(216,90,122,0.06);
      border-color: rgba(216,90,122,0.22);
    }

    .starter-icon {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      background: rgba(255,255,255,0.05);
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
      font-size: 1.05rem;
    }

    .user-opt .starter-icon { color: var(--x); }
    .ai-opt .starter-icon { color: var(--o); }

    .starter-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .starter-info strong { font-size: 0.88rem; }
    .starter-info span { font-size: 0.7rem; color: var(--muted); }

    .btn-start {
      width: 100%;
      border: none;
      border-radius: 14px;
      padding: 14px 16px;
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
      color: white;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 12px 20px rgba(124,92,255,0.18);
    }

    .scoreboard {
      display: grid;
      grid-template-columns: repeat(3, minmax(0,1fr));
      gap: 10px;
    }

    .score-card {
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
    }

    .score-label {
      font-size: 0.66rem;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: var(--muted);
      font-weight: 600;
    }

    .score-val {
      font-family: 'JetBrains Mono', monospace;
      font-size: clamp(1.1rem, 2vw, 1.45rem);
      font-weight: 700;
    }

    .x-card .score-val { color: var(--x); }
    .o-card .score-val { color: var(--o); }
    .d-card .score-val { color: #94a3b8; }

    .status-wrap {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      padding: 11px 14px;
      border-radius: 14px;
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--border);
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
    }

    #status-text { font-weight: 700; }
    #telemetry { color: var(--muted); }

    .board-shell {
      width: 100%;
      background: rgba(255,255,255,0.5);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 12px;
      box-shadow: 0 16px 32px rgba(17,24,39,0.05);
      position: relative;
    }

    .board {
      width: 100%;
      aspect-ratio: 1 / 1;
      display: grid;
      gap: 10px;
      position: relative;
    }

    .cell {
      background: var(--tile);
      border: 1px solid var(--border);
      border-radius: 14px;
      display: grid;
      place-items: center;
      cursor: pointer;
      transition: transform 0.18s ease, border-color 0.2s ease, background 0.2s ease;
      overflow: hidden;
      aspect-ratio: 1 / 1;
      min-height: 0;
    }

    .cell:hover:not(.taken):not(.locked) {
      border-color: var(--border-strong);
      transform: translateY(-1px);
    }

    .cell.taken, .cell.locked { cursor: default; }

    .symbol {
      width: 58%;
      height: 58%;
      display: block;
      overflow: visible;
    }

    .symbol.x-sym { stroke: var(--x); }
    .symbol.o-sym { stroke: var(--o); }

    .symbol path, .symbol circle {
      fill: none;
      stroke-width: 10;
      stroke-linecap: round;
      stroke-dasharray: 260;
      stroke-dashoffset: 260;
      animation: drawStroke 0.32s ease forwards;
    }

    .symbol path.second { animation-delay: 0.08s; }

    @keyframes drawStroke {
      to { stroke-dashoffset: 0; }
    }

    .cell.win {
      background: rgba(42,182,125,0.09);
      border-color: rgba(42,182,125,0.36);
    }

    #win-overlay {
      position: absolute;
      inset: 12px;
      width: calc(100% - 24px);
      height: calc(100% - 24px);
      pointer-events: none;
      z-index: 10;
    }

    #win-line {
      stroke: var(--win);
      stroke-width: 6;
      stroke-linecap: round;
      filter: drop-shadow(0 0 12px rgba(42,182,125,0.4));
      stroke-dasharray: 1000;
      stroke-dashoffset: 1000;
      transition: stroke-dashoffset 0.45s ease;
    }

    .game-footer {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .btn-secondary, .btn-primary-sm {
      border-radius: 14px;
      padding: 12px 10px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.15s ease, border-color 0.2s ease;
    }

    .btn-secondary {
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--border);
      color: var(--text);
    }

    .btn-primary-sm {
      border: none;
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
      color: white;
      box-shadow: 0 8px 20px rgba(124,92,255,0.22);
    }

    .btn-secondary:hover, .btn-primary-sm:hover {
      transform: translateY(-1px);
    }

    @media (max-width: 420px) {
      body { padding: 12px; }
      .menu-card { padding: 18px 16px; }
      .size-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
      .starter-grid { grid-template-columns: 1fr; }
      .game-footer { grid-template-columns: 1fr; }
      .depth-ticks { font-size: 0.6rem; }
    }
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"topbar\">
      <div class=\"brand\">
        <div class=\"dot-live\"></div>
        <div class=\"title\">TIC<span>//</span>TAC<span>//</span>TOE</div>
      </div>
      <button class=\"icon-btn\" id=\"sound-btn\" onclick=\"toggleSound()\" title=\"Dźwięk\">🔊</button>
    </div>

    <div id=\"menu-screen\" class=\"screen\">
      <div class=\"menu-card\">
        <div class=\"hero\">
          <span class=\"hero-badge\">Minimax α-β Engine</span>
          <h1>Skonfiguruj partię</h1>
          <p>Wybierz rozmiar planszy, poziom trudności i stronę rozpoczynającą.</p>
        </div>

        <div class=\"section\">
          <div class=\"section-head\">
            <span class=\"section-label\">Rozmiar planszy</span>
            <span class=\"section-hint\" id=\"size-hint\">3×3 · klasyczna</span>
          </div>
          <div class=\"size-grid\" id=\"size-options\">
            <div class=\"option-pill active\" data-val=\"3\" onclick=\"selectSize(3)\">
              <strong>3×3</strong>
              <span>Standard</span>
            </div>
            <div class=\"option-pill\" data-val=\"4\" onclick=\"selectSize(4)\">
              <strong>4×4</strong>
              <span>Taktyczna</span>
            </div>
            <div class=\"option-pill\" data-val=\"5\" onclick=\"selectSize(5)\">
              <strong>5×5</strong>
              <span>Rozszerzona</span>
            </div>
            <div class=\"option-pill\" data-val=\"6\" onclick=\"selectSize(6)\">
              <strong>6×6</strong>
              <span>Arena</span>
            </div>
          </div>
        </div>

        <div class=\"section\">
          <div class=\"section-head\">
            <span class=\"section-label\">Poziom inteligencji AI</span>
            <span class=\"section-hint\" id=\"depth-label\">Depth 9 · Niepokonany</span>
          </div>
          <div class=\"depth-box\">
            <input type=\"range\" id=\"depth-slider\" min=\"1\" max=\"9\" value=\"9\" oninput=\"updateDepthLabel()\">
            <div class=\"depth-ticks\">
              <span>1</span>
              <span>3</span>
              <span>6</span>
              <span>9</span>
            </div>
          </div>
        </div>

        <div class=\"section\">
          <div class=\"section-head\">
            <span class=\"section-label\">Kto zaczyna?</span>
          </div>
          <div class=\"starter-grid\">
            <div class=\"starter-card user-opt active\" id=\"opt-user\" onclick=\"selectStarter('user')\">
              <div class=\"starter-icon\">X</div>
              <div class=\"starter-info\">
                <strong>Gracz</strong>
                <span>Zaczynasz jako X</span>
              </div>
            </div>
            <div class=\"starter-card ai-opt\" id=\"opt-ai\" onclick=\"selectStarter('ai')\">
              <div class=\"starter-icon\">O</div>
              <div class=\"starter-info\">
                <strong>Komputer</strong>
                <span>AI zaczyna jako X</span>
              </div>
            </div>
          </div>
        </div>

        <button class=\"btn-start\" onclick=\"startGameFromMenu()\">Rozpocznij grę →</button>
      </div>
    </div>

    <div id=\"game-screen\" class=\"screen hidden\">
      <div class=\"scoreboard\">
        <div class=\"score-card x-card\">
          <span class=\"score-label\" id=\"lbl-human\">Ty (X)</span>
          <span class=\"score-val\" id=\"score-human\">0</span>
        </div>
        <div class=\"score-card d-card\">
          <span class=\"score-label\">Remisy</span>
          <span class=\"score-val\" id=\"score-draw\">0</span>
        </div>
        <div class=\"score-card o-card\">
          <span class=\"score-label\" id=\"lbl-ai\">AI (O)</span>
          <span class=\"score-val\" id=\"score-ai\">0</span>
        </div>
      </div>

      <div class=\"status-wrap\">
        <span id=\"status-text\">Gotowy</span>
        <span id=\"telemetry\">α-β pruning</span>
      </div>

      <div class=\"board-shell\">
        <div class=\"board\" id=\"board\"></div>
        <svg id=\"win-overlay\" viewBox=\"0 0 100 100\" preserveAspectRatio=\"none\">
          <line id=\"win-line\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"0\" opacity=\"0\"></line>
        </svg>
      </div>

      <div class=\"game-footer\">
        <button class=\"btn-secondary\" onclick=\"backToMenu()\">← Zmień ustawienia</button>
        <button class=\"btn-primary-sm\" onclick=\"newGame()\">↻ Zagraj ponownie</button>
      </div>
    </div>
  </div>

  <script>
    let selectedSize = 3;
    let selectedDepth = 9;
    let selectedStarter = 'user';

    let N = 3;
    let board = [];
    let human = 'X', ai = 'O';
    let gameOver = false;
    let thinking = false;
    let soundOn = true;
    const scores = { human: 0, ai: 0, draw: 0 };

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    function playTone(freq, type = 'sine', duration = 0.09, delay = 0) {
      if (!soundOn) return;
      if (audioCtx.state === 'suspended') audioCtx.resume();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime + delay);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime + delay);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + delay + duration);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(audioCtx.currentTime + delay);
      osc.stop(audioCtx.currentTime + delay + duration);
    }

    function toggleSound() {
      soundOn = !soundOn;
      document.getElementById('sound-btn').textContent = soundOn ? '🔊' : '🔇';
    }

    function selectSize(val) {
      selectedSize = val;
      document.querySelectorAll('#size-options .option-pill').forEach(el => {
        el.classList.toggle('active', parseInt(el.dataset.val) === val);
      });

      const hints = {
        3: '3×3 · klasyczna',
        4: '4×4 · taktyczna',
        5: '5×5 · rozszerzona',
        6: '6×6 · arena'
      };
      document.getElementById('size-hint').textContent = hints[val];

      const recommendedDepth = val === 3 ? 9 : 3;
      document.getElementById('depth-slider').value = recommendedDepth;
      updateDepthLabel();
      playTone(440, 'sine', 0.05);
    }

    function updateDepthLabel() {
      selectedDepth = parseInt(document.getElementById('depth-slider').value);
      let tier = 'Łatwy';
      if (selectedDepth >= 8) tier = 'Niepokonany';
      else if (selectedDepth >= 5) tier = 'Trudny';
      else if (selectedDepth >= 3) tier = 'Średni';

      document.getElementById('depth-label').textContent = `Depth ${selectedDepth} · ${tier}`;
    }

    function selectStarter(who) {
      selectedStarter = who;
      document.getElementById('opt-user').classList.toggle('active', who === 'user');
      document.getElementById('opt-ai').classList.toggle('active', who === 'ai');
      playTone(500, 'sine', 0.05);
    }

    function startGameFromMenu() {
      playTone(580, 'triangle', 0.1);
      document.getElementById('menu-screen').classList.add('hidden');
      document.getElementById('game-screen').classList.remove('hidden');
      newGame();
    }

    function backToMenu() {
      playTone(380, 'sine', 0.07);
      document.getElementById('game-screen').classList.add('hidden');
      document.getElementById('menu-screen').classList.remove('hidden');
    }

    function svgSymbol(player, isGhost = false) {
      if (player === 'X') {
        return `
          <svg class="${isGhost ? 'ghost symbol x-sym' : 'symbol x-sym'}" viewBox="0 0 100 100">
            <path d="M 20 20 L 80 80"></path>
            <path class="second" d="M 80 20 L 20 80"></path>
          </svg>
        `;
      }

      return `
        <svg class="${isGhost ? 'ghost symbol o-sym' : 'symbol o-sym'}" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="33"></circle>
        </svg>
      `;
    }

    function newGame() {
      N = selectedSize;
      const userStarts = selectedStarter === 'user';
      human = userStarts ? 'X' : 'O';
      ai = userStarts ? 'O' : 'X';
      board = Array.from({ length: N }, () => Array(N).fill(''));
      gameOver = false;
      thinking = false;

      document.getElementById('lbl-human').textContent = `Ty (${human})`;
      document.getElementById('lbl-ai').textContent = `AI (${ai})`;
      document.getElementById('telemetry').textContent = `depth ${selectedDepth}`;

      const line = document.getElementById('win-line');
      line.setAttribute('opacity', '0');
      line.style.strokeDashoffset = '1000';

      renderBoard();

      if (userStarts) {
        setStatus(`Twój ruch [${human}]`, human === 'X' ? 'var(--x)' : 'var(--o)');
      } else {
        setStatus('AI myśli...', 'var(--muted)');
        requestAiMove();
      }
    }

    function setStatus(text, color = 'var(--text)') {
      const el = document.getElementById('status-text');
      el.textContent = text;
      el.style.color = color;
    }

    function renderBoard() {
      const el = document.getElementById('board');
      el.style.gridTemplateColumns = `repeat(${N}, minmax(0, 1fr))`;
      el.innerHTML = '';

      for (let r = 0; r < N; r++) {
        for (let c = 0; c < N; c++) {
          const val = board[r][c];
          const cell = document.createElement('div');
          cell.className = 'cell' + (val ? ' taken' : '') + ((gameOver || thinking) ? ' locked' : '');
          cell.dataset.r = r;
          cell.dataset.c = c;

          if (val) {
            cell.innerHTML = svgSymbol(val);
          }

          cell.onclick = () => handleCellClick(r, c);
          el.appendChild(cell);
        }
      }
    }

    function handleCellClick(r, c) {
      if (gameOver || thinking || board[r][c] !== '') return;
      board[r][c] = human;
      playTone(520, 'triangle', 0.08);
      renderBoard();
      requestAiMove();
    }

    function drawWinLine(coords) {
      if (!coords || coords.length < 2) return;

      const [r1, c1] = coords[0];
      const [r2, c2] = coords[coords.length - 1];
      const step = 100 / N;
      const x1 = (c1 + 0.5) * step;
      const y1 = (r1 + 0.5) * step;
      const x2 = (c2 + 0.5) * step;
      const y2 = (r2 + 0.5) * step;

      const line = document.getElementById('win-line');
      line.setAttribute('x1', x1);
      line.setAttribute('y1', y1);
      line.setAttribute('x2', x2);
      line.setAttribute('y2', y2);
      line.setAttribute('opacity', '1');
      requestAnimationFrame(() => {
        line.style.strokeDashoffset = '0';
      });
    }

    async function requestAiMove() {
      thinking = true;
      setStatus('AI analizuje...', 'var(--muted)');

      const res = await fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          board,
          depth: selectedDepth,
          human,
          ai
        })
      });

      const data = await res.json();
      thinking = false;

      document.getElementById('telemetry').textContent = `depth ${selectedDepth} · ${data.elapsed_ms} ms`;

      if (data.ai_move) {
        const [ar, ac] = data.ai_move;
        board[ar][ac] = ai;
        playTone(360, 'sine', 0.09);
      }

      renderBoard();

      if (data.winner) {
        gameOver = true;
        renderBoard();

        if (data.winner === 'DRAW') {
          scores.draw++;
          document.getElementById('score-draw').textContent = scores.draw;
          setStatus('Remis — brak ruchów', 'var(--muted)');
          playTone(280, 'sine', 0.15);
        } else {
          data.win_coords.forEach(([wr, wc]) => {
            const target = document.querySelector(`.cell[data-r=\"${wr}\"][data-c=\"${wc}\"]`);
            if (target) target.classList.add('win');
          });
          drawWinLine(data.win_coords);

          if (data.winner === human) {
            scores.human++;
            document.getElementById('score-human').textContent = scores.human;
            setStatus('Zwycięstwo!', 'var(--win)');
            [523, 659, 784].forEach((f, i) => playTone(f, 'triangle', 0.18, i * 0.08));
          } else {
            scores.ai++;
            document.getElementById('score-ai').textContent = scores.ai;
            setStatus('AI wygrywa partię', 'var(--o)');
            [330, 260].forEach((f, i) => playTone(f, 'sawtooth', 0.18, i * 0.1));
          }
        }
      } else {
        setStatus(`Twój ruch [${human}]`, human === 'X' ? 'var(--x)' : 'var(--o)');
      }
    }
  </script>
</body>
</html>
"""


class MinimaxEngine:
    def __init__(self, n, human, ai, max_depth):
        self.N = n
        self.HUMAN = human
        self.AI = ai
        self.max_depth = max_depth

    def lines_with_coords(self):
        n = self.N
        res = [[(r, c) for c in range(n)] for r in range(n)]
        res += [[(r, c) for r in range(n)] for c in range(n)]
        res.append([(i, i) for i in range(n)])
        res.append([(i, n - 1 - i) for i in range(n)])
        return res

    def check_winner(self, b):
        for coords in self.lines_with_coords():
            vals = [b[r][c] for r, c in coords]
            if vals[0] != "" and len(set(vals)) == 1:
                return vals[0], coords
        if all(cell != "" for row in b for cell in row):
            return "DRAW", []
        return None, []

    def evaluate(self, b):
        score = 0;
        for coords in self.lines_with_coords():
            line = [b[r][c] for r, c in coords];
            if self.HUMAN not in line and self.AI in line:
                score += 10 ** line.count(self.AI);
            elif self.AI not in line and self.HUMAN in line:
                score -= 10 ** line.count(self.HUMAN);
        return score;

    def minimax(self, b, depth, is_max, alpha, beta):
        winner, _ = self.check_winner(b)
        if winner == self.AI:
            return 10 ** (self.N + 1) - depth, None
        if winner == self.HUMAN:
            return -(10 ** (self.N + 1)) + depth, None
        if winner == "DRAW":
            return 0, None
        if depth >= self.max_depth:
            return self.evaluate(b), None

        best_score = -math.inf if is_max else math.inf
        best_move = None

        for r in range(self.N):
            for c in range(self.N):
                if b[r][c] == "":
                    b[r][c] = self.AI if is_max else self.HUMAN
                    score, _ = self.minimax(b, depth + 1, not is_max, alpha, beta)
                    b[r][c] = ""
                    if is_max:
                        if score > best_score:
                            best_score, best_move = score, (r, c)
                        alpha = max(alpha, best_score)
                    else:
                        if score < best_score:
                            best_score, best_move = score, (r, c)
                        beta = min(beta, best_score)
                    if beta <= alpha:
                        return best_score, best_move

        return best_score, best_move;


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        if self.path != "/move":
            self.send_error(404)
            return

        t0 = time.perf_counter()
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))

        board = payload["board"]
        engine = MinimaxEngine(
            n=len(board),
            human=payload["human"],
            ai=payload["ai"],
            max_depth=max(1, min(9, int(payload["depth"]))),
        )

        winner, coords = engine.check_winner(board)
        ai_move = None

        if not winner:
            _, move = engine.minimax(board, 0, True, -math.inf, math.inf)
            if move:
                ai_move = list(move)
                board[move[0]][move[1]] = engine.AI
            winner, coords = engine.check_winner(board)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "ai_move": ai_move,
                    "winner": winner,
                    "win_coords": coords,
                    "elapsed_ms": elapsed_ms,
                }
            ).encode("utf-8")
        )


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}"
    print(f"Serwer uruchomiony: {url} (Ctrl+C aby zakończyć)")
    threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()