"""Shared algorithms for area-02 generators: functional dependencies, keys, normal
forms, decomposition checks and small relational-algebra helpers.

Attributes are single upper-case letters in FD problems so that sets print compactly
("AB", "{A, B, C}"). Every function here is a real algorithm; generators use them both
for the right answer and for simulating named mistakes.
"""
from __future__ import annotations

from itertools import combinations

from core import make_question

NF_NAME = {1: "제1정규형(1NF)", 2: "제2정규형(2NF)", 3: "제3정규형(3NF)", 4: "BCNF"}
NF_SHORT = {1: "1NF", 2: "2NF", 3: "3NF", 4: "BCNF"}


# ----------------------------------------------------------------- formatting
def s(attrs) -> str:
    """Compact attribute set: AB."""
    return "".join(sorted(attrs))


def braces(attrs) -> str:
    return "{" + ", ".join(sorted(attrs)) + "}"


def fd_text(fd) -> str:
    l, r = fd
    return f"{s(l)}→{s(r)}"


def fds_text(F) -> str:
    return ", ".join(fd_text(fd) for fd in F)


def keys_text(keys) -> str:
    return ", ".join(sorted((s(k) for k in keys), key=lambda x: (len(x), x)))


def parse_fds(spec: str):
    """"AB>C, C>D" -> [(frozenset('AB'), frozenset('C')), ...]"""
    out = []
    for part in spec.split(","):
        l, r = part.strip().split(">")
        out.append((frozenset(l), frozenset(r)))
    return out


# --------------------------------------------------------------- FD algorithms
def closure(X, F):
    res = set(X)
    changed = True
    while changed:
        changed = False
        for l, r in F:
            if l <= res and not r <= res:
                res |= r
                changed = True
    return frozenset(res)


def closure_steps(X, F):
    """Closure with a trace: list of (fd, added attrs, result so far)."""
    res = set(X)
    steps = []
    changed = True
    while changed:
        changed = False
        for l, r in F:
            if l <= res and not r <= res:
                added = r - res
                res |= r
                steps.append(((l, r), frozenset(added), frozenset(res)))
                changed = True
    return frozenset(res), steps


def closure_direct(X, F):
    """Mistake: apply only FDs whose LHS lies inside the ORIGINAL X (no chaining)."""
    res = set(X)
    for l, r in F:
        if l <= set(X):
            res |= r
    return frozenset(res)


def closure_single_lhs(X, F):
    """Mistake: ignore FDs with a composite determinant."""
    return closure(X, [fd for fd in F if len(fd[0]) == 1])


def closure_partial_lhs(X, F):
    """Mistake: fire a composite-LHS FD when ANY part of its LHS is present."""
    res = set(X)
    changed = True
    while changed:
        changed = False
        for l, r in F:
            if (l & res) and not r <= res:
                res |= r
                changed = True
    return frozenset(res)


def all_subsets(R, min_size=1, max_size=None):
    R = sorted(R)
    max_size = len(R) if max_size is None else max_size
    for k in range(min_size, max_size + 1):
        for c in combinations(R, k):
            yield frozenset(c)


def candidate_keys(R, F, clos=closure):
    R = frozenset(R)
    keys = []
    for X in all_subsets(R):
        if any(k <= X for k in keys):
            continue
        if clos(X, F) >= R:
            keys.append(X)
    return keys


def is_superkey(X, R, F):
    return closure(X, F) >= frozenset(R)


def prime_attrs(keys):
    out = set()
    for k in keys:
        out |= k
    return frozenset(out)


def project_fds(Ri, F):
    """Non-trivial FDs X->A holding on Ri (A single attribute, X minimal-ish)."""
    Ri = frozenset(Ri)
    out = []
    for X in all_subsets(Ri, 1, len(Ri) - 1):
        cl = closure(X, F) & Ri
        for a in sorted(cl - X):
            out.append((X, frozenset(a)))
    return out


def nf_exact(R, F):
    """Highest of 1..4 (1NF assumed) checked over all X, not just listed FDs."""
    R = frozenset(R)
    keys = candidate_keys(R, F)
    prime = prime_attrs(keys)
    nonprime = R - prime
    # 2NF: no nonprime attribute depends on a proper subset of a candidate key
    for k in keys:
        for X in all_subsets(k, 1, len(k) - 1):
            if (closure(X, F) - X) & nonprime:
                return 1
    bcnf_ok = True
    for X in all_subsets(R, 1, len(R) - 1):
        cl = closure(X, F)
        if cl >= R:
            continue
        extra = cl - X
        if extra & nonprime:
            return 2
        if extra:
            bcnf_ok = False
    return 4 if bcnf_ok else 3


def nf_of_sub(Ri, F):
    """Normal form of a projected relation Ri (FDs projected from F)."""
    G = project_fds(Ri, F)
    return nf_exact(Ri, G)


