import { test, expect } from "@playwright/test";

test("a late question response does not replace the page reached with Back", async ({ page }) => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route("**/data/chunks/*.json", async route => { await gate; await route.continue(); });
  await page.goto("./");
  await page.getByRole("link", { name: "문제풀기", exact: true }).click();
  await expect(page.getByText("문제를 불러오는 중…", { exact: true })).toBeVisible();
  await page.goBack();
  release();
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("link", { name: "문제풀기", exact: true })).toBeVisible();
  await expect(page.locator("section.question")).toHaveCount(0);
});

test("record filters update immediately when revisit is switched on and off", async ({ page, request, baseURL }) => {
  const idx = await index(request, baseURL);
  const ids = idx.items.map(item => item[0]);
  const qid = ids[0];
  await seed(page, stateWithAllCorrectExcept(ids, []));
  await page.goto("./#/records");
  await page.locator(`[data-revisit-id="${qid}"]`).click();
  const filter = page.locator('[data-filter="revisit"]');
  await expect(filter).toHaveText("다시 만나기 1");
  await filter.click();
  await page.locator(`[data-revisit-id="${qid}"]`).click();
  await expect(page.locator('[data-filter="revisit"]')).toHaveText("다시 만나기 0");
  await expect(page.locator(".rec-count")).toHaveText("0개");
  await expect(page.locator(".rec-list > li")).toHaveCount(0);
  await expect(page.locator('[data-filter="revisit"]')).toBeFocused();
});

const KEY = "pe500:progress";
let INDEX = null;
const chunkCache = new Map();

async function index(request, baseURL) {
  if (!INDEX) INDEX = await (await request.get(new URL("data/index.json", baseURL).href)).json();
  return INDEX;
}

async function question(request, baseURL, qid) {
  const idx = await index(request, baseURL);
  const n = idx.items.find((x) => x[0] === qid)[4];
  if (!chunkCache.has(n)) {
    const name = `data/chunks/c${String(n).padStart(3, "0")}.json`;
    chunkCache.set(n, await (await request.get(new URL(name, baseURL).href)).json());
  }
  return chunkCache.get(n).find((q) => q.id === qid);
}

function stateWithAllCorrectExcept(ids, except) {
  const records = {};
  for (const id of ids) if (!except.includes(id)) records[id] = { attempts: 1, correctCount: 1, last: "correct", lastAt: 1 };
  return { version: 1, records, revisit: {}, recent: [] };
}

async function seed(page, state) {
  await page.addInitScript(([k, v]) => {
    if (!sessionStorage.getItem("seeded")) {
      localStorage.setItem(k, v);
      sessionStorage.setItem("seeded", "1");
    }
  }, [KEY, JSON.stringify(state)]);
}

async function currentQid(page) {
  const sec = page.locator("section.question");
  await expect(sec).toBeVisible();
  return sec.getAttribute("data-qid");
}

async function displayedTexts(page) {
  return page.locator(".choice .choice-text").allTextContents();
}

async function answer(page, request, baseURL, correct) {
  const qid = await currentQid(page);
  const q = await question(request, baseURL, qid);
  const ans = q.choices.find((c) => c.id === q.answer).text;
  const texts = await displayedTexts(page);
  const pos = correct ? texts.indexOf(ans) : texts.findIndex((t) => t !== ans);
  expect(pos).toBeGreaterThanOrEqual(0);
  await page.locator(".choice").nth(pos).click();
  await page.getByRole("button", { name: "제출", exact: true }).click();
  await expect(page.locator(".result-title")).toHaveText(correct ? "정답입니다" : "오답입니다");
  return { qid, q, pos, ans };
}

test("home shows 문제풀기 and full counts", async ({ page }) => {
  await page.goto("./");
  await expect(page.getByRole("link", { name: "문제풀기" })).toBeVisible();
  await expect(page.locator(".stat").first()).toContainText("500");
});

test("question shows ≥10 choices and hides answer/explanation before submit", async ({ page, request, baseURL }) => {
  await page.goto("./#/quiz");
  const qid = await currentQid(page);
  const q = await question(request, baseURL, qid);
  await expect(page.locator(".choice")).toHaveCount(q.choices.length);
  expect(q.choices.length).toBeGreaterThanOrEqual(10);
  // Nothing from the explanation or per-choice notes exists anywhere in the DOM yet.
  const html = await page.content();
  expect(html).not.toContain(q.explain.ask);
  for (const c of q.choices) expect(html).not.toContain(c.note);
  await expect(page.locator(".explain, .result, .mark")).toHaveCount(0);
  expect(await page.title()).not.toContain(q.choices.find((c) => c.id === q.answer).text);
  const aria = await page.locator("body").ariaSnapshot();
  expect(aria).not.toContain("정답");
  await expect(page.getByRole("button", { name: "제출", exact: true })).toBeDisabled();
});

