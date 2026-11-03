"""Shared helpers for the Java program-output families (java_*.py).

Not a family itself: generate() returns []. Each family imports from here:

    from families.java_kit import jq, java_semantics...

Conventions checked by `jq`:
- the program declares `public class Main` with main; other classes are
  package-private in the same file; no package line, no System.exit, no stdin;
- every line <= 80 columns, 4-space indent, no tabs;
- ids start with `j-`, area 10, label 1.
"""
from __future__ import annotations

from codekit import code_question, trace_table  # noqa: F401  (re-export)
from core import QuestionError, norm, pick, rng  # noqa: F401  (re-export)


def generate():
    return []


# ---------------------------------------------------------------- Java numerics
def i32(v: int) -> int:
    """Wrap to Java int (two's complement 32-bit)."""
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >= (1 << 31) else v


def i64(v: int) -> int:
    v &= 0xFFFFFFFFFFFFFFFF
    return v - (1 << 64) if v >= (1 << 63) else v


def i8(v: int) -> int:
    v &= 0xFF
    return v - 256 if v >= 128 else v


def i16(v: int) -> int:
    v &= 0xFFFF
    return v - 65536 if v >= 32768 else v


def jdiv(a: int, b: int) -> int:
    """Java integer division: truncates toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def jmod(a: int, b: int) -> int:
    """Java %: sign follows the dividend."""
    return a - jdiv(a, b) * b


def jdouble(v: float) -> str:
    """Double.toString for the simple values these questions use."""
    if v != v:
        return "NaN"
    if v in (float("inf"), float("-inf")):
        return "Infinity" if v > 0 else "-Infinity"
    if v == int(v) and abs(v) < 1e7:
        return f"{int(v)}.0"
    r = repr(float(v))
    if "e" in r or abs(v) >= 1e7 or abs(v) < 1e-3:
        raise QuestionError(f"jdouble: avoid value {v!r} (scientific notation)")
    return r


def jbool(b: bool) -> str:
    return "true" if b else "false"


# ---------------------------------------------------------------- question
def check_code(qid: str, code: str) -> None:
    if "public class Main" not in code or "public static void main" not in code:
        raise QuestionError(f"{qid}: Java program needs public class Main with main")
    if "\t" in code:
        raise QuestionError(f"{qid}: tab in code")
    for ln in code.splitlines():
        if len(ln) > 80:
            raise QuestionError(f"{qid}: line over 80 cols: {ln}")
        if ln.lstrip().startswith("package ") or "System.exit" in ln or "System.in" in ln:
            raise QuestionError(f"{qid}: forbidden construct: {ln}")
    if code.count("public class") != 1:
        raise QuestionError(f"{qid}: only Main may be public")


def distinct_wrong(output: str, wrong) -> int:
    right = norm(output.rstrip("\n"))
    return len({norm(w.rstrip("\n")) for w, _ in wrong if norm(w.rstrip("\n"))} - {right})


def jq(*, id: str, code: str, output: str, solve: list, wrong, ask: str, tip: str, topic: str,
       tags: list[str], difficulty: int, family: str, sources=(), stem: str | None = None,
       answer_note: str | None = None, trail: bool = False) -> dict:
    """Java program-output question. `wrong` is [(output, note)] most relevant first.
    trail=True: the program prints tokens as `x + " "` then println(), so the real
    output line ends with one space; it is appended to the right answer only."""
    if not id.startswith("j-"):
        raise QuestionError(f"{id}: Java ids start with j-")
    code = code.rstrip("\n") + "\n"
    check_code(id, code)
    if trail:
        output = output.rstrip("\n") + " "
    if not output.endswith("\n"):
        output += "\n"
    wrong = [(w if w.endswith("\n") else w + "\n", n) for w, n in wrong]
    return code_question(
        id=id, lang="java", code=code, output=output, solve=solve, wrong=wrong, ask=ask, tip=tip,
        topic=topic, tags=["Java", *tags], difficulty=difficulty, stem=stem, family=family,
        sources=sources, answer_note=answer_note,
    )


def lines(*parts) -> str:
    """Join code lines; nested lists are flattened."""
    out = []
    for p in parts:
        if isinstance(p, (list, tuple)):
            out.extend(p)
        else:
            out.append(p)
    return "\n".join(out) + "\n"


def indent(block: list[str], n: int = 1) -> list[str]:
    pad = "    " * n
    return [pad + ln if ln else ln for ln in block]


def main_class(body: list[str], before: list[str] = (), members: list[str] = ()) -> str:
    """Render `before` (other classes) + public class Main { members; main(body) }."""
    out = list(before)
    if out and out[-1] != "":
        out.append("")
    out.append("public class Main {")
    if members:
        out += indent(list(members))
        out.append("")
    out.append("    public static void main(String[] args) {")
    out += indent(list(body), 2)
    out.append("    }")
    out.append("}")
    return "\n".join(out) + "\n"


def sp(*vals) -> str:
    """Space-joined output line (Java side usually prints with + " ")."""
    return " ".join(str(v) for v in vals)


def misconceptions(sim, bugs: dict, pairs=(), combos: bool = False) -> list:
    """sim(bugset) -> output string. bugs: {name: note}. pairs: [(a, b)] extra
    two-error combinations (or all pairs when combos=True); their note joins both."""
    import itertools
    wrong = [(sim({name}), note) for name, note in bugs.items()]
    plist = list(pairs) or (list(itertools.combinations(bugs, 2)) if combos else [])
    for a, b in plist:
        wrong.append((sim({a, b}), f"두 가지를 함께 착각했다. ① {bugs[a]} ② {bugs[b]}"))
    return wrong
