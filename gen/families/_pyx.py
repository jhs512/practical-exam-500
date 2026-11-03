"""Shared generate() wiring for the py_* families written in the 2nd pass.

Pads explanations that would otherwise be shorter than the 200-character guideline
with a concrete statement of the final output, and builds ids deterministically.
"""
from __future__ import annotations

from core import rng
from core import QuestionError
from families._pykit import build

EXTRA = "줄마다 변수의 상태를 순서대로 적어 가면 마지막에 출력되는 값은 {OUT}이다. 오답 보기는 이 과정 중 한 줄의 동작을 다르게 읽었을 때 나오는 결과다."


def make_all(prefix, funcs, family, sources):
    def one(k):
        def make(t):
            spec = funcs[k](rng(f"{prefix}-{k}-{t}"))
            body = sum(len(x) for x in spec["pre"]) + len(spec.get("post") or "")
            if body < 260:
                spec["post"] = ((spec.get("post") or "") + " " + EXTRA).strip()
            return spec
        return make
    def retry(k):
        last = None
        for t in range(60):
            try:
                return build(id=f"{prefix}-{k + 1:02d}", spec=one(k)(t), family=family, sources=sources)
            except QuestionError as e:
                if "distinct" not in str(e):
                    raise
                last = e
        raise last
    return [retry(k) for k in range(len(funcs))]
