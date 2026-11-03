"""Area 02: highest normal form of a relation from its functional dependencies, and
choosing a valid decomposition (lossless, dependency preserving, 3NF).

nf shape: wrong choices pair another normal form with a listed FD whose real kind does
not support that claim; every note is computed from classify().
decomp shape: candidate decompositions are checked by chase / Ullman / projected-NF
tests; the single valid candidate is the answer, notes list the computed defects.
"""
from __future__ import annotations

from core import rng
from families._d02kit import (NF_SHORT, KIND_DESC, braces, candidate_keys, check_decomp, classify,
                              decomp_text, fd_text, fds_text, keys_text, nf_exact,
                              prime_attrs, q, s, table_block, uniq_choices)
from families.d02_fd_keys import LET, rand_fds

SOURCES = ["sinagong-5-13", "sinagong-5-5"]
CLAIM = {
    1: "부분 함수 종속 {fd}",
    2: "이행(비키) 종속 {fd}",
    3: "{fd}(결정자는 슈퍼키가 아니고 종속자는 주요 속성)",
}
NEED = {1: {"partial"}, 2: {"transitive", "mixed"}, 3: {"prime"}}
CLAIM_OK_LEVEL = {1: "2NF 미달", 2: "3NF 미달", 3: "BCNF 미달"}


def nf_choice_text(level, fds):
    if level == 4:
        return "BCNF: 모든 결정자가 슈퍼키"
    return f"{NF_SHORT[level]}: " + CLAIM[level].format(fd=", ".join(fd_text(f) for f in fds))


def nf_variant(seed, target):
    r = rng(seed)
    for _ in range(40000):
        R = list(LET[:r.choice([5, 5, 6])])
        F = rand_fds(r, R, r.choice([4, 4, 5]))
        if nf_exact(R, F) != target:
            continue
        kinds = [(fd, classify(fd, R, F)[1]) for fd in F]
        hit = [fd for fd, k in kinds if k in NEED.get(target, set())]
        if target < 4 and not hit:
            continue
        keys = candidate_keys(R, F)
        if len(keys) > 2:
            continue
        return R, F, keys, target, hit, kinds
    raise RuntimeError(seed)


def nf_distractors(R, F, n, kinds):
    out = []
    keys = candidate_keys(R, F)
    for fd, kind in kinds:
        for m in (1, 2, 3):
            if m == n:
                continue
            ok = kind in NEED[m]
            txt = f"{NF_SHORT[m]}: " + CLAIM[m].format(fd=fd_text(fd))
            if m < n:
                note = (f"{fd_text(fd)}는 {KIND_DESC[kind]}이다. 이를 근거로 {NF_SHORT[m]}에 머문다고 보았지만, "
                        f"R에는 {NF_SHORT[m + 1]} 조건을 깨는 종속이 없어 실제로는 그보다 높다.")
            elif ok:
                note = (f"{fd_text(fd)}는 {KIND_DESC[kind]}이라 {CLAIM_OK_LEVEL[m]}의 근거가 되지만, "
                        f"더 낮은 단계의 위반이 먼저 있어 최고 정규형은 {NF_SHORT[n]}이다.")
            else:
                note = (f"{fd_text(fd)}는 {KIND_DESC[kind]}이라 이 단계의 위반 근거로 맞지 않는다. "
                        f"단계를 차례로 따져 보면 {NF_SHORT[n]}에서 멈춘다.")
            out.append((txt, note))
    if n != 4:
        out.append(("BCNF: 모든 결정자가 슈퍼키",
                    "R에는 결정자가 슈퍼키가 아닌 종속이 있다. 후보키 " + keys_text(keys) + "를 기준으로 폐포를 구하면 R 전체를 결정하지 못하는 결정자가 나온다."))
    return out