def classify(fd, R, F):
    """Return (level, kind) for a single-attribute-RHS FD that holds.

    level 0: X superkey (no violation); 1: partial (violates 2NF);
    2: transitive (violates 3NF); 3: X not superkey but A prime (violates BCNF only).
    kind is None for mixed determinants (part of a key + non-key attribute).
    """
    X, Y = fd
    keys = candidate_keys(R, F)
    prime = prime_attrs(keys)
    if is_superkey(X, R, F):
        return 0, "key"
    A = next(iter(Y))
    if A in prime:
        return 3, "prime"
    if any(X < k for k in keys):
        return 1, "partial"
    if not (X & prime):
        return 2, "transitive"
    return 2, "mixed"


KIND_DESC = {
    "key": "결정자가 슈퍼키인 종속",
    "partial": "후보키의 일부가 비주요 속성을 결정하는 부분 함수 종속",
    "transitive": "키가 아닌 속성이 비주요 속성을 결정하는 이행 함수 종속",
    "mixed": "키 일부와 일반 속성이 섞인 비키 결정자에 의한 종속",
    "prime": "슈퍼키가 아닌 결정자가 주요 속성(후보키 구성 속성)을 결정하는 종속",
}


# ------------------------------------------------------------ decompositions
def chase_lossless(R, parts, F):
    """Tableau (chase) test for lossless join."""
    R = sorted(R)
    rows = []
    for i, P in enumerate(parts):
        rows.append({a: ("a", a) if a in P else ("b", i, a) for a in R})
    changed = True
    while changed:
        changed = False
        for l, r in F:
            groups = {}
            for row in rows:
                groups.setdefault(tuple(row[a] for a in sorted(l)), []).append(row)
            for g in groups.values():
                if len(g) < 2:
                    continue
                for a in r:
                    vals = {row[a] for row in g}
                    if len(vals) > 1:
                        target = ("a", a) if ("a", a) in vals else min(vals)
                        for row in rows:
                            if row[a] in vals and row[a] != target:
                                row[a] = target
                                changed = True
    return any(all(row[a] == ("a", a) for a in R) for row in rows)


def preserves(parts, F):
    """Dependency preservation test (Ullman's algorithm)."""
    lost = []
    for l, r in F:
        Z = set(l)
        changed = True
        while changed:
            changed = False
            for P in parts:
                t = closure(Z & set(P), F) & set(P)
                if not t <= Z:
                    Z |= t
                    changed = True
        if not r <= Z:
            lost.append((l, r))
    return lost


def decomp_text(parts) -> str:
    ps = sorted((s(p) for p in parts), key=lambda x: (x[0], len(x), x))
    return ", ".join(f"R{i + 1}({', '.join(p)})" for i, p in enumerate(ps))


def check_decomp(R, parts, F, target=3):
    """Return list of problems (empty = valid lossless, preserving, all parts >= target NF)."""
    probs = []
    cover = set().union(*parts) if parts else set()
    if cover != set(R):
        miss = set(R) - cover
        probs.append(f"속성 {braces(miss)}이(가) 어느 릴레이션에도 없어 원래 정보를 복원할 수 없다")
        return probs
    for P in parts:
        nf = nf_of_sub(P, F)
        if nf < target:
            G = project_fds(P, F)
            keys = candidate_keys(P, G)
            bad = None
            for X in all_subsets(P, 1, len(P) - 1):
                cl = closure(X, F) & set(P)
                if cl >= set(P):
                    continue
                extra = cl - X
                prime = prime_attrs(keys)
                np_ = extra - prime
                if np_ or (target == 4 and extra):
                    bad = (X, np_ or extra)
                    break
            why = f" ({s(bad[0])}→{s(bad[1])} 때문)" if bad else ""
            probs.append(f"R({', '.join(sorted(P))})이(가) {NF_SHORT[nf]}에 머문다{why}")
    if not chase_lossless(R, parts, F):
        probs.append("공통 속성이 어느 쪽의 키도 되지 못해 자연 조인하면 가짜 튜플이 생기는 손실 분해다")
    lost = preserves(parts, F)
    if lost:
        probs.append(f"함수 종속 {', '.join(fd_text(x) for x in lost)}을(를) 어떤 릴레이션 안에서도 검사할 수 없어 종속성이 보존되지 않는다")
    return probs


# -------------------------------------------------------------- choice helper
def uniq_choices(answer_text, candidates, need=9):
    """candidates: [(text, note)] in priority order. Drop duplicates/answer."""
    seen = {answer_text.strip()}
    out = []
    for t, n in candidates:
        t = t.strip()
        if t in seen or not t:
            continue
        seen.add(t)
        out.append((t, n))
    return out


def q(**kw):
    kw.setdefault("area", "02")
    return make_question(**kw)


def table_block(caption, columns, rows):
    return {"table": {"caption": caption, "columns": list(columns), "rows": [[str(v) for v in r] for r in rows]}}
