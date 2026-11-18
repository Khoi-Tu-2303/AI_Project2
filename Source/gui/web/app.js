/* =========================================================================
   HỒ SƠ LOGIC: GRIDUCTIVE — LOGIC TƯƠNG TÁC & TRỰC QUAN HÓA LUỒNG DPLL (APP.JS)
   ========================================================================= */

/* =========================================================================
   ĐỘNG CƠ KHÍ QUYỂN ĐIỆN ẢNH (CINEMATIC ATMOSPHERE CANVAS ENGINE)
   Ánh sáng đèn bàn rọi (Spotlight) lướt êm ái & Hạt bụi hổ phách / Khói lơ lửng
   ========================================================================= */
class AtmosphereEngine {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.particles = [];
    this.numParticles = 48;
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.mouseX = this.width * 0.5;
    this.mouseY = this.height * 0.35;
    this.spotX = this.mouseX;
    this.spotY = this.mouseY;
    this.lastMouseMove = Date.now();
    this.animId = null;
    this.init();
  }

  init() {
    this.resize();
    window.addEventListener("resize", () => this.resize(), { passive: true });
    window.addEventListener("mousemove", (e) => {
      this.mouseX = e.clientX;
      this.mouseY = e.clientY;
      this.lastMouseMove = Date.now();
    }, { passive: true });

    // Khởi tạo các hạt bụi hổ phách và tàn khói
    for (let i = 0; i < this.numParticles; i++) {
      this.particles.push({
        x: Math.random() * this.width,
        y: Math.random() * this.height,
        vx: (Math.random() - 0.5) * 0.45,
        vy: -0.2 - Math.random() * 0.4,
        size: 1.2 + Math.random() * 2.8,
        baseAlpha: 0.25 + Math.random() * 0.55,
        pulseOffset: Math.random() * Math.PI * 2,
        isSmoke: Math.random() < 0.25,
      });
    }

    this.start();
  }

  resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.canvas.width = Math.floor(this.width * dpr);
    this.canvas.height = Math.floor(this.height * dpr);
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(dpr, dpr);
  }

  start() {
    const loop = (t) => {
      this.draw(t);
      this.animId = requestAnimationFrame(loop);
    };
    this.animId = requestAnimationFrame(loop);
  }

  draw(t) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Quán tính vị trí đèn rọi bàn (Lerp hoặc tự đung đưa khi chuột đứng yên)
    const idleTime = Date.now() - this.lastMouseMove;
    if (idleTime > 1600) {
      const angle = (t * 0.00035);
      const wanderX = this.width * 0.5 + Math.cos(angle) * (this.width * 0.22);
      const wanderY = this.height * 0.38 + Math.sin(angle * 1.4) * (this.height * 0.14);
      this.spotX += (wanderX - this.spotX) * 0.03;
      this.spotY += (wanderY - this.spotY) * 0.03;
    } else {
      this.spotX += (this.mouseX - this.spotX) * 0.07;
      this.spotY += (this.mouseY - this.spotY) * 0.07;
    }

    // 2. Lớp phủ khí quyển điện ảnh bán trong suốt (không che khuất ảnh nền)
    const tintGrad = ctx.createLinearGradient(0, 0, 0, this.height);
    tintGrad.addColorStop(0, "rgba(6, 9, 15, 0.40)");
    tintGrad.addColorStop(0.5, "rgba(10, 14, 24, 0.28)");
    tintGrad.addColorStop(1, "rgba(6, 9, 15, 0.50)");
    ctx.fillStyle = tintGrad;
    ctx.fillRect(0, 0, this.width, this.height);

    // 3. Vệt sáng rèm cửa sổ chớp đặc trưng phim noir (Venetian Blinds Effect)
    ctx.save();
    ctx.rotate(-0.22);
    const blindStep = 64;
    const blindWidth = 28;
    for (let bx = -this.height * 1.5; bx < this.width + this.height * 1.5; bx += blindStep) {
      const bAlpha = 0.065 + 0.035 * Math.sin(t * 0.0008 + bx * 0.03);
      const bGrad = ctx.createLinearGradient(bx, 0, bx + blindWidth, 0);
      bGrad.addColorStop(0, "rgba(255, 205, 120, 0)");
      bGrad.addColorStop(0.5, `rgba(255, 205, 120, ${bAlpha})`);
      bGrad.addColorStop(1, "rgba(255, 205, 120, 0)");
      ctx.fillStyle = bGrad;
      ctx.fillRect(bx, -this.height * 2, blindWidth, this.height * 4);
    }
    ctx.restore();

    // 4. Lưới tọa độ bàn sa bàn thám tử mờ nhẹ
    ctx.strokeStyle = "rgba(245, 185, 80, 0.055)";
    ctx.lineWidth = 1;
    const step = 56;
    for (let x = 0; x < this.width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.height);
      ctx.stroke();
    }
    for (let y = 0; y < this.height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.width, y);
      ctx.stroke();
    }

    // 5. Quầng sáng ấm áp của đèn chụp bàn thám tử (Desk Lamp Spotlight)
    const spotRadius = Math.max(560, Math.min(this.width, this.height) * 0.85);
    const spotGrad = ctx.createRadialGradient(
      this.spotX, this.spotY, 15,
      this.spotX, this.spotY, spotRadius
    );
    spotGrad.addColorStop(0, "rgba(255, 195, 90, 0.45)");
    spotGrad.addColorStop(0.2, "rgba(240, 160, 55, 0.26)");
    spotGrad.addColorStop(0.5, "rgba(180, 100, 30, 0.11)");
    spotGrad.addColorStop(0.8, "rgba(120, 60, 15, 0.035)");
    spotGrad.addColorStop(1, "rgba(0, 0, 0, 0)");

    ctx.fillStyle = spotGrad;
    ctx.fillRect(0, 0, this.width, this.height);

    // 6. Hạt bụi vàng lơ lửng bắt sáng trong chùm đèn & làn khói mảnh
    const timeSec = t * 0.001;
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.x += p.vx + Math.sin(timeSec + p.pulseOffset) * 0.3;
      p.y += p.vy;

      if (p.y < -20) {
        p.y = this.height + 15;
        p.x = Math.random() * this.width;
      }
      if (p.x < -20) p.x = this.width + 15;
      if (p.x > this.width + 20) p.x = -15;

      const dist = Math.hypot(p.x - this.spotX, p.y - this.spotY);
      const inLight = Math.max(0.35, 1.0 - dist / spotRadius);
      const pulse = 0.7 + 0.3 * Math.sin(timeSec * 2.2 + p.pulseOffset);
      const alpha = p.baseAlpha * inLight * pulse;

      ctx.save();
      ctx.beginPath();
      if (p.isSmoke) {
        ctx.arc(p.x, p.y, p.size * 3.8, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(225, 205, 175, ${alpha * 0.35})`;
        ctx.fill();
      } else {
        ctx.arc(p.x, p.y, p.size * 1.6, 0, Math.PI * 2);
        ctx.shadowColor = "rgba(255, 215, 95, 0.85)";
        ctx.shadowBlur = p.size * 3.5;
        ctx.fillStyle = `rgba(255, 220, 115, ${Math.min(1, alpha * 1.6)})`;
        ctx.fill();
      }
      ctx.restore();
    }
  }
}

let currentState = null;
let autoTimer = null;
let lastAnimatedCell = null;
let lastAnimationKind = null;
let currentCaseFilter = "official";
let victoryShownForSession = null;
let selectedVisualStep = null; // null = tự động bám theo bước mới nhất; 0..k = bước đang xem
let visualizerOpen = true;

// Các trạng thái mở rộng: Âm thanh, Ghi chú nháp, Dây chỉ đỏ SVG, Playback
let audioCtx = null;
let soundEnabled = localStorage.getItem("griductive_sound") !== "off";
let pencilNotes = {}; // cell -> "innocent" | "criminal"
let pencilModeActive = false;
let crimeStringsEnabled = true;
let playbackTimer = null;
let playbackSpeed = 1.0;

function initAudio() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) audioCtx = new AudioContextClass();
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }
}

function playSfx(type) {
  if (!soundEnabled) return;
  try {
    initAudio();
    if (!audioCtx) return;
    const now = audioCtx.currentTime;
    if (type === "click" || type === "flip") {
      // Tiếng gõ phím máy chữ cơ học (Vintage Typewriter Key Click)
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(1200, now);
      osc.frequency.exponentialRampToValueAtTime(150, now + 0.038);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.038);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.038);
    } else if (type === "stamp_innocent") {
      // Con dấu Vô Tội mộc cao su (Emerald Stamp Thud)
      [240, 480].forEach((freq, i) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = i === 0 ? "triangle" : "sine";
        osc.frequency.setValueAtTime(freq, now + i * 0.025);
        osc.frequency.exponentialRampToValueAtTime(75, now + i * 0.025 + 0.16);
        gain.gain.setValueAtTime(0.24, now + i * 0.025);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.025 + 0.17);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now + i * 0.025);
        osc.stop(now + i * 0.025 + 0.17);
      });
    } else if (type === "stamp_criminal") {
      // Con dấu Thủ Phạm đập đanh thép (Crimson Stamp Heavy Thud)
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(160, now);
      osc.frequency.exponentialRampToValueAtTime(45, now + 0.22);
      gain.gain.setValueAtTime(0.32, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.22);
    } else if (type === "paper") {
      // Tiếng lật xào xạc của hồ sơ tài liệu
      const bufferSize = Math.floor(audioCtx.sampleRate * 0.08);
      const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.35));
      }
      const noise = audioCtx.createBufferSource();
      noise.buffer = buffer;
      const filter = audioCtx.createBiquadFilter();
      filter.type = "bandpass";
      filter.frequency.value = 1800;
      filter.Q.value = 1.4;
      const gain = audioCtx.createGain();
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      noise.connect(filter);
      filter.connect(gain);
      gain.connect(audioCtx.destination);
      noise.start(now);
    } else if (type === "twang") {
      // Tiếng gảy dây chỉ đỏ liên kết (Red Yarn String Twang)
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(340, now);
      osc.frequency.exponentialRampToValueAtTime(110, now + 0.14);
      gain.gain.setValueAtTime(0.16, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(now);
      osc.stop(now + 0.14);
    } else if (type === "not_provable") {
      [360, 240].forEach((freq, i) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "square";
        osc.frequency.setValueAtTime(freq, now + i * 0.08);
        gain.gain.setValueAtTime(0.09, now + i * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.08 + 0.12);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now + i * 0.08);
        osc.stop(now + i * 0.08 + 0.12);
      });
    } else if (type === "victory") {
      [261.63, 329.63, 392.00, 523.25].forEach((freq, i) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, now + i * 0.09);
        gain.gain.setValueAtTime(0.18, now + i * 0.09);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.09 + 0.45);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now + i * 0.09);
        osc.stop(now + i * 0.09 + 0.45);
      });
    }
  } catch (e) {}
}

function toggleSound() {
  soundEnabled = !soundEnabled;
  localStorage.setItem("griductive_sound", soundEnabled ? "on" : "off");
  updateSoundIcon();
  if (soundEnabled) playSfx("click");
}

function updateSoundIcon() {
  const iconOn = document.getElementById("iconSoundOn");
  const iconOff = document.getElementById("iconSoundOff");
  if (iconOn && iconOff) {
    iconOn.style.display = soundEnabled ? "block" : "none";
    iconOff.style.display = soundEnabled ? "none" : "block";
  }
}

function togglePencilMode() {
  pencilModeActive = !pencilModeActive;
  const btn = document.getElementById("btnPencilMode");
  if (btn) btn.classList.toggle("active", pencilModeActive);
  playSfx("click");
}

function cyclePencilNote(cell) {
  const cur = pencilNotes[cell];
  if (!cur) {
    pencilNotes[cell] = "innocent";
  } else if (cur === "innocent") {
    pencilNotes[cell] = "criminal";
  } else {
    delete pencilNotes[cell];
  }
  playSfx("click");
  if (currentState) render(currentState);
}

function toggleCrimeStrings() {
  crimeStringsEnabled = !crimeStringsEnabled;
  const btn = document.getElementById("btnStringsToggle");
  if (btn) btn.classList.toggle("active", crimeStringsEnabled);
  const layer = document.getElementById("crimeStringsLayer");
  if (layer) {
    if (!crimeStringsEnabled) layer.innerHTML = "";
    else renderCrimeStrings(currentState);
  }
  playSfx("click");
}

const OFFICIAL_SIX_IDS = [
  "3x3_classic",
  "3x3_extensions",
  "4x4_detective",
  "4x4_crossfire",
  "5x5_mastermind",
  "5x5_syndicate",
];

function isOfficialSix(caseId) {
  return OFFICIAL_SIX_IDS.includes(caseId);
}

function getSolvedCases() {
  try {
    return JSON.parse(localStorage.getItem("griductive_solved_cases") || "[]");
  } catch (e) {
    return [];
  }
}

function markCaseSolved(puzzleId) {
  try {
    const list = getSolvedCases();
    if (!list.includes(puzzleId)) {
      list.push(puzzleId);
      localStorage.setItem("griductive_solved_cases", JSON.stringify(list));
    }
  } catch (e) {}
}

function showScreen(screenId) {
  stopAutoSolve();
  playSfx("paper");
  document.querySelectorAll(".screen").forEach(el => el.classList.remove("active"));
  const target = document.getElementById(screenId);
  if (target) target.classList.add("active");
  if (screenId === "screenStart") {
    updateStartScreenStats();
  }
  if (screenId === "screenCases" && currentState) {
    renderCaseSelection(currentState.puzzles || []);
  }
}

function updateStartScreenStats() {
  const solved = getSolvedCases();
  const officialSolved = solved.filter(id => isOfficialSix(id)).length;
  const total = 6;
  const pct = Math.min(100, Math.round((officialSolved / total) * 100));

  const fillEl = document.getElementById("startProgressBarFill");
  if (fillEl) fillEl.style.width = `${pct}%`;

  const progLbl = document.getElementById("lblDetectiveProgress");
  if (progLbl) progLbl.textContent = `Tiến độ: ${officialSolved}/${total} vụ án chuẩn`;

  const rankLbl = document.getElementById("lblDetectiveRank");
  if (rankLbl) {
    let rankText = "CẤP BẬC: THÁM TỬ TẬP SỰ";
    if (officialSolved >= 6) {
      rankText = "CẤP BẬC: BẬC THẦY LOGIC MỆNH ĐỀ";
    } else if (officialSolved >= 4) {
      rankText = "CẤP BẬC: CHUYÊN GIA PHÁ ÁN";
    } else if (officialSolved >= 2) {
      rankText = "CẤP BẬC: TRINH SÁT HIỆN TRƯỜNG";
    } else if (officialSolved >= 1) {
      rankText = "CẤP BẬC: THÁM TỬ ĐIỀU TRA";
    }
    rankLbl.textContent = rankText;
  }
}

const DOSSIER_DATA = {
  "3x3": {
    id: "3x3_classic",
    stamp: "ÁN LỆ #01 · PHẢN CHỨNG",
    diff: "⭐☆☆ ĐỘ KHÓ: CĂN BẢN",
    title: "Chuỗi Suy Luận Phản Chứng",
    n: 3,
    specs: ["📐 Kích Thước: <strong>3×3 (9 Ô)</strong>", "👤 Nghi Phạm: <strong>9 Người</strong>", "🎯 Kẻ Chủ Mưu: <strong>1 Thủ Phạm</strong>"],
    quote: "Nghi phạm ban đầu chỉ điểm kẻ đồng lõa, kích hoạt chuỗi suy luận phản chứng liên hoàn trên bàn cờ 9 ô để bóc tách kẻ nói dối."
  },
  "4x4": {
    id: "4x4_detective",
    stamp: "ÁN LỆ #03 · GALA THƯỢNG LƯU",
    diff: "⭐⭐☆ ĐỘ KHÓ: NÂNG CAO",
    title: "Thám Tử Gala Thượng Lưu",
    n: 4,
    specs: ["📐 Kích Thước: <strong>4×4 (16 Ô)</strong>", "👤 Nghi Phạm: <strong>16 Người</strong>", "🔍 Ràng Buộc: <strong>Vùng Lân Cận</strong>"],
    quote: "Vụ án mạng tại dạ tiệc thượng lưu với các lời khai so sánh vùng lân cận và đếm số lượng phức tạp trên 16 ô."
  },
  "5x5": {
    id: "5x5_mastermind",
    stamp: "ÁN LỆ #05 · ĐẠI MA TRẬN",
    diff: "⭐⭐⭐ ĐỘ KHÓ: THỬ THÁCH",
    title: "Bậc Thầy Trí Tuệ Logic",
    n: 5,
    specs: ["📐 Kích Thước: <strong>5×5 (25 Ô)</strong>", "👤 Nghi Phạm: <strong>25 Người</strong>", "⚡ Thách Thức: <strong>Bộ Giải DPLL</strong>"],
    quote: "Ma trận 25 nghi phạm với hàng chục biến phụ trợ và mạng lưới lời khai quy mô lớn, thử thách bộ giải DPLL đỉnh cao."
  }
};

function switchDossierTab(tier) {
  playSfx("click");
  document.querySelectorAll(".dossier-pill-btn").forEach(btn => btn.classList.remove("active"));
  const btnId = tier === "3x3" ? "tabDossier3" : (tier === "4x4" ? "tabDossier4" : "tabDossier5");
  const btn = document.getElementById(btnId);
  if (btn) btn.classList.add("active");

  const data = DOSSIER_DATA[tier] || DOSSIER_DATA["3x3"];
  const stampEl = document.getElementById("dossierStamp");
  const diffEl = document.getElementById("dossierDiff");
  const titleEl = document.getElementById("dossierTitle");
  const specsEl = document.getElementById("dossierSpecs");
  const quoteEl = document.getElementById("dossierQuote");
  const playBtn = document.getElementById("btnPlayDossier");
  const gridEl = document.getElementById("dossierMiniGrid");

  if (stampEl) stampEl.textContent = data.stamp;
  if (diffEl) diffEl.textContent = data.diff;
  if (titleEl) titleEl.textContent = data.title;
  if (specsEl) specsEl.innerHTML = data.specs.map(s => `<span class="spec-chip">${s}</span>`).join("");
  if (quoteEl) quoteEl.textContent = `"${data.quote}"`;
  if (playBtn) playBtn.onclick = () => launchSpotlightCase(data.id);

  if (gridEl) {
    gridEl.innerHTML = "";
    gridEl.style.gridTemplateColumns = `repeat(${data.n}, 1fr)`;
    const totalCells = data.n * data.n;
    for (let i = 0; i < totalCells; i++) {
      const cell = document.createElement("div");
      cell.className = "mini-cell";
      if (i === 0) cell.classList.add("revealed");
      if (i === Math.floor(totalCells / 2)) cell.classList.add("target");
      gridEl.appendChild(cell);
    }
  }
}

async function launchSpotlightCase(caseId) {
  stopAutoSolve();
  selectedVisualStep = null;
  playSfx("flip");
  const data = await apiCall("/api/load", { case_id: caseId });
  render(data);
  showScreen("screenGame");
}

function openModal(id) {
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

function toggleDrawer(open) {
  const dr = document.getElementById("aiDrawer");
  const bd = document.getElementById("drawerBackdrop");
  if (open) {
    dr.classList.add("open");
    bd.classList.add("open");
  } else {
    dr.classList.remove("open");
    bd.classList.remove("open");
  }
}

function toggleVisualizerPanel(forceOpen) {
  if (typeof forceOpen === "boolean") {
    visualizerOpen = forceOpen;
  } else {
    visualizerOpen = !visualizerOpen;
  }
  const panel = document.getElementById("liveVisualizer");
  const btn = document.getElementById("btnToggleVisualizer");
  if (panel) panel.classList.toggle("hidden", !visualizerOpen);
  if (btn) btn.classList.toggle("active", visualizerOpen);
}

function toggleTheme() {
  const html = document.documentElement;
  const next = html.dataset.theme === "noir" ? "paper" : "noir";
  html.dataset.theme = next;
  const lbl = document.getElementById("lblThemeStart");
  if (lbl) {
    lbl.textContent = next === "noir"
      ? "Giao diện: Đêm Trinh Thám"
      : "Giao diện: Hồ Sơ Cổ Điển";
  }
}

async function startImmediateInvestigation() {
  if (!currentState) {
    await apiCall("/api/state", {});
  }
  showScreen("screenGame");
}

function setCaseFilter(f) {
  currentCaseFilter = f;
  document.querySelectorAll("#caseFilterTabs .filter-tab").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.filter === f);
  });
  if (currentState && currentState.puzzles) {
    renderCaseSelection(currentState.puzzles);
  }
}

function renderCaseSelection(puzzles) {
  const grid = document.getElementById("casesGrid");
  if (!grid) return;
  grid.innerHTML = "";
  const solved = getSolvedCases();

  const isFixture = id => id === "chain_demo" || id === "3x3_chain";
  const filtered = puzzles.filter(p => {
    if (currentCaseFilter === "official") return isOfficialSix(p.case_id);
    if (currentCaseFilter === "all") return true;
    if (currentCaseFilter === "edge") return (p.kind !== "normal" && p.kind !== "stress") || isFixture(p.case_id);
    return String(p.n) === currentCaseFilter && isOfficialSix(p.case_id);
  }).sort((a, b) => {
    const ia = OFFICIAL_SIX_IDS.indexOf(a.case_id);
    const ib = OFFICIAL_SIX_IDS.indexOf(b.case_id);
    if (ia !== -1 && ib !== -1) return ia - ib;
    if (ia !== -1) return -1;
    if (ib !== -1) return 1;
    return 0;
  });

  filtered.forEach(p => {
    const isSolved = solved.includes(p.case_id);
    const diffLevel = p.difficulty || 1;
    const diffStars = "★".repeat(diffLevel) + "☆".repeat(Math.max(0, 3 - diffLevel));
    const diffLabel = `CẤP ĐỘ ${diffLevel}/3`;
    const card = document.createElement("div");
    card.className = "dossier-card" + (isSolved ? " is-solved" : "");
    card.innerHTML = `
      <div class="dossier-folder-tab">
        <span class="dossier-code">${p.code || "HỒ SƠ"} · ${p.n}×${p.n}</span>
        <span class="dossier-tab-security">MẬT</span>
      </div>
      <div class="dossier-paperclip" title="Kẹp hồ sơ kim loại hiện trường">
        <svg width="22" height="38" viewBox="0 0 24 44" fill="none" stroke="#D4AF37" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 14v18a5 5 0 0 0 10 0V9a3 3 0 0 0-6 0v21a1 1 0 0 0 2 0V14" />
        </svg>
      </div>
      <div class="dossier-stamp-classified ${isSolved ? 'dossier-stamp-solved' : ''}">
        ${isSolved ? 'ĐÃ PHÁ ÁN' : 'TỐI MẬT'}
      </div>
      <div class="dossier-body">
        <div class="dossier-top">
          <div class="dossier-stars-rating" title="Độ khó: ${diffLabel}">
            <span class="stars-gold">${diffStars}</span>
            <span class="diff-text">${diffLabel}</span>
          </div>
          ${isSolved ? '<span class="solved-pill">✓ ĐÃ PHÁ ÁN</span>' : '<span class="unsolved-pill">ĐANG ĐIỀU TRA</span>'}
        </div>
        <div class="dossier-title">${p.title || p.case_id}</div>
        <div class="dossier-sub">${p.subtitle || ""}</div>
        <div class="dossier-story-box">
          <p class="dossier-story">${p.story || ""}</p>
        </div>
      </div>
      <div class="dossier-footer">
        <span class="dossier-tag">${p.badge || (p.n + "×" + p.n)}</span>
        <button type="button" class="btn-dossier-open dossier-cta">
          <span>Mở Hồ Sơ Điều Tra</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
      </div>
    `;
    card.addEventListener("click", async () => {
      selectedVisualStep = null;
      const data = await apiCall("/api/load", { case_id: p.case_id });
      render(data);
      showScreen("screenGame");
    });
    grid.appendChild(card);
  });
}

/* Minh họa Chân dung Hồ sơ Mugshot Noir theo 14 nhóm nghề nghiệp */
function suspectPortraitSvg(profession, isRevealed, status) {
  const p = (profession || "").toLowerCase();
  let accent = "#F59E0B";
  let suit = "#263147";
  let lapel = "#475569";
  let accessory = "";

  if (p.includes("thám tử") || p.includes("thanh tra") || p.includes("cảnh sát") || p.includes("đặc vụ") || p.includes("chỉ huy") || p.includes("tình báo")) {
    accent = "#F59E0B"; suit = "#1E293B"; lapel = "#D97706";
    // Fedora noir hat + brass detective lapel star
    accessory = `
      <path d="M9 15 Q22 10.5 35 15" stroke="${accent}" stroke-width="2.2" stroke-linecap="round"/>
      <path d="M14 14.5 L16.2 9.2 L27.8 9.2 L30 14.5 Z" fill="${accent}" fill-opacity="0.88"/>
      <circle cx="27.5" cy="33" r="1.8" fill="#FDE68A"/>`;
  } else if (p.includes("vệ sĩ") || p.includes("bảo vệ") || p.includes("tuần tra") || p.includes("an ninh") || p.includes("quân") || p.includes("đại tá")) {
    accent = "#38BDF8"; suit = "#172554"; lapel = "#3B82F6";
    // Security tactical collar + coiled earpiece
    accessory = `
      <rect x="15.5" y="16.5" width="13" height="3.2" rx="1.5" fill="#0F172A" stroke="${accent}" stroke-width="1"/>
      <path d="M28.5 21 C31 22, 30 26, 28 28" stroke="${accent}" stroke-width="1.3" fill="none"/>`;
  } else if (p.includes("bác sĩ") || p.includes("dược") || p.includes("pháp y") || p.includes("y tá") || p.includes("quân y")) {
    accent = "#2DD4BF"; suit = "#134E4A"; lapel = "#5EEAD4";
    // Stethoscope + medical cross pin
    accessory = `
      <path d="M16 26 C16 32, 28 32, 28 26" stroke="${accent}" stroke-width="1.6" fill="none"/>
      <circle cx="25.5" cy="32.5" r="1.9" fill="${accent}"/>`;
  } else if (p.includes("bếp") || p.includes("pha chế") || p.includes("hầu bàn") || p.includes("rượu") || p.includes("baker") || p.includes("chef")) {
    accent = "#FB923C"; suit = "#3F2E26"; lapel = "#FDBA74";
    // Classic toque / bow-tie
    accessory = `
      <path d="M14 13.5 C13 8, 31 8, 30 13.5 Z" fill="#F8FAFC" stroke="${accent}" stroke-width="1.3"/>
      <polygon points="19,28 22,29.6 19,31.2" fill="${accent}"/>
      <polygon points="25,28 22,29.6 25,31.2" fill="${accent}"/>`;
  } else if (p.includes("tàu") || p.includes("thuyền") || p.includes("hoa tiêu") || p.includes("thủy thủ") || p.includes("phi công") || p.includes("cảng") || p.includes("hải đăng")) {
    accent = "#60A5FA"; suit = "#1E3A8A"; lapel = "#93C5FD";
    // Officer peaked cap + gold wing emblem
    accessory = `
      <path d="M12 14.5 L32 14.5 L29.5 9.8 L14.5 9.8 Z" fill="#1E3A8A" stroke="${accent}" stroke-width="1.4"/>
      <path d="M11 14.8 Q22 13 33 14.8" stroke="#FBBF24" stroke-width="2" stroke-linecap="round"/>
      <circle cx="22" cy="12.2" r="1.3" fill="#FBBF24"/>`;
  } else if (p.includes("luật sư") || p.includes("thẩm phán") || p.includes("ngoại giao") || p.includes("đại sứ") || p.includes("tùy viên") || p.includes("nghị sự")) {
    accent = "#C084FC"; suit = "#2E1065"; lapel = "#E9D5FF";
    // Diplomatic cravat + gold pin
    accessory = `
      <path d="M19 26.5 L22 35 L25 26.5 Z" fill="#FDE68A" fill-opacity="0.9"/>
      <circle cx="22" cy="29.5" r="1.3" fill="${accent}"/>`;
  } else if (p.includes("mật mã") || p.includes("kỹ sư") || p.includes("kiến trúc") || p.includes("it") || p.includes("radar") || p.includes("dữ liệu") || p.includes("điện tín") || p.includes("viễn thông") || p.includes("mở khóa")) {
    accent = "#34D399"; suit = "#064E3B"; lapel = "#6EE7B7";
    // Precision round frames
    accessory = `
      <circle cx="19" cy="18.2" r="2.5" stroke="${accent}" stroke-width="1.4" fill="#0F172A" fill-opacity="0.45"/>
      <circle cx="25" cy="18.2" r="2.5" stroke="${accent}" stroke-width="1.4" fill="#0F172A" fill-opacity="0.45"/>
      <line x1="21.5" y1="18.2" x2="22.5" y2="18.2" stroke="${accent}" stroke-width="1.4"/>`;
  } else if (p.includes("ca sĩ") || p.includes("opera") || p.includes("vũ công") || p.includes("nghệ sĩ") || p.includes("nhạc") || p.includes("họa sĩ") || p.includes("nhiếp ảnh") || p.includes("jazz") || p.includes("piano") || p.includes("saxophone") || p.includes("phục trang")) {
    accent = "#F472B6"; suit = "#500724"; lapel = "#FBCFE8";
    // Beret / stage pearl strand
    accessory = `
      <ellipse cx="23" cy="11.2" rx="8" ry="3.2" transform="rotate(-8 23 11.2)" fill="${accent}" fill-opacity="0.85"/>
      <path d="M17.5 27.5 Q22 31 26.5 27.5" stroke="#FDE68A" stroke-width="1.6" stroke-dasharray="1.5 2" fill="none"/>`;
  } else if (p.includes("giám tuyển") || p.includes("giáo sư") || p.includes("sử học") || p.includes("thực vật") || p.includes("kiểm định") || p.includes("sưu tầm") || p.includes("lưu trữ")) {
    accent = "#FBBF24"; suit = "#3E2723"; lapel = "#D7CCC8";
    // Scholar monocle + chain
    accessory = `
      <circle cx="25" cy="18.2" r="2.7" stroke="#FBBF24" stroke-width="1.5" fill="none"/>
      <path d="M27.3 19.8 Q28.5 24 26.5 28" stroke="#FBBF24" stroke-width="1" fill="none"/>`;
  } else if (p.includes("nhà báo") || p.includes("phóng viên") || p.includes("phiên dịch")) {
    accent = "#FDBA74"; suit = "#292524"; lapel = "#E7E5E4";
    // Press fedora with white press card
    accessory = `
      <path d="M10 14.5 Q22 11 34 14.5" stroke="${accent}" stroke-width="2" stroke-linecap="round"/>
      <path d="M15 14.2 L17 9.5 L27 9.5 L29 14.2 Z" fill="#44403C"/>
      <rect x="23.5" y="10.6" width="3.2" height="2.4" rx="0.4" fill="#FEF3C7"/>`;
  } else if (p.includes("tài phiệt") || p.includes("chủ") || p.includes("bá tước") || p.includes("nữ hoàng") || p.includes("thừa kế") || p.includes("kim hoàn") || p.includes("thương")) {
    accent = "#FDE047"; suit = "#3B0764"; lapel = "#FEF08A";
    // Diamond lapel brooch + high collar
    accessory = `
      <polygon points="22,27 24.4,29.6 22,32.2 19.6,29.6" fill="#FEF08A" stroke="${accent}" stroke-width="0.9"/>`;
  } else {
    accent = "#94A3B8"; suit = "#1E293B"; lapel = "#CBD5E1";
    // Formal bow-tie / executive tie
    accessory = `
      <polygon points="18.8,27.8 22,29.5 18.8,31.2" fill="${accent}"/>
      <polygon points="25.2,27.8 22,29.5 25.2,31.2" fill="${accent}"/>`;
  }

  if (isRevealed) {
    if (status === "INNOCENT") {
      suit = "#065F46";
      lapel = "#34D399";
      accent = "#10B981";
    } else {
      suit = "#9F1239";
      lapel = "#FDA4AF";
      accent = "#F43F5E";
    }
  }

  const headFill = isRevealed ? "#F5E6CA" : "#1E293B";
  const headStroke = isRevealed ? accent : "rgba(248, 250, 252, 0.32)";
  const ruleStroke = isRevealed ? "rgba(15, 23, 42, 0.12)" : "rgba(255, 255, 255, 0.09)";

  return `<svg class="mugshot-svg" viewBox="0 0 44 44" fill="none" aria-hidden="true">
    <line x1="5" y1="11" x2="39" y2="11" stroke="${ruleStroke}" stroke-width="0.9"/>
    <line x1="5" y1="19" x2="39" y2="19" stroke="${ruleStroke}" stroke-width="0.9"/>
    <line x1="5" y1="27" x2="39" y2="27" stroke="${ruleStroke}" stroke-width="0.9"/>
    <path d="M7.5 41 C8 30.2, 36 30.2, 36.5 41 Z" fill="${suit}" stroke="${headStroke}" stroke-width="1.1"/>
    <path d="M17.5 27.2 L22 34.5 L26.5 27.2" stroke="${lapel}" stroke-width="1.5" fill="none" stroke-linejoin="round"/>
    <circle cx="22" cy="18.5" r="6.4" fill="${headFill}" stroke="${headStroke}" stroke-width="1.4"/>
    ${isRevealed
      ? `<circle cx="19.8" cy="18.2" r="0.95" fill="#1E293B"/><circle cx="24.2" cy="18.2" r="0.95" fill="#1E293B"/><path d="M19.8 21.3 Q22 22.4 24.2 21.3" stroke="#334155" stroke-width="1.1" stroke-linecap="round"/>`
      : `<text x="22" y="21.2" text-anchor="middle" fill="rgba(245, 158, 11, 0.72)" font-size="8.5" font-family="JetBrains Mono, monospace" font-weight="800">?</text>`
    }
    ${accessory}
  </svg>`;
}

function getHighlightTopTag(role) {
  if (!role) return "";
  if (role === "LEFT") return `<span class="hl-top-tag hl-left">VẾ TRÁI</span>`;
  if (role === "RIGHT") return `<span class="hl-top-tag hl-right">VẾ PHẢI</span>`;
  if (role === "L∩R") return `<span class="hl-top-tag hl-overlap">GIAO NHAU</span>`;
  return `<span class="hl-top-tag hl-ref">Ô LIÊN QUAN</span>`;
}

const BANNER_LABEL_VN = {
  READY: "ĐANG ĐIỀU TRA",
  ACCEPTED: "SUY LUẬN CHÍNH XÁC",
  NOT_PROVABLE: "CHƯA ĐỦ BẰNG CHỨNG",
  CONTRADICTED: "MÂU THUẪN LOGIC",
  HINT: "GỢI Ý TỪ AI",
  STUCK: "TẠM DỪNG SUY DIỄN",
  SOLVED: "PHÁ ÁN THÀNH CÔNG",
  INCONSISTENT: "LỜI KHAI MÂU THUẪN",
  ERROR: "THÔNG BÁO LỖI",
};

async function apiCall(path, body = {}) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return await res.json();
}

/* =========================================================================
   VẼ BẢNG TRỰC QUAN HÓA CÔNG THỨC & LUỒNG CHẠY DPLL (FORENSIC DPLL CONSOLE)
   ========================================================================= */
function escapeHtmlText(raw) {
  return String(raw || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatLogicFormulaHtml(expr) {
  let s = escapeHtmlText(expr);
  s = s.replace(/KB₀/g, '<span class="m-kb">KB<sub>0</sub></span>');
  s = s.replace(/KB_(\d+)/g, '<span class="m-kb">KB<sub>$1</sub></span>');
  s = s.replace(/¬C_([A-E]\d+)/g, '<span class="m-lit-neg">¬C<sub>$1</sub></span>');
  s = s.replace(/C_([A-E]\d+)/g, '<span class="m-lit-pos">C<sub>$1</sub></span>');
  s = s.replace(/aux_(\d+)/g, '<span class="m-aux">aux<sub>$1</sub></span>');
  s = s.replace(/\(UNSAT\)|\bUNSAT\b/g, '<span class="m-tag-unsat">UNSAT</span>');
  s = s.replace(/\(SAT\)|\bSAT\b/g, '<span class="m-tag-sat">SAT</span>');
  return s;
}

function renderLiveVisualizer(data) {
  const steps = data.deduction_steps || [];
  const initClues = data.initial_clues || [];
  const totalSteps = steps.length;
  const expectedTotalSteps = Math.max(totalSteps, (data.total_cells || 0) - initClues.length);

  let activeStepIdx = selectedVisualStep !== null ? selectedVisualStep : totalSteps;
  if (activeStepIdx > totalSteps) activeStepIdx = totalSteps;

  const isAutoRunning = Boolean(autoTimer);
  const isReplayRunning = Boolean(playbackTimer);

  const pulseDot = document.getElementById("lvPulseDot");
  if (pulseDot) {
    pulseDot.classList.toggle("running", isAutoRunning || isReplayRunning);
  }

  const pbPlayBtn = document.getElementById("pbPlayPause");
  const pbPlayIcon = document.getElementById("pbPlayIcon");
  const pbPlayText = document.getElementById("pbPlayText");
  const playSvg = `<svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 4 20 12 6 20 6 4"/></svg>`;
  const pauseSvg = `<svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/></svg>`;
  const replaySvg = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>`;

  if (pbPlayBtn) {
    pbPlayBtn.classList.toggle("is-active", isAutoRunning || isReplayRunning);
  }
  if (isAutoRunning) {
    if (pbPlayIcon) pbPlayIcon.innerHTML = pauseSvg;
    if (pbPlayText) pbPlayText.textContent = "Tạm dừng";
  } else if (isReplayRunning) {
    if (pbPlayIcon) pbPlayIcon.innerHTML = pauseSvg;
    if (pbPlayText) pbPlayText.textContent = "Dừng tua";
  } else if (!data.is_complete && (totalSteps === 0 || activeStepIdx === totalSteps)) {
    if (pbPlayIcon) pbPlayIcon.innerHTML = playSvg;
    if (pbPlayText) pbPlayText.textContent = "Chạy DPLL";
  } else {
    if (pbPlayIcon) pbPlayIcon.innerHTML = replaySvg;
    if (pbPlayText) pbPlayText.textContent = "Phát lại";
  }

  const pbSpeedLabel = document.getElementById("pbSpeedLabel");
  if (pbSpeedLabel) {
    pbSpeedLabel.textContent = `${playbackSpeed.toFixed(1)}×`;
  }

  const st = activeStepIdx > 0 ? steps[activeStepIdx - 1] : null;

  // 1. Thanh Tiến Trình Chuỗi Phá Án (Forensic Chain Progress Rail)
  const pbStepText = document.getElementById("pbStepText");
  if (pbStepText) {
    if (activeStepIdx === 0) {
      pbStepText.innerHTML = `Khởi điểm <span class="m-kb">KB<sub>0</sub></span> · ${initClues.length} ô mở sẵn`;
    } else if (st) {
      const vCls = st.verdict === "INNOCENT" ? "txt-innocent" : "txt-criminal";
      pbStepText.innerHTML = `Bước #${activeStepIdx} · <strong>${escapeHtmlText(st.name)} (${st.cell})</strong> · <span class="${vCls}">${st.verdict_vn}</span>`;
    }
  }

  const pbStepCounter = document.getElementById("pbStepCounter");
  if (pbStepCounter) {
    pbStepCounter.textContent = `${activeStepIdx} / ${expectedTotalSteps}`;
  }

  const prevBtn = document.getElementById("pbPrev");
  const nextBtn = document.getElementById("pbNext");
  if (prevBtn) prevBtn.disabled = activeStepIdx <= 0;
  if (nextBtn) nextBtn.disabled = activeStepIdx >= totalSteps;

  const dotsWrap = document.getElementById("lvDotsWrap");
  if (dotsWrap) {
    dotsWrap.innerHTML = "";
    const isCompact = expectedTotalSteps > 10;
    dotsWrap.classList.toggle("compact-track", isCompact);

    const kb0Dot = document.createElement("button");
    kb0Dot.type = "button";
    kb0Dot.className = "step-dot kb0-dot" + (activeStepIdx === 0 ? " active" : "");
    kb0Dot.innerHTML = "<span>KB<sub>0</sub></span>";
    kb0Dot.title = "Khởi điểm KB0 (Dữ kiện mở sẵn ban đầu)";
    kb0Dot.addEventListener("click", () => playbackGoTo(0));
    dotsWrap.appendChild(kb0Dot);

    for (let idx = 1; idx <= expectedTotalSteps; idx++) {
      const solvedStep = idx <= totalSteps ? steps[idx - 1] : null;
      const dot = document.createElement("button");
      dot.type = "button";
      if (solvedStep) {
        const dotKind = solvedStep.verdict === "INNOCENT" ? "innocent" : "criminal";
        dot.className = `step-dot ${dotKind}` + (activeStepIdx === idx ? " active" : "");
        dot.textContent = String(idx);
        dot.title = `Bước #${idx}: ${solvedStep.name} (${solvedStep.cell}) = ${solvedStep.verdict_vn}`;
        dot.addEventListener("click", () => playbackGoTo(idx));
      } else {
        dot.className = "step-dot pending";
        dot.textContent = String(idx);
        dot.disabled = true;
        dot.title = `Bước #${idx}: Đang chờ chứng minh phản chứng`;
      }
      dotsWrap.appendChild(dot);
    }
  }

  // 2. Thân Bảng Forensic DPLL Console
  const flowBody = document.getElementById("lvFlowBody");
  if (!flowBody) return;

  if (activeStepIdx === 0) {
    const remainingCells = Math.max(0, (data.total_cells || 0) - (data.revealed_count || 0));

    const initItemsHtml = initClues.map(ic => {
      const isCrim = ic.status === "CRIMINAL";
      const unitLit = isCrim ? `(C_${ic.cell})` : `(¬C_${ic.cell})`;
      const stLabel = isCrim ? "THỦ PHẠM" : "VÔ TỘI";
      const stCls = isCrim ? "criminal" : "innocent";
      const isSel = Boolean(ic.selected);
      const clickArg = isSel ? "null" : `'${ic.cell}'`;

      return `
        <div class="witness-dossier-card clickable-evidence ${isSel ? 'is-selected' : ''}" onclick="selectClue(${clickArg})" title="Bấm để soi vùng lời khai của ${escapeHtmlText(ic.owner)} (${ic.cell}) trên bàn cờ">
          <div class="witness-card-head">
            <div class="witness-identity-group">
              <div class="witness-mugshot">${suspectPortraitSvg(ic.profession || "", true, ic.status)}</div>
              <div class="witness-meta">
                <div class="witness-name-line">
                  <span class="witness-name">${escapeHtmlText(ic.owner)}</span>
                  <span class="witness-coord">Ô ${ic.cell}</span>
                  <span class="witness-verdict-chip ${stCls}">${stLabel}</span>
                </div>
                <div class="witness-prof">${escapeHtmlText(ic.profession || "Nhân chứng hiện trường")}</div>
              </div>
            </div>
            <span class="evidence-jump-pill ${isSel ? 'active' : ''}">${isSel ? "Đang soi ●" : "Soi vùng ↗"}</span>
          </div>

          <div class="witness-quote-box">“${escapeHtmlText(ic.text)}”</div>

          <div class="witness-formula-bar">
            <div class="wf-item">
              <span class="wf-lbl">Đơn vị</span>
              <code class="wf-code">${formatLogicFormulaHtml(unitLit)}</code>
            </div>
            <span class="wf-divider" aria-hidden="true"></span>
            <div class="wf-item wf-grow">
              <span class="wf-lbl">Đại số</span>
              <code class="wf-code">${formatLogicFormulaHtml(ic.math_formula)}</code>
            </div>
          </div>

          <details class="cnf-collapse" onclick="event.stopPropagation()">
            <summary>
              <span>Xem khai triển chuẩn CNF (+${ic.clause_count} mệnh đề)</span>
              <span class="cnf-chevron" aria-hidden="true">▾</span>
            </summary>
            <div class="cnf-collapse-body">
              <code>${formatLogicFormulaHtml(ic.cnf_preview)}</code>
            </div>
          </details>
        </div>
      `;
    }).join("");

    const quickActionHtml = !data.is_complete ? `
      <div class="console-action-dock">
        <button type="button" class="btn-console-primary" onclick="stopAutoSolve(); stepSolve();">
          <div class="console-primary-text">
            <span class="console-primary-title">GIẢI 1 BƯỚC PHẢN CHỨNG</span>
            <span class="console-primary-sub">Kiểm định UNSAT / SAT từ KB<sub>0</sub> để mở ô kế tiếp</span>
          </div>
          <svg class="console-primary-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12"/><polyline points="13 6 19 12 13 18"/>
          </svg>
        </button>
        <button type="button" class="btn-console-secondary" onclick="requestHint()" title="Nhờ AI chỉ điểm ô có thể suy luận tiếp theo mà không tự mở thẻ">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="22"/><line x1="2" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="22" y2="12"/>
          </svg>
          <span>Chỉ điểm gợi ý</span>
        </button>
      </div>
    ` : "";

    flowBody.innerHTML = `
      <div class="kb0-console-wrap">
        <div class="kb0-overview-card">
          <div class="kb0-overview-top">
            <div class="kb0-heading-group">
              <div class="kb0-heading">Cơ Sở Tri Thức Khởi Điểm <span class="m-kb">KB<sub>0</sub></span></div>
              <div class="kb0-subheading">Tiên đề sự thật ban đầu &amp; hệ ràng buộc CNF của bàn cờ</div>
            </div>
            <span class="kb0-ready-pill"><span class="kb0-ready-dot"></span>SẴN SÀNG</span>
          </div>
          <div class="kb0-telemetry-strip">
            <div class="kb0-stat-cell">
              <div class="kb0-stat-val">${data.telemetry.num_primary}<span class="kb0-stat-aux">+${data.telemetry.num_aux} phụ</span></div>
              <div class="kb0-stat-lbl">Biến mệnh đề</div>
            </div>
            <div class="kb0-stat-cell">
              <div class="kb0-stat-val">${data.telemetry.num_clauses}</div>
              <div class="kb0-stat-lbl">Mệnh đề CNF</div>
            </div>
            <div class="kb0-stat-cell">
              <div class="kb0-stat-val">${remainingCells}</div>
              <div class="kb0-stat-lbl">Ô chờ suy diễn</div>
            </div>
          </div>
        </div>

        <div class="console-witness-block">
          <div class="console-section-hdr">
            <span class="stage-num">TIỀN ĐỀ</span>
            <span class="stage-name">Hồ Sơ Nhân Chứng Mở Sẵn (${initClues.length})</span>
          </div>
          ${initItemsHtml}
        </div>

        ${quickActionHtml}
      </div>
    `;
    return;
  }

  if (!st) return;

  const isInn = st.verdict === "INNOCENT";
  const badgeClass = isInn ? "innocent" : "criminal";
  const badgeText = isInn ? "VÔ TỘI" : "THỦ PHẠM";

  // Lời khai tiền đề (Supporting Evidence) — bấm vào để soi vùng trực tiếp trên bàn cờ
  const supCluesHtml = (st.supporting_clues || []).map(sc => `
    <div class="story-evidence-card clickable-evidence" onclick="selectClue('${sc.cell}')" title="Bấm để soi vùng lời khai của ${escapeHtmlText(sc.owner)} (${sc.cell})">
      <div class="story-card-title">
        <span>Nhân chứng ${escapeHtmlText(sc.owner)} (${sc.cell})</span>
        <span class="evidence-jump-pill">Soi vùng ↗</span>
      </div>
      <div class="story-quote">“${escapeHtmlText(sc.text)}”</div>
      <div class="story-formula-line">
        <code>${formatLogicFormulaHtml(sc.math_formula)}</code>
      </div>
    </div>
  `).join("");

  // Lời khai mới mở khóa
  const newClueHtml = st.new_clue ? `
    <div class="story-unlocked-card">
      <div class="story-card-title">
        <span>Lời khai mới từ ${escapeHtmlText(st.name)} (${st.cell})</span>
        <span class="unlocked-clause-tag">+${st.new_clue.clause_count} CNF → KB<sub>${st.step_no}</sub></span>
      </div>
      <div class="story-quote">“${escapeHtmlText(st.new_clue.text)}”</div>
      <div class="story-unlocked-meta">
        <code>${formatLogicFormulaHtml(st.new_clue.math_formula)}</code>
        <code>${formatLogicFormulaHtml(st.unit_clause)}</code>
      </div>
      ${st.new_clue.cnf_preview ? `
        <details class="cnf-collapse">
          <summary>
            <span>Chi tiết mệnh đề CNF nạp thêm</span>
            <span class="cnf-chevron" aria-hidden="true">▾</span>
          </summary>
          <div class="cnf-collapse-body">
            <code>${formatLogicFormulaHtml(st.new_clue.cnf_preview)}</code>
          </div>
        </details>
      ` : ""}
    </div>
  ` : '';

  const hasBacktracks = (st.telemetry.backtracks || 0) > 0;
  const nextStepBtnHtml = (!data.is_complete && activeStepIdx === totalSteps) ? `
    <div class="console-action-dock compact-dock">
      <button type="button" class="btn-console-primary compact-btn" onclick="stopAutoSolve(); stepSolve();">
        <span class="console-primary-title">GIẢI BƯỚC #${totalSteps + 1} TIẾP THEO</span>
        <svg class="console-primary-arrow" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <line x1="5" y1="12" x2="19" y2="12"/><polyline points="13 6 19 12 13 18"/>
        </svg>
      </button>
    </div>
  ` : "";

  flowBody.innerHTML = `
    <div class="pipeline-4layer">
      <!-- TẦNG 1: TIỀN ĐỀ TRI THỨC -->
      <div class="pipeline-stage">
        <div class="pipeline-stage-head">
          <span class="stage-num">01</span>
          <span class="stage-name">Tiền Đề Tri Thức Công Khai (<span class="m-kb">KB<sub>${st.step_no - 1}</sub></span>)</span>
        </div>
        ${supCluesHtml || '<div class="story-evidence-card"><div class="story-quote">Tổng hợp các mệnh đề đã mở trong KB hiện hành.</div></div>'}
      </div>

      <!-- TẦNG 2: PHÉP THỬ PHẢN CHỨNG -->
      <div class="pipeline-stage">
        <div class="pipeline-stage-head">
          <span class="stage-num">02</span>
          <span class="stage-name">Kiểm Tra Phản Chứng (Proof by Refutation)</span>
        </div>
        <div class="refute-storyboard">
          <div class="story-branch unsat">
            <div class="story-branch-header">
              <span>✕ Giả thiết đối lập</span>
              <code>${formatLogicFormulaHtml(st.refutation_query)}</code>
            </div>
            <div class="story-branch-desc">${formatLogicFormulaHtml(st.refutation_desc)}</div>
          </div>
          <div class="story-branch sat">
            <div class="story-branch-header">
              <span>✓ Nhánh nhất quán</span>
              <code>${formatLogicFormulaHtml(st.consistency_query)}</code>
            </div>
            <div class="story-branch-desc">
              Mọi mô hình thỏa mãn <span class="m-kb">KB<sub>${st.step_no - 1}</sub></span> đều buộc <strong>${escapeHtmlText(st.name)} (${st.cell}) = ${st.verdict_vn}</strong>.
            </div>
          </div>
        </div>
      </div>

      <!-- TẦNG 3: ĐỘNG CƠ DPLL SAT -->
      <div class="pipeline-stage">
        <div class="pipeline-stage-head">
          <span class="stage-num">03</span>
          <span class="stage-name">Động Cơ DPLL SAT (${st.telemetry.runtime_ms}ms tích lũy)</span>
        </div>
        <div class="dpll-live-strip">
          <div class="dpll-mini-box">
            <div class="dpll-mini-val">${st.telemetry.propagations}</div>
            <div class="dpll-mini-lbl">Unit Prop</div>
          </div>
          <div class="dpll-mini-box">
            <div class="dpll-mini-val">${st.telemetry.decisions}</div>
            <div class="dpll-mini-lbl">Decisions</div>
          </div>
          <div class="dpll-mini-box ${hasBacktracks ? 'has-bt' : ''}">
            <div class="dpll-mini-val">${st.telemetry.backtracks}</div>
            <div class="dpll-mini-lbl">Backtracks</div>
          </div>
          <div class="dpll-mini-box">
            <div class="dpll-mini-val">${st.telemetry.sat_calls}</div>
            <div class="dpll-mini-lbl">SAT Calls</div>
          </div>
        </div>
      </div>

      <!-- TẦNG 4: PHÁN QUYẾT & MỞ KHÓA KB MỚI -->
      <div class="pipeline-stage stage-last">
        <div class="pipeline-stage-head">
          <span class="stage-num">04</span>
          <span class="stage-name">Kết Luận Tất Yếu &amp; Cập Nhật <span class="m-kb">KB<sub>${st.step_no}</sub></span></span>
        </div>
        <div class="hero-verdict-card ${badgeClass}">
          <div class="hero-verdict-top">
            <div class="hero-suspect-profile">
              <div class="hero-mugshot-mini">${suspectPortraitSvg(st.profession || "", true, st.verdict)}</div>
              <div>
                <div class="hero-suspect-name">${escapeHtmlText(st.name)}</div>
                <span class="hero-suspect-cell">Ô ${st.cell}${st.profession ? ' · ' + escapeHtmlText(st.profession) : ''}</span>
              </div>
            </div>
            <span class="hero-stamp-badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="hero-entailment-formula">
            <span>Hệ quả logic</span>
            <code>${formatLogicFormulaHtml(st.entailment_formula)}</code>
          </div>
        </div>
        ${newClueHtml}
      </div>
    </div>
    ${nextStepBtnHtml}
  `;
}