def gen_nf():
    out = []
    targets = [1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4]
    for i, t in enumerate(targets, 1):
        R, F, keys, n, hit, kinds = nf_variant(f"d02-fd-nf-{i}", t)
        ans = nf_choice_text(n, hit)
        cands = uniq_choices(ans, nf_distractors(R, F, n, kinds))
        if len(cands) < 9:
            raise RuntimeError(f"nf {i}: {len(cands)}")
        prime = prime_attrs(keys)
        rows = [[fd_text(fd), KIND_DESC[k]] for fd, k in kinds]
        why = {
            1: "후보키 일부가 비주요 속성을 결정하는 부분 함수 종속이 있어 제2정규형 조건에서 막힌다.",
            2: "부분 종속은 없지만 슈퍼키가 아닌 결정자가 비주요 속성을 결정하는 종속이 있어 제3정규형에서 막힌다.",
            3: "비주요 속성은 모두 키에 직접 종속되어 3NF를 만족하지만, 슈퍼키가 아닌 결정자가 주요 속성을 결정해 BCNF에서 막힌다.",
            4: "모든 결정자가 슈퍼키라서 BCNF를 만족한다.",
        }[n]
        nonprime = set(R) - prime
        out.append(q(
            id=f"d02-fd-nf-{i:02d}", label=2, difficulty=2 if n in (1, 4) else 3,
            topic="함수 종속으로 정규형 판정", tags=["정규화", "정규형 판정", "함수 종속"],
            stem=(f"모든 속성이 원자값인 릴레이션 R({', '.join(R)})에 함수 종속 F = {{{fds_text(F)}}}만 성립한다. "
                  "R이 만족하는 가장 높은 정규형과 그 판정 근거로 옳은 것은?"),
            answer=(ans, why),
            distractors=cands,
            ask="후보키를 구한 뒤 각 함수 종속의 결정자가 슈퍼키인지, 후보키의 진부분집합인지, 종속자가 주요 속성인지를 따져 막히는 첫 단계를 찾는 문제다.",
            solve=[
                f"① 후보키: {keys_text(keys)}. 주요 속성은 {braces(prime)}, 비주요 속성은 {braces(nonprime) if nonprime else '없음'}이다.",
                table_block("종속별 종류", ["함수 종속", "종류"], rows),
                f"② 판정: {why} 따라서 가장 높은 정규형은 {NF_SHORT[n]}이다.",
                "정규형은 1NF→2NF→3NF→BCNF 순서로 더 엄격하다. 낮은 단계 위반이 있으면 그 단계에서 멈추고, 위 단계의 위반 여부는 따지지 않는다.",
            ],
            tip="키를 먼저 구하고 FD마다 '결정자가 슈퍼키인가 → 아니면 키의 일부인가 → 종속자가 주요 속성인가'를 차례로 물으면 1NF·2NF·3NF·BCNF가 갈린다.",
            family="d02-fd-nf", source_ideas=SOURCES))
    return out


def synth_3nf(R, F):
    by_lhs = {}
    for l, rr in F:
        by_lhs.setdefault(l, set()).update(rr)
    parts = [frozenset(l | rr) for l, rr in by_lhs.items()]
    keys = candidate_keys(R, F)
    if not any(k <= p for p in parts for k in keys):
        parts.append(sorted(keys, key=lambda k: (len(k), s(k)))[0])
    parts = [p for p in parts if not any(p < o for o in parts)]
    return sorted(set(parts), key=lambda p: s(p))


def mutate(parts, R, r):
    Rf = frozenset(R)
    out = []
    if len(parts) >= 3:
        a, b = r.sample(range(len(parts)), 2)
        out.append([p for i, p in enumerate(parts) if i not in (a, b)] + [parts[a] | parts[b]])
    for i, p in enumerate(parts):
        if len(p) > 2:
            a = r.choice(sorted(p))
            out.append([x for j, x in enumerate(parts) if j != i] + [p - {a}])
        if len(p) >= 3:
            a, b, c = sorted(p)[:3]
            out.append([x for j, x in enumerate(parts) if j != i] + [frozenset({a, b}), frozenset({b, c}) if len(p) == 3 else p - {a}])
    lst = sorted(R)
    for cut in range(2, len(lst)):
        out.append([frozenset(lst[:cut]), frozenset(lst[cut - 1:])])
        out.append([frozenset(lst[:cut]), Rf - frozenset(lst[:cut - 1])])
    out.append([frozenset(lst[i:i + 2]) for i in range(len(lst) - 1)])
    k = r.randint(1, len(lst) - 2)
    out.append([frozenset(lst[k:]), frozenset(lst[:k + 1])])
    return out


