// Question data: a light index up front, 100-question chunks fetched on demand.
const BASE = new URL("../data/", import.meta.url);

let indexPromise = null;
const chunkCache = new Map();

export function loadIndex() {
  if (!indexPromise) {
    indexPromise = fetch(new URL("index.json", BASE)).then((r) => {
      if (!r.ok) throw new Error(`index ${r.status}`);
      return r.json();
    }).then((idx) => {
      const byId = new Map();
      for (const [id, area, label, topic, chunk] of idx.items) byId.set(id, { id, area, label, topic, chunk });
      return { ...idx, byId, ids: idx.items.map((x) => x[0]), areaName: Object.fromEntries(idx.areas.map((a) => [a.id, a.name])) };
    });
    indexPromise.catch(() => { indexPromise = null; });
  }
  return indexPromise;
}

function loadChunk(n) {
  if (!chunkCache.has(n)) {
    const name = `chunks/c${String(n).padStart(3, "0")}.json`;
    const p = fetch(new URL(name, BASE)).then((r) => {
      if (!r.ok) throw new Error(`${name} ${r.status}`);
      return r.json();
    }).then((list) => new Map(list.map((q) => [q.id, q])));
    p.catch(() => chunkCache.delete(n));
    chunkCache.set(n, p);
  }
  return chunkCache.get(n);
}

export async function loadQuestion(id) {
  const idx = await loadIndex();
  const meta = idx.byId.get(id);
  if (!meta) throw new Error(`unknown question ${id}`);
  const chunk = await loadChunk(meta.chunk);
  return chunk.get(id);
}

export async function prefetchQuestion(id) {
  try {
    await loadQuestion(id);
  } catch {
    /* prefetch is opportunistic */
  }
}