function toggleToolsMenu(force) {
  const pop = document.getElementById("toolsPopover");
  if (!pop) return;
  if (typeof force === "boolean") {
    pop.classList.toggle("open", force);
  } else {
    pop.classList.toggle("open");
  }
}

document.addEventListener("click", (e) => {
  const wrap = document.querySelector(".menu-popover-wrap");
  if (wrap && !wrap.contains(e.target)) {
    const pop = document.getElementById("toolsPopover");
    if (pop) pop.classList.remove("open");
  }
});

/* =========================================================================
   CÁC HÀM ĐIỀU KHIỂN TUA LẠI LUỒNG SUY DIỄN (PLAYBACK CONTROLLER)
   ========================================================================= */
function playbackGoTo(idx) {
  if (!currentState) return;
  const total = (currentState.deduction_steps || []).length;
  selectedVisualStep = Math.max(0, Math.min(idx, total));
  playSfx("click");
  renderLiveVisualizer(currentState);
  renderCrimeStrings(currentState);
}

function playbackStepPrev() {
  if (!currentState) return;
  const total = (currentState.deduction_steps || []).length;
  let cur = selectedVisualStep !== null ? selectedVisualStep : total;
  playbackGoTo(cur - 1);
}

function playbackStepNext() {
  if (!currentState) return;
  const total = (currentState.deduction_steps || []).length;
  let cur = selectedVisualStep !== null ? selectedVisualStep : total;
  playbackGoTo(cur + 1);
}

