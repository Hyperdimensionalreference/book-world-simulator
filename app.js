/* 书中世界模拟器 · 前端 */
const $ = (id) => document.getElementById(id);

const DEFAULTS = {
  theme: "paper",
  font: "17",
  glass: "soft",
  motion: "on",
  numbers: "on",
  autosave: "on",
  confirm: "on",
  toast: "on",
};

const state = {
  view: "home",
  sid: null,
  snap: null,
  book: "xinghuagou",
  books: [],
  settings: { ...DEFAULTS },
  ingest: { title: "", text: "", extract: null },
  meta: { unlocked: [], endings: [], books: [], ingested: false },
  allAch: [],
  shelf: [],
  llm: null,
};

/* 地点 → 场景插画 */
const SCENE_ART = {
  home: { src: "assets/scenes/home.jpg", caption: "院里的风，已经硬了" },
  field: { src: "assets/scenes/field.jpg", caption: "河滩地，界石说不清" },
  village: { src: "assets/scenes/village.jpg", caption: "消息比人腿快" },
  shop: { src: "assets/scenes/village.jpg", caption: "价钱与闲话" },
  gate: { src: "assets/scenes/village.jpg", caption: "车停的地方，也是人走的地方" },
  river: { src: "assets/scenes/field.jpg", caption: "水浅，话深" },
  school: { src: "assets/scenes/home.jpg", caption: "旗杆有点歪" },
  li_home: { src: "assets/scenes/li_home.jpg", caption: "沟口，药味很重" },
  clinic: { src: "assets/scenes/li_home.jpg", caption: "得养着" },
  threshing: { src: "assets/scenes/threshing.jpg", caption: "席面一开，人情就亮出来" },
  ancestral: { src: "assets/scenes/threshing.jpg", caption: "账本摊在长桌上" },
  zhao_home: { src: "assets/scenes/home.jpg", caption: "摩托后座的礼盒" },
  accountant: { src: "assets/scenes/home.jpg", caption: "灯亮到后半夜" },
  zhen: { src: "assets/scenes/village.jpg", caption: "镇上人杂，话虚" },
  sun_home: { src: "assets/scenes/home.jpg", caption: "泥墙塌了半边" },
  chen_home: { src: "assets/scenes/home.jpg", caption: "门楼新些，规矩也多些" },
  hub: { src: "assets/scenes/village.jpg", caption: "中心" },
  work: { src: "assets/scenes/tongzilou.jpg", caption: "劳作处" },
  street: { src: "assets/scenes/village.jpg", caption: "消息场" },
  edge: { src: "assets/scenes/field.jpg", caption: "离开与归来" },
};
const BOOK_ART = {
  xinghuagou: "assets/scenes/home.jpg",
  tongzilou: "assets/scenes/tongzilou.jpg",
};

function updateSceneArt(snap) {
  const box = $("scene-art");
  const img = $("scene-art-img");
  const placeEl = $("scene-art-place");
  const capEl = $("scene-art-caption");
  if (!box || !img) return;
  const scene = snap?.scene;
  const placeId = scene?.place_id || scene?.place || "";
  const bookMeta = (state.books || []).find((b) => b.id === state.book) || {};
  const placeArt = bookMeta.place_art || {};
  const art =
    (placeArt[placeId] && { src: placeArt[placeId], caption: "" }) ||
    SCENE_ART[placeId] ||
    (bookMeta.cover && { src: bookMeta.cover, caption: snap?.turn_note || "这一季" }) ||
    { src: "assets/scenes/home.jpg", caption: snap?.turn_note || "这一季" };
  const placeName = scene?.place || bookMeta.title || state.book;
  if (img.getAttribute("src") !== art.src) {
    img.style.opacity = "0.35";
    img.onload = () => {
      img.style.opacity = "1";
    };
    img.onerror = () => {
      box.classList.add("fallback");
    };
    img.src = art.src;
    box.classList.remove("fallback");
  }
  placeEl.textContent = placeName;
  capEl.textContent = art.caption || snap?.turn_note || "";
}

