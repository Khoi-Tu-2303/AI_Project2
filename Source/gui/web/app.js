/* =========================================================================
   HỒ SƠ LOGIC: GRIDUCTIVE — LOGIC TƯƠNG TÁC FRONTEND (APP.JS)
   ========================================================================= */

let currentState = null;
let autoTimer = null;
let lastAnimatedCell = null;
let lastAnimationKind = null;
let currentCaseFilter = "all";
let victoryShownForSession = null;

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
  document.querySelectorAll(".screen").forEach(el => el.classList.remove("active"));
  const target = document.getElementById(screenId);
  if (target) target.classList.add("active");
  if (screenId === "screenCases" && currentState) {
    renderCaseSelection(currentState.puzzles || []);
  }
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

function render(data) {
  currentState = data;

  if (data.is_complete) {
    markCaseSolved(data.puzzle_id);
  }

  const qSel = document.getElementById("quickPuzzleSelect");
  if (data.puzzles && qSel) {
    qSel.innerHTML = "";
    data.puzzles.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.case_id;
      opt.textContent = `${p.code}: ${p.title} (${p.n}×${p.n})`;
      if (p.case_id === data.puzzle_id || data.puzzle_id.includes(p.case_id)) {
        opt.selected = true;
      }
      qSel.appendChild(opt);
    });
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

        card.innerHTML = `
          <div class="card-top">
            <div class="card-top-left">
              <span class="coord-pill">${item.cell}</span>
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
            selectClue(isSelected ? null : item.cell);
          });
        }
      } else {
        const topRight = item.is_hinted
          ? `<span class="stamp-badge hint-pill">AI GỢI Ý</span>`
          : `<span class="stamp-badge unsolved-pill">CHƯA MỞ</span>`;
        card.innerHTML = `
          <div class="card-top">
            <div class="card-top-left">
              <span class="coord-pill">${item.cell}</span>
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

  const t = data.telemetry;
  document.getElementById("mPrimary").textContent = t.num_primary;
  document.getElementById("mAux").textContent = t.num_aux;
  document.getElementById("mClauses").textContent = t.num_clauses;
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
      item.innerHTML = `<span class="clue-drawer-tag">[${rc.cell} · ${rc.owner}]</span>${rc.text}`;
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
    document.getElementById("vStatCells").textContent = `${data.revealed_count}/${data.total_cells}`;
    document.getElementById("vStatClauses").textContent = t.num_clauses;
    document.getElementById("vStatProps").textContent = t.propagations;
    setTimeout(() => openModal("modalVictory"), 420);
  }
}

async function selectClue(cell) {
  const data = await apiCall("/api/select_clue", { cell });
  render(data);
}

async function submitVerdict(cell, verdict) {
  stopAutoSolve();
  const data = await apiCall("/api/verdict", { cell, verdict });
  if (data.last_outcome) {
    lastAnimatedCell = cell;
    lastAnimationKind = data.last_outcome.result === "ACCEPTED" ? "anim-flip" : "anim-shake";
  }
  render(data);
}

async function requestHint() {
  stopAutoSolve();
  const data = await apiCall("/api/hint", {});
  render(data);
}

async function stepSolve() {
  const data = await apiCall("/api/step", {});
  if (data.last_outcome && data.last_outcome.cell) {
    lastAnimatedCell = data.last_outcome.cell;
    lastAnimationKind = data.last_outcome.result === "ACCEPTED" ? "anim-flip" : "anim-shake";
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
}

async function loopAutoSolve() {
  if (!autoTimer) return;
  const data = await stepSolve();
  if (!autoTimer || data.is_complete || !data.last_outcome || data.last_outcome.result !== "ACCEPTED") {
    stopAutoSolve();
    return;
  }
  const speed = parseInt(document.getElementById("speedSelect").value, 10) || 480;
  autoTimer = setTimeout(loopAutoSolve, speed);
}

async function playNextCase() {
  closeModal("modalVictory");
  if (!currentState || !currentState.puzzles || !currentState.puzzles.length) return;
  const list = currentState.puzzles;
  const idx = list.findIndex(p => p.case_id === currentState.puzzle_id);
  const nextItem = list[(idx + 1) % list.length];
  const data = await apiCall("/api/load", { case_id: nextItem.case_id });
  render(data);
}

document.getElementById("btnAuto").addEventListener("click", () => {
  if (autoTimer) {
    stopAutoSolve();
    return;
  }
  document.getElementById("lblAuto").textContent = "Tạm dừng";
  autoTimer = setTimeout(loopAutoSolve, 60);
});

document.getElementById("btnHint").addEventListener("click", requestHint);
document.getElementById("btnStep").addEventListener("click", () => { stopAutoSolve(); stepSolve(); });
document.getElementById("btnRestart").addEventListener("click", async () => {
  stopAutoSolve();
  victoryShownForSession = null;
  render(await apiCall("/api/restart", {}));
});

document.getElementById("quickPuzzleSelect").addEventListener("change", async (e) => {
  stopAutoSolve();
  victoryShownForSession = null;
  render(await apiCall("/api/load", { case_id: e.target.value }));
});

document.getElementById("uploadJsonCases").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  stopAutoSolve();
  victoryShownForSession = null;
  const text = await file.text();
  const data = await apiCall("/api/load_raw", { content: text });
  render(data);
  showScreen("screenGame");
  e.target.value = "";
});

// Tải dữ liệu trạng thái khi mở trang
apiCall("/api/state", {}).then(render);