function playbackGoToLatest() {
  if (!currentState) return;
  selectedVisualStep = null;
  playSfx("click");
  renderLiveVisualizer(currentState);
  renderCrimeStrings(currentState);
}

function togglePlaybackPlay() {
  if (autoTimer) {
    stopAutoSolve();
    playSfx("click");
    if (currentState) renderLiveVisualizer(currentState);
    return;
  }
  if (playbackTimer) {
    clearInterval(playbackTimer);
    playbackTimer = null;
    playSfx("click");
    renderLiveVisualizer(currentState);
    return;
  }
  if (!currentState) return;
  const total = (currentState.deduction_steps || []).length;
  const curIdx = selectedVisualStep !== null ? selectedVisualStep : total;

  // Nếu bàn cờ chưa giải xong và đang ở bước hiện hành (hoặc chưa có bước nào), kích hoạt chạy DPLL trực tiếp
  if (!currentState.is_complete && (total === 0 || curIdx === total)) {
    selectedVisualStep = null;
    const lblAuto = document.getElementById("lblAuto");
    if (lblAuto) lblAuto.textContent = "Tạm dừng";
    playSfx("click");
    autoTimer = setTimeout(loopAutoSolve, 80);
    renderLiveVisualizer(currentState);
    return;
  }

  if (total === 0) return;
  if (selectedVisualStep === null || selectedVisualStep >= total) {
    selectedVisualStep = 0;
  }
  playSfx("click");
  renderLiveVisualizer(currentState);
  renderCrimeStrings(currentState);

  const intervalMs = Math.round(1100 / playbackSpeed);
  playbackTimer = setInterval(() => {
    if (!currentState) {
      clearInterval(playbackTimer);
      playbackTimer = null;
      return;
    }
    const maxSteps = (currentState.deduction_steps || []).length;
    if (selectedVisualStep < maxSteps) {
      selectedVisualStep++;
      playSfx("click");
      renderLiveVisualizer(currentState);
      renderCrimeStrings(currentState);
    } else {
      clearInterval(playbackTimer);
      playbackTimer = null;
      renderLiveVisualizer(currentState);
    }
  }, intervalMs);
}

