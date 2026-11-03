"""Shared helper for t07 computed families (area 07)."""
from __future__ import annotations

from core import make_question, norm


def q(id, topic, stem, ans, wrong, ask, solve, tip, diff, tags=(), code=None, tables=None,
      label=2, pad=None, unit=""):
    """ans=(text,note); wrong=[(text,note)]; pad=int answer -> pad with neighbours."""
    dis = list(wrong)
    if pad is not None:
        have = {norm(ans[0]).lower()} | {norm(t).lower() for t, _ in dis}
        for k in (1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, 7, 8, 9, 10, 12):
            v = pad + k
            if v > 0 and f"{v}{unit}" not in have:
                have.add(f"{v}{unit}")
                dis.append((f"{v}{unit}", f"정답 {pad}{unit}에서 {abs(k)}만큼 어긋난 값이다. 개수를 세는 과정에서 "
                                          f"항목 하나를 더하거나 빠뜨리면 나오지만 풀이의 단계별 계산과 맞지 않는다."))
    return make_question(id=id, area="07", label=label, difficulty=diff, topic=topic,
                         tags=["테스트", *tags], stem=stem, answer=ans, distractors=dis, ask=ask,
                         solve=solve, tip=tip, code=code, tables=tables,
                         family=id.rsplit("-", 1)[0], source_ideas=[])


def fmt(vals) -> str:
    return ", ".join(str(v) for v in vals)
