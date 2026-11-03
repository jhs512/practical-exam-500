"""Oracle-based family builder for Java program-output questions (j-*).

Not a family: generate() returns []. A family module defines

    make(i, r) -> spec dict     (i = variant index, r = seeded random.Random)

and calls `family(...)`. A spec holds the program text plus *mutants*: textual
patches (old -> new) of the program that encode one named misconception each.
Correct output and every mutant output are produced by really compiling and running
the programs (runners/run.py, one javac call per round), so wrong answers are what a
person with that misconception would really compute. Mutants that do not compile or
that throw are dropped. If fewer than 9 distinct wrong outputs remain, the variant is
re-drawn with the next seed (capped), as the authoring rules require.

spec keys: code, muts [(subs, note)], wrong [(output, note)] optional direct wrongs,
solve (list or callable(out) -> list), ask, tip, diff, tags, trail (bool).
subs is (old, new) or a list of such pairs; every `old` must occur in the code.
"""
from __future__ import annotations

import re

from families.java_kit import QuestionError, jq, rng, trace_table  # noqa: F401
from run import _key, run_all


def generate():
    return []


def pr(exprs, ind=8, sep=' + " " + ', fn="println"):
    """System.out.println(e1 + " " + e2 ...) wrapped to <= 80 columns."""
    pad = " " * ind
    head = f"{pad}System.out.{fn}("
    lines, cur = [], head
    for k, e in enumerate(exprs):
        piece = e if k == 0 else sep.strip(" ") + " " + e if False else e
        token = piece if k == 0 else sep + piece
        if len(cur + token) + 2 > 80 and cur.strip() != head.strip():
            lines.append(cur.rstrip() if not cur.endswith(" ") else cur.rstrip())
            cur = pad + "        " + token.lstrip()
        else:
            cur += token
    lines.append(cur + ");")
    return lines


def patch(code: str, subs):
    if isinstance(subs, tuple) and len(subs) == 2 and isinstance(subs[0], str):
        subs = [subs]
    for old, new in subs:
        if old not in code:
            return None
        code = code.replace(old, new)
    return code


def run_batch(codes):
    """-> (outputs by code, set of codes that failed to compile)."""
    uniq = list(dict.fromkeys(codes))
    bad = set()
    while True:
        todo = [c for c in uniq if c not in bad]
        try:
            outs = run_all([("java", c) for c in todo])
            return dict(zip(todo, outs)), bad
        except RuntimeError as e:
            names = set(re.findall(r"(p[0-9a-f]{20})[/\\]Main\.java", str(e)))
            nb = {c for c in todo if "p" + _key("java", c)[:20] in names}
            if not nb:
                raise
            bad |= nb


def _blen(b):
    if isinstance(b, str):
        return len(b)
    t = b["table"]
    return sum(len(str(c)) for r in t["rows"] for c in r)


def _blocks(spec, out):
    s = spec["solve"]
    return s(out) if callable(s) else s


def _clean(o, trail):
    if o.startswith("<<"):
        return None
    if trail:
        o = o.rstrip(chr(10))
        o = o[:-1] if o.endswith(" ") else o
    return o


def _wrongs(sp, outs, bad, right):
    wrong, seen = [], {right}
    for mc, note in sp["_mut"]:
        if mc in bad or mc not in outs:
            continue
        mo = _clean(outs[mc], sp.get("trail"))
        if mo is None:
            continue
        key = " ".join(mo.split())
        if key and key not in seen:
            seen.add(key)
            wrong.append((mo.rstrip(chr(10)), note))
    for wo, note in sp.get("wrong", []):
        key = " ".join(wo.split())
        if key and key not in seen:
            seen.add(key)
            wrong.append((wo, note))
    return wrong


def _pairs(sp):
    """Two-misconception combinations of the mutants that apply (stage 2)."""
    out = []
    muts = [(subs, note) for subs, note in sp.get("muts", [])
            if patch(sp["code"], subs) is not None]
    for a in range(len(muts)):
        for b in range(a + 1, len(muts)):
            c1 = patch(sp["code"], muts[a][0])
            c2 = patch(c1, muts[b][0])
            if c2 is not None and c2 != c1:
                out.append((c2, "두 가지를 함께 착각했다. ① " + muts[a][1]
                            + " ② " + muts[b][1]))
    return out


def family(fam: str, pfx: str, topic: str, n: int, make, sources=(), rounds=14):
    done = {}
    for attempt in range(rounds):
        todo = [i for i in range(n) if i not in done]
        if not todo:
            break
        specs, codes = {}, []
        for i in todo:
            sp = make(i, rng(f"{fam}-{i}-{attempt}"))
            sp["_mut"] = [(mc, note) for subs, note in sp.get("muts", [])
                          if (mc := patch(sp["code"], subs)) is not None]
            specs[i] = sp
            codes.append(sp["code"])
            codes += [mc for mc, _ in sp["_mut"]]
        outs, bad = run_batch(codes)
        short = {}
        for i, sp in specs.items():
            if sp["code"] in bad:
                raise QuestionError(f"{fam}-{i}: base program does not compile")
            right = _clean(outs[sp["code"]], sp.get("trail"))
            if right is None:
                raise QuestionError(f"{fam}-{i}: base program failed: {outs[sp['code']][:80]}")
            for mc, note in sp["_mut"]:
                if mc in bad:
                    print(f"  [warn] {fam}-{i}: mutant does not compile: {note[:40]}")
            if len(_wrongs(sp, outs, bad, " ".join(right.split()))) < 9:
                short[i] = _pairs(sp)[:70]
        if short:
            more, mbad = run_batch([c for ps in short.values() for c, _ in ps])
            outs.update(more)
            bad |= mbad
            for i, ps in short.items():
                specs[i]["_mut"] += ps
        for i, sp in specs.items():
            right = _clean(outs[sp["code"]], sp.get("trail"))
            wrong = _wrongs(sp, outs, bad, " ".join(right.split()))
            if len(wrong) < 9:
                if attempt == rounds - 1:
                    print(f"  [short] {fam}-{i}: {len(wrong)} wrong of {len(sp['_mut'])}")
                continue
            # prefer single-misconception wrongs, keep pair combos last
            wrong.sort(key=lambda w: w[1].startswith("두 가지"))
            wrong = wrong[:12]
            solve = _blocks(sp, right.rstrip(chr(10)))
            if sum(_blen(b) for b in solve) < 220:
                raise QuestionError(f"{fam}-{i}: solve text under 220 chars")
            done[i] = jq(
                id=f"j-{pfx}-{i + 1:02d}", code=sp["code"], output=right.rstrip(chr(10)),
                solve=solve, wrong=wrong, ask=sp["ask"], tip=sp["tip"], topic=topic,
                tags=sp.get("tags", []), difficulty=sp["diff"], family=fam,
                sources=sources, trail=bool(sp.get("trail")),
            )
    missing = [i for i in range(n) if i not in done]
    if missing:
        raise QuestionError(f"{fam}: variants {missing} lack 9 distinct wrong outputs")
    return [done[i] for i in range(n)]