function cyclePlaybackSpeed() {
  if (playbackSpeed === 1.0) playbackSpeed = 2.0;
  else if (playbackSpeed === 2.0) playbackSpeed = 0.5;
  else playbackSpeed = 1.0;
  playSfx("click");
  const pbSpeedLabel = document.getElementById("pbSpeedLabel");
  if (pbSpeedLabel) pbSpeedLabel.textContent = `${playbackSpeed.toFixed(1)}×`;
  if (playbackTimer) {
    clearInterval(playbackTimer);
    playbackTimer = null;
    togglePlaybackPlay();
  }
}

function onScrubberInput(val) {
  if (!currentState) return;
  selectedVisualStep = parseInt(val, 10);
  renderLiveVisualizer(currentState);
  renderCrimeStrings(currentState);
}

/* =========================================================================
   VẼ MẠNG LƯỚI "DÂY CHỈ ĐỎ THÁM TỬ" (SVG CRIME BOARD STRINGS)
   ========================================================================= */
function renderCrimeStrings(data) {
  const svg = document.getElementById("crimeStringsLayer");
  if (!svg) return;
  svg.innerHTML = "";
  if (!crimeStringsEnabled || !data) return;

  const shell = document.getElementById("boardShell");
  if (!shell) return;
  const shellRect = shell.getBoundingClientRect();
  if (shellRect.width === 0 || shellRect.height === 0) return;

  svg.setAttribute("viewBox", `0 0 ${shellRect.width} ${shellRect.height}`);

  const steps = data.deduction_steps || [];
  const totalSteps = steps.length;
  let activeStepIdx = selectedVisualStep !== null ? selectedVisualStep : totalSteps;
  if (activeStepIdx > totalSteps) activeStepIdx = totalSteps;

  let sourceCell = null;
  let targetCellsWithRoles = []; // [{cell, role}]

  if (data.selected_inspector) {
    sourceCell = data.selected_inspector.cell;
    const insp = data.selected_inspector;
    (insp.overlap || []).forEach(c => targetCellsWithRoles.push({ cell: c, role: "overlap-line" }));
    (insp.left || []).forEach(c => targetCellsWithRoles.push({ cell: c, role: "left-line" }));
    (insp.right || []).forEach(c => targetCellsWithRoles.push({ cell: c, role: "right-line" }));
    (insp.referenced || []).forEach(c => {
      if (!targetCellsWithRoles.find(x => x.cell === c)) {
        targetCellsWithRoles.push({ cell: c, role: "ref-line" });
      }
    });
  } else if (activeStepIdx > 0 && steps[activeStepIdx - 1]) {
    const st = steps[activeStepIdx - 1];
    sourceCell = st.cell;
    (st.supporting_clues || st.premise_clues || []).forEach(pc => {
      targetCellsWithRoles.push({ cell: pc.cell, role: "deduce-line" });
    });
  }

  if (!sourceCell || !targetCellsWithRoles.length) return;

  const getCenter = (cStr) => {
    const el = document.querySelector(`[data-cell-id="${cStr}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      x: r.left - shellRect.left + r.width / 2,
      y: r.top - shellRect.top + 10,
    };
  };

  const sPt = getCenter(sourceCell);
  if (!sPt) return;

  targetCellsWithRoles.forEach(({ cell, role }) => {
    if (cell === sourceCell) return;
    const tPt = getCenter(cell);
    if (!tPt) return;

    const dx = tPt.x - sPt.x;
    const dy = tPt.y - sPt.y;
    const dist = Math.hypot(dx, dy);
    if (dist < 5) return;

    const midX = (sPt.x + tPt.x) / 2;
    const midY = (sPt.y + tPt.y) / 2;
    const curvature = Math.min(dist * 0.16, 34);
    const nx = -dy / dist;
    const ny = dx / dist;
    const cx = midX + nx * curvature;
    const cy = midY + ny * curvature;

    const dAttr = role === "deduce-line"
      ? `M ${tPt.x} ${tPt.y} Q ${cx} ${cy} ${sPt.x} ${sPt.y}`
      : `M ${sPt.x} ${sPt.y} Q ${cx} ${cy} ${tPt.x} ${tPt.y}`;

    const shadow = document.createElementNS("http://www.w3.org/2000/svg", "path");
    shadow.setAttribute("d", dAttr);
    shadow.setAttribute("class", "crime-string-shadow");
    svg.appendChild(shadow);

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", dAttr);
    path.setAttribute("class", `crime-string-path ${role}`);
    svg.appendChild(path);

    const pulse = document.createElementNS("http://www.w3.org/2000/svg", "path");
    pulse.setAttribute("d", dAttr);
    pulse.setAttribute("class", `crime-string-pulse ${role}`);
    svg.appendChild(pulse);

    [sPt, tPt].forEach((pt, pIdx) => {
      const halo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      halo.setAttribute("cx", pt.x);
      halo.setAttribute("cy", pt.y);
      halo.setAttribute("r", pIdx === 0 ? "7" : "5.5");
      halo.setAttribute("fill", pIdx === 0 ? "rgba(245, 158, 11, 0.25)" : "rgba(244, 63, 94, 0.22)");
      svg.appendChild(halo);

      const pin = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      pin.setAttribute("cx", pt.x);
      pin.setAttribute("cy", pt.y);
      pin.setAttribute("r", pIdx === 0 ? "4.6" : "3.8");
      pin.setAttribute("fill", pIdx === 0 ? "#F59E0B" : "#F43F5E");
      pin.setAttribute("stroke", "#FEF3C7");
      pin.setAttribute("stroke-width", "1.4");
      svg.appendChild(pin);
    });
  });
}

window.addEventListener("resize", () => {
  if (currentState) renderCrimeStrings(currentState);
});

function render(data) {
  currentState = data;

  if (data.is_complete) {
    markCaseSolved(data.puzzle_id);
    updateStartScreenStats();
  }

  const qSel = document.getElementById("quickPuzzleSelect");
  if (data.puzzles && qSel) {
    qSel.innerHTML = "";
    const grpOfficial = document.createElement("optgroup");
    grpOfficial.label = "6 Hồ Sơ Chính Thức (Unique Solution)";
    const grpExtra = document.createElement("optgroup");
    grpExtra.label = "Hồ Sơ Mở Rộng & Kiểm Thử Biên AI";

    data.puzzles.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.case_id;
      opt.textContent = `${p.code}: ${p.title} (${p.n}×${p.n})`;
      if (p.case_id === data.puzzle_id || data.puzzle_id.includes(p.case_id)) {
        opt.selected = true;
      }
      if (isOfficialSix(p.case_id)) {
        grpOfficial.appendChild(opt);
      } else {
        grpExtra.appendChild(opt);
      }
    });
    qSel.appendChild(grpOfficial);
    qSel.appendChild(grpExtra);
    renderCaseSelection(data.puzzles);
  }

  const hdrCode = document.getElementById("hdrCaseCode");
  if (hdrCode) hdrCode.textContent = data.case_code || "HỒ SƠ";
  const hdrTitle = document.getElementById("hdrCaseTitle");
  if (hdrTitle) hdrTitle.textContent = data.case_title || data.puzzle_id;

  const progLbl = document.getElementById("progressLabel");
  if (progLbl) progLbl.textContent = `${data.revealed_count}/${data.total_cells} ô`;
  const pct = data.total_cells > 0 ? Math.round((data.revealed_count / data.total_cells) * 100) : 0;
  const progFill = document.getElementById("progressBarFill");
  if (progFill) progFill.style.width = `${pct}%`;

  const badgeClause = document.getElementById("badgeClauseCount");
  if (badgeClause) badgeClause.textContent = `${data.telemetry.num_clauses} CNF`;
  const topClause = document.getElementById("topClauseCount");
  if (topClause) {
    const bt = data.telemetry.backtracks || 0;
    topClause.textContent = bt > 0 ? `${data.telemetry.num_clauses} CNF · ${bt} BT` : `${data.telemetry.num_clauses} CNF`;
  }

  const kind = data.banner_kind || "READY";
  const spInner = document.getElementById("spotlightInner");
  const stBadge = document.getElementById("statusBadge");
  if (spInner) spInner.dataset.kind = kind;
  if (stBadge) {
    stBadge.dataset.kind = kind;
    stBadge.textContent = BANNER_LABEL_VN[kind] || kind;
  }
  const stText = document.getElementById("statusText");
  if (stText) stText.textContent = data.banner_message || "";

  const insp = data.selected_inspector;
  const cluePill = document.getElementById("activeCluePill");
  if (cluePill) {
    if (insp) {
      cluePill.style.display = "flex";
      document.getElementById("activeClueOwner").textContent = `Đang soi lời khai ${insp.owner} (${insp.cell}):`;
      if ((insp.left && insp.left.length) || (insp.right && insp.right.length)) {
        const parts = [];
        if (insp.left.length) parts.push(`Vế trái: ${insp.left.join(", ")}`);
        if (insp.right.length) parts.push(`Vế phải: ${insp.right.join(", ")}`);
        if (insp.overlap.length) parts.push(`Giao nhau: ${insp.overlap.join(", ")}`);
        document.getElementById("activeClueRefs").textContent = parts.join(" | ");
      } else {
        document.getElementById("activeClueRefs").textContent = `Ô liên quan (${insp.referenced.length}): ${insp.referenced.join(", ")}`;
      }
    } else {
      cluePill.style.display = "none";
    }
  }

  const n = data.n;
  const shell = document.getElementById("boardShell");
  if (shell) shell.dataset.n = String(n);

  const originBadge = document.getElementById("coordOriginBadge");
  if (originBadge) originBadge.textContent = `${n}×${n}`;

  const colHdr = document.getElementById("boardColHeaders");
  if (colHdr) {
    colHdr.innerHTML = "";
    colHdr.style.gridTemplateColumns = `repeat(${n}, 1fr)`;
    for (let c = 0; c < n; c++) {
      const colLet = String.fromCharCode(65 + c);
      const chip = document.createElement("div");
      chip.className = "coord-ruler-chip col-chip";
      chip.innerHTML = `<span class="ruler-sub">CỘT</span><span class="ruler-main">${colLet}</span>`;
      chip.title = `Rê chuột để soi nhanh Cột ${colLet}`;
      chip.addEventListener("mouseenter", () => highlightAxis("col", colLet, true));
      chip.addEventListener("mouseleave", () => highlightAxis("col", colLet, false));
      colHdr.appendChild(chip);
    }
  }

  const rowHdr = document.getElementById("boardRowHeaders");
  if (rowHdr) {
    rowHdr.innerHTML = "";
    rowHdr.style.gridTemplateRows = `repeat(${n}, 1fr)`;
    for (let r = 1; r <= n; r++) {
      const chip = document.createElement("div");
      chip.className = "coord-ruler-chip row-chip";
      chip.innerHTML = `<span class="ruler-sub">H</span><span class="ruler-main">${r}</span>`;
      chip.title = `Rê chuột để soi nhanh Hàng ${r}`;
      chip.addEventListener("mouseenter", () => highlightAxis("row", String(r), true));
      chip.addEventListener("mouseleave", () => highlightAxis("row", String(r), false));
      rowHdr.appendChild(chip);
    }
  }

  const rowsWrap = document.getElementById("boardRowsWrap");
  if (rowsWrap) {
    rowsWrap.innerHTML = "";
    rowsWrap.style.gridTemplateColumns = `repeat(${n}, 1fr)`;

    for (let i = 0; i < data.cells.length; i++) {
      const item = data.cells[i];
      const scene = document.createElement("div");
      scene.className = "suspect-scene";

      const card = document.createElement("div");
      card.dataset.cellId = item.cell;
      card.dataset.col = item.cell.charAt(0);
      card.dataset.row = item.cell.slice(1);
      const classes = ["suspect-card"];
      if (item.revealed) {
        classes.push(item.status === "INNOCENT" ? "revealed-innocent" : "revealed-criminal");
      } else {
        classes.push("unsolved");
      }
      if (item.is_selected_clue) classes.push("selected-clue");
      if (item.is_hinted) classes.push("hinted");
      if (item.highlight_role) {
        if (item.highlight_role === "RIGHT") classes.push("hl-card-right");
        else if (item.highlight_role === "L∩R") classes.push("hl-card-overlap");
        else classes.push("hl-card-ref");
      }
      if (lastAnimatedCell === item.cell && lastAnimationKind) {
        classes.push(lastAnimationKind);
      }
      card.className = classes.join(" ");

      const hlTopTag = getHighlightTopTag(item.highlight_role);

      if (item.revealed) {
        const isInn = item.status === "INNOCENT";
        const badgeClass = isInn ? "innocent" : "criminal";
        const badgeText = isInn ? "VÔ TỘI" : "THỦ PHẠM";
        const clueText = n === 5 ? item.clue.short_text : item.clue.text;
        const isSelected = Boolean(item.is_selected_clue);
        const rStep = item.reveal_step || 0;
        const stepBadgeHtml = rStep === 0
          ? `<span class="step-order-badge">MỞ SẴN</span>`
          : `<span class="step-order-badge step-deduced">BƯỚC #${rStep}</span>`;

        card.innerHTML = `
          <div class="card-paperclip" aria-hidden="true"></div>
          <div class="card-top">
            <div class="card-top-left">
              <span class="coord-pill">${item.cell}</span>
              ${stepBadgeHtml}
              ${hlTopTag}
            </div>
            <span class="stamp-badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="identity-revealed">
            <div class="avatar-wrap">${suspectPortraitSvg(item.profession, true, item.status)}</div>
            <div>
              <div class="char-name">${item.name}</div>
              <div class="char-prof">${item.profession}</div>
            </div>
          </div>
          <div class="clue-bubble">
            “${clueText}”
          </div>
          <button type="button" class="btn-clue-helper ${isSelected ? 'active' : ''}" data-cell="${item.cell}">
            <svg class="icon-svg-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="8"/><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
            </svg>
            <span>${isSelected ? 'Đang soi vùng (Tắt)' : 'Soi vùng lời khai'}</span>
          </button>
        `;
        const helperBtn = card.querySelector(".btn-clue-helper");
        if (helperBtn) {
          helperBtn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            playSfx("click");
            selectClue(isSelected ? null : item.cell);
          });
        }
      } else {
        const topRight = item.is_hinted
          ? `<span class="stamp-badge hint-pill">AI GỢI Ý</span>`
          : `<span class="stamp-badge unsolved-pill">CHƯA MỞ</span>`;
        const pNote = pencilNotes[item.cell];
        const pencilBadgeHtml = pNote
          ? `<span class="pencil-tag pencil-${pNote}" title="Ghi chú nháp (Click phải đổi/xóa)">? ${pNote === 'innocent' ? 'Vô tội' : 'Thủ phạm'}</span>`
          : '';

        card.innerHTML = `
          <div class="card-paperclip" aria-hidden="true"></div>
          <div class="card-top">
            <div class="card-top-left">
              <span class="coord-pill">${item.cell}</span>
              ${pencilBadgeHtml}
              ${hlTopTag}
            </div>
            ${topRight}
          </div>
          <div class="identity-unsolved">
            <div class="avatar-wrap">${suspectPortraitSvg(item.profession, false, null)}</div>
            <div class="char-name">${item.name}</div>
            <div class="char-prof">${item.profession}</div>
          </div>
          <div class="verdict-row">
            <button type="button" class="btn-verdict innocent" data-cell="${item.cell}" data-v="INNOCENT">Vô tội</button>
            <button type="button" class="btn-verdict criminal" data-cell="${item.cell}" data-v="CRIMINAL">Thủ phạm</button>
          </div>
        `;
        card.addEventListener("contextmenu", (ev) => {
          ev.preventDefault();
          cyclePencilNote(item.cell);
        });
        card.addEventListener("click", (ev) => {
          if (pencilModeActive && !ev.target.closest(".btn-verdict")) {
            cyclePencilNote(item.cell);
          }
        });
        card.querySelectorAll(".btn-verdict").forEach(btn => {
          btn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            submitVerdict(btn.dataset.cell, btn.dataset.v);
          });
        });
      }

      scene.appendChild(card);
      rowsWrap.appendChild(scene);
    }
  }

  lastAnimatedCell = null;
  lastAnimationKind = null;

  renderLiveVisualizer(data);
  renderCrimeStrings(data);

  const t = data.telemetry;
  document.getElementById("mPrimary").textContent = t.num_primary;
  document.getElementById("mAux").textContent = t.num_aux;
  document.getElementById("mClauses").textContent = t.num_clauses;
  const mSteps = document.getElementById("mSteps");
  if (mSteps) mSteps.textContent = t.deduction_steps !== undefined ? t.deduction_steps : (data.deduction_steps || []).length;
  document.getElementById("mQueries").textContent = t.sat_calls;
  document.getElementById("mDecisions").textContent = t.decisions;
  document.getElementById("mProps").textContent = t.propagations;
  document.getElementById("mBacktracks").textContent = t.backtracks;
  document.getElementById("mRuntime").textContent = `${t.runtime_ms.toFixed(1)}ms`;

  const cList = document.getElementById("clueDrawerList");
  if (cList) {
    cList.innerHTML = "";
    data.revealed_clues.forEach(rc => {
      const item = document.createElement("div");
      item.className = "clue-drawer-item" + (rc.selected ? " active" : "");
      item.innerHTML = `
        <div><span class="clue-drawer-tag">[${rc.cell} · ${rc.owner}]</span>${rc.text}</div>
        <div class="formula-cnf" style="margin-top:3px;">Công thức: ${rc.math_formula || ""} | CNF: ${rc.cnf_preview || ""}</div>
      `;
      item.addEventListener("click", () => selectClue(rc.selected ? null : rc.cell));
      cList.appendChild(item);
    });
  }

  const traceBox = document.getElementById("traceBox");
  if (traceBox) {
    traceBox.innerHTML = "";
    data.trace.forEach(tr => {
      const row = document.createElement("div");
      row.className = "trace-entry";
      row.innerHTML = `<span class="trace-tag ${tr.outcome}">#${String(tr.step_no).padStart(2, '0')} [${tr.outcome}]</span> ${tr.detail}`;
      traceBox.appendChild(row);
    });
    traceBox.scrollTop = traceBox.scrollHeight;
  }

  if (data.is_complete && victoryShownForSession !== data.session_id) {
    victoryShownForSession = data.session_id;
    playSfx("victory");
    document.getElementById("vStatCells").textContent = `${data.revealed_count}/${data.total_cells}`;
    const vVars = document.getElementById("vStatVars");
    if (vVars) vVars.textContent = `${t.num_primary} / ${t.num_aux}`;
    document.getElementById("vStatClauses").textContent = t.num_clauses;
    const vQueries = document.getElementById("vStatQueries");
    if (vQueries) vQueries.textContent = t.sat_calls;
    document.getElementById("vStatProps").textContent = `${t.propagations} (${t.decisions} dec)`;
    const vBt = document.getElementById("vStatBacktracks");
    if (vBt) vBt.textContent = `${t.backtracks} BT · ${t.runtime_ms.toFixed(1)}ms`;
    setTimeout(() => openModal("modalVictory"), 520);
  }
}

