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
        vx: (Math.random() - 0.5) * 0.4,
        vy: -0.15 - Math.random() * 0.35,
        size: 0.9 + Math.random() * 2.2,
        baseAlpha: 0.12 + Math.random() * 0.45,
        pulseOffset: Math.random() * Math.PI * 2,
        isSmoke: Math.random() < 0.22,
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
      const wanderX = this.width * 0.5 + Math.cos(angle) * (this.width * 0.24);
      const wanderY = this.height * 0.38 + Math.sin(angle * 1.4) * (this.height * 0.16);
      this.spotX += (wanderX - this.spotX) * 0.025;
      this.spotY += (wanderY - this.spotY) * 0.025;
    } else {
      this.spotX += (this.mouseX - this.spotX) * 0.065;
      this.spotY += (this.mouseY - this.spotY) * 0.065;
    }

    // 2. Vẽ quầng sáng đèn bàn thám tử (Desk Lamp Spotlight)
    const spotRadius = Math.max(380, Math.min(this.width, this.height) * 0.65);
    const spotGrad = ctx.createRadialGradient(
      this.spotX, this.spotY, 30,
      this.spotX, this.spotY, spotRadius
    );
    spotGrad.addColorStop(0, "rgba(230, 160, 50, 0.12)");
    spotGrad.addColorStop(0.35, "rgba(210, 140, 40, 0.05)");
    spotGrad.addColorStop(0.72, "rgba(16, 20, 30, 0.45)");
    spotGrad.addColorStop(1, "rgba(7, 9, 14, 0.90)");

    ctx.fillStyle = spotGrad;
    ctx.fillRect(0, 0, this.width, this.height);

    // 3. Chuyển động hạt bụi vàng và khói thuốc lơ lửng
    const timeSec = t * 0.001;
    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      p.x += p.vx + Math.sin(timeSec + p.pulseOffset) * 0.18;
      p.y += p.vy;

      if (p.y < -15) {
        p.y = this.height + 10;
        p.x = Math.random() * this.width;
      }
      if (p.x < -15) p.x = this.width + 10;
      if (p.x > this.width + 15) p.x = -10;

      const dist = Math.hypot(p.x - this.spotX, p.y - this.spotY);
      const spotFactor = Math.max(0.35, 1.35 - dist / spotRadius);
      const alpha = p.baseAlpha * (0.7 + 0.3 * Math.sin(timeSec * 2.2 + p.pulseOffset)) * spotFactor;

      ctx.beginPath();
      if (p.isSmoke) {
        ctx.arc(p.x, p.y, p.size * 2.6, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(215, 195, 165, ${alpha * 0.28})`;
      } else {
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(245, 185, 75, ${alpha})`;
      }
      ctx.fill();
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
  "chain_demo",
  "3x3_chain",
  "3x3_classic",
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

  const filtered = puzzles.filter(p => {
    if (currentCaseFilter === "official") return isOfficialSix(p.case_id);
    if (currentCaseFilter === "all") return true;
    if (currentCaseFilter === "edge") return p.kind !== "normal" && p.kind !== "stress";
    return String(p.n) === currentCaseFilter && (p.kind === "normal" || p.kind === "stress");
  });

  filtered.forEach(p => {
    const isSolved = solved.includes(p.case_id);
    const diffLevel = p.difficulty || 1;
    const diffLabel = `CẤP ĐỘ ${diffLevel}/3`;
    const card = document.createElement("div");
    card.className = "dossier-card";
    card.innerHTML = `
      <div>
        <div class="dossier-top">
          <span class="dossier-code">${p.code || "HỒ SƠ"} · ${p.n}×${p.n}</span>
          <div class="dossier-badges">
            ${isSolved ? '<span class="solved-pill">ĐÃ PHÁ ÁN</span>' : ''}
            <span class="stars" title="Độ khó">${diffLabel}</span>
          </div>
        </div>
        <div class="dossier-title">${p.title || p.case_id}</div>
        <div class="dossier-sub">${p.subtitle || ""}</div>
        <div class="dossier-story">${p.story || ""}</div>
      </div>
      <div class="dossier-footer">
        <span class="dossier-tag">${p.badge || (p.n + "×" + p.n)}</span>
        <span class="dossier-cta">Mở Hồ Sơ Điều Tra →</span>
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

/* Minh họa SVG nhân vật theo nghề nghiệp */
function suspectPortraitSvg(profession, isRevealed, status) {
  const p = (profession || "").toLowerCase();
  let accent = "#F59E0B";
  let coat = "#334155";
  let badge = "";

  if (p.includes("thám tử") || p.includes("detective") || p.includes("cảnh sát")) {
    accent = "#F59E0B"; coat = "#1E293B";
    badge = `<path d="M9 13 Q18 8 27 13" stroke="#FBBF24" stroke-width="2.2" fill="none"/><ellipse cx="18" cy="10" rx="6" ry="3.2" fill="#F59E0B"/>`;
  } else if (p.includes("bác sĩ") || p.includes("dược") || p.includes("pháp y") || p.includes("nurse") || p.includes("doctor")) {
    accent = "#38BDF8"; coat = "#0F766E";
    badge = `<rect x="16.5" y="24" width="3" height="7" rx="1" fill="#38BDF8"/><rect x="14" y="26.5" width="8" height="2.6" rx="1" fill="#38BDF8"/>`;
  } else if (p.includes("đầu bếp") || p.includes("baker") || p.includes("chef")) {
    accent = "#FB923C"; coat = "#475569";
    badge = `<path d="M12 11 C12 6, 24 6, 24 11" fill="#F8FAFC" stroke="#FB923C" stroke-width="1.5"/>`;
  } else if (p.includes("phi công") || p.includes("thuyền trưởng") || p.includes("pilot")) {
    accent = "#60A5FA"; coat = "#1E3A8A";
    badge = `<polygon points="18,8 25,11 18,13 11,11" fill="#FBBF24"/>`;
  } else if (p.includes("thẩm phán") || p.includes("luật sư") || p.includes("ngoại giao")) {
    accent = "#C084FC"; coat = "#312E81";
    badge = `<path d="M15 24 L18 29 L21 24" stroke="#FBBF24" stroke-width="1.8" fill="none"/>`;
  } else if (p.includes("kỹ sư") || p.includes("kiến trúc") || p.includes("mật mã")) {
    accent = "#34D399"; coat = "#065F46";
    badge = `<rect x="12" y="13" width="12" height="3.2" rx="1.5" fill="#38BDF8"/>`;
  } else if (p.includes("nghệ sĩ") || p.includes("nhạc") || p.includes("đạo diễn")) {
    accent = "#F472B6"; coat = "#701A75";
    badge = `<ellipse cx="19" cy="9.5" rx="7" ry="3" fill="#F472B6"/>`;
  } else {
    accent = "#A78BFA"; coat = "#374151";
  }

  if (isRevealed) {
    coat = status === "INNOCENT" ? "#059669" : "#E11D48";
  }

  return `<svg width="32" height="32" viewBox="0 0 36 36" fill="none" aria-hidden="true">
    <path d="M7 33 C7 24.5, 29 24.5, 29 33" fill="${coat}"/>
    <circle cx="18" cy="15.5" r="6" fill="#FDE68A" stroke="${accent}" stroke-width="1.4"/>
    <circle cx="16" cy="15" r="0.9" fill="#1E293B"/>
    <circle cx="20" cy="15" r="0.9" fill="#1E293B"/>
    <path d="M16 18 Q18 19.4 20 18" stroke="#1E293B" stroke-width="1.1" fill="none" stroke-linecap="round"/>
    ${badge}
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
   VẼ BẢNG TRỰC QUAN HÓA CÔNG THỨC & LUỒNG CHẠY DPLL (THẺ PHÁ ÁN TRINH THÁM)
   ========================================================================= */
function renderLiveVisualizer(data) {
  const steps = data.deduction_steps || [];
  const initClues = data.initial_clues || [];
  const totalSteps = steps.length;

  let activeStepIdx = selectedVisualStep !== null ? selectedVisualStep : totalSteps;
  if (activeStepIdx > totalSteps) activeStepIdx = totalSteps;

  const pulseDot = document.getElementById("lvPulseDot");
  if (pulseDot) {
    pulseDot.classList.toggle("running", Boolean(autoTimer));
  }

  const pbPlayIcon = document.getElementById("pbPlayIcon");
  if (pbPlayIcon) {
    pbPlayIcon.textContent = playbackTimer ? "⏸" : "▶";
  }
  const pbSpeedLabel = document.getElementById("pbSpeedLabel");
  if (pbSpeedLabel) {
    pbSpeedLabel.textContent = `${playbackSpeed.toFixed(1)}×`;
  }

  const st = activeStepIdx > 0 ? steps[activeStepIdx - 1] : null;

  // 1. Thanh điều hướng bước tinh gọn (Clean Stepper Bar)
  const pbStepText = document.getElementById("pbStepText");
  if (pbStepText) {
    if (activeStepIdx === 0) {
      pbStepText.textContent = `Khởi điểm KB₀ (${initClues.length} ô mở sẵn)`;
    } else if (st) {
      pbStepText.textContent = `Bước #${activeStepIdx} / ${totalSteps}: ${st.name} (${st.cell}) = ${st.verdict_vn}`;
    }
  }

  const dotsWrap = document.getElementById("lvDotsWrap");
  if (dotsWrap) {
    dotsWrap.innerHTML = "";
    const kb0Dot = document.createElement("button");
    kb0Dot.type = "button";
    kb0Dot.className = "step-dot" + (activeStepIdx === 0 ? " active" : "");
    kb0Dot.textContent = "0";
    kb0Dot.title = "KB₀ (Dữ kiện mở sẵn ban đầu)";
    kb0Dot.addEventListener("click", () => playbackGoTo(0));
    dotsWrap.appendChild(kb0Dot);

    steps.forEach((s) => {
      const dot = document.createElement("button");
      dot.type = "button";
      const dotKind = s.verdict === "INNOCENT" ? "innocent" : "criminal";
      dot.className = `step-dot ${dotKind}` + (activeStepIdx === s.step_no ? " active" : "");
      dot.textContent = String(s.step_no);
      dot.title = `Bước #${s.step_no}: ${s.name} (${s.cell}) = ${s.verdict_vn}`;
      dot.addEventListener("click", () => playbackGoTo(s.step_no));
      dotsWrap.appendChild(dot);
    });
  }

  // 2. Thân Thẻ Phá Án Trinh Thám (Hero Detective Storyboard)
  const flowBody = document.getElementById("lvFlowBody");
  if (!flowBody) return;

  if (activeStepIdx === 0) {
    const initItemsHtml = initClues.map(ic => {
      const unitLit = ic.status === "CRIMINAL" ? `(C_${ic.cell})` : `(¬C_${ic.cell})`;
      const stLabel = ic.status === "CRIMINAL" ? "THỦ PHẠM" : "VÔ TỘI";
      return `
        <div class="story-evidence-card">
          <div class="story-card-title">${ic.owner} (${ic.cell}) · ${stLabel}</div>
          <div class="story-quote">“${ic.text}”</div>
          <div style="font-family:var(--font-mono); font-size:11px; color:var(--ink-muted); margin-top:3px;">
            Mệnh đề đơn vị: <code>${unitLit}</code> | CNF: <code>${ic.cnf_preview}</code>
          </div>
        </div>
      `;
    }).join("");

    flowBody.innerHTML = `
      <div class="hero-verdict-card">
        <div class="hero-verdict-top">
          <div class="hero-suspect-profile">
            <div>
              <div class="hero-suspect-name">Cơ Sở Tri Thức Khởi Điểm KB₀</div>
              <div style="font-size:11.5px; color:var(--ink-secondary); margin-top:2px;">
                Chứa các sự thật mở sẵn và ràng buộc suy diễn của bàn cờ
              </div>
            </div>
          </div>
          <span class="hero-stamp-badge innocent">SẴN SÀNG</span>
        </div>
        <div class="hero-entailment-formula">
          <span>Công thức khởi điểm</span>
          <span>${data.telemetry.num_clauses} mệnh đề CNF</span>
        </div>
      </div>

      <div class="refute-storyboard">
        <div class="story-branch sat">
          <div class="story-branch-header">
            <span>Dữ kiện ban đầu (${initClues.length} thẻ mở sẵn)</span>
          </div>
          <div class="story-branch-desc">
            Lời khai từ các nhân chứng này là tiền đề logic để bộ giải DPLL suy luận phản chứng các bước tiếp theo.
          </div>
        </div>
        ${initItemsHtml}
      </div>

      <div class="story-unlocked-card">
        <div class="story-card-title">Hướng dẫn thao tác</div>
        <div class="story-quote" style="font-style:normal; font-size:12px;">
          Bấm nút <strong>“Tự động phá án”</strong> hoặc <strong>“Giải 1 bước”</strong> trên thanh công cụ để xem bộ giải chứng minh phản chứng từng ô!
        </div>
      </div>
    `;
    return;
  }

  if (!st) return;

  const isInn = st.verdict === "INNOCENT";
  const badgeClass = isInn ? "innocent" : "criminal";
  const badgeText = isInn ? "VÔ TỘI" : "THỦ PHẠM";

  // Lời khai tiền đề (Supporting Evidence)
  const supCluesHtml = (st.supporting_clues || []).map(sc => `
    <div class="story-evidence-card">
      <div class="story-card-title">Lời khai từ ${sc.owner} (${sc.cell})</div>
      <div class="story-quote">“${sc.text}”</div>
      <div style="font-family:var(--font-mono); font-size:10.5px; color:var(--ink-muted); margin-top:2px;">
        Công thức: <code>${sc.math_formula}</code>
      </div>
    </div>
  `).join("");

  // Lời khai mới mở khóa
  const newClueHtml = st.new_clue ? `
    <div class="story-unlocked-card">
      <div class="story-card-title">Lời khai mới hé lộ từ ${st.name} (${st.cell})</div>
      <div class="story-quote">“${st.new_clue.text}”</div>
      <div style="font-family:var(--font-mono); font-size:11px; color:var(--gold-bright); margin-top:3px;">
        +${st.new_clue.clause_count} mệnh đề CNF nạp vào KB_${st.step_no}
      </div>
    </div>
  ` : '';

  flowBody.innerHTML = `
    <!-- 1. Thẻ Phán Quyết Nổi Bật -->
    <div class="hero-verdict-card ${badgeClass}">
      <div class="hero-verdict-top">
        <div class="hero-suspect-profile">
          <div>
            <div class="hero-suspect-name">${st.name}</div>
            <span class="hero-suspect-cell">Ô ${st.cell}</span>
          </div>
        </div>
        <span class="hero-stamp-badge ${badgeClass}">${badgeText}</span>
      </div>
      <div class="hero-entailment-formula">
        <span>Suy diễn tất yếu</span>
        <code>${st.entailment_formula}</code>
      </div>
    </div>

    <!-- 2. Sơ Đồ Phản Chứng 2 Nhánh Trực Quan -->
    <div class="refute-storyboard">
      <div class="story-branch unsat">
        <div class="story-branch-header">
          <span>✕ Bác bỏ giả thiết: ${st.refutation_query}</span>
        </div>
        <div class="story-branch-desc">
          ${st.refutation_desc}
        </div>
      </div>
      <div class="story-branch sat">
        <div class="story-branch-header">
          <span>✓ Khẳng định: ${st.consistency_query}</span>
        </div>
        <div class="story-branch-desc">
          Do giả thiết đối lập bị bác bỏ hoàn toàn, ${st.name} (${st.cell}) bắt buộc phải là <strong>${st.verdict_vn}</strong>!
        </div>
      </div>
    </div>

    <!-- 3. Bằng chứng làm tiền đề -->
    ${supCluesHtml ? `
      <div style="display:flex; flex-direction:column; gap:6px;">
        <div style="font-size:11px; font-weight:800; color:var(--ink-muted); text-transform:uppercase; letter-spacing:0.04em;">Chứng cứ tiền đề đã dùng</div>
        ${supCluesHtml}
      </div>
    ` : ''}

    <!-- 4. Lời khai mới mở khóa -->
    ${newClueHtml}

    <!-- 5. Chi tiết thuật toán DPLL & Mệnh đề CNF (Thu gọn mặc định) -->
    <details class="dpll-tech-accordion">
      <summary>Chi tiết kỹ thuật CNF &amp; DPLL Solver (${st.telemetry.runtime_ms}ms) ▾</summary>
      <div class="dpll-tech-body">
        <div class="dpll-mini-metrics" style="display:grid; grid-template-columns:repeat(4,1fr); gap:6px;">
          <div class="dpll-mini-box">
            <div class="dpll-mini-val">${st.telemetry.propagations}</div>
            <div class="dpll-mini-lbl">Unit Prop</div>
          </div>
          <div class="dpll-mini-box">
            <div class="dpll-mini-val">${st.telemetry.decisions}</div>
            <div class="dpll-mini-lbl">Decisions</div>
          </div>
          <div class="dpll-mini-box">
            <div class="dpll-mini-val">${st.telemetry.backtracks}</div>
            <div class="dpll-mini-lbl">Backtracks</div>
          </div>
          <div class="dpll-mini-box">
            <div class="dpll-mini-val">${st.telemetry.sat_calls}</div>
            <div class="dpll-mini-lbl">SAT Calls</div>
          </div>
        </div>
        <div style="font-family:var(--font-mono); font-size:11px; color:var(--ink-muted);">
          Mệnh đề đơn vị sinh ra: <code>${st.unit_clause}</code> | Tổng mệnh đề KB: <code>${st.telemetry.num_clauses}</code>
        </div>
      </div>
    </details>
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
  if (playbackTimer) {
    clearInterval(playbackTimer);
    playbackTimer = null;
    playSfx("click");
    renderLiveVisualizer(currentState);
    return;
  }
  if (!currentState) return;
  const total = (currentState.deduction_steps || []).length;
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
    (st.premise_clues || []).forEach(pc => {
      targetCellsWithRoles.push({ cell: pc.cell, role: "ref-line" });
    });
  }

  if (!sourceCell || !targetCellsWithRoles.length) return;

  const getCenter = (cStr) => {
    const el = document.querySelector(`[data-cell-id="${cStr}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      x: r.left - shellRect.left + r.width / 2,
      y: r.top - shellRect.top + r.height / 2,
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
    const curvature = Math.min(dist * 0.18, 36);
    const nx = -dy / dist;
    const ny = dx / dist;
    const cx = midX + nx * curvature;
    const cy = midY + ny * curvature;

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M ${sPt.x} ${sPt.y} Q ${cx} ${cy} ${tPt.x} ${tPt.y}`);
    path.setAttribute("class", `crime-string-path ${role}`);
    svg.appendChild(path);

    [sPt, tPt].forEach((pt, pIdx) => {
      const pin = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      pin.setAttribute("cx", pt.x);
      pin.setAttribute("cy", pt.y);
      pin.setAttribute("r", pIdx === 0 ? "4.5" : "3.5");
      pin.setAttribute("fill", pIdx === 0 ? "#F59E0B" : "#F43F5E");
      pin.setAttribute("stroke", "#FFFFFF");
      pin.setAttribute("stroke-width", "1.2");
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
    document.getElementById("vStatClauses").textContent = t.num_clauses;
    document.getElementById("vStatProps").textContent = t.propagations;
    setTimeout(() => openModal("modalVictory"), 520);
  }
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

// Khởi tạo nền động khí quyển điện ảnh (Cinematic Atmosphere Canvas)
let atmosphere = null;
if (document.getElementById("noirAtmosphereCanvas")) {
  atmosphere = new AtmosphereEngine("noirAtmosphereCanvas");
}

// Tải dữ liệu trạng thái khi mở trang
apiCall("/api/state", {}).then(render);