/* ---------- 设置 ---------- */
function loadSettings() {
  try {
    const raw = localStorage.getItem("bws_settings");
    if (raw) state.settings = { ...DEFAULTS, ...JSON.parse(raw) };
  } catch (_) {}
  applySettings();
  syncSettingsUI();
}
function saveSettings() {
  localStorage.setItem("bws_settings", JSON.stringify(state.settings));
  applySettings();
}
function applySettings() {
  const s = state.settings;
  document.documentElement.setAttribute("data-theme", s.theme === "ink" ? "ink" : "paper");
  document.documentElement.setAttribute("data-motion", s.motion === "off" ? "off" : s.motion === "lite" ? "lite" : "on");
  document.documentElement.setAttribute("data-glass", s.glass === "off" ? "off" : s.glass === "strong" ? "strong" : "soft");
  document.documentElement.style.setProperty("--scene-fs", s.font + "px");
  document.documentElement.style.setProperty("--choice-fs", Math.max(13, Number(s.font) - 2) + "px");
}
function syncSettingsUI() {
  const map = {
    "set-theme": state.settings.theme,
    "set-font": state.settings.font,
    "set-glass": state.settings.glass,
    "set-motion": state.settings.motion,
    "set-numbers": state.settings.numbers,
    "set-autosave": state.settings.autosave,
    "set-confirm": state.settings.confirm,
    "set-toast": state.settings.toast,
    "set-llm-enabled": state.settings.llmEnabled || "off",
  };
  Object.entries(map).forEach(([id, val]) => {
    const root = $(id);
    if (!root) return;
    root.querySelectorAll("button").forEach((b) => {
      b.classList.toggle("on", b.dataset.value === String(val));
    });
  });
}

/* ---------- API ---------- */
async function api(path, body) {
  const opt = body
    ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    : undefined;
  const res = await fetch(path, opt);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

/* ---------- Toast / Modal ---------- */
function toast(title, desc) {
  if (state.settings.toast === "off") return;
  const root = $("toast-root");
  const el = document.createElement("div");
  el.className = "toast glass";
  el.innerHTML = `<div class="tt">${escapeHtml(title)}</div>${desc ? `<div class="td">${escapeHtml(desc)}</div>` : ""}`;
  root.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transform = "translateX(12px)";
    setTimeout(() => el.remove(), 280);
  }, 3200);
}

function confirmDialog(text, okText = "确定") {
  return new Promise((resolve) => {
    const root = $("modal-root");
    root.classList.remove("hidden");
    $("modal-text").textContent = text;
    $("modal-ok").textContent = okText;
    const done = (v) => {
      root.classList.add("hidden");
      $("modal-ok").onclick = null;
      $("modal-cancel").onclick = null;
      resolve(v);
    };
    $("modal-ok").onclick = () => done(true);
    $("modal-cancel").onclick = () => done(false);
  });
}

/* ---------- 导航 ---------- */
function showView(name) {
  state.view = name;
  ["home", "play", "ingest", "settings", "saves", "achievements"].forEach((v) => {
    const el = $("view-" + v);
    if (el) el.classList.toggle("hidden", v !== name);
  });
  document.querySelectorAll(".nav-item").forEach((b) => {
    const active = b.dataset.nav === name || (name === "play" && b.dataset.nav === "home");
    b.classList.toggle("active", active);
  });
  $("game-jieqi").classList.toggle("hidden", name !== "play");
  $("game-player-chip").classList.toggle("hidden", name !== "play");
  if (name === "ingest") setIngestStep(1);
  if (name === "home") refreshBooks();
  if (name === "saves") refreshSaves();
  if (name === "achievements") refreshAchievements();
  window.scrollTo({ top: 0, behavior: "auto" });
}

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/* ---------- 书目 ---------- */
async function refreshBooks() {
  try {
    const info = await api("/api/info");
    state.books = info.books || [];
    renderBooks();
  } catch (_) {}
}
function renderBooks() {
  const root = $("book-list");
  if (!root) return;
  root.innerHTML = "";
  if (!state.books.length) {
    root.innerHTML = `<p class="empty-tip">还没有世界。可以「投一本书」。</p>`;
    return;
  }
  if (!state.books.find((b) => b.id === state.book)) state.book = state.books[0].id;
  state.books.forEach((b) => {
    const div = document.createElement("div");
    div.className = "book-item" + (b.id === state.book ? " active" : "");
    const cover = b.cover
      ? `<img class="book-cover" src="${escapeHtml(b.cover)}" alt="" />`
      : `<div class="book-cover" style="display:grid;place-items:center;font-family:var(--serif);color:var(--vermilion)">${escapeHtml((b.title || "书")[0])}</div>`;
    div.innerHTML = `${cover}<div><div class="bt">${escapeHtml(b.title)}</div><div class="bi">${escapeHtml((b.intro || "").slice(0, 64))}</div></div>`;
    div.addEventListener("click", () => {
      state.book = b.id;
      renderBooks();
    });
    root.appendChild(div);
  });
  const btn = $("btn-start");
  const hit = state.books.find((b) => b.id === state.book);
  if (btn && hit) btn.textContent = "进入 " + hit.title;
}

/* ---------- 游玩渲染 ---------- */
function labelOfTurn(snap, index) {
  const t = (snap.calendar || []).find((x) => x.index === index);
  return t ? t.label : String(index);
}