function highlightAxis(kind, val, active) {
  const attr = kind === "col" ? "data-col" : "data-row";
  document.querySelectorAll(`.suspect-card[${attr}="${val}"]`).forEach(el => {
    el.classList.toggle("axis-hover-glow", active);
  });
}

async function selectClue(cell) {
  if (cell) playSfx("twang");
  const data = await apiCall("/api/select_clue", { cell });
  render(data);
}

async function submitVerdict(cell, verdict) {
  stopAutoSolve();
  selectedVisualStep = null;
  const data = await apiCall("/api/verdict", { cell, verdict });
  if (data.last_outcome) {
    lastAnimatedCell = cell;
    lastAnimationKind = data.last_outcome.result === "ACCEPTED" ? "anim-flip" : "anim-shake";
    if (data.last_outcome.result === "ACCEPTED") {
      playSfx(verdict === "INNOCENT" ? "stamp_innocent" : "stamp_criminal");
    } else {
      playSfx("not_provable");
    }
  }
  render(data);
}

async function requestHint() {
  stopAutoSolve();
  const data = await apiCall("/api/hint", {});
  playSfx("click");
  render(data);
}

async function stepSolve() {
  toggleVisualizerPanel(true);
  selectedVisualStep = null;
  const data = await apiCall("/api/step", {});
  if (data.last_outcome && data.last_outcome.cell) {
    lastAnimatedCell = data.last_outcome.cell;
    lastAnimationKind = data.last_outcome.result === "ACCEPTED" ? "anim-flip" : "anim-shake";
    if (data.last_outcome.result === "ACCEPTED") {
      playSfx(data.last_outcome.verdict === "INNOCENT" ? "stamp_innocent" : "stamp_criminal");
    }
  }
  render(data);
  return data;
}

