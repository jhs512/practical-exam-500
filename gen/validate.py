"""Whole-bank machine checks. Errors fail the build; warnings go to reports/validation.json."""
from __future__ import annotations

import collections
import re

from core import AREAS, ID_RE, MIN_CHOICES, norm

from release import QUOTA, TOTAL

# Tell-tale absolute words inside distractors, and filler phrases inside explanations.
ABSOLUTE = re.compile(r"(항상|무조건|절대로|반드시|오직|모든 경우)")
FILLER = re.compile(r"(이 문제는 .{0,10}출제 목표|중요한 개념이므로|꼭 암기|자주 출제되는 개념입니다|시험에 잘 나옵니다)")


def _grams(text: str, n: int = 3) -> set[str]:
    t = re.sub(r"\s+", "", text.lower())
    return {t[i:i + n] for i in range(max(1, len(t) - n + 1))}


def _skeleton(q: dict) -> str:
    s = q["stem"] + "\n" + (q["code"]["text"] if q.get("code") else "")
    return re.sub(r"\d+", "#", re.sub(r"\s+", " ", s))


def validate(qs: list[dict], full: bool = True) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    ids = collections.Counter(q["id"] for q in qs)
    errors += [f"duplicate id {i} x{n}" for i, n in ids.items() if n > 1]
    for q in qs:
        qid = q["id"]
        if not ID_RE.match(qid):
            errors.append(f"{qid}: bad id")
        if len(q["choices"]) < MIN_CHOICES:
            errors.append(f"{qid}: {len(q['choices'])} choices")
        texts = [norm(c["text"]).lower() for c in q["choices"]]
        if len(set(texts)) != len(texts):
            errors.append(f"{qid}: duplicate choice text")
        cids = [c["id"] for c in q["choices"]]
        if len(set(cids)) != len(cids) or cids.count(q["answer"]) != 1:
            errors.append(f"{qid}: answer id not exactly once")
        for c in q["choices"]:
            if not norm(c["text"]) or not norm(c["note"]):
                errors.append(f"{qid}: empty choice text/note")
            if c["id"] != q["answer"] and ABSOLUTE.search(c["text"]):
                warnings.append(f"{qid}: absolute word in distractor: {c['text'][:60]}")
        ex = q["explain"]
        if not norm(ex["ask"]) or not ex["solve"] or not norm(ex["tip"]):
            errors.append(f"{qid}: empty explanation part")
        body = " ".join(b if isinstance(b, str) else "" for b in ex["solve"])
        if FILLER.search(body + ex["ask"] + ex["tip"]):
            warnings.append(f"{qid}: filler phrase in explanation")
        if len(body) < 120:
            warnings.append(f"{qid}: short solve ({len(body)} chars)")
        stem = q["stem"]
        if re.search(r"(다음|아래)\s*(코드|프로그램|소스)", stem) and not q.get("code"):
            errors.append(f"{qid}: stem refers to code but none attached")
        if re.search(r"(다음|아래)\s*(표|테이블|릴레이션)", stem) and not (q.get("tables") or q.get("code")):
            errors.append(f"{qid}: stem refers to table but none attached")
        if re.search(r"(?:다음|아래|위|제시된)\s*(?:그림|이미지)", stem) and not q.get("code"):
            warnings.append(f"{qid}: stem mentions a figure")
        ans_text = next(c["text"] for c in q["choices"] if c["id"] == q["answer"])
        if len(ans_text) >= 4 and q["label"] != 1 and norm(ans_text).lower() in stem.lower():
            errors.append(f"{qid}: answer text appears in stem")

    by_area = collections.Counter(q["area"] for q in qs)
    by_label = collections.Counter(q["label"] for q in qs)
    by_diff = collections.Counter(q["difficulty"] for q in qs)
    if full:
        if len(qs) != TOTAL:
            errors.append(f"total {len(qs)} != {TOTAL}")
        for a, n in QUOTA.items():
            if by_area.get(a, 0) != n:
                errors.append(f"area {a} has {by_area.get(a, 0)} != quota {n}")

    # Near-duplicate stems (same answer text + very similar stem/code) inside a family.
    fam = collections.defaultdict(list)
    for q in qs:
        fam[q["_family"]].append(q)
    near = []
    for f, group in fam.items():
        grams = [(_grams(q["stem"] + (q["code"]["text"] if q.get("code") else "") +
                         " ".join(t["caption"] + str(t["rows"]) for t in (q.get("tables") or []))), q) for q in group]
        for i in range(len(grams)):
            for j in range(i + 1, len(grams)):
                a, qa = grams[i]
                b, qb = grams[j]
                sim = len(a & b) / max(1, len(a | b))
                if sim > 0.97:
                    near.append((qa["id"], qb["id"], round(sim, 3)))
    for a, b, s in near:
        errors.append(f"near-duplicate {a} ~ {b} ({s})")

    skel = collections.Counter(_skeleton(q) for q in qs)
    repeated_skeletons = sorted(((n, s[:90]) for s, n in skel.items() if n > 1), reverse=True)[:30]
    fam_sizes = sorted(((len(g), f) for f, g in fam.items()), reverse=True)
    answer_div = {f: len({next(c["text"] for c in q["choices"] if c["id"] == q["answer"]) for q in g}) / len(g)
                  for f, g in fam.items() if len(g) >= 5}
    low_div = sorted((round(v, 2), f) for f, v in answer_div.items() if v < 0.5)
    return {
        "total": len(qs),
        "byArea": {a: by_area.get(a, 0) for a in AREAS},
        "byLabel": dict(sorted(by_label.items())),
        "byDifficulty": dict(sorted(by_diff.items())),
        "families": len(fam),
        "largestFamilies": fam_sizes[:25],
        "lowAnswerDiversityFamilies": low_div,
        "repeatedSkeletons": repeated_skeletons,
        "nearDuplicates": near,
        "errors": errors,
        "warnings": warnings,
    }
