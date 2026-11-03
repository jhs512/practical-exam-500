"""Concept-bank JSON -> questions.

Bank file (gen/concepts/<name>.json):
{
  "prefix": "sec-atk",            # id prefix, unique per file
  "area": "09", "label": 3, "topic": "보안 공격 기법",
  "concepts": [{
      "id": "land", "name": "랜드 어택(Land Attack)", "group": "dos",
      "def": "한 문장 정의",
      "points": ["핵심 특징", ...],
      "tip": "구별 요령",
      "contrast": {"<other concept id>": "이 개념과 그 개념의 구체적 차이"},
      "aliases": ["랜드", "Land"],          # stem에 나오면 안 되는 이름 조각(정답 유출 검사)
      "scenarios": [{
          "stem": "문제 문장(상황 묘사, 용어 이름 없이)",
          "clue": "이 문제에서 정답을 가리키는 결정적 단서와 그 이유",
          "solve": ["풀이 블록", ...],      # 원리·실무 연결, 시나리오에 맞춰 구체적으로
          "traps": {"<other id>": "이 시나리오에서 그 보기가 빗나가는 구체 이유"},
          "difficulty": 2, "label": 3       # label 생략 시 파일 label
      }]
  }],
  "items": [ { 완결 문항: id, stem, answer{text,note}, distractors[{text,note}]≥9,
               ask, solve[], tip, difficulty, label?, topic?, tags?, code?, tables? } ]
}

Optional "match": N — also build N (가)(나)(다) matching questions from the file's
scenarios (gen/matching.py; each scenario reused at most twice, so N <= 2*scenarios/3).

Scenario question: stem -> pick the concept name among 10. Distractors come from
`traps` keys first, then `contrast` keys, then same group, then the rest of the file.
Each distractor note: trap text > contrast text (either direction) > its definition.
"""
from __future__ import annotations

import json
from pathlib import Path

from core import QuestionError, make_question, pick
from matching import matching_questions

CONCEPT_DIR = Path(__file__).resolve().parent / "concepts"


def _strip_particle_name(name: str) -> str:
    return name.split("(")[0].strip()


def _distractor_note(target: dict, other: dict, scenario: dict) -> str:
    traps = scenario.get("traps", {})
    if other["id"] in traps:
        return traps[other["id"]]
    if other["id"] in target.get("contrast", {}):
        return target["contrast"][other["id"]]
    if target["id"] in other.get("contrast", {}):
        return other["contrast"][target["id"]]
    return f"{other['name']}: {other['def']} 문제의 상황과 핵심 단서가 다르다."


def bank_questions(path: Path) -> list[dict]:
    bank = json.loads(path.read_text(encoding="utf-8"))
    prefix, area, label, topic = bank["prefix"], bank["area"], bank["label"], bank["topic"]
    concepts = bank.get("concepts", [])
    by_id = {c["id"]: c for c in concepts}
    if len(by_id) != len(concepts):
        raise QuestionError(f"{path.name}: duplicate concept ids")
    out = []
    for c in concepts:
        for n, sc in enumerate(c.get("scenarios", []), 1):
            qid = f"{prefix}-{c['id']}-{n}"
            stem_l = sc["stem"].lower()
            for frag in [_strip_particle_name(c["name"])] + c.get("aliases", []):
                if frag and len(frag) >= 2 and frag.lower() in stem_l:
                    raise QuestionError(f"{qid}: stem leaks answer name {frag!r}")
            order = []
            for oid in list(sc.get("traps", {})) + list(c.get("contrast", {})):
                if oid in by_id and oid != c["id"] and oid not in order:
                    order.append(oid)
                elif oid not in by_id:
                    raise QuestionError(f"{qid}: unknown concept ref {oid!r}")
            same = [o["id"] for o in concepts if o["group"] == c["group"] and o["id"] != c["id"]]
            rest = [o["id"] for o in concepts if o["group"] != c["group"]]
            for oid in pick(same, qid) + pick(rest, qid):
                if oid not in order:
                    order.append(oid)
            distractors = [(by_id[o]["name"], _distractor_note(c, by_id[o], sc)) for o in order[:9]]
            answer_note = f"{c['def']} {sc['clue']}"
            solve = list(sc["solve"])
            if c.get("points"):
                solve.append("핵심 정리\n" + "\n".join(f"- {p}" for p in c["points"]))
            out.append(make_question(
                id=qid, area=area, label=sc.get("label", label), difficulty=sc.get("difficulty", 2),
                topic=sc.get("topic", topic), tags=[topic, _strip_particle_name(c["name"])],
                stem=sc["stem"], answer=(c["name"], answer_note), distractors=distractors,
                ask=f"설명된 상황이나 특징에 해당하는 용어를 고르는 문제다. {sc['clue']}",
                solve=solve, tip=c["tip"], family=f"{prefix}-{c['group']}",
                source_ideas=sc.get("sources", c.get("sources", bank.get("sources", []))),
            ))
    rev = bank.get("reverse")
    if rev:
        out.extend(_reverse_questions(bank, concepts, None if rev is True else int(rev)))
    if bank.get("match"):
        entries = [{"concept": c, "scenario": sc} for c in concepts for sc in c.get("scenarios", [])]
        out.extend(matching_questions(prefix=prefix, area=area, label=label, topic=topic, concepts=concepts,
                                      entries=entries, count=int(bank["match"]), sources=bank.get("sources", [])))
    for it in bank.get("items", []):
        qid = it["id"] if it["id"].startswith(prefix + "-") else f"{prefix}-{it['id']}"
        out.append(make_question(
            id=qid, area=area, label=it.get("label", label), difficulty=it.get("difficulty", 2),
            topic=it.get("topic", topic), tags=it.get("tags", [topic]), stem=it["stem"],
            answer=(it["answer"]["text"], it["answer"]["note"]),
            distractors=[(d["text"], d["note"]) for d in it["distractors"]],
            ask=it["ask"], solve=it["solve"], tip=it["tip"], code=it.get("code"), tables=it.get("tables"),
            family=it.get("family", f"{prefix}-items"),
            source_ideas=it.get("sources", bank.get("sources", [])),
        ))
    return out


