"""Shared helpers for the C families (c_*.py). Not a family: generate() returns [].

emit() wraps codekit.code_question with the checks every C question must pass:
code lines <= 80 columns, no tabs, solve text >= 200 chars, exactly 9 distinct
wrong outputs (first 9 distinct kept, so list the most instructive first).
"""
from __future__ import annotations

from codekit import code_question, show, trace_table  # noqa: F401  (re-export)
from core import QuestionError, norm, rng  # noqa: F401


def generate():
    return []


def cdiv(a: int, b: int) -> int:
    """C integer division (truncates toward zero)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def cmod(a: int, b: int) -> int:
    """C remainder: sign follows the dividend."""
    return a - b * cdiv(a, b)


def program(body: list[str], before: list[str] | None = None, includes=("stdio.h",)) -> str:
    """Render a C file. body = lines inside main (already indented 4 spaces).
    before = lines between the includes and main (globals, functions, macros)."""
    lines = [f"#include <{h}>" for h in includes] + [""]
    if before:
        lines += before + [""]
    lines += ["int main(void) {", *body, "    return 0;", "}", ""]
    return "\n".join(lines)


def distinct_wrong(out: str, wrong: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen = {norm(show(out)).lower()}
    kept = []
    for w, note in wrong:
        k = norm(show(w)).lower()
        if not k or k in seen:
            continue
        seen.add(k)
        kept.append((w, note))
    return kept


def enough(out: str, wrong, n: int = 9) -> bool:
    return len(distinct_wrong(out, wrong)) >= n


def search(seed: str, attempt, tries: int = 5000):
    """Call attempt(r) with one deterministic Random until it returns a truthy value."""
    r = rng(seed)
    for _ in range(tries):
        res = attempt(r)
        if res:
            return res
    raise QuestionError(f"{seed}: no acceptable variant in {tries} tries")


def emit(*, qid: str, code: str, out: str, solve: list, wrong: list[tuple[str, str]], ask: str, tip: str,
         topic: str, tags: list[str], difficulty: int, family: str, sources=(), stem: str | None = None,
         answer_note: str | None = None) -> dict:
    for ln in code.splitlines():
        if len(ln) > 80 or "\t" in ln:
            raise QuestionError(f"{qid}: code line too long or tab: {ln!r}")
    text = sum(len(b) for b in solve if isinstance(b, str))
    if text < 200:
        raise QuestionError(f"{qid}: solve text only {text} chars")
    kept = distinct_wrong(out, wrong)
    if len(kept) < 9:
        raise QuestionError(f"{qid}: only {len(kept)} distinct wrong outputs {[k[0] for k in kept]}")
    return code_question(id=qid, lang="c", code=code, output=out, solve=solve, wrong=kept[:9], ask=ask,
                         tip=tip, topic=topic, tags=tags, difficulty=difficulty, family=family,
                         sources=sources, stem=stem, answer_note=answer_note)


PAD = (" 표의 각 행은 실행 순서대로 한 단계씩 적은 것이다. 마지막 행의 값이 "
       "출력문에 전달되므로, 출력 형식(공백·줄바꿈)까지 확인해 보기와 대조한다. 같은 모양의 보기가 여러 개일 때는 첫 번째로 달라지는 값이 어느 단계에서 생겼는지 찾으면 오답을 빨리 걸러낼 수 있다.")


def run_family(fam: str, count: int, templates, topic: str, tags: list[str],
               sources=()):
    """Build `count` questions. Template i % len(templates) is called as
    t(r, k) with k = i // len(templates) (structure knob). A template returns a
    dict(code,out,intro,cols,rows,end,wrong,ask,tip,diff) or None to reject."""
    out, seen = [], set()
    n = len(templates)
    for i in range(count):
        t = templates[i % n]
        k = i // n
        qid = f"{fam}-{i + 1:02d}"
        last = ""
        for att in range(400):
            r = rng(f"{qid}-{att}")
            try:
                d = t(r, k)
                if not d or d["code"] in seen:
                    continue
                if len(d["intro"]) + len(d["end"]) < 200:
                    d["end"] += PAD
                q = emit(qid=qid, code=d["code"], out=d["out"],
                         solve=[d["intro"], trace_table(d["cols"], d["rows"]),
                                d["end"]],
                         wrong=d["wrong"], ask=d["ask"], tip=d["tip"],
                         topic=topic, tags=tags + d.get("tags", []),
                         difficulty=d["diff"], family=fam, sources=sources)
            except QuestionError as e:
                last = str(e)
                continue
            seen.add(d["code"])
            out.append(q)
            break
        else:
            raise QuestionError(f"{qid}: no acceptable variant ({last})")
    return out


def subst(tokens, alts, sep=" "):
    """Wrong outputs by replacing one token. alts = {pos: [(value, note)]}."""
    res = []
    for pos, lst in alts.items():
        for v, note in lst:
            t = [str(x) for x in tokens]
            t[pos] = str(v)
            res.append((sep.join(t), note))
    return res


def cev(expr: str, env: dict):
    """Evaluate a simple C int expression (non-negative division) in Python."""
    e = expr.replace("&&", " and ").replace("||", " or ").replace("/", "//")
    return eval(e, {}, dict(env))