test("selecting does not move options; submit shows feedback and linked explanation", async ({ page, request, baseURL }) => {
  await page.goto("./#/quiz");
  await currentQid(page);
  const before = await displayedTexts(page);
  await page.locator(".choice").nth(3).click();
  await page.locator(".choice").nth(5).click();
  expect(await displayedTexts(page)).toEqual(before);
  const { q, pos, ans } = await answer(page, request, baseURL, false);
  expect(await displayedTexts(page)).toEqual(before);
  const ansPos = before.indexOf(ans) + 1;
  await expect(page.locator(".result")).toContainText(`정답은 ${String.fromCodePoint(0x2460 + ansPos - 1)}번`);
  const notes = page.locator(".choice-notes li");
  await expect(notes).toHaveCount(q.choices.length);
  // Note i explains displayed choice i, and the answer note sits at the answer's displayed position.
  for (let i = 0; i < before.length; i++) await expect(notes.nth(i).locator(".cn-text")).toHaveText(before[i]);
  await expect(notes.nth(ansPos - 1)).toHaveClass(/ans/);
  await expect(notes.nth(pos)).toHaveClass(/mine/);
  const tipText = q.explain.tip.split("\n")[0].replace(/^\s*[-•]\s*/, "").replaceAll("`", "");
  await expect(page.locator(".explain")).toContainText(tipText.slice(0, 20));
});

test("correct answers leave the pool, wrong ones return, then completion", async ({ page, request, baseURL }) => {
  const idx = await index(request, baseURL);
  const ids = idx.items.map((x) => x[0]);
  const [A, B] = [ids[5], ids[250]];
  await seed(page, stateWithAllCorrectExcept(ids, [A, B]));
  await page.goto("./");
  await expect(page.locator(".stat").first()).toContainText("2");
  await page.getByRole("link", { name: "문제풀기" }).click();
  const first = await currentQid(page);
  expect([A, B]).toContain(first);
  const other = first === A ? B : A;
  await answer(page, request, baseURL, false); // first stays unresolved
  await page.getByRole("button", { name: "다음 문제", exact: true }).click();
  expect(await currentQid(page)).toBe(other); // not the same one twice in a row
  await answer(page, request, baseURL, true);
  await page.getByRole("button", { name: "다음 문제", exact: true }).click();
  expect(await currentQid(page)).toBe(first); // the wrong one comes back
  await answer(page, request, baseURL, true);
  await page.getByRole("button", { name: "다음 문제", exact: true }).click();
  await expect(page.getByRole("heading", { name: "출제할 문제가 없습니다" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "출제할 문제가 없습니다" })).toBeVisible();
});

test("revisit ON re-adds a solved question, survives a correct answer, OFF removes it", async ({ page, request, baseURL }) => {
  const idx = await index(request, baseURL);
  const ids = idx.items.map((x) => x[0]);
  const X = ids[123];
  await seed(page, stateWithAllCorrectExcept(ids, []));
  await page.goto("./#/records");
  await page.getByRole("searchbox", { name: "기록 검색" }).fill(X);
  const toggle = page.getByRole("button", { name: new RegExp(`\\(${X}\\) 다시 만나기`) });
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-pressed", "true");
  await page.goto("./#/");
  await expect(page.locator(".stat").first()).toContainText("1");
  await page.getByRole("link", { name: "문제풀기" }).click();
  expect(await currentQid(page)).toBe(X);
  await answer(page, request, baseURL, true);
  const tg = page.locator(".topbar .toggle");
  await expect(tg).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "다음 문제", exact: true }).click();
  expect(await currentQid(page)).toBe(X); // only eligible question; shown again instead of looping
  await page.locator(".topbar .toggle").click();
  await expect(page.locator(".topbar .toggle")).toHaveAttribute("aria-pressed", "false");
  await page.getByRole("link", { name: "← 처음" }).click();
  await page.getByRole("link", { name: "완료 화면 보기" }).click();
  await expect(page.getByRole("heading", { name: "출제할 문제가 없습니다" })).toBeVisible();
  const stored = await page.evaluate((k) => JSON.parse(localStorage.getItem(k)), KEY);
  expect(stored.records[X].attempts).toBe(2);
  expect(stored.revisit[X]).toBeUndefined();
});

