import {
  cryptoRandInt, isRevisit, markShown, pickNext, recordAnswer, setRevisit, shuffle, statusOf, summarize, emptyState,
} from "./domain.js";
import { clearAll, load, save } from "./storage.js";
import { loadIndex, loadQuestion, prefetchQuestion } from "./data.js";

const APP_TITLE = "정보처리기사 실기 500";
const STATUS_LABEL = { new: "미풀이", correct: "맞힘", wrong: "틀림" };
const DIFF_LABEL = { 1: "기본", 2: "응용", 3: "심화" };

const view = document.getElementById("view");
const notice = document.getElementById("notice");

let index = null;
let state = emptyState();
let persistent = true;
let saveFailed = false;
// Current presentation: the shuffled order is fixed for the life of this object and is
// never stored, so a saved index can never change which choice is graded as correct.
let current = null;
let nextId = null;
let presentationRequest = 0;

// ---------- helpers ----------
function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

function inline(text) {
  // `code` spans; everything else is text (never parsed as HTML).
  const out = [];
  String(text).split(/(`[^`\n]+`)/).forEach((part) => {
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) out.push(h("code", {}, part.slice(1, -1)));
    else if (part) out.push(part);
  });
  return out;
}

function richText(text) {
  // Paragraphs separated by blank lines; "- " lines become a list; other newlines are kept.
  const frag = document.createDocumentFragment();
  const lines = String(text).split("\n");
  let para = [];
  let list = null;
  const flushPara = () => {
    if (para.length) {
      const p = h("p");
      para.forEach((l, i) => { if (i) p.append(h("br")); p.append(...inline(l)); });
      frag.append(p);
      para = [];
    }
  };
  for (const line of lines) {
    const m = line.match(/^\s*[-•]\s+(.*)$/);
    if (m) {
      flushPara();
      if (!list) { list = h("ul"); frag.append(list); }
      list.append(h("li", {}, ...inline(m[1])));
    } else if (!line.trim()) {
      flushPara();
      list = null;
    } else {
      list = null;
      para.push(line);
    }
  }
  flushPara();
  return frag;
}

function tableEl(t) {
  return h("div", { class: "table-wrap", tabindex: "0", role: "region", "aria-label": t.caption ? `표: ${t.caption}` : "표" },
    h("table", {},
      t.caption ? h("caption", {}, t.caption) : null,
      h("thead", {}, h("tr", {}, t.columns.map((c) => h("th", { scope: "col" }, c)))),
      h("tbody", {}, t.rows.map((r) => h("tr", {}, r.map((v) => h("td", {}, v)))))));
}

function codeEl(code) {
  const lang = { c: "C", java: "Java", python: "Python", sql: "SQL", cpp: "C++", text: "" }[code.lang] ?? "";
  return h("div", { class: "code-wrap" },
    lang ? h("div", { class: "code-lang", "aria-hidden": "true" }, lang) : null,
    h("pre", { class: "code", tabindex: "0", role: "region", "aria-label": `${lang} 코드 (가로로 스크롤 가능)` },
      h("code", {}, code.text)));
}

function persist() {
  const ok = save(state);
  if (!ok && !saveFailed) {
    saveFailed = true;
    showNotice();
  }
}

function showNotice(extra) {
  const msgs = [];
  if (!persistent || saveFailed) msgs.push("이 브라우저에 학습 기록을 저장할 수 없습니다(저장 차단 또는 용량 부족). 지금 탭에서는 계속 풀 수 있지만 새로고침하면 기록이 사라집니다.");
  if (extra) msgs.push(extra);
  notice.replaceChildren(...msgs.map((m) => h("p", {}, m)));
  notice.hidden = msgs.length === 0;
}

const circled = (n) => (n <= 20 ? String.fromCodePoint(0x2460 + n - 1) : `(${n})`);

function setTitle(t) {
  document.title = t ? `${t} — ${APP_TITLE}` : APP_TITLE;
}

function focusMain() {
  const hd = view.querySelector("h1, h2");
  if (hd) { hd.setAttribute("tabindex", "-1"); hd.focus({ preventScroll: true }); }
  window.scrollTo(0, 0);
}

// ---------- home ----------
function renderHome() {
  setTitle("");
  const s = summarize(state, index.ids);
  const stat = (label, value, hint) => h("div", { class: "stat" },
    h("dt", {}, label), h("dd", {}, value.toLocaleString("ko-KR")), hint ? h("p", { class: "stat-hint" }, hint) : null);
  view.replaceChildren(
    h("section", { class: "home" },
      h("h1", { class: "home-title" }, "정보처리기사 실기", h("span", {}, "500문항 랜덤 훈련")),
      h("p", { class: "lead small" }, "12개 영역 · 자체 제작 연습문제"),
      h("p", { class: "lead" }, "들어올 때마다 아직 못 맞힌 문제 중 하나가 무작위로 나옵니다. 맞힌 문제는 빠지고, 틀린 문제는 다시 나옵니다."),
      s.eligible > 0
        ? h("a", { class: "btn btn-primary btn-xl", href: "#/quiz" }, "문제풀기")
        : h("div", { class: "done-inline" }, h("p", {}, "지금 출제할 문제가 없습니다."), h("a", { class: "btn", href: "#/quiz" }, "완료 화면 보기")),
      h("dl", { class: "stats" },
        stat("지금 출제 대상", s.eligible, "미풀이 + 틀림 + 다시 만나기"),
        stat("미풀이", s.new),
        stat("맞힘", s.correct, "마지막 제출이 정답"),
        stat("틀림", s.wrong, "마지막 제출이 오답"),
        stat("다시 만나기", s.revisit, "맞혀도 계속 출제")),
      h("div", { class: "home-links" },
        h("a", { class: "btn", href: "#/records" }, "기록·다시 만나기 관리"),
        h("button", { class: "btn btn-quiet", type: "button", onclick: openReset }, "진도 초기화"))));
  focusMain();
}

// ---------- quiz ----------
async function startQuiz(specificId) {
  const request = ++presentationRequest;
  let id = specificId;
  if (!id) {
    id = nextId && index.byId.has(nextId) && pickable(nextId) ? nextId : pickNext(state, index.ids, cryptoRandInt);
    nextId = null;
  }
  if (!id) { renderDone(); return; }
  view.replaceChildren(h("p", { class: "loading", role: "status" }, "문제를 불러오는 중…"));
  let q;
  try {
    q = await loadQuestion(id);
  } catch (e) {
    if (request !== presentationRequest) return;
    view.replaceChildren(h("section", { class: "error" },
      h("h1", {}, "문제를 불러오지 못했습니다"),
      h("p", {}, "네트워크 연결을 확인한 뒤 다시 시도하세요."),
      h("button", { class: "btn btn-primary", type: "button", onclick: () => startQuiz(specificId) }, "다시 시도")));
    return;
  }
  if (request !== presentationRequest) return;
  current = { q, order: shuffle(q.choices.map((c) => c.id), cryptoRandInt), selected: null, submitted: false };
  state = markShown(state, id);
  persist();
  renderQuestion();
  focusMain();
  // Warm the next question's chunk so "다음 문제" is instant.
  const peek = pickNext(state, index.ids, cryptoRandInt);
  if (peek) { nextId = peek; prefetchQuestion(peek); }
}

function goNext() {
  if (location.hash === "#/quiz") startQuiz();
  else location.hash = "#/quiz";
}

function pickable(id) {
  return state.recent[0] !== id && (statusOf(state, id) !== "correct" || isRevisit(state, id));
}

function renderQuestion() {
  const { q } = current;
  const meta = index.byId.get(q.id);
  const status = statusOf(state, q.id);
  const rec = state.records[q.id];
  setTitle("문제 풀기");
  const mono = q.code != null || q.area === "10" || q.choices.some((c) => c.text.includes("\n"));
  const byId = new Map(q.choices.map((c) => [c.id, c]));

  const choiceList = h("div", { class: `choices${mono ? " mono" : ""}` },
    current.order.map((cid, i) => {
      const c = byId.get(cid);
      const input = h("input", {
        type: "radio", name: "choice", value: cid, id: `opt-${i}`,
        checked: current.selected === cid, disabled: current.submitted,
        onchange: () => { current.selected = cid; updateSubmit(); },
      });
      let mark = null;
      let cls = "choice";
      if (current.submitted) {
        if (cid === q.answer) { cls += " is-answer"; mark = h("span", { class: "mark" }, "정답"); }
        else if (cid === current.selected) { cls += " is-wrong"; mark = h("span", { class: "mark" }, "내 선택"); }
      }
      return h("label", { class: cls, for: `opt-${i}` }, input,
        h("span", { class: "num", "aria-hidden": "true" }, circled(i + 1)),
        h("span", { class: "choice-text" }, c.text), mark);
    }));

  const submitBtn = h("button", { class: "btn btn-primary btn-wide", type: "submit", disabled: !current.selected || current.submitted }, "제출");
  function updateSubmit() { submitBtn.disabled = !current.selected || current.submitted; }

  const form = h("form", { class: "quiz-form", onsubmit: onSubmit },
    h("fieldset", {}, h("legend", { class: "sr-only" }, "보기 중 하나를 고르세요"), choiceList),
    current.submitted ? null : submitBtn);

  const revisitOn = isRevisit(state, q.id);
  const revisitBtn = h("button", {
    class: `toggle${revisitOn ? " on" : ""}`, type: "button", "aria-pressed": revisitOn ? "true" : "false",
    onclick: () => {
      state = setRevisit(state, q.id, !isRevisit(state, q.id));
      persist();
      const on = isRevisit(state, q.id);
      revisitBtn.setAttribute("aria-pressed", on ? "true" : "false");
      revisitBtn.classList.toggle("on", on);
    },
  }, h("span", { class: "toggle-track", "aria-hidden": "true" }, h("span", { class: "toggle-thumb" })), "다시 만나기");

  const header = h("div", { class: "q-meta" },
    h("span", { class: "chip" }, index.areaName[q.area]),
    h("span", { class: "chip chip-soft" }, q.topic),
    h("span", { class: "chip chip-soft" }, DIFF_LABEL[q.difficulty]),
    !current.submitted && status !== "new" ? h("span", { class: "chip chip-soft" }, `이전: ${STATUS_LABEL[status]} · ${rec.attempts}회 시도`) : null);

  const body = h("section", { class: "question", "aria-labelledby": "q-stem", "data-qid": q.id },
    header,
    h("h1", { id: "q-stem", class: "stem" }, richText(q.stem)),
    q.code ? codeEl(q.code) : null,
    (q.tables || []).map(tableEl),
    form);

  const feedback = h("div", { class: "feedback-live", "aria-live": "polite", role: "status" });
  const parts = [h("div", { class: "topbar" }, h("a", { class: "back", href: "#/" }, "← 처음"), revisitBtn), body, feedback];

  if (current.submitted) {
    const correct = current.selected === q.answer;
    const ansPos = current.order.indexOf(q.answer) + 1;
    feedback.append(h("div", { class: `result ${correct ? "ok" : "ng"}` },
      h("p", { class: "result-title" }, correct ? "정답입니다" : "오답입니다"),
      correct ? null : h("p", {}, `정답은 ${circled(ansPos)}번입니다.`),
      h("button", { class: "btn btn-primary btn-wide", type: "button", onclick: goNext }, "다음 문제")));
    parts.push(renderExplanation(q), h("div", { class: "next-row" },
      h("button", { class: "btn btn-wide", type: "button", id: "next-btn", onclick: goNext }, "다음 문제 풀기")));
  }
  view.replaceChildren(...parts);

  function onSubmit(ev) {
    ev.preventDefault();
    if (!current.selected || current.submitted) return;
    current.submitted = true;
    state = recordAnswer(state, q.id, current.selected === q.answer);
    persist();
    renderQuestion();
    const res = view.querySelector(".result");
    if (res) { res.setAttribute("tabindex", "-1"); res.focus({ preventScroll: false }); }
  }
}

function renderExplanation(q) {
  const byId = new Map(q.choices.map((c) => [c.id, c]));
  const ex = q.explain;
  const solve = ex.solve.map((b) => {
    if (typeof b === "string") return h("div", { class: "solve-block" }, richText(b));
    if (b.pre) return h("pre", { class: "code", tabindex: "0" }, h("code", {}, b.pre));
    if (b.table) return tableEl(b.table);
    return null;
  });
  const notes = h("ol", { class: "choice-notes" }, current.order.map((cid, i) => {
    const c = byId.get(cid);
    const isAns = cid === q.answer;
    const mine = cid === current.selected;
    return h("li", { class: isAns ? "ans" : mine ? "mine" : "" },
      h("div", { class: "cn-head" },
        h("span", { class: "num" }, circled(i + 1)),
        h("span", { class: "cn-tag" }, isAns ? "정답" : mine ? "내 선택 · 오답" : "오답"),
        h("span", { class: "cn-text" }, c.text)),
      h("div", { class: "cn-note" }, richText(c.note)));
  }));
  return h("section", { class: "explain", "aria-labelledby": "ex-title" },
    h("h2", { id: "ex-title" }, "해설"),
    h("h3", {}, "무엇을 묻는가"), h("div", {}, richText(ex.ask)),
    h("h3", {}, "풀이"), ...solve,
    h("h3", {}, "보기별 해설"), notes,
    h("h3", {}, "비슷한 문제에서 볼 점"), h("div", {}, richText(ex.tip)));
}

function renderDone() {
  setTitle("완료");
  const s = summarize(state, index.ids);
  view.replaceChildren(h("section", { class: "done" },
    h("h1", {}, "출제할 문제가 없습니다"),
    h("p", {}, `${s.total.toLocaleString("ko-KR")}문항 중 ${s.correct.toLocaleString("ko-KR")}문항을 맞혔고, 틀린 문제와 다시 만나기 문제가 남아 있지 않습니다.`),
    h("p", {}, "기록 화면에서 다시 풀고 싶은 문제의 ‘다시 만나기’를 켜거나, 진도를 초기화하면 다시 출제됩니다."),
    h("div", { class: "home-links" },
      h("a", { class: "btn btn-primary", href: "#/records" }, "기록·다시 만나기 관리"),
      h("button", { class: "btn", type: "button", onclick: openReset }, "진도 초기화"),
      h("a", { class: "btn btn-quiet", href: "#/" }, "처음으로"))));
  focusMain();
}

// ---------- records ----------
const recUi = { filter: "tried", query: "", area: "", limit: 50 };

function renderRecords() {
  setTitle("기록");
  const s = summarize(state, index.ids);
  const filters = [
    ["tried", `푼 문제 ${s.correct + s.wrong}`],
    ["wrong", `틀림 ${s.wrong}`],
    ["correct", `맞힘 ${s.correct}`],
    ["revisit", `다시 만나기 ${s.revisit}`],
    ["all", `전체 ${s.total}`],
  ];
  const list = h("ul", { class: "rec-list" });
  const countLine = h("p", { class: "rec-count", role: "status" });
  const more = h("button", { class: "btn", type: "button", onclick: () => { recUi.limit += 50; fill(); } }, "더 보기");

  function matches(meta) {
    const st = statusOf(state, meta.id);
    if (recUi.filter === "tried" && st === "new") return false;
    if (recUi.filter === "wrong" && st !== "wrong") return false;
    if (recUi.filter === "correct" && st !== "correct") return false;
    if (recUi.filter === "revisit" && !isRevisit(state, meta.id)) return false;
    if (recUi.area && meta.area !== recUi.area) return false;
    const qy = recUi.query.trim().toLowerCase();
    if (qy && !(meta.id.includes(qy) || meta.topic.toLowerCase().includes(qy) || index.areaName[meta.area].includes(qy))) return false;
    return true;
  }

  function fill() {
    const totals = summarize(state, index.ids);
    const counts = { tried: totals.correct + totals.wrong, wrong: totals.wrong, correct: totals.correct, revisit: totals.revisit, all: totals.total };
    const names = { tried: "푼 문제", wrong: "틀림", correct: "맞힘", revisit: "다시 만나기", all: "전체" };
    for (const button of filterBar.querySelectorAll("[data-filter]")) {
      const key = button.dataset.filter;
      button.textContent = `${names[key]} ${counts[key]}`;
    }
    const metas = index.ids.map((id) => index.byId.get(id)).filter(matches);
    metas.sort((a, b) => (state.records[b.id]?.lastAt || 0) - (state.records[a.id]?.lastAt || 0));
    countLine.textContent = `${metas.length.toLocaleString("ko-KR")}개`;
    list.replaceChildren(...metas.slice(0, recUi.limit).map((m) => {
      const st = statusOf(state, m.id);
      const r = state.records[m.id];
      const on = isRevisit(state, m.id);
      const tg = h("button", {
        class: `toggle small${on ? " on" : ""}`, type: "button", "aria-pressed": on ? "true" : "false",
        "data-revisit-id": m.id,
        "aria-label": `${m.topic} (${m.id}) 다시 만나기`,
        onclick: () => {
          const rowIndex = [...list.children].indexOf(tg.closest("li"));
          state = setRevisit(state, m.id, !isRevisit(state, m.id));
          persist();
          fill();
          const replacement = list.querySelector(`[data-revisit-id="${m.id}"]`)
            ?? list.children[Math.min(rowIndex, list.children.length - 1)]?.querySelector("button")
            ?? filterBar.querySelector('[aria-pressed="true"]');
          replacement?.focus({ preventScroll: true });
        },
      }, h("span", { class: "toggle-track", "aria-hidden": "true" }, h("span", { class: "toggle-thumb" })), "다시 만나기");
      return h("li", { class: "rec" },
        h("div", { class: "rec-main" },
          h("span", { class: `badge st-${st}` }, STATUS_LABEL[st]),
          h("span", { class: "rec-topic" }, m.topic),
          h("span", { class: "rec-sub" }, `${index.areaName[m.area]} · ${m.id}${r ? ` · ${r.attempts}회 시도, 정답 ${r.correctCount}회` : ""}`)),
        h("div", { class: "rec-actions" }, tg, h("a", { class: "btn btn-small", href: `#/q/${m.id}` }, "풀기")));
    }));
    more.hidden = metas.length <= recUi.limit;
  }

  const search = h("input", {
    type: "search", class: "search", placeholder: "주제·영역·문항 ID 검색", "aria-label": "기록 검색", value: recUi.query,
    oninput: (e) => { recUi.query = e.target.value; recUi.limit = 50; fill(); },
  });
  const areaSel = h("select", {
    "aria-label": "영역", class: "area-select",
    onchange: (e) => { recUi.area = e.target.value; recUi.limit = 50; fill(); },
  }, h("option", { value: "" }, "모든 영역"), index.areas.map((a) => h("option", { value: a.id, selected: recUi.area === a.id }, `${a.id} ${a.name}`)));
  const filterBar = h("div", { class: "filters", role: "group", "aria-label": "상태 필터" },
    filters.map(([k, label]) => h("button", {
      type: "button", class: `filter${recUi.filter === k ? " on" : ""}`, "aria-pressed": recUi.filter === k ? "true" : "false",
      "data-filter": k,
      onclick: () => { recUi.filter = k; recUi.limit = 50; renderRecords(); },
    }, label)));

  view.replaceChildren(h("section", { class: "records" },
    h("div", { class: "topbar" }, h("a", { class: "back", href: "#/" }, "← 처음")),
    h("h1", {}, "기록·다시 만나기"),
    h("p", { class: "lead small" }, "‘다시 만나기’를 켠 문제는 이미 맞혔어도 랜덤 출제에 다시 포함됩니다. 끄면 맞힌 문제는 다시 빠집니다(틀린 문제는 끄더라도 맞힐 때까지 나옵니다)."),
    filterBar, h("div", { class: "search-row" }, search, areaSel), countLine, list, more,
    h("div", { class: "home-links" }, h("button", { class: "btn btn-quiet", type: "button", onclick: openReset }, "진도 초기화"))));
  fill();
  focusMain();
}

