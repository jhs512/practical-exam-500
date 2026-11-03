"""Helpers for program-output questions (C / Java / Python).

A family module renders a program from a variant, simulates it in Python to get the
output plus a step trace for the explanation, and simulates misconceptions to get
wrong outputs. `code_question` attaches a verify spec so the build executes the real
program and fails if the simulator disagrees with the real compiler/interpreter.
"""
from __future__ import annotations

from core import QuestionError, make_question, norm

LANG_NAME = {"c": "C", "java": "Java", "python": "Python"}


def show(out: str) -> str:
    """Choice text for program output. Multi-line output keeps its newlines."""
    return out.rstrip("\n")


def code_question(*, id: str, lang: str, code: str, output: str, solve: list, wrong: list[tuple[str, str]],
                  ask: str, tip: str, topic: str, tags: list[str], difficulty: int,
                  stem: str | None = None, area: str = "10", label: int = 1, family: str | None = None,
                  sources=(), answer_note: str | None = None, verify: bool = True) -> dict:
    """wrong: [(wrong_output, why_someone_gets_it)] — most relevant first. Duplicates and
    values equal to the right output are dropped; at least 9 distinct must remain."""
    right = show(output)
    seen = {norm(right)}
    distractors = []
    for out, note in wrong:
        o = show(out)
        if norm(o) in seen or not norm(o):
            continue
        seen.add(norm(o))
        distractors.append((o, note))
    if len(distractors) < 9:
        raise QuestionError(f"{id}: only {len(distractors)} distinct wrong outputs: {[d[0] for d in distractors]}")
    return make_question(
        id=id, area=area, label=label, difficulty=difficulty, topic=topic, tags=tags,
        stem=stem or f"다음 {LANG_NAME[lang]} 프로그램을 실행했을 때 출력 결과는?",
        code={"lang": lang, "text": code},
        answer=(right, answer_note or "위 실행 추적대로 실제 실행한 출력과 일치한다."),
        distractors=distractors, ask=ask, solve=solve, tip=tip, family=family, source_ideas=sources,
        verify={"lang": lang, "src": code, "expect": output} if verify else None,
    )


def trace_table(columns: list[str], rows: list[list], caption: str = "실행 추적") -> dict:
    return {"table": {"caption": caption, "columns": columns, "rows": [[str(v) for v in r] for r in rows]}}