function renderStats(stats) {
  $("stat-list").innerHTML = (stats || [])
    .map((s) => {
      const max = Math.max(s.max, s.value, 1);
      const pct = Math.max(0, Math.min(100, Math.round((s.value / max) * 100)));
      return `<div class="stat-row" data-id="${s.id}" title="${escapeHtml(s.description || "")}">
        <div class="stat-name">${escapeHtml(s.name)}</div>
        <div class="stat-bar"><div class="stat-fill" style="width:${pct}%"></div></div>
        <div class="stat-value">${s.value}</div>
      </div>`;
    })
    .join("");
}

function renderRels(rels) {
  const root = $("rel-list");
  if (!rels?.length) {
    root.innerHTML = `<p class="empty-tip">还没有人把你放在心上。</p>`;
    return;
  }
  root.innerHTML = rels
    .slice(0, 8)
    .map((r) => `<div class="rel-row"><span>${escapeHtml(r.name)}</span><span class="rel-val">${r.value > 0 ? "+" : ""}${r.value}</span></div>`)
    .join("");
}

function renderTimeline(snap) {
  $("canon-timeline").innerHTML = (snap.canon_timeline || [])
    .map(
      (c) => `<div class="canon-item ${c.done ? "done" : ""}">
        <div class="canon-turn">${labelOfTurn(snap, c.turn)}</div>
        <div class="canon-title">${escapeHtml(c.title)}${c.done ? " · 已发生" : ""}</div>
      </div>`
    )
    .join("");
}

