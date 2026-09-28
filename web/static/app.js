/* 杏花沟前端：只与本地 API 通信，不调用外部模型 */
const $ = (id) => document.getElementById(id);

const state = {
  sid: null,
  snap: null,
  book: "xinghuagou",
  books: [],
};

async function api(path, body) {
  const opt = body
    ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    : undefined;
  const res = await fetch(path, opt);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function showScreen(name) {
  $("screen-home").classList.toggle("hidden", name !== "home");
  $("screen-game").classList.toggle("hidden", name !== "game");
}

function renderStats(stats) {
  const root = $("stat-list");
  root.innerHTML = stats
    .map((s) => {
      const max = Math.max(s.max, s.value, 1);
      const pct = Math.max(0, Math.min(100, Math.round((s.value / max) * 100)));
      return `
        <div class="stat-row" data-id="${s.id}" title="${s.description || ""}">
          <div class="stat-name">${s.name}</div>
          <div class="stat-bar"><div class="stat-fill" style="width:${pct}%"></div></div>
          <div class="stat-value">${s.value}</div>
        </div>`;
    })
    .join("");
}

function renderRels(rels) {
  const root = $("rel-list");
  if (!rels.length) {
    root.innerHTML = `<p class="empty-tip">还没有人把你放在心上。</p>`;
    return;
  }
  root.innerHTML = rels
    .slice(0, 8)
    .map((r) => {
      const sign = r.value > 0 ? "+" : "";
      return `<div class="rel-row"><span>${r.name}</span><span class="rel-val">${sign}${r.value}</span></div>`;
    })
    .join("");
}

function renderTimeline(snap) {
  const root = $("canon-timeline");
  root.innerHTML = (snap.canon_timeline || [])
    .map(
      (c) => `
      <div class="canon-item ${c.done ? "done" : ""}">
        <div class="canon-turn">${labelOfTurn(snap, c.turn)}</div>
        <div class="canon-title">${c.title}${c.done ? " · 已发生" : ""}</div>
      </div>`
    )
    .join("");
}

function labelOfTurn(snap, index) {
  const t = (snap.calendar || []).find((x) => x.index === index);
  return t ? t.label : String(index);
}

function renderMessages(messages) {
  const root = $("message-stack");
  if (!messages || !messages.length) {
    root.innerHTML = "";
    return;
  }
  root.innerHTML = messages
    .map((m) => {
      let cls = "msg";
      if (m.includes("迟来") || m.includes("【后来】")) cls += " late";
      if (m.includes("定数")) cls += " canon";
      if (m.includes("·") && m.includes("现")) cls += " effect";
      return `<div class="${cls}">${escapeHtml(m)}</div>`;
    })
    .join("");
}

function renderScene(scene) {
  const card = $("scene-card");
  const pick = $("pick-card");
  const ending = $("ending-card");
  ending.classList.add("hidden");

  if (!scene) {
    card.classList.add("hidden");
    pick.classList.remove("hidden");
    renderOpenScenes();
    return;
  }
  pick.classList.add("hidden");
  card.classList.remove("hidden");

  $("scene-place").textContent = scene.place || scene.place_id || "";
  $("scene-title").textContent = scene.title;
  $("scene-body").textContent = scene.narration;
  $("scene-npcs").innerHTML = (scene.npcs || [])
    .map((n) => `<span class="npc-chip" title="${n.style || ""}">${n.name}</span>`)
    .join("");

  const list = $("choice-list");
  list.innerHTML = "";
  scene.choices.forEach((c, i) => {
    const btn = document.createElement("button");
    btn.className = "choice";
    btn.disabled = !c.available;
    btn.innerHTML = `<strong>${i + 1}.</strong> ${escapeHtml(c.text)}` +
      (c.available ? "" : `<span class="choice-reason">还做不到：${escapeHtml(c.reason)}</span>`);
    btn.addEventListener("click", () => sendChoice(c.id, scene.id));
    list.appendChild(btn);
  });
}

function renderOpenScenes() {
  const list = $("pick-list");
  list.innerHTML = "";
  const scenes = state.snap?.open_scenes || [];
  scenes.forEach((s, i) => {
    const btn = document.createElement("button");
    btn.className = "choice";
    const tags = (s.tags || []).map((t) => `<span class="choice-tag">${t}</span>`).join("");
    btn.innerHTML = `<strong>${i + 1}.</strong> ${escapeHtml(s.title)}${tags}`;
    btn.addEventListener("click", () => sendChoice(s.id));
    list.appendChild(btn);
  });
  const rest = document.createElement("button");
  rest.className = "choice";
  rest.innerHTML = `<strong>0.</strong> 什么都不做，歇着`;
  rest.addEventListener("click", () => sendChoice("rest"));
  list.appendChild(rest);
}

function renderSide(snap) {
  const rumorRoot = $("rumor-list");
  if (snap.rumors?.length) {
    rumorRoot.innerHTML = snap.rumors
      .map(
        (r) => `<div class="rumor">${escapeHtml(r.text)}<span class="src">${escapeHtml(r.source || "")}</span></div>`
      )
      .join("");
  }

  const pend = $("pending-list");
  if (snap.pending?.length) {
    pend.innerHTML = snap.pending
      .map((p) => {
        const turn = labelOfTurn(snap, p.fire_turn);
        return `<div class="pending-item">「${escapeHtml((p.text || p.type).slice(0, 42))}…」· ${turn}</div>`;
      })
      .join("");
  }

  const mem = $("memory-list");
  if (snap.memory?.length) {
    mem.innerHTML = snap.memory
      .slice()
      .reverse()
      .slice(0, 8)
      .map((m) => `<div class="memory-item">${escapeHtml(m.text)}</div>`)
      .join("");
  }
}

function renderEnding(ending, snap) {
  $("scene-card").classList.add("hidden");
  $("pick-card").classList.add("hidden");
  const card = $("ending-card");
  card.classList.remove("hidden");
  $("ending-title").textContent = ending.title;
  $("ending-body").textContent = ending.body;
  $("ending-epithet").textContent = `✦ ${ending.epithet}`;

  const log = $("memory-log");
  log.classList.add("hidden");
  $("btn-timeline").onclick = () => {
    log.classList.toggle("hidden");
    log.innerHTML = (snap.memory || [])
      .map((m) => `<div class="memory-item">〔${labelOfTurn(snap, m.turn)}〕${escapeHtml(m.text)}</div>`)
      .join("");
  };
}

function render(snap) {
  state.snap = snap;
  $("turn-label").textContent = snap.turn_label || `第${snap.turn}日`;
  $("turn-note").textContent = snap.turn_note || "";
  $("player-name").textContent = snap.player?.name || "马小满";
  renderStats(snap.stats || []);
  renderRels(snap.relationships || []);
  renderTimeline(snap);
  renderMessages(snap.messages || []);
  renderSide(snap);

  if (snap.finished && snap.ending) {
    renderEnding(snap.ending, snap);
    return;
  }
  if (snap.scene) renderScene(snap.scene);
  else if (snap.phase === "choose_scene") renderScene(null);
}

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function startGame() {
  const snap = await api("/api/new_game", { book: state.book });
  state.sid = snap.sid;
  showScreen("game");
  render(snap);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function sendChoice(choiceId, sceneId) {
  if (!state.sid) return;
  const snap = await api("/api/choose", {
    sid: state.sid,
    choice_id: choiceId,
    scene_id: sceneId,
  });
  render(snap);
}

function renderBooks(books) {
  const root = $("book-list");
  if (!root) return;
  root.innerHTML = "";
  (books || []).forEach((b) => {
    const div = document.createElement("div");
    div.className = "book-item" + (b.id === state.book ? " active" : "");
    div.innerHTML = `<div class="bt">${escapeHtml(b.title)}</div><div class="bi">${escapeHtml((b.intro || "").slice(0, 48))}</div>`;
    div.addEventListener("click", () => {
      state.book = b.id;
      renderBooks(books);
      const btn = $("btn-start");
      if (btn) btn.textContent = "进入 " + b.title;
    });
    root.appendChild(div);
  });
}

function bind() {
  $("btn-start").addEventListener("click", startGame);
  $("btn-again").addEventListener("click", startGame);
  $("btn-home").addEventListener("click", () => showScreen("home"));
  api("/api/info")
    .then((info) => {
      state.books = info.books || [];
      renderBooks(state.books);
      const hit = state.books.find((b) => b.id === state.book) || state.books[0];
      if (hit) {
        state.book = hit.id;
        renderBooks(state.books);
        const btn = $("btn-start");
        if (btn) btn.textContent = "进入 " + hit.title;
      }
    })
    .catch(() => {});
}

bind();
