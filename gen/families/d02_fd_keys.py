"""Area 02: candidate keys and attribute closure from functional dependencies.

Two question shapes:
- keys: list every candidate key of R(A..) under F (attribute-closure algorithm).
- closure: compute X+ for a given attribute set.
Wrong choices come from simulated mistakes (no chaining, composite determinant fired
by a part, reversed FDs, stopping after one key, superkey vs candidate key ...);
remaining slots are filled with near-miss sets whose notes are computed.
"""
from __future__ import annotations

from core import rng
from families._d02kit import (all_subsets, braces, candidate_keys, closure, closure_direct,
                              closure_partial_lhs, closure_single_lhs, closure_steps, fd_text,
                              fds_text, keys_text, q, s, table_block, uniq_choices)

SOURCES = ["sinagong-5-13", "sinagong-5-5"]
LET = "ABCDEF"


def rand_fds(r, R, k):
    F = []
    tries = 0
    while len(F) < k and tries < 200:
        tries += 1
        lsz = 1 if r.random() < 0.55 else 2
        lhs = frozenset(r.sample(R, lsz))
        rhs_opts = [a for a in R if a not in lhs]
        a = r.choice(rhs_opts)
        fd = (lhs, frozenset(a))
        if fd in F or any(l == lhs and a in rr for l, rr in F):
            continue
        # skip FDs already implied (keeps F free of redundancy)
        if a in closure(lhs, F):
            continue
        F.append(fd)
    return F


def key_note(sets, R, F, keys):
    R = frozenset(R)
    parts = []
    for X in sets:
        cl = closure(X, F)
        if not cl >= R:
            parts.append(f"{s(X)}+ = {braces(cl)}이어서 {braces(R - cl)}을(를) 결정하지 못하므로 키가 아니다.")
        elif X not in keys:
            k = next(k for k in keys if k <= X)
            parts.append(f"{s(X)}는 슈퍼키이지만 그 일부인 {s(k)}만으로 R 전체가 결정되므로 최소성을 어긴다.")
    missing = [k for k in keys if k not in sets]
    if missing:
        if parts:
            parts.append(f"또 후보키 {keys_text(missing)}이(가) 빠졌다.")
        else:
            parts.append(f"나열한 집합은 모두 후보키가 맞지만 {keys_text(missing)}도 후보키라 목록이 불완전하다.")
    return " ".join(parts)


def keys_variant(n, seed, want_keys, size):
    r = rng(seed)
    R = list(LET[:size])
    for _ in range(5000):
        F = rand_fds(r, R, r.choice([3, 4, 4, 5]))
        keys = candidate_keys(R, F)
        if len(keys) != want_keys or max(len(k) for k in keys) > 3 or min(len(k) for k in keys) < 2 and want_keys == 1:
            continue
        # need a key that is only found by chaining
        if all(closure_direct(k, F) >= set(R) for k in keys):
            continue
        cands = build_key_distractors(R, F, keys)
        if len(cands) >= 9:
            return R, F, keys, cands
    raise RuntimeError(seed)


