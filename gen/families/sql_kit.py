"""Shared helpers for area 08 (SQL) generators. Not a family: generate() returns [].

Every SQL question is computed by real execution in sqlite3. A spec builds small
tables, the correct statement gives the answer, and deliberately mutated statements
(each tied to a named misconception) give the wrong choices. Only behaviour that is
identical in standard SQL / Oracle is used: no LIMIT, no NULL sort position, no
integer division, deterministic ORDER BY whenever row order matters.
"""
from __future__ import annotations

import sqlite3

from core import QuestionError, make_question, norm, rng

AREA = "08"
EMPTY = "결과 없음"
FMT_RULE = "결과가 여러 행이면 행 순서대로 ' / '로, 한 행의 여러 열은 ', '로 구분해 적는다"

NAMES = ["김민수", "이서연", "박지훈", "최유진", "정다은", "강하늘", "조수아", "윤도현",
         "장예린", "임태호", "한지민", "오세훈", "서지우", "신동엽", "권나래", "황보람"]
DEPTS = ["영업", "개발", "인사", "기획", "총무"]
CITIES = ["서울", "부산", "대구", "광주", "인천"]


def generate():
    return []


def fv(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return f"{v:.2f}".rstrip("0").rstrip(".")
    return str(v)


def fmt(rows) -> str:
    if not rows:
        return EMPTY
    return " / ".join(", ".join(fv(v) for v in r) for r in rows)


class DB:
    """In-memory sqlite database built from [(table, ["col TYPE", ...], rows), ...]."""

    def __init__(self, schema):
        self.schema = schema
        self.c = sqlite3.connect(":memory:")
        self.cols = {}
        for name, cols, rows in schema:
            self.c.execute(f"CREATE TABLE {name} ({', '.join(cols)})")
            self.c.executemany(f"INSERT INTO {name} VALUES ({','.join('?' * len(cols))})", rows)
            self.cols[name] = [c.split()[0] for c in cols]

    def fresh(self) -> "DB":
        return DB(self.schema)

    def rows(self, sql):
        return [tuple(r) for r in self.c.execute(sql).fetchall()]

    def head(self, sql):
        cur = self.c.execute(sql)
        return [d[0] for d in cur.description], [tuple(r) for r in cur.fetchall()]

    def run(self, stmts):
        for s in ([stmts] if isinstance(stmts, str) else stmts):
            self.c.execute(s)

    def f(self, sql) -> str:
        return fmt(self.rows(sql))

    def table(self, name, caption=None, order=None) -> dict:
        cols = self.cols[name]
        rows = self.rows(f"SELECT * FROM {name}" + (f" ORDER BY {order}" if order else ""))
        return {"caption": caption or name, "columns": cols, "rows": [[fv(v) for v in r] for r in rows]}

    def block(self, sql, caption) -> dict:
        cols, rows = self.head(sql)
        if not rows:
            rows = [tuple("(없음)" for _ in cols)]
        return {"table": {"caption": caption, "columns": cols, "rows": [[fv(v) for v in r] for r in rows]}}

    def tblock(self, name, caption=None, order=None) -> dict:
        return {"table": self.table(name, caption, order)}


def eval_muts(fn, muts):
    """fn(statement) -> result text. muts: [(statement, note)]. Errors are dropped."""
    out = []
    for stmt, note in muts:
        try:
            out.append((fn(stmt), note))
        except sqlite3.Error:
            continue
    return out


def distinct_wrong(answer: str, wrong):
    seen = {norm(answer).lower()}
    out = []
    for t, n in wrong:
        k = norm(t).lower()
        if k in seen:
            continue
        seen.add(k)
        out.append((t, n))
    return out


def search(seed: str, build, need: int = 9, tries: int = 4000):
    """build(r) -> spec dict with 'answer' and 'wrong' (or None). Returns first spec
    with at least `need` distinct wrong values."""
    r = rng(seed)
    for _ in range(tries):
        spec = build(r)
        if not spec:
            continue
        w = distinct_wrong(spec["answer"], spec["wrong"])
        if len(w) >= need and spec["answer"] not in ("",):
            spec["wrong"] = w
            return spec
    raise QuestionError(f"{seed}: no data found with {need} distinct mutations")


def query_spec(db: DB, query: str, muts):
    """Evaluate a SELECT and its mutations on db."""
    return db.f(query), eval_muts(db.f, muts)


def dml_eval(db: DB, final: str):
    """Returns fn(stmts) that replays stmts on a fresh copy and formats `final`."""
    def fn(stmts):
        d = db.fresh()
        d.run(stmts)
        return d.f(final)
    return fn


def q(*, id, difficulty, topic, tags, stem, spec, ask, solve, tip, family, sources,
      code=None, tables=None, answer_note=None, label=1):
    return make_question(
        id=id, area=AREA, label=label, difficulty=difficulty, topic=topic, tags=tags, stem=stem,
        answer=(spec["answer"], answer_note or "실제 실행 결과와 일치하는 유일한 보기다."),
        distractors=spec["wrong"], ask=ask, solve=solve, tip=tip, code=code, tables=tables,
        family=family, source_ideas=sources,
    )


def sqlcode(text: str) -> dict:
    return {"lang": "sql", "text": text.strip("\n")}


def cond_block(db: DB, table: str, cols, conds, caption="행별 조건 평가", order="id", tri=False):
    """Per-row truth table of WHERE conditions, computed by sqlite itself.
    conds: [(label, sql boolean expr)]. tri=True shows UNKNOWN for NULL comparisons."""
    parts = list(cols)
    for label, expr in conds:
        if tri:
            parts.append(f"CASE WHEN {expr} THEN 'TRUE' WHEN NOT ({expr}) THEN 'FALSE' "
                         f"ELSE 'UNKNOWN' END AS \"{label}\"")
        else:
            parts.append(f"CASE WHEN {expr} THEN 'O' ELSE 'X' END AS \"{label}\"")
    sql = f"SELECT {', '.join(parts)} FROM {table}" + (f" ORDER BY {order}" if order else "")
    return db.block(sql, caption)


def pick_names(r, n):
    return r.sample(NAMES, n)


def lst(rows) -> str:
    return fmt(rows)
