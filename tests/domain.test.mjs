import test from "node:test";
import assert from "node:assert/strict";
import {
  emptyState, recordAnswer, setRevisit, isEligible, pickNext, markShown, summarize, migrate, shuffle, statusOf, cryptoRandInt,
} from "../site/js/domain.js";

const ids = ["a", "b", "c", "d"];
const seq = (...xs) => { let i = 0; return (n) => xs[i++ % xs.length] % n; };

test("viewing never marks solved; only submissions do", () => {
  let s = emptyState();
  s = markShown(s, "a");
  assert.equal(statusOf(s, "a"), "new");
  assert.ok(isEligible(s, "a"));
});

test("correct answer leaves the pool; wrong stays", () => {
  let s = recordAnswer(emptyState(), "a", true);
  s = recordAnswer(s, "b", false);
  assert.equal(isEligible(s, "a"), false);
  assert.equal(isEligible(s, "b"), true);
  assert.deepEqual(summarize(s, ids), { total: 4, new: 2, correct: 1, wrong: 1, revisit: 0, eligible: 3 });
});

test("revisit ON brings a solved question back; OFF removes it again", () => {
  let s = recordAnswer(emptyState(), "a", true);
  s = setRevisit(s, "a", true);
  assert.ok(isEligible(s, "a"));
  s = recordAnswer(s, "a", true); // answering right again must not clear the toggle
  assert.equal(s.revisit.a, true);
  s = setRevisit(s, "a", false);
  assert.equal(isEligible(s, "a"), false);
  assert.equal(s.records.a.attempts, 2);
});

test("wrong question stays eligible even with revisit OFF", () => {
  let s = recordAnswer(emptyState(), "a", true);
  s = recordAnswer(s, "a", false);
  s = setRevisit(s, "a", false);
  assert.ok(isEligible(s, "a"));
});

test("pickNext avoids the question just shown when others exist", () => {
  let s = emptyState();
  for (const id of ["b", "c", "d"]) s = recordAnswer(s, id, true);
  s = recordAnswer(s, "a", false);
  s = recordAnswer(s, "b", false);
  s = markShown(s, "a");
  for (let k = 0; k < 20; k++) assert.equal(pickNext(s, ids, cryptoRandInt), "b");
});

test("pickNext repeats the only remaining question instead of looping", () => {
  let s = emptyState();
  for (const id of ids) s = recordAnswer(s, id, id !== "c");
  s = markShown(s, "c");
  assert.equal(pickNext(s, ids, cryptoRandInt), "c");
});

test("pickNext returns null when nothing is eligible (completion)", () => {
  let s = emptyState();
  for (const id of ids) s = recordAnswer(s, id, true);
  assert.equal(pickNext(s, ids, cryptoRandInt), null);
});

test("pickNext prefers questions outside the recent window", () => {
  let s = emptyState();
  for (const id of ["a", "b", "c"]) s = markShown(s, id);
  for (let k = 0; k < 30; k++) assert.equal(pickNext(s, ids, cryptoRandInt), "d");
});

test("shuffle is a permutation and unbiased (chi-square over 4 items)", () => {
  const counts = {};
  const N = 48000;
  for (let i = 0; i < N; i++) {
    const p = shuffle(ids, cryptoRandInt).join("");
    counts[p] = (counts[p] || 0) + 1;
  }
  assert.equal(Object.keys(counts).length, 24);
  const exp = N / 24;
  const chi = Object.values(counts).reduce((t, c) => t + (c - exp) ** 2 / exp, 0);
  assert.ok(chi < 49.7, `chi-square ${chi}`); // df=23, p≈0.001
});

test("grading by choice id is independent of shuffle order (many seeds)", () => {
  const choices = Array.from({ length: 10 }, (_, i) => ({ id: `c${i}`, correct: i === 7 }));
  for (let seed = 0; seed < 500; seed++) {
    const order = shuffle(choices.map((c) => c.id), cryptoRandInt);
    const pos = order.indexOf("c7");
    const picked = order[pos];
    assert.equal(picked, "c7");
    assert.equal(choices.find((c) => c.id === picked).correct, true);
  }
});

test("migrate handles empty, corrupt, future and partial data", () => {
  assert.deepEqual(migrate(null), { state: emptyState(), ok: true });
  assert.equal(migrate("{not json").ok, false);
  assert.equal(migrate(JSON.stringify({ version: 99 })).ok, false);
  const { state, ok } = migrate(JSON.stringify({
    version: 1, records: { a: { attempts: 2, correctCount: 1, last: "correct", lastAt: 5 }, bad: { last: "x" } },
    revisit: { a: true, b: "yes" }, recent: ["a", 3],
  }));
  assert.ok(ok);
  assert.deepEqual(Object.keys(state.records), ["a"]);
  assert.deepEqual(state.revisit, { a: true });
  assert.deepEqual(state.recent, ["a"]);
});

test("cryptoRandInt stays in range", () => {
  for (let i = 0; i < 1000; i++) { const v = cryptoRandInt(10); assert.ok(v >= 0 && v < 10); }
  assert.equal(seq(3)(2), 1);
});