def build_key_distractors(R, F, keys):
    Rf = frozenset(R)
    rhs = set().union(*(r for _, r in F))
    core = frozenset(a for a in R if a not in rhs)
    ans = keys_text(keys)
    out = []

    def add(sets, why):
        sets = sorted(set(sets), key=lambda x: (len(x), s(x)))
        if not sets:
            return
        out.append((keys_text(sets), why + " " + key_note(sets, R, F, keys)))

    if core and not closure(core, F) >= Rf:
        add([core], "오른쪽에 한 번도 나오지 않는 속성만 모으면 곧 키라고 보고 폐포 확인을 생략했다.")
    wk = candidate_keys(R, F, closure_direct)
    add(wk, "폐포를 구할 때 처음 집합에 있던 속성으로만 FD를 적용하고, 새로 얻은 속성으로 다른 FD를 다시 적용하지 않았다(연쇄 단계 누락).")
    wk = candidate_keys(R, F, closure_partial_lhs)
    add(wk, "결합 결정자를 가진 FD를 결정자 일부만 있어도 적용했다(예: AB→C를 A만 있어도 적용).")
    wk = candidate_keys(R, F, closure_single_lhs)
    add(wk, "결정자가 두 속성인 FD는 무시하고 단일 결정자 FD만 사용했다.")
    rev = [(r, l) for l, r in F]
    add(candidate_keys(R, rev), "함수 종속 X→Y의 방향을 거꾸로(Y가 X를 결정) 읽고 키를 구했다.")
    if len(keys) > 1:
        add([keys[0]], "후보키 하나를 찾은 뒤 다른 후보키가 있는지 확인하지 않았다.")
        add(keys[1:], "가장 먼저 찾을 수 있는 짧은 후보키를 빠뜨렸다.")
    lhs_union = frozenset().union(*(l for l, _ in F))
    if lhs_union not in keys:
        add([lhs_union], "모든 FD의 왼쪽 속성을 합치면 키가 된다고 생각했다.")
    for k in keys:
        for a in R:
            if a not in k:
                add([k | {a}], "슈퍼키와 후보키를 구별하지 않고 속성을 하나 더 붙인 집합을 키로 보았다.")
                break
    others = [X for X in all_subsets(R, 1, 3) if X not in keys]
    others.sort(key=lambda X: (-(len(X & core)), len(X), s(X)))
    for X in others[:12]:
        add([X], "결정자 몇 개만 보고 키를 짐작했다.")
    if len(keys) >= 1:
        sup = next((X for X in others if closure(X, F) >= Rf), None)
        if sup is not None:
            add(list(keys) + [sup], "후보키 목록에 슈퍼키까지 함께 넣었다.")
    return uniq_choices(ans, out)


def keys_solve(R, F, keys):
    Rf = frozenset(R)
    rhs = set().union(*(r for _, r in F))
    core = frozenset(a for a in R if a not in rhs)
    blocks = []
    if core:
        blocks.append(f"① 어떤 FD의 오른쪽에도 나오지 않는 속성 {braces(core)}은(는) 다른 속성으로 결정되지 않으므로 모든 후보키에 들어가야 한다. "
                      f"{s(core)}+ = {braces(closure(core, F))}" +
                      ("로 이미 R 전체이므로 이것이 유일한 후보키다." if closure(core, F) >= Rf else "로 R 전체가 아니므로 속성을 하나씩 더해 본다."))
    else:
        blocks.append("① 모든 속성이 어떤 FD의 오른쪽에 나오므로 꼭 포함해야 하는 속성은 없다. 작은 집합부터 폐포를 구해 R 전체를 결정하는지 본다.")
    rows = []
    shown = set()
    tried = [X for X in all_subsets(R, 1, max(len(k) for k in keys)) if core <= X]
    for X in tried:
        cl, steps = closure_steps(X, F)
        if any(k < X for k in keys):
            verdict = "슈퍼키(최소 아님)"
        elif cl >= Rf:
            verdict = "후보키"
        else:
            verdict = "키 아님"
        chain = " → ".join(f"{fd_text(fd)}로 +{s(add)}" for fd, add, _ in steps) or "적용할 FD 없음"
        rows.append([s(X), braces(cl), chain, verdict])
        shown.add(X)
        if len(rows) >= 9:
            break
    for k in keys:
        if k not in shown:
            cl, steps = closure_steps(k, F)
            rows.append([s(k), braces(cl), " → ".join(f"{fd_text(fd)}로 +{s(a)}" for fd, a, _ in steps), "후보키"])
    blocks.append(table_block("폐포 계산", ["집합 X", "X+", "적용 순서", "판정"], rows))
    blocks.append(f"② 폐포가 R = {braces(R)} 전체이면 슈퍼키이고, 그중 어떤 속성을 빼도 R 전체가 되지 않는 최소 집합이 후보키다. "
                  f"따라서 후보키는 {keys_text(keys)}이다. 폐포를 구할 때는 새로 들어온 속성으로 다시 FD를 훑어, 더 늘지 않을 때까지 반복해야 한다.")
    blocks.append("실무에서 후보키를 정확히 찾아야 기본키·대체키를 고를 수 있고, 어떤 속성이 주요 속성인지가 정해져 부분·이행 종속(정규형) 판정이 가능하다.")
    return blocks