def gen_decomp():
    out = []
    for seed_i in range(1, 400):
        if len(out) >= 12:
            break
        r = rng(f"d02-decomp-{seed_i}")
        R = list(LET[:r.choice([5, 5, 6])])
        F = rand_fds(r, R, r.choice([3, 4, 4]))
        keys = candidate_keys(R, F)
        if len(keys) > 2 or min(len(k) for k in keys) > 3:
            continue
        good = synth_3nf(R, F)
        if not 2 <= len(good) <= 4 or check_decomp(R, good, F, 3):
            continue
        pool = {}
        for _ in range(10):
            for m in mutate(good, R, r):
                m = [p for p in set(m) if p]
                m = [p for p in m if not any(p < o for o in m)]
                key = decomp_text(m)
                if len(m) < 2 or key in pool or key == decomp_text(good):
                    continue
                probs = check_decomp(R, m, F, 3)
                if probs:
                    pool[key] = probs
        if len(pool) < 9:
            continue
        items = sorted(pool.items(), key=lambda kv: (len(kv[1]), kv[0]))
        cands = [(t, "기준을 만족하지 못한다. " + " / ".join(p) + ".") for t, p in items][:9]
        n = len(out) + 1
        ans = decomp_text(good)
        steps = [[fd_text(fd), s(fd[0] | fd[1])] for fd in F]
        out.append(q(
            id=f"d02-decomp-{n:02d}", label=2, difficulty=3 if len(keys) > 1 else 2,
            topic="무손실·종속성 보존 분해", tags=["정규화", "릴레이션 분해", "무손실 조인", "종속성 보존"],
            stem=(f"릴레이션 R({', '.join(R)})에 함수 종속 F = {{{fds_text(F)}}}가 성립한다. "
                  "R을 제3정규형 이상의 릴레이션으로 분해하되, 무손실 조인이 가능하고 모든 함수 종속이 보존되는 분해로 옳은 것은?"),
            answer=(ans, f"각 FD의 속성들을 한 릴레이션으로 묶고 후보키 {keys_text(keys)}를 담은 릴레이션을 확보한 구성이다. 3NF이고 무손실이며 종속성이 보존된다."),
            distractors=cands,
            ask="분해 후보마다 (1) 각 릴레이션의 정규형 (2) 공통 속성이 키 역할을 해 무손실 조인이 되는지 (3) 모든 FD를 어느 한 릴레이션 안에서 검사할 수 있는지를 확인하는 문제다.",
            solve=[
                f"① 후보키는 {keys_text(keys)}이다.",
                table_block("FD별 릴레이션 구성", ["함수 종속", "묶은 속성"], steps),
                f"② 위 속성 집합들을 합치고 다른 집합에 포함되는 것을 제거하면 {ans}가 된다. 어느 FD의 속성도 한 릴레이션 안에 모두 들어 있어 종속성이 보존되고, 후보키를 포함한 릴레이션이 있어 자연 조인 때 가짜 튜플이 생기지 않는다.",
                "③ 오답은 속성 누락, 키를 잃은 분할, FD를 가르는 분할, 너무 크게 합쳐 3NF가 깨지는 경우 중 하나다. 보기마다 어떤 결함인지는 보기 해설에 계산해 두었다.",
            ],
            tip="3NF 분해: 'FD마다 릴레이션 하나 + 후보키를 담은 릴레이션 하나'. 이 틀에서 벗어나면 손실·종속성 상실·정규형 미달 중 하나가 생긴다.",
            family="d02-decomp", source_ideas=SOURCES))
    if len(out) < 12:
        raise RuntimeError(f"decomp only {len(out)}")
    return out


def generate():
    return gen_nf() + gen_decomp()