function stopAutoSolve() {
  if (autoTimer) {
    clearTimeout(autoTimer);
    autoTimer = null;
  }
  const lblAuto = document.getElementById("lblAuto");
  if (lblAuto) lblAuto.textContent = "Tự động phá án";
  const pulseDot = document.getElementById("lvPulseDot");
  if (pulseDot) pulseDot.classList.remove("running");
  if (currentState) renderLiveVisualizer(currentState);
}

async function loopAutoSolve() {
  if (!autoTimer) return;
  const data = await stepSolve();
  if (!autoTimer || data.is_complete || !data.last_outcome || data.last_outcome.result !== "ACCEPTED") {
    stopAutoSolve();
    return;
  }
  const speed = parseInt(document.getElementById("speedSelect").value, 10) || 850;
  autoTimer = setTimeout(loopAutoSolve, speed);
}

async function playNextCase() {
  closeModal("modalVictory");
  if (!currentState || !currentState.puzzles || !currentState.puzzles.length) return;
  const list = currentState.puzzles;
  const idx = list.findIndex(p => p.case_id === currentState.puzzle_id);
  const nextItem = list[(idx + 1) % list.length];
  selectedVisualStep = null;
  const data = await apiCall("/api/load", { case_id: nextItem.case_id });
  render(data);
}