def closure_variant(n, seed, size):
    r = rng(seed)
    R = list(LET[:size])
    for _ in range(5000):
        F = rand_fds(r, R, r.choice([4, 4, 5]))
        X = frozenset(r.sample(R, r.choice([1, 2, 2])))
        cl, steps = closure_steps(X, F)
        if len(steps) < 3 or cl == frozenset(R) and r.random() < 0.6:
            continue
        cands = closure_distractors(R, F, X, cl)
        if len(cands) >= 9:
            return R, F, X, cl, steps, cands
    raise RuntimeError(seed)


def closure_note(T, cl, F, X):
    parts = []
    miss = cl - T
    extra = T - cl
    if miss:
        parts.append(f"{braces(miss)}이(가) 빠졌다: 폐포를 끝까지 반복하면 이 속성도 결정된다.")
    if extra:
        parts.append(f"{braces(extra)}은(는) {s(X)}에서 출발해 어떤 FD로도 얻을 수 없다.")
    return " ".join(parts)


def closure_distractors(R, F, X, cl):
    out = []

    def add(T, why):
        T = frozenset(T)
        if T == cl:
            return
        out.append((braces(T), why + " " + closure_note(T, cl, F, X)))

    add(closure_direct(X, F), "처음 집합에 있는 속성으로 바로 적용되는 FD만 쓰고, 새로 얻은 속성으로 FD를 다시 적용하지 않았다.")
    add(closure_single_lhs(X, F), "결정자가 두 속성인 FD를 적용 대상에서 뺐다.")
    add(closure_partial_lhs(X, F), "결합 결정자 FD를 결정자 일부만 있어도 적용했다.")
    add(cl - X, "결과에서 출발 집합 자신을 뺐다. X+는 반사 규칙에 따라 X를 포함한다.")
    rev = [(r, l) for l, r in F]
    add(closure(X, rev), "FD의 화살표 방향을 거꾸로 읽어 X를 결정하는 속성을 모았다.")
    # one pass in listed order
    res = set(X)
    for l, r in F:
        if l <= res:
            res |= r
    add(res, "FD 목록을 위에서 아래로 한 번만 훑고 멈췄다. 뒤쪽 FD로 얻은 속성이 앞쪽 FD의 결정자가 되면 다시 훑어야 한다.")
    add(X, "X로 시작하는 FD가 바로 보이지 않아 더 결정되는 속성이 없다고 보았다.")
    for a in sorted(cl - X):
        add(cl - {a}, "연쇄 적용 중 한 단계를 빠뜨렸다.")
    for a in sorted(set(R) - cl):
        add(cl | {a}, "결정되지 않는 속성까지 포함했다.")
    der = sorted(cl - X)
    for i in range(len(der)):
        for j in range(i + 1, len(der)):
            add(cl - {der[i], der[j]}, "연쇄 적용을 중간에 멈춰 마지막 두 단계를 놓쳤다.")
    for a in der:
        for b in sorted(set(R) - cl):
            add((cl - {a}) | {b}, "FD의 오른쪽과 왼쪽을 일부 혼동했다.")
    return uniq_choices(braces(cl), out)