function renderMessages(messages) {
  const root = $("message-stack");
  if (!messages?.length) {
    root.innerHTML = "";
    return;
  }
  root.innerHTML = messages
    .map((m) => {
      let cls = "msg glass";
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
  $("ending-card").classList.add("hidden");
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
    .map((n) => `<span class="npc-chip" title="${escapeHtml(n.style || "")}">${escapeHtml(n.name)}</span>`)
    .join("");
  const showNum = state.settings.numbers !== "off";
  const list = $("choice-list");
  list.innerHTML = "";
  scene.choices.forEach((c, i) => {
    const btn = document.createElement("button");
    btn.className = "choice";
    btn.disabled = !c.available;
    btn.innerHTML =
      (showNum ? `<strong>${i + 1}.</strong> ` : "") +
      escapeHtml(c.text) +
      (c.available ? "" : `<span class="choice-reason">还做不到：${escapeHtml(c.reason)}</span>`);
    btn.addEventListener("click", () => sendChoice(c.id, scene.id));
    list.appendChild(btn);
  });
}

function renderOpenScenes() {
  const showNum = state.settings.numbers !== "off";
  const list = $("pick-list");
  list.innerHTML = "";
  const scenes = state.snap?.open_scenes || [];
  scenes.forEach((s, i) => {
    const btn = document.createElement("button");
    btn.className = "choice";
    const tags = (s.tags || []).map((t) => `<span class="choice-tag">${escapeHtml(t)}</span>`).join("");
    btn.innerHTML = (showNum ? `<strong>${i + 1}.</strong> ` : "") + escapeHtml(s.title) + tags;
    btn.addEventListener("click", () => sendChoice(s.id));
    list.appendChild(btn);
  });
  const rest = document.createElement("button");
  rest.className = "choice";
  rest.innerHTML = (showNum ? `<strong>0.</strong> ` : "") + "什么都不做，歇着";
  rest.addEventListener("click", () => sendChoice("rest"));
  list.appendChild(rest);
}

function renderSide(snap) {
  const rumorRoot = $("rumor-list");
  if (snap.rumors?.length) {
    rumorRoot.innerHTML = snap.rumors
      .map((r) => `<div class="rumor">${escapeHtml(r.text)}<span class="src">${escapeHtml(r.source || "")}</span></div>`)
      .join("");
  }
  const pend = $("pending-list");
  if (snap.pending?.length) {
    pend.innerHTML = snap.pending
      .map((p) => {
        const turn = labelOfTurn(snap, p.fire_turn);
        return `<div class="pending-item">「${escapeHtml((p.text || p.type).slice(0, 40))}…」· ${turn}</div>`;
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
  $("ending-epithet").textContent = "✦ " + ending.epithet;
  const log = $("memory-log");
  log.classList.add("hidden");
  $("btn-timeline").onclick = () => {
    log.classList.toggle("hidden");
    log.innerHTML = (snap.memory || [])
      .map((m) => `<div class="memory-item">〔${labelOfTurn(snap, m.turn)}〕${escapeHtml(m.text)}</div>`)
      .join("");
  };
}

function renderGame(snap) {
  state.snap = snap;
  $("turn-label").textContent = snap.turn_label || "—";
  $("turn-note").textContent = snap.turn_note || "";
  $("player-name").textContent = snap.player?.name || "旅人";
  renderStats(snap.stats || []);
  renderRels(snap.relationships || []);
  renderTimeline(snap);
  renderMessages(snap.messages || []);
  renderSide(snap);
  updateSceneArt(snap);
  if (snap.finished && snap.ending) return renderEnding(snap.ending, snap);
  if (snap.scene) renderScene(snap.scene);
  else renderScene(null);
}

/* ---------- 一局 ---------- */
async function startGame() {
  // 若已有进行中的局，先写入该书槽位
  if (state.sid) {
    try {
      await api("/api/shelf_save", { sid: state.sid });
    } catch (_) {}
  }
  const snap = await api("/api/new_game", { book: state.book });
  state.sid = snap.sid;
  showView("play");
  renderGame(snap);
  refreshShelf();
  toast("进入世界", "进度写入书架，可随时切换");
}

async function switchBook(bookId) {
  if (!bookId) return;
  if (state.sid) {
    try {
      await api("/api/shelf_save", { sid: state.sid });
    } catch (_) {}
  }
  try {
    const snap = await api("/api/shelf_load", { book: bookId });
    state.sid = snap.sid;
    state.book = bookId;
    showView("play");
    renderGame(snap);
    refreshShelf();
    closeShelf();
    toast(snap.resumed ? "已接上进度" : "开新篇", bookId);
  } catch (e) {
    toast("切换失败", e.message);
  }
}

async function refreshShelf() {
  try {
    const res = await api("/api/shelf");
    state.shelf = res.shelf || [];
    state.books = res.books || state.books;
    renderShelf();
  } catch (_) {}
}

function renderShelf() {
  const root = $("shelf-list");
  if (!root) return;
  const byId = Object.fromEntries((state.books || []).map((b) => [b.id, b]));
  if (!state.shelf.length) {
    root.innerHTML = `<p class="empty-tip">书架是空的。选一本世界开始。</p>`;
    return;
  }
  root.innerHTML = "";
  state.shelf.forEach((s) => {
    const book = byId[s.package_id] || {};
    const title = book.title || s.title || s.package_id;
    const cover = book.cover
      ? `<img class="shelf-cover" src="${escapeHtml(book.cover)}" alt="" />`
      : `<div class="shelf-cover" style="display:grid;place-items:center;font-family:var(--serif);color:var(--vermilion)">${escapeHtml((title || "书")[0])}</div>`;
    const div = document.createElement("div");
    div.className = "shelf-item" + (s.package_id === state.book ? " active" : "");
    const status = s.has_save
      ? s.finished
        ? "已结局"
        : `进行中 · ${s.turn != null ? "第 " + s.turn + " 幕" : ""}`
      : "未开始";
    div.innerHTML = `
      ${cover}
      <div>
        <div class="sn">${escapeHtml(title)}</div>
        <div class="sm">${escapeHtml(status)}${s.player ? " · " + escapeHtml(s.player) : ""}</div>
        <div class="sm">${escapeHtml((s.preview || "").slice(0, 28))}</div>
      </div>
    `;
    div.addEventListener("click", () => switchBook(s.package_id));
    root.appendChild(div);
  });
}

function openShelf() {
  $("shelf")?.classList.add("open");
  $("shelf-backdrop")?.classList.remove("hidden");
  document.body.classList.add("shelf-open");
  refreshShelf();
}
function closeShelf() {
  $("shelf")?.classList.remove("open");
  $("shelf-backdrop")?.classList.add("hidden");
  document.body.classList.remove("shelf-open");
}
function toggleShelf() {
  if ($("shelf")?.classList.contains("open")) closeShelf();
  else openShelf();
}

/* ---------- 创造模式 ---------- */
function fillGodSelects() {
  const snap = state.snap || {};
  const rels = snap.relationships || [];
  const stats = snap.stats || [];
  const t = $("god-target");
  const s = $("god-stat");
  if (t) {
    t.innerHTML = `<option value="">—</option>` + rels.map((r) => `<option value="${escapeHtml(r.id)}">${escapeHtml(r.name)}</option>`).join("");
  }
  if (s) {
    s.innerHTML = `<option value="">—</option>` + stats.map((x) => `<option value="${escapeHtml(x.id)}">${escapeHtml(x.name)}</option>`).join("");
  }
}

function openGodMode() {
  $("god-panel")?.classList.remove("hidden");
  fillGodSelects();
  if (!$("god-out")?.textContent) {
    $("god-out").textContent = "准备好了。先看「限度」，再写下你的手谕。";
  }
}
function closeGodMode() {
  $("god-panel")?.classList.add("hidden");
}

async function applyGod() {
  if (!state.sid) {
    toast("先进入一个世界");
    return;
  }
  const kind = $("god-kind")?.value || "directive";
  const body = {
    sid: state.sid,
    kind,
    target: $("god-target")?.value || "",
    stat: $("god-stat")?.value || "",
    delta: Number($("god-delta")?.value || 0),
    note: $("god-note")?.value || "",
    directive: $("god-note")?.value || "",
  };
  if ((kind === "relation" || kind === "attitude") && !body.target) {
    toast("请选择人物");
    return;
  }
  if (kind === "stat" && !body.stat) {
    toast("请选择数值");
    return;
  }
  $("god-out").textContent = "命运正在被拧动…";
  try {
    const res = await api("/api/god_apply", body);
    const r = res.result || {};
    const rw = res.rewrite || {};
    if (res.snapshot) renderGame(res.snapshot);
    let text = r.ok ? r.message : r.message;
    if (r.effect_lines?.length) text += "\n" + r.effect_lines.map((x) => "· " + x).join("\n");
    if (r.blocked?.length) text += "\n【限度】\n" + r.blocked.map((x) => "· " + x).join("\n");
    if (rw.flavor) {
      text += "\n\n【命运侧写 · " + (rw.source === "llm" ? "模型" : "本地") + "】\n" + rw.flavor;
    }
    if (rw.beats?.length) {
      text += "\n后续走向：\n" + rw.beats.map((x) => "→ " + x).join("\n");
    }
    if (rw.warning) text += "\n⚠ " + rw.warning;
    $("god-out").style.color = r.ok ? "var(--moss)" : "var(--vermilion-deep)";
    $("god-out").textContent = text;
    toast(r.ok ? "已写入命运" : "干预被限度拦下");
  } catch (e) {
    $("god-out").style.color = "var(--vermilion-deep)";
    $("god-out").textContent = e.message;
    toast("干预失败", e.message);
  }
}

async function restartGame() {
  if (state.settings.confirm !== "off") {
    const ok = await confirmDialog("确定放弃当前进度，重新开始这一季？", "重开");
    if (!ok) return;
  }
  await startGame();
}

async function sendChoice(choiceId, sceneId) {
  if (!state.sid) return;
  const snap = await api("/api/choose", {
    sid: state.sid,
    choice_id: choiceId,
    scene_id: sceneId,
  });
  renderGame(snap);
  if (state.settings.autosave !== "off") {
    try {
      const res = await api("/api/save_write", { sid: state.sid, slot: "auto", auto: true });
      if (res.new_achievements?.length) {
        res.new_achievements.forEach((a) => toast("解锁成就 · " + a.title, a.desc));
      }
    } catch (_) {}
  }
  try {
    const res = await api("/api/game_meta", { sid: state.sid });
    state.meta = res.meta || state.meta;
    (res.new || []).forEach((a) => toast("解锁成就 · " + a.title, a.desc));
  } catch (_) {}
}

/* ---------- 存档 ---------- */
async function refreshSaves() {
  try {
    const res = await api("/api/saves");
    state.meta = res.meta || state.meta;
    renderSaves(res.saves || []);
  } catch (e) {
    $("save-list").innerHTML = `<p class="empty-tip">${escapeHtml(e.message)}</p>`;
  }
}

function renderSaves(saves) {
  const root = $("save-list");
  if (!saves.length) {
    root.innerHTML = `<p class="empty-tip">还没有存档。进入一局后会自动写入。</p>`;
    return;
  }
  root.innerHTML = "";
  saves.forEach((s) => {
    const div = document.createElement("div");
    div.className = "save-item glass";
    const badges = [
      s.auto ? `<span class="badge auto">自动</span>` : `<span class="badge">手动</span>`,
      s.finished ? `<span class="badge done">已结局</span>` : "",
    ]
      .filter(Boolean)
      .join(" ");
    div.innerHTML = `
      <div>
        <div class="st">${escapeHtml(s.title || s.package_id || "世界")} ${badges}</div>
        <div class="sm">${escapeHtml(s.player || "")} · ${escapeHtml(s.slot)} · ${escapeHtml(s.updated_at || "")}</div>
        <div class="sm">${escapeHtml(s.preview || "")}</div>
      </div>
      <div class="save-actions">
        <button class="btn-primary btn-sm" data-act="load">读档</button>
        <button class="btn-ghost" data-act="del">删除</button>
      </div>`;
    div.querySelector('[data-act="load"]').addEventListener("click", () => loadSave(s.slot));
    div.querySelector('[data-act="del"]').addEventListener("click", async () => {
      if (state.settings.confirm !== "off") {
        const ok = await confirmDialog("删除这个存档？", "删除");
        if (!ok) return;
      }
      await api("/api/save_delete", { slot: s.slot });
      refreshSaves();
      toast("已删除存档");
    });
    root.appendChild(div);
  });
}

async function saveNow(slot) {
  if (!state.sid) {
    toast("当前没有进行中的故事", "先开一局或读档");
    return;
  }
  const name = slot || "main";
  try {
    const res = await api("/api/save_write", { sid: state.sid, slot: name, auto: false });
    toast("已保存", "槽位 " + res.slot);
    if (res.new_achievements?.length) {
      res.new_achievements.forEach((a) => toast("解锁成就 · " + a.title, a.desc));
    }
  } catch (e) {
    toast("保存失败", e.message);
  }
}

async function loadSave(slot) {
  try {
    const snap = await api("/api/save_load", { slot });
    state.sid = snap.sid;
    state.book = snap.book || state.book;
    showView("play");
    renderGame(snap);
    refreshShelf();
    toast("已读档", slot);
  } catch (e) {
    toast("读档失败", e.message);
  }
}

/* ---------- 成就 ---------- */
async function refreshAchievements() {
  try {
    const res = await api("/api/achievements");
    state.allAch = res.all || [];
    state.meta = res.meta || state.meta;
    renderAchievements();
  } catch (e) {
    $("ach-list").innerHTML = `<p class="empty-tip">${escapeHtml(e.message)}</p>`;
  }
}

function renderAchievements() {
  const unlocked = new Set(state.meta.unlocked || []);
  $("ach-summary").textContent = `已解锁 ${unlocked.size} / ${state.allAch.length} · 结局 ${new Set(state.meta.endings || []).size} 种`;
  $("ach-list").innerHTML = state.allAch
    .map((a) => {
      const on = unlocked.has(a.id);
      return `<div class="ach-item glass ${on ? "unlocked" : ""}">
        <div class="ai">${escapeHtml(a.icon || "★")}</div>
        <div class="at">${escapeHtml(a.title)}</div>
        <div class="ad">${escapeHtml(a.desc)}</div>
      </div>`;
    })
    .join("");
}

/* ---------- 投书 ---------- */
function setIngestStep(n) {
  [1, 2, 3].forEach((i) => {
    const el = $("ingest-step-" + i);
    if (el) el.classList.toggle("hidden", i !== n);
  });
  document.querySelectorAll(".step").forEach((s) => {
    s.classList.toggle("active", Number(s.dataset.step) === n);
  });
}

function collectIngestForm() {
  state.ingest.title = ($("ingest-title")?.value || "").trim();
  state.ingest.text = $("ingest-text")?.value || "";
  const raw = ($("ingest-extract")?.value || "").trim();
  if (raw) {
    try {
      state.ingest.extract = JSON.parse(raw);
    } catch (_) {
      state.ingest.extract = null;
    }
  }
}

function validateExtractClient(extract) {
  const errs = [];
  const meta = extract?.meta || {};
  if (!meta.source_id) errs.push("meta.source_id 缺失");
  if (!meta.source_title) errs.push("meta.source_title 缺失");
  const wf = extract?.world_frame || {};
  ["scale", "setting", "time_unit", "threat_style"].forEach((k) => {
    if (!wf[k]) errs.push("world_frame." + k + " 缺失");
  });
  if ((extract?.conflict_sources || []).length < 4) errs.push("conflict_sources 至少 4 个");
  if ((extract?.characters || []).length < 5) errs.push("characters 至少 5 人");
  const canons = extract?.canon_events || [];
  if (canons.length < 4) errs.push("canon_events 至少 4 个");
  canons.forEach((e) => {
    if ((e.foreshadow || []).length < 2) errs.push("canon " + e.id + " 前置线索不足");
    if (e.turn == null) errs.push("canon " + e.id + " 缺 turn");
  });
  if (!extract?.play_space_note) errs.push("play_space_note 缺失");
  return errs;
}

async function doDraft() {
  collectIngestForm();
  if (!state.ingest.text.trim()) {
    toast("请先粘贴或上传正文");
    return;
  }
  try {
    const res = await api("/api/ingest", {
      mode: "draft",
      title: state.ingest.title,
      text: state.ingest.text,
    });
    state.ingest.extract = res.draft;
    $("ingest-extract").value = JSON.stringify(res.draft, null, 2);
    setIngestStep(2);
    $("ingest-validate-out").textContent = "已从正文起草结构。请修订人物与定数描述。";
    toast("已起草结构");
  } catch (e) {
    toast("起草失败", e.message);
  }
}

function doValidateExtract() {
  collectIngestForm();
  const out = $("ingest-validate-out");
  let extract = state.ingest.extract;
  if (!extract) {
    const raw = ($("ingest-extract").value || "").trim();
    if (!raw) {
      out.textContent = "请先填写 extract JSON，或从正文起草。";
      return;
    }
    try {
      extract = JSON.parse(raw);
    } catch (err) {
      out.textContent = "JSON 解析失败：" + err.message;
      return;
    }
  }
  const errs = validateExtractClient(extract);
  out.style.color = errs.length ? "var(--vermilion-deep)" : "var(--moss)";
  out.textContent = errs.length ? "未通过：\n" + errs.map((e) => "· " + e).join("\n") : "结构校验通过。可以生成可玩世界。";
}

async function doBuild() {
  collectIngestForm();
  const raw = ($("ingest-extract").value || "").trim();
  let extract = null;
  try {
    extract = raw ? JSON.parse(raw) : state.ingest.extract;
  } catch (e) {
    toast("extract JSON 解析失败", e.message);
    return;
  }
  const button = $("btn-build");
  button.disabled = true;
  $("ingest-validate-out").textContent = "正在制作。模型加厚可能需要数分钟，请保持页面打开。";
  try {
    const res = await api("/api/ingest", {
      mode: "extract",
      title: state.ingest.title,
      text: state.ingest.text,
      extract,
      llm: $("ingest-use-llm").checked,
    });
    const warn = (res.warnings || []).map((w) => "· " + w).join("\n");
    const quality = res.quality || {};
    const issues = (quality.issues || []).map((issue) =>
      `<li>${escapeHtml(issue.location)}：${escapeHtml(issue.message)}</li>`
    ).join("");
    $("ingest-result").innerHTML = `
      <div><strong>${escapeHtml(res.title)}</strong></div>
      <div class="hint">数据包：${escapeHtml(res.package_path)}</div>
      <div class="hint">${res.mode === "llm" ? "模型加厚候选稿" : "本地脚手架草稿"} · ${quality.blockers || 0} 个阻断项 · ${quality.warnings || 0} 个提醒</div>
      <div class="hint">${escapeHtml(quality.note || "发布前请逐幕人工复核。")}</div>
      ${issues ? `<details><summary>查看机检问题（${quality.issues.length}）</summary><ul>${issues}</ul></details>` : ""}
      <div class="hint">制作记录与完整报告：${escapeHtml(res.workdir)}</div>
      ${warn ? `<div class="hint">${escapeHtml(warn)}</div>` : ""}
      <div class="hint">已加入本机世界列表，可试玩；请勿将未经人工审阅的草稿当成可发布成品。</div>
    `;
    state.book = res.id;
    if (res.books) state.books = res.books;
    setIngestStep(3);
    toast("世界已生成", res.title);
  } catch (e) {
    toast("生成失败", e.message);
    $("ingest-validate-out").textContent = e.message;
    setIngestStep(2);
  } finally {
    button.disabled = false;
  }
}

function bindIngest() {
  $("btn-draft")?.addEventListener("click", doDraft);
  $("btn-to-step2")?.addEventListener("click", () => {
    collectIngestForm();
    setIngestStep(2);
    if (state.ingest.extract && !$("ingest-extract").value.trim()) {
      $("ingest-extract").value = JSON.stringify(state.ingest.extract, null, 2);
    }
  });
  $("btn-to-step1")?.addEventListener("click", () => setIngestStep(1));
  $("btn-validate-extract")?.addEventListener("click", doValidateExtract);
  $("btn-build")?.addEventListener("click", doBuild);
  $("btn-play-new")?.addEventListener("click", startGame);
  $("btn-ingest-again")?.addEventListener("click", () => {
    $("ingest-title").value = "";
    $("ingest-text").value = "";
    $("ingest-extract").value = "";
    $("ingest-use-llm").checked = false;
    $("ingest-validate-out").textContent = "";
    state.ingest = { title: "", text: "", extract: null };
    setIngestStep(1);
  });
  $("ingest-file")?.addEventListener("change", async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const text = await f.text();
    $("ingest-text").value = text;
    if (!$("ingest-title").value) $("ingest-title").value = f.name.replace(/\.(txt|md)$/i, "");
  });
}

/* ---------- 绑定 ---------- */
function bind() {
  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.addEventListener("click", () => showView(el.dataset.nav));
  });
  $("btn-start")?.addEventListener("click", startGame);
  $("btn-again")?.addEventListener("click", startGame);
  $("btn-restart")?.addEventListener("click", restartGame);
  $("btn-save")?.addEventListener("click", () => saveNow("main"));
  $("btn-quick-save")?.addEventListener("click", () => saveNow("quick"));
  $("btn-open-saves")?.addEventListener("click", () => showView("saves"));
  $("btn-save-now")?.addEventListener("click", () => saveNow("main"));
  $("btn-refresh-saves")?.addEventListener("click", refreshSaves);
  $("btn-toggle-shelf")?.addEventListener("click", toggleShelf);
  $("shelf-backdrop")?.addEventListener("click", closeShelf);
  $("btn-shelf-refresh")?.addEventListener("click", refreshShelf);
  $("btn-god-mode")?.addEventListener("click", () => {
    if ($("god-panel")?.classList.contains("hidden")) openGodMode();
    else closeGodMode();
  });
  $("btn-god-close")?.addEventListener("click", closeGodMode);
  $("btn-god-apply")?.addEventListener("click", applyGod);
  $("btn-god-limits")?.addEventListener("click", async () => {
    try {
      const lim = await api("/api/god_limits", {});
      $("god-out").textContent =
        "可改：\n" +
        lim.can_change.map((x) => "· " + x).join("\n") +
        "\n\n不可改：\n" +
        lim.cannot_change.map((x) => "· " + x).join("\n") +
        `\n\n幅度上限：数值 ±${lim.max_stat_delta}，关系 ±${lim.max_rel_delta}`;
    } catch (e) {
      $("god-out").textContent = e.message;
    }
  });

  const settingKeys = {
    "set-theme": "theme",
    "set-font": "font",
    "set-glass": "glass",
    "set-motion": "motion",
    "set-numbers": "numbers",
    "set-autosave": "autosave",
    "set-confirm": "confirm",
    "set-toast": "toast",
    "set-llm-enabled": "llmEnabled",
  };
  Object.entries(settingKeys).forEach(([id, key]) => {
    $(id)?.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      if (key === "llmEnabled") {
        // 先存 UI，保存配置时一起提交
        state.settings.llmEnabled = btn.dataset.value;
        saveSettings();
        syncSettingsUI();
        return;
      }
      state.settings[key] = btn.dataset.value;
      saveSettings();
      syncSettingsUI();
    });
  });
  $("btn-reset-settings")?.addEventListener("click", async () => {
    const ok = await confirmDialog("恢复默认界面偏好？", "重置");
    if (!ok) return;
    state.settings = { ...DEFAULTS };
    saveSettings();
    syncSettingsUI();
    toast("偏好已重置");
  });
  $("btn-reset-achievements")?.addEventListener("click", async () => {
    const ok = await confirmDialog("清空成就记录？存档不受影响。", "清空");
    if (!ok) return;
    try {
      const res = await api("/api/meta_reset", {});
      state.meta = res.meta || state.meta;
      refreshAchievements();
      toast("成就已清空");
    } catch (e) {
      toast("清空失败", e.message);
    }
  });

  $("btn-save-llm")?.addEventListener("click", async () => {
    try {
      const res = await api("/api/llm_config_save", {
        enabled: (state.settings.llmEnabled || "off") === "on",
        base_url: $("llm-base-url")?.value || "",
        api_key: $("llm-api-key")?.value || "",
        model: $("llm-model")?.value || "",
        image_model: $("llm-image-model")?.value || "",
      });
      if ($("llm-api-key")) $("llm-api-key").value = "";
      $("llm-status").style.color = "var(--moss)";
      $("llm-status").textContent =
        "已保存" + (res.config?.api_key_set ? "（Key 已设置）" : "（尚未设置 Key）");
      toast("API 配置已保存");
    } catch (e) {
      $("llm-status").style.color = "var(--vermilion-deep)";
      $("llm-status").textContent = e.message;
    }
  });
  $("btn-test-llm")?.addEventListener("click", async () => {
    $("llm-status").textContent = "测试中…";
    try {
      const res = await api("/api/llm_test", {});
      if (res.ok) {
        $("llm-status").style.color = "var(--moss)";
        $("llm-status").textContent = "连通可用";
      } else {
        $("llm-status").style.color = "var(--vermilion-deep)";
        $("llm-status").textContent = "失败：" + res.error;
      }
    } catch (e) {
      $("llm-status").style.color = "var(--vermilion-deep)";
      $("llm-status").textContent = e.message;
    }
  });
  $("btn-clear-llm-key")?.addEventListener("click", async () => {
    try {
      await api("/api/llm_config_save", { clear_api_key: true });
      $("llm-api-key").value = "";
      $("llm-status").style.color = "var(--moss)";
      $("llm-status").textContent = "本机保存的 Key 已清除";
      toast("Key 已清除");
    } catch (e) {
      $("llm-status").style.color = "var(--vermilion-deep)";
      $("llm-status").textContent = e.message;
    }
  });

  bindIngest();
  loadSettings();
  refreshBooks();
  refreshShelf();
  api("/api/llm_config")
    .then((r) => {
      state.llm = r.config;
      if ($("llm-base-url")) $("llm-base-url").value = r.config.base_url || "";
      if ($("llm-model")) $("llm-model").value = r.config.model || "";
      if ($("llm-status")) {
        $("llm-status").textContent = r.config.api_key_set
          ? "当前：已设置 Key · " + (r.config.model || "")
          : "���前：未设置 Key（游玩不需要）";
      }
      if (r.config.enabled) {
        state.settings.llmEnabled = "on";
        syncSettingsUI();
      }
    })
    .catch(() => {});
  api("/api/achievements")
    .then((r) => {
      state.allAch = r.all || [];
      state.meta = r.meta || state.meta;
    })
    .catch(() => {});
}

bind();
