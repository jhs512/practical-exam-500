"""Shared helpers for area-11 computational families (calc11_*).

Each family computes the right answer with a real algorithm and builds wrong
choices by re-running the computation with one named mistake. `enough()` lets a
generator retry an instance until the mistakes give at least 9 distinct values.
"""
from __future__ import annotations

from fractions import Fraction

from core import QuestionError, make_question, norm


def generate():  # helper module: contributes no questions
    return []


def fmt(x) -> str:
    """Number for a choice: integers plain, otherwise up to 2 decimals."""
    x = Fraction(x)
    if x.denominator == 1:
        return str(x.numerator)
    s = f"{float(x):.2f}".rstrip("0").rstrip(".")
    return s


def tbl(caption: str, columns, rows) -> dict:
    return {"table": {"caption": caption, "columns": [str(c) for c in columns],
                      "rows": [[str(v) for v in r] for r in rows]}}


def table(caption: str, columns, rows) -> dict:
    return {"caption": caption, "columns": [str(c) for c in columns],
            "rows": [[str(v) for v in r] for r in rows]}


def distinct(answer: str, wrong) -> list:
    seen = {norm(answer).lower()}
    out = []
    for text, note in wrong:
        k = norm(text).lower()
        if k in seen or not k:
            continue
        seen.add(k)
        out.append((text, note))
    return out


def enough(answer: str, wrong, n: int = 9) -> bool:
    return len(distinct(answer, wrong)) >= n


def qbuild(*, id: str, family: str, topic: str, tags, stem: str, answer: str, answer_note: str,
           wrong, ask: str, solve, tip: str, difficulty: int, tables=None, sources=(), label: int = 3):
    d = distinct(answer, wrong)
    if len(d) < 9:
        raise QuestionError(f"{id}: only {len(d)} distinct wrong choices: {[x[0] for x in d]}")
    if len(norm(answer)) >= 4 and norm(answer).lower() in stem.lower():
        raise QuestionError(f"{id}: answer text appears in stem")
    return make_question(
        id=id, area="11", label=label, difficulty=difficulty, topic=topic, tags=list(tags), stem=stem,
        answer=(answer, answer_note), distractors=d, ask=ask, solve=solve, tip=tip, tables=tables,
        family=family, source_ideas=list(sources))
