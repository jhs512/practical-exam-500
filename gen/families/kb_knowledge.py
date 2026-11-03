"""(가)(나)(다) matching questions over the original case bank in gen/knowledge.py
(areas 01-06). Each case appears in at most two questions."""
from __future__ import annotations

import knowledge
from matching import matching_questions

TOPIC = {"01": "요구사항·모델링 판단", "02": "데이터 설계·트랜잭션 판단", "03": "연계·통합 방식 판단",
         "04": "서버 설계 원리 판단", "05": "인터페이스 설계 판단", "06": "화면 설계 원리 판단"}
LABEL = {"01": 3, "02": 2, "03": 2, "04": 2, "05": 2, "06": 3}


def generate():
    out = []
    for area, cases in knowledge.KNOWLEDGE.items():
        concepts = [{"id": cid, "name": name, "def": expl, "tip": expl, "group": "all"}
                    for cid, name, _sc, expl, _d in cases]
        entries = [{"concept": c, "scenario": {"stem": sc, "clue": "", "difficulty": d}}
                   for c, (_cid, _n, sc, _e, d) in zip(concepts, cases)]
        count = (2 * len(cases)) // 3
        out += matching_questions(prefix=f"kb{area}", area=area, label=LABEL[area], topic=TOPIC[area],
                                  concepts=concepts, entries=entries, count=count)
    return out