document.getElementById("btnAuto").addEventListener("click", () => {
  if (autoTimer) {
    stopAutoSolve();
    return;
  }
  toggleVisualizerPanel(true);
  selectedVisualStep = null;
  document.getElementById("lblAuto").textContent = "Tạm dừng";
  autoTimer = setTimeout(loopAutoSolve, 80);
});

document.getElementById("btnHint").addEventListener("click", requestHint);
document.getElementById("btnStep").addEventListener("click", () => { stopAutoSolve(); stepSolve(); });
document.getElementById("btnRestart").addEventListener("click", async () => {
  stopAutoSolve();
  victoryShownForSession = null;
  selectedVisualStep = null;
  playSfx("click");
  render(await apiCall("/api/restart", {}));
});

document.getElementById("quickPuzzleSelect").addEventListener("change", async (e) => {
  stopAutoSolve();
  victoryShownForSession = null;
  selectedVisualStep = null;
  playSfx("click");
  render(await apiCall("/api/load", { case_id: e.target.value }));
});

async function handleJsonFileUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  stopAutoSolve();
  victoryShownForSession = null;
  selectedVisualStep = null;
  const text = await file.text();
  const data = await apiCall("/api/load_raw", { content: text });
  playSfx("click");
  render(data);
  showScreen("screenGame");
  e.target.value = "";
}

