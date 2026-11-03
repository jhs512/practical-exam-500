// Learning-state domain: pure functions over a plain state object.
// A question's status comes only from submissions; viewing records nothing.

export const STATE_VERSION = 1;

export function emptyState() {
  return { version: STATE_VERSION, records: {}, revisit: {}, recent: [] };
}

export function statusOf(state, qid) {
  const r = state.records[qid];
  if (!r) return "new";
  return r.last === "correct" ? "correct" : "wrong";
}

export function isRevisit(state, qid) {
  return state.revisit[qid] === true;
}

// Pool = never tried, last answer wrong, or revisit ON. Only "correct and OFF" is excluded.
export function isEligible(state, qid) {
  return statusOf(state, qid) !== "correct" || isRevisit(state, qid);
}

export function recordAnswer(state, qid, correct, now = Date.now()) {
  const prev = state.records[qid] || { attempts: 0, correctCount: 0 };
  return {
    ...state,
    records: {
      ...state.records,
      [qid]: {
        attempts: prev.attempts + 1,
        correctCount: prev.correctCount + (correct ? 1 : 0),
        last: correct ? "correct" : "wrong",
        lastAt: now,
      },
    },
  };
}

export function setRevisit(state, qid, on) {
  const revisit = { ...state.revisit };
  if (on) revisit[qid] = true;
  else delete revisit[qid];
  return { ...state, revisit };
}

export const RECENT_MAX = 5;

export function markShown(state, qid) {
  const recent = [qid, ...state.recent.filter((x) => x !== qid)].slice(0, RECENT_MAX);
  return { ...state, recent };
}

// Uniform pick from the pool, avoiding recently shown questions when there is any
// alternative. Returns null when the pool is empty (completion state).
export function pickNext(state, allIds, randInt) {
  const pool = allIds.filter((id) => isEligible(state, id));
  if (pool.length === 0) return null;
  const recent = new Set(state.recent);
  let candidates = pool.filter((id) => !recent.has(id));
  if (candidates.length === 0) {
    const last = state.recent[0];
    candidates = pool.length > 1 ? pool.filter((id) => id !== last) : pool;
  }
  return candidates[randInt(candidates.length)];
}

export function summarize(state, allIds) {
  const s = { total: allIds.length, new: 0, correct: 0, wrong: 0, revisit: 0, eligible: 0 };
  for (const id of allIds) {
    s[statusOf(state, id)] += 1;
    if (isRevisit(state, id)) s.revisit += 1;
    if (isEligible(state, id)) s.eligible += 1;
  }
  return s;
}

// Accepts anything read from storage. Returns {state, ok}; ok=false means the input
// was unusable and the caller should keep a backup of the raw value.
export function migrate(raw) {
  if (raw == null) return { state: emptyState(), ok: true };
  let data = raw;
  if (typeof raw === "string") {
    try {
      data = JSON.parse(raw);
    } catch {
      return { state: emptyState(), ok: false };
    }
  }
  if (!data || typeof data !== "object" || typeof data.version !== "number") {
    return { state: emptyState(), ok: false };
  }
  if (data.version > STATE_VERSION) return { state: emptyState(), ok: false };
  // version 1 is current; future versions add steps here.
  const state = emptyState();
  for (const [qid, r] of Object.entries(data.records || {})) {
    if (!r || (r.last !== "correct" && r.last !== "wrong")) continue;
    state.records[qid] = {
      attempts: Math.max(1, r.attempts | 0),
      correctCount: Math.max(0, r.correctCount | 0),
      last: r.last,
      lastAt: Number(r.lastAt) || 0,
    };
  }
  for (const [qid, on] of Object.entries(data.revisit || {})) if (on === true) state.revisit[qid] = true;
  if (Array.isArray(data.recent)) state.recent = data.recent.filter((x) => typeof x === "string").slice(0, RECENT_MAX);
  return { state, ok: true };
}

// Unbiased Fisher-Yates. randInt(n) must return a uniform integer in [0, n).
export function shuffle(items, randInt) {
  const a = items.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = randInt(i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// Uniform integer in [0, n) from crypto with rejection sampling (no modulo bias).
export function cryptoRandInt(n) {
  const limit = Math.floor(0x100000000 / n) * n;
  const buf = new Uint32Array(1);
  for (;;) {
    crypto.getRandomValues(buf);
    if (buf[0] < limit) return buf[0] % n;
  }
}