// ---------- reset ----------
const dialog = document.getElementById("reset-dialog");
function openReset() {
  if (typeof dialog.showModal === "function") dialog.showModal();
  else if (confirm("이 앱의 학습 기록(맞힘·틀림·시도 횟수·다시 만나기)을 모두 지울까요?")) doReset();
}
dialog.addEventListener("close", () => {
  if (dialog.returnValue === "reset") doReset();
});
function doReset() {
  presentationRequest++;
  clearAll();
  state = emptyState();
  saveFailed = false;
  current = null;
  nextId = null;
  persist();
  showNotice("학습 기록을 초기화했습니다. 500문항이 다시 출제 대상입니다.");
  if (location.hash === "#/" || location.hash === "") renderHome();
  else location.hash = "#/";
}

// ---------- routing ----------
function route() {
  presentationRequest++;
  const hash = location.hash || "#/";
  if (hash !== "#/") showNotice();
  if (hash.startsWith("#/q/")) startQuiz(decodeURIComponent(hash.slice(4)));
  else if (hash === "#/quiz") startQuiz();
  else if (hash === "#/records") renderRecords();
  else renderHome();
}

async function boot() {
  const loaded = load();
  state = loaded.state;
  persistent = loaded.persistent;
  if (persistent && !save(state)) saveFailed = true;
  showNotice(loaded.recovered ? "저장된 기록을 읽을 수 없어 새로 시작합니다(이전 내용은 백업 키에 보관)." : undefined);
  try {
    index = await loadIndex();
  } catch {
    view.replaceChildren(h("section", { class: "error" }, h("h1", {}, "문항 목록을 불러오지 못했습니다"),
      h("p", {}, "네트워크 연결을 확인한 뒤 새로고침하세요."),
      h("button", { class: "btn btn-primary", type: "button", onclick: () => location.reload() }, "새로고침")));
    return;
  }
  window.addEventListener("hashchange", route);
  route();
}

boot();