document.getElementById("uploadJsonCases").addEventListener("change", handleJsonFileUpload);
const uploadTopbar = document.getElementById("uploadJsonTopbar");
if (uploadTopbar) {
  uploadTopbar.addEventListener("change", handleJsonFileUpload);
}
const uploadStart = document.getElementById("uploadJsonStart");
if (uploadStart) {
  uploadStart.addEventListener("change", handleJsonFileUpload);
}

// Lớp phủ Kéo Thả File JSON (Drag & Drop Dropzone Overlay)
const dropOverlay = document.getElementById("dropzoneOverlay");
let dragCounter = 0;

window.addEventListener("dragenter", (e) => {
  e.preventDefault();
  dragCounter++;
  if (dropOverlay) dropOverlay.classList.add("active");
});

window.addEventListener("dragleave", (e) => {
  e.preventDefault();
  dragCounter--;
  if (dragCounter <= 0 && dropOverlay) {
    dragCounter = 0;
    dropOverlay.classList.remove("active");
  }
});

window.addEventListener("dragover", (e) => {
  e.preventDefault();
});

window.addEventListener("drop", async (e) => {
  e.preventDefault();
  dragCounter = 0;
  if (dropOverlay) dropOverlay.classList.remove("active");
  const files = e.dataTransfer ? e.dataTransfer.files : null;
  if (!files || !files.length) return;
  const file = files[0];
  if (!file.name.endsWith(".json")) {
    alert("Vui lòng thả file có định dạng .json hợp lệ!");
    return;
  }
  stopAutoSolve();
  victoryShownForSession = null;
  selectedVisualStep = null;
  const text = await file.text();
  try {
    const data = await apiCall("/api/load_raw", { content: text });
    playSfx("click");
    render(data);
    showScreen("screenGame");
  } catch (err) {
    alert("Lỗi nạp file JSON: " + err);
  }
});

// Khởi tạo icon âm thanh theo thiết lập
updateSoundIcon();
updateStartScreenStats();
if (document.getElementById("dossierTitle")) {
  switchDossierTab('3x3');
}

// Khởi tạo nền động khí quyển điện ảnh (Cinematic Atmosphere Canvas)
let atmosphere = null;
if (document.getElementById("noirAtmosphereCanvas")) {
  atmosphere = new AtmosphereEngine("noirAtmosphereCanvas");
}

// Tải dữ liệu trạng thái khi mở trang
apiCall("/api/state", {}).then(render);