test("progress survives reload", async ({ page, request, baseURL }) => {
  await page.goto("./#/quiz");
  const { qid } = await answer(page, request, baseURL, true);
  await page.goto("./");
  await page.reload();
  const stats = page.locator(".stat");
  await expect(stats.nth(2)).toContainText("1"); // 맞힘
  await expect(stats.first()).toContainText("499");
  const stored = await page.evaluate((k) => JSON.parse(localStorage.getItem(k)), KEY);
  expect(stored.records[qid].last).toBe("correct");
});

test("reset: cancel keeps data, confirm clears only this app's keys", async ({ page, request, baseURL }) => {
  await page.goto("./");
  await page.evaluate(() => localStorage.setItem("other-app:data", "keep me"));
  await page.goto("./#/quiz");
  await answer(page, request, baseURL, false);
  await page.goto("./#/");
  await page.getByRole("button", { name: "진도 초기화" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "취소" }).click();
  await expect(page.locator(".stat").nth(3)).toContainText("1"); // 틀림 still 1
  await page.getByRole("button", { name: "진도 초기화" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "초기화" }).click();
  await expect(page.locator(".stat").nth(3)).toContainText("0");
  await expect(page.locator(".stat").first()).toContainText("500");
  expect(await page.evaluate(() => localStorage.getItem("other-app:data"))).toBe("keep me");
  const stored = await page.evaluate((k) => JSON.parse(localStorage.getItem(k)), KEY);
  expect(Object.keys(stored.records)).toHaveLength(0);
});

test("each presentation reshuffles; grading follows choice identity across seeds", async ({ page, request, baseURL }) => {
  const idx = await index(request, baseURL);
  const qid = idx.items[77][0];
  const orders = new Set();
  for (let i = 0; i < 6; i++) {
    await page.goto(`./#/q/${qid}`);
    await page.reload();
    expect(await currentQid(page)).toBe(qid);
    orders.add((await displayedTexts(page)).join("\u0001"));
    await answer(page, request, baseURL, i % 2 === 0); // finds the answer by content in each new order
  }
  expect(orders.size).toBeGreaterThan(1);
});

test("storage failure keeps the session usable and tells the user", async ({ page, request, baseURL }) => {
  await page.addInitScript(() => {
    Storage.prototype.setItem = function () { throw new DOMException("full", "QuotaExceededError"); };
  });
  await page.goto("./");
  await expect(page.locator("#notice")).toContainText("저장할 수 없습니다");
  await page.getByRole("link", { name: "문제풀기" }).click();
  await answer(page, request, baseURL, true);
  await expect(page.locator(".explain")).toBeVisible();
  await page.getByRole("link", { name: "← 처음" }).click();
  await expect(page.locator(".stat").nth(2)).toContainText("1");
});

test("keyboard: choose with arrows/space and submit with Enter", async ({ page }) => {
  await page.goto("./#/quiz");
  await currentQid(page);
  await page.locator(".choice input").first().focus();
  await page.keyboard.press("Space");
  await page.keyboard.press("ArrowDown");
  await expect(page.locator(".choice input").nth(1)).toBeChecked();
  await page.keyboard.press("Enter");
  await expect(page.locator(".result")).toBeVisible();
});

test("layout: no page-level horizontal overflow; code scrolls inside its box", async ({ page, request, baseURL }) => {
  const idx = await index(request, baseURL);
  // Pick a question with the longest code line to stress the layout.
  let best = null;
  for (const n of [...new Set(idx.items.map(item => item[4]))]) {
    const name = `data/chunks/c${String(n).padStart(3, "0")}.json`;
    const list = await (await request.get(new URL(name, baseURL).href)).json();
    for (const q of list) if (q.code) {
      const w = Math.max(...q.code.text.split("\n").map((l) => l.length));
      if (!best || w > best.w) best = { id: q.id, w };
    }
  }
  test.skip(!best, "no code questions in sampled chunks");
  await page.goto(`./#/q/${best.id}`);
  await currentQid(page);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  const pre = page.locator("pre.code").first();
  await expect(pre).toHaveCSS("overflow-x", "auto");
  const box = await page.locator(".choice").first().boundingBox();
  expect(box.height).toBeGreaterThanOrEqual(44);
});
