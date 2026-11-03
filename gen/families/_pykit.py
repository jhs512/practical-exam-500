"""Shared helpers for the Python program-output families (py_*.py).

For Python the simulator is the language itself: `run` executes the rendered program
in-process to get the output, `trace` records a line-by-line state table with
sys.settrace (the explanation's trace table), and each misconception is modelled as a
concrete source transformation (`sub`) or a hand-derived value (`val`) whose output is
computed, never guessed. The build then re-executes the program with `python -I`.
"""
from __future__ import annotations

import contextlib
import io
import sys

from codekit import code_question, trace_table
from core import QuestionError

PROG = "<prog>"


def run(src: str) -> str:
    buf = io.StringIO()
    g = {"__name__": "__main__"}
    with contextlib.redirect_stdout(buf):
        exec(compile(src, PROG, "exec"), g)
    return buf.getvalue()


def try_run(src: str):
    try:
        return run(src)
    except Exception:  # a misconception that crashes is simply not offered as a choice
        return None


def fmt(v, depth=0) -> str:
    t = type(v)
    if t.__module__ == "__main__" and hasattr(v, "__dict__") and not isinstance(v, type):
        inner = ", ".join(f"{k}={fmt(x, depth + 1)}" for k, x in vars(v).items())
        return f"{t.__name__}({inner})"
    if t.__name__ == "generator":
        return "제너레이터"
    s = repr(v)
    return s if len(s) <= 40 else s[:37] + "..."


def _user_vars(frame, module: bool) -> dict:
    src = frame.f_globals if module else frame.f_locals
    out = {}
    for k, v in list(src.items()):
        if k.startswith("__") or callable(v) and not hasattr(v, "__next__") or type(v).__name__ == "module":
            continue
        if isinstance(v, type):
            continue
        out[k] = fmt(v)
    return out


def trace(src: str, watch=None, max_rows: int = 18, skip_lines=()):
    """Rows [line, code, changes, output] in completion order."""
    lines = src.split("\n")
    rows = []
    pend = {}
    prev = {}
    buf = io.StringIO()
    cursor = [0]

    def snap(frame):
        snapshot = _user_vars(frame, frame.f_code.co_name == "<module>")
        if watch is not None:
            snapshot = {k: v for k, v in snapshot.items() if k in watch}
        return snapshot

    def emit(frame, lineno):
        cur = snap(frame)
        old = prev.get(id(frame), {})
        changed = [f"{k}={v}" for k, v in cur.items() if old.get(k) != v]
        prev[id(frame)] = cur
        text = buf.getvalue()
        out = text[cursor[0]:]
        cursor[0] = len(text)
        if lineno in skip_lines and not out:
            return
        if not changed and not out and lines[lineno - 1].strip().startswith(("def ", "class ")):
            return
        code = lines[lineno - 1].strip()
        if len(code) > 30:
            code = code[:28] + "…"
        where = "" if frame.f_code.co_name == "<module>" else f" ({frame.f_code.co_name})"
        rows.append([f"{lineno}{where}", code, ", ".join(changed) or "-",
                     out.rstrip("\n").replace("\n", " ⏎ ") or "-"])

    def local(frame, event, arg):
        if event in ("line", "return"):
            p = pend.pop(id(frame), None)
            if p is not None:
                emit(frame, p)
            if event == "line":
                pend[id(frame)] = frame.f_lineno
            elif event == "return":
                prev.pop(id(frame), None)
        return local

    def glob(frame, event, arg):
        if frame.f_code.co_filename != PROG:
            return None
        name = frame.f_code.co_name
        if name.startswith("<") and name != "<module>":
            return None
        if frame.f_code.co_name != "<module>":
            prev[id(frame)] = {}
        return local

    g = {"__name__": "__main__"}
    code = compile(src, PROG, "exec")
    old = sys.gettrace()
    with contextlib.redirect_stdout(buf):
        sys.settrace(glob)
        try:
            exec(code, g)
        finally:
            sys.settrace(old)
    if len(rows) > max_rows:
        head = max_rows - 4
        rows = rows[:head] + [["…", "(반복 중략)", "…", "…"]] + rows[-3:]
    return rows


def apply_subs(src: str, subs) -> str:
    out = src
    for old, new in subs:
        if old not in out:
            raise QuestionError(f"mutation target not in source: {old!r}")
        out = out.replace(old, new, 1)
    return out


def sub(note, *pairs):
    return ("sub", list(pairs), note)


def val(text, note):
    return ("val", text, note)


def build(*, id: str, spec: dict, family: str, sources=()) -> dict:
    code = spec["code"].strip("\n") + "\n"
    for ln in code.split("\n"):
        if len(ln) > 80 or "\t" in ln:
            raise QuestionError(f"{id}: line too long or tab: {ln!r}")
    out = run(code)
    wrong = []
    for w in spec["wrong"]:
        if w[0] == "sub":
            got = try_run(apply_subs(code, w[1]))
            if got is not None:
                wrong.append((got, w[2]))
        else:
            text = w[1]
            wrong.append((text if text.endswith("\n") else text + "\n", w[2]))
    solve = list(spec["pre"])
    if spec.get("table") is not None:
        solve.append(spec["table"])
    if spec.get("trace", True):
        rows = trace(code, watch=spec.get("watch"), max_rows=spec.get("max_rows", 18))
        solve.append(trace_table(["줄", "코드", "변화", "출력"], rows,
                                 caption=spec.get("caption", "실행 추적(줄이 끝난 순서)")))
    post = spec.get("post")
    if post:
        solve.append(post.replace("{OUT}", out.rstrip("\n").replace("\n", " / ")))
    return code_question(
        id=id, lang="python", code=code.rstrip("\n"), output=out, solve=solve, wrong=wrong,
        ask=spec["ask"], tip=spec["tip"], topic=spec["topic"], tags=["Python"] + spec.get("tags", []),
        difficulty=spec["difficulty"], family=family, sources=sources,
    )


def build_retry(*, id: str, make, family: str, sources=(), tries: int = 60) -> dict:
    """make(t) -> spec for attempt t; the first attempt whose misconceptions give at
    least nine distinct wrong outputs wins (deterministic)."""
    last = None
    for t in range(tries):
        try:
            return build(id=id, spec=make(t), family=family, sources=sources)
        except QuestionError as e:
            if "distinct wrong outputs" not in str(e):
                raise
            last = e
    raise last


def josa(word, pair: str) -> str:
    """word + correct particle from pair like '을/를', '이/가', '은/는', '과/와', '으로/로'."""
    w = str(word)
    a, b = pair.split("/")
    last = w[-1] if w else ""
    if last.isdigit():
        tail_sound = {"0": True, "1": True, "2": False, "3": True, "4": False, "5": False,
                      "6": True, "7": True, "8": True, "9": False}[last]
        rieul = last in "178"
    elif "가" <= last <= "힣":
        jong = (ord(last) - 0xAC00) % 28
        tail_sound, rieul = jong != 0, jong == 8
    else:
        tail_sound, rieul = last.lower() in "lmnrbkpt", last.lower() == "l"
    if a == "으로":
        return w + ("로" if (not tail_sound or rieul) else "으로")
    return w + (a if tail_sound else b)