def generate():
    out = []
    plan = [(1, 5), (1, 6), (2, 5), (2, 5), (2, 6), (2, 6), (3, 5), (3, 6), (1, 5), (2, 6), (3, 6), (2, 5)]
    for n, (nk, size) in enumerate(plan, 1):
        seed = f"d02-fd-keys-{n}"
        R, F, keys, cands = keys_variant(n, seed, nk, size)
        diff = 2 if nk == 1 else 3
        out.append(q(
            id=f"d02-fd-keys-{n:02d}", label=2, difficulty=diff, topic="후보키 찾기(속성 폐포)",
            tags=["함수 종속", "후보키", "속성 폐포"],
            stem=f"릴레이션 R({', '.join(R)})에 함수 종속 집합 F = {{{fds_text(F)}}}가 성립한다. R의 후보키를 빠짐없이 나열한 것은?",
            answer=(keys_text(keys), f"각 집합의 폐포가 R 전체이고, 어떤 속성을 빼도 R 전체가 되지 않는다. 다른 최소 집합은 없으므로 후보키는 {keys_text(keys)}이다."),
            distractors=cands,
            ask="F로부터 R 전체를 결정하는 최소 속성 집합(후보키)을 모두 찾는 문제다. 폐포를 끝까지 반복하는지, 슈퍼키와 후보키를 구별하는지, 후보키가 여러 개인지 확인해야 한다.",
            solve=keys_solve(R, F, keys),
            tip="오른쪽에 나오지 않는 속성은 모든 키에 들어간다. 그 집합에서 출발해 폐포를 구하고, 모자라면 오른쪽에만 나오는 속성을 제외한 나머지를 하나씩 더해 본다.",
            family="d02-fd-keys", source_ideas=SOURCES,
        ))
    cplan = [5, 6, 6, 5, 6, 6, 5, 6]
    for n, size in enumerate(cplan, 1):
        seed = f"d02-fd-closure-{n}"
        R, F, X, cl, steps, cands = closure_variant(n, seed, size)
        rows = [[i + 1, fd_text(fd), f"{s(fd[0])} ⊆ 현재 집합", braces(res)] for i, (fd, add, res) in enumerate(steps)]
        out.append(q(
            id=f"d02-fd-closure-{n:02d}", label=2, difficulty=2 if len(steps) <= 3 else 3,
            topic="속성 폐포 계산", tags=["함수 종속", "속성 폐포", "암스트롱 공리"],
            stem=f"릴레이션 R({', '.join(R)})에서 F = {{{fds_text(F)}}}일 때, 속성 집합 {braces(X)}의 폐포 ({s(X)})+는?",
            answer=(braces(cl), f"{s(X)}에서 출발해 결정자가 현재 집합에 포함된 FD를 더 늘지 않을 때까지 반복 적용한 결과다."),
            distractors=cands,
            ask=f"{s(X)}가 함수적으로 결정하는 속성을 모두 모은 집합을 묻는다. 새로 얻은 속성이 또 다른 FD의 결정자가 되는 연쇄를 끝까지 따라가는지가 핵심이다.",
            solve=[
                f"시작: 반사 규칙에 따라 {braces(X)}를 결과에 넣는다. 이후 F를 반복해서 훑으며, 왼쪽(결정자) 속성이 모두 현재 집합에 들어 있는 FD의 오른쪽을 추가한다.",
                table_block("폐포 계산 과정", ["단계", "적용 FD", "적용 조건", "현재 집합"], rows),
                f"한 바퀴를 더 돌아도 추가되는 속성이 없으므로 종료한다. ({s(X)})+ = {braces(cl)}" +
                (f"이고 R 전체이므로 {s(X)}는 슈퍼키다." if cl == frozenset(R) else f"이고 {braces(set(R) - cl)}이(가) 빠지므로 {s(X)}는 슈퍼키가 아니다."),
                "폐포는 후보키 판정(폐포 = R 전체인가), 어떤 FD가 F에서 유도되는지(Y ⊆ X+인가), 정규형 판정의 출발점이 된다. 결합 결정자는 모든 구성 속성이 모였을 때만 적용한다는 점을 지켜야 한다.",
            ],
            tip="폐포는 '한 번 훑기'가 아니라 '변화가 없을 때까지 반복'이다. 결합 결정자 AB→C는 A와 B가 모두 모였을 때만 적용한다.",
            family="d02-fd-closure", source_ideas=SOURCES,
        ))
    return out
