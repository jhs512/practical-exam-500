"""(가)(나)(다) matching questions built from already-written scenarios.

Three scenarios about three different concepts are shown; the learner picks the row
that maps each to its term. Wrong rows are real confusions: two positions swapped, a
rotation, or one position replaced by a confusable sibling. Every scenario is used in
at most two matching questions so the bank does not lean on repetition.

entry = {"concept": {id, name, def, tip, group, contrast?}, "scenario": {stem, clue, ...}}
"""
from __future__ import annotations

from core import QuestionError, make_question, pick

LABELS = ["(가)", "(나)", "(다)"]


def _short(name: str) -> str:
    return name.split("(")[0].strip() or name


def _note(target: dict, other: dict, scenario: dict) -> str:
    traps = scenario.get("traps", {})
    if other["id"] in traps:
        return traps[other["id"]]
    if other["id"] in target.get("contrast", {}):
        return target["contrast"][other["id"]]
    if target["id"] in other.get("contrast", {}):
        return other["contrast"][target["id"]]
    return f"{other['name']}: {other['def']}"


def _triples(entries: list[dict], count: int, seed: str) -> list[tuple[int, int, int]]:
    """Deterministic triples with distinct concepts; each entry used at most twice."""
    used = [0] * len(entries)
    seen: set[frozenset] = set()
    out: list[tuple[int, int, int]] = []
    for rnd in range(6):
        order = pick(list(range(len(entries))), f"{seed}-round{rnd}")
        bucket: list[int] = []
        for i in order:
            if used[i] >= 2 or any(entries[j]["concept"]["id"] == entries[i]["concept"]["id"] for j in bucket):
                continue
            bucket.append(i)
            if len(bucket) == 3:
                key = frozenset(bucket)
                cids = frozenset(entries[j]["concept"]["id"] for j in bucket)
                if key not in seen and cids not in seen:
                    seen.add(key)
                    seen.add(cids)
                    for j in bucket:
                        used[j] += 1
                    out.append(tuple(bucket))
                    if len(out) == count:
                        return out
                bucket = []
    if len(out) < count:
        raise QuestionError(f"{seed}: only {len(out)} matching triples possible, wanted {count}")
    return out


def matching_questions(*, prefix: str, area: str, label: int, topic: str, concepts: list[dict],
                       entries: list[dict], count: int, sources=()) -> list[dict]:
    if count <= 0:
        return []
    by_id = {c["id"]: c for c in concepts}
    out = []
    for n, tri in enumerate(_triples(entries, count, prefix), 1):
        qid = f"{prefix}-match-{n}"
        es = [entries[i] for i in tri]
        cs = [e["concept"] for e in es]
        ids = {c["id"] for c in cs}
        for e in es:
            low = e["scenario"]["stem"].lower()
            for c in cs:
                for frag in [_short(c["name"])] + c.get("aliases", []):
                    if frag and len(frag) >= 2 and frag.lower() in low:
                        raise QuestionError(f"{qid}: scenario leaks {frag!r}")

        def sib(pos: int) -> list[dict]:
            c = cs[pos]
            sc = es[pos]["scenario"]
            prefer = list(sc.get("traps", {})) + list(c.get("contrast", {}))
            same = [o["id"] for o in concepts if o["group"] == c["group"]]
            rest = [o["id"] for o in concepts]
            order = []
            for oid in prefer + pick(same, f"{qid}-{pos}") + pick(rest, f"{qid}-{pos}r"):
                if oid in by_id and oid not in ids and oid not in order:
                    order.append(oid)
            return [by_id[o] for o in order]

        sibs = [sib(p) for p in range(3)]
        rows: list[list[dict]] = []
        a, b, c = cs
        rows += [[b, a, c], [a, c, b]]
        for p in range(3):
            if sibs[p]:
                r = list(cs)
                r[p] = sibs[p][0]
                rows.append(r)
        rows += [[c, b, a], [b, c, a]]
        for p in range(3):
            if len(sibs[p]) > 1:
                r = list(cs)
                r[p] = sibs[p][1]
                rows.append(r)
        rows.append([c, a, b])

        def text(row):
            return " / ".join(f"{LABELS[i]} {_short(x['name'])}" for i, x in enumerate(row))

        distractors = []
        for row in rows:
            parts = []
            for i, x in enumerate(row):
                if x["id"] != cs[i]["id"]:
                    parts.append(f"{LABELS[i]}를 {_short(x['name'])}(으)로 연결했다. {_note(cs[i], x, es[i]['scenario'])}")
            distractors.append((text(row), " ".join(parts)))
        stem = "다음 (가)~(다)의 설명에 해당하는 용어를 순서대로 바르게 연결한 것은?\n\n" + "\n\n".join(
            f"{LABELS[i]} {e['scenario']['stem']}" for i, e in enumerate(es))
        solve = []
        for i, (e, k) in enumerate(zip(es, cs)):
            solve.append(f"{LABELS[i]} → {k['name']}\n{e['scenario']['clue']} {k['def']}")
        solve.append("세 설명은 서로 비슷한 영역에 있지만 결정적 단서가 다르다. 하나라도 바뀐 연결은 오답이므로 각 설명의 단서를 따로 확인한 뒤 맞춘다.")
        tip = "\n".join(f"- {_short(k['name'])}: {k['tip']}" for k in cs)
        diff = min(3, max(e["scenario"].get("difficulty", 2) for e in es) + 0)
        out.append(make_question(
            id=qid, area=area, label=label, difficulty=max(2, diff), topic=topic,
            tags=[topic] + [_short(k["name"]) for k in cs], stem=stem,
            answer=(text(cs), "세 설명의 단서가 각각 " + ", ".join(f"{LABELS[i]} {_short(k['name'])}" for i, k in enumerate(cs)) + "을(를) 가리킨다."),
            distractors=distractors,
            ask="세 가지 설명이 각각 어떤 용어를 가리키는지 판단해 순서대로 연결하는 문제다. 한 곳만 어긋나도 오답이다.",
            solve=solve, tip=tip, family=f"{prefix}-match",
            source_ideas=list(sources),
        ))
    return out
