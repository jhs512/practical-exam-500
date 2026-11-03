// localStorage persistence for this app only. Every key starts with PREFIX; reset
// removes only those keys. Failures (blocked storage, quota) never lose the in-memory
// session — the caller is told so it can show a notice.
import { emptyState, migrate } from "./domain.js";

export const PREFIX = "pe500:";
export const KEY = PREFIX + "progress";
export const CORRUPT_KEY = PREFIX + "progress.corrupt";

function storage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function load() {
  const ls = storage();
  if (!ls) return { state: emptyState(), persistent: false, recovered: false };
  let raw;
  try {
    raw = ls.getItem(KEY);
  } catch {
    return { state: emptyState(), persistent: false, recovered: false };
  }
  const { state, ok } = migrate(raw);
  if (!ok) {
    try {
      ls.setItem(CORRUPT_KEY, String(raw));
    } catch {
      /* backup is best effort */
    }
  }
  return { state, persistent: true, recovered: !ok };
}

export function save(state) {
  const ls = storage();
  if (!ls) return false;
  try {
    ls.setItem(KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

export function clearAll() {
  const ls = storage();
  if (!ls) return false;
  try {
    const keys = [];
    for (let i = 0; i < ls.length; i++) {
      const k = ls.key(i);
      if (k && k.startsWith(PREFIX)) keys.push(k);
    }
    keys.forEach((k) => ls.removeItem(k));
    return true;
  } catch {
    return false;
  }
}