def _names(c: dict) -> list[str]:
    return [f for f in [_strip_particle_name(c["name"])] + c.get("aliases", []) if f and len(f) >= 2]


def _reverse_questions(bank: dict, concepts: list[dict], limit: int | None) -> list[dict]:
    """Term -> pick its definition among sibling definitions. No new prose: uses def,
    points, contrast and tip already written for each concept."""
    prefix, area, label, topic = bank["prefix"], bank["area"], bank["label"], bank["topic"]
    out = []
    for c in concepts:
        if limit is not None and len(out) >= limit:
            break
        own = c["def"].lower()
        if any(f.lower() in own for f in _names(c)):
            continue  # the definition names its own term; would be a giveaway
        qid = f"{prefix}-{c['id']}-def"
        same = [o for o in concepts if o["group"] == c["group"] and o["id"] != c["id"]]
        rest = [o for o in concepts if o["group"] != c["group"]]
        prefer = [o for o in concepts if o["id"] in c.get("contrast", {})]
        order = []
        for o in prefer + pick(same, qid) + pick(rest, qid):
            if o in order or o["id"] == c["id"]:
                continue
            if any(f.lower() in o["def"].lower() for f in _names(c)):
                continue  # a distractor that mentions the target term would be odd
            order.append(o)
        if len(order) < 9:
            continue

        def note(o):
            extra = c.get("contrast", {}).get(o["id"]) or o.get("contrast", {}).get(c["id"]) or ""
            return f"{o['name']}에 대한 설명이다. {extra}".strip()

        solve = [f"{c['name']}: {c['def']}"]
        if c.get("points"):
            solve.append("핵심 특징\n" + "\n".join(f"- {p}" for p in c["points"]))
        diffs = [f"- {o['name']}: {c['contrast'][o['id']]}" for o in order[:9] if o["id"] in c.get("contrast", {})]
        if diffs:
            solve.append("헷갈리는 개념과의 차이\n" + "\n".join(diffs))
        out.append(make_question(
            id=qid, area=area, label=label, difficulty=1, topic=topic,
            tags=[topic, _strip_particle_name(c["name"])],
            stem=f"다음 중 {c['name']}에 대한 설명으로 가장 알맞은 것은?",
            answer=(c["def"], f"{c['name']}의 정의다. " + (c.get("points") or [""])[0]),
            distractors=[(o["def"], note(o)) for o in order[:9]],
            ask=f"{c['name']}의 정의를 같은 영역의 비슷한 개념 설명과 구별하는 문제다. 각 설명이 어떤 개념의 고유한 특징을 말하는지 따져야 한다.",
            solve=solve, tip=c["tip"], family=f"{prefix}-def",
            source_ideas=c.get("sources", bank.get("sources", [])),
        ))
    return out


def all_bank_questions() -> list[dict]:
    out = []
    for p in sorted(CONCEPT_DIR.glob("*.json")):
        out.extend(bank_questions(p))
    return out
