"""Second shared helper for area 08: data builders and a template-driven generator.

A template is `t(r, i) -> spec or None` where spec holds db, query (displayed code),
muts [(statement, note)], stem/ask/solve/tip and so on; `run_plan` turns templates
into questions. Not a family (no generate()).
"""
from __future__ import annotations

from families.sql_kit import (DB, DEPTS, FMT_RULE, NAMES, CITIES, eval_muts, q, search, sqlcode, fv)

EMP_COLS = ["id INTEGER", "name TEXT", "dept TEXT", "pos TEXT", "sal INTEGER"]
POS = ["사원", "대리", "과장"]
PRODS = ["노트북", "마우스", "키보드", "모니터", "케이블"]


def emp_rows(r, n, depts=None, sal=(250, 600), sal_step=10):
    depts = depts or r.sample(DEPTS, 3)
    names = r.sample(NAMES, n)
    return [(101 + i, nm, r.choice(depts), r.choice(POS), r.randrange(sal[0], sal[1], sal_step))
            for i, nm in enumerate(names)]


def fin(db, query, muts, fn=None, **kw):
    """Compute answer + wrong values. fn(stmt)->text defaults to db.f."""
    fn = fn or db.f
    ans = fn(query)
    wrong = eval_muts(fn, muts)
    return dict(db=db, query=query, answer=ans, wrong=wrong, **kw)


def differs(s, k=3):
    """True when the first k mutations all change the result (trap matters)."""
    return all(w[0] != s["answer"] for w in s["wrong"][:k])


def run_plan(fam, topic, srcs, plan):
    """plan: [(template, count)]. Returns questions with ids fam-NN."""
    out, n = [], 1
    for t, k in plan:
        for i in range(k):
            s = search(f"{fam}-{t.__name__}-{i}", lambda r, t=t, i=i: t(r, i))
            tabs = s.get("tables") or [s["db"].table(nm) for nm in s["db"].cols]
            out.append(q(id=f"{fam}-{n:02d}", difficulty=s["diff"], topic=s.get("topic", topic),
                         tags=["SQL"] + s["tags"], stem=s["stem"], spec=s, ask=s["ask"],
                         solve=s["solve"], tip=s["tip"], family=fam, sources=srcs,
                         code=sqlcode(s["code"] if "code" in s else s["query"]), tables=tabs))
            n += 1
    return out


def swap_muts(fmt_sql, exprs, cands):
    """fmt_sql has '{e}' placeholder for the comma-joined expression list. cands:
    {expr: meaning}. For each position j and each candidate != exprs[j], one mutation."""
    out = []
    for j in range(len(exprs)):
        for c, why in cands.items():
            if c == exprs[j] or c in exprs:
                continue
            new = list(exprs)
            new[j] = c
            out.append((fmt_sql.format(e=", ".join(new)),
                        f"{j + 1}번째 출력을 {c}로 읽었다. 이 식은 {why}이다. 문제의 {exprs[j]}과(와) 대상이 다르다."))
    if len(exprs) >= 2:
        for a in range(len(exprs)):
            for b in range(a + 1, len(exprs)):
                new = list(exprs)
                new[a], new[b] = new[b], new[a]
                out.append((fmt_sql.format(e=", ".join(new)),
                            f"출력 순서를 바꾸어 {a + 1}번째와 {b + 1}번째 값을 뒤바꿨다. SELECT 목록의 순서가 출력 열 순서다."))
    return out
