"""Area 02: relational algebra evaluated on small tables shown in the question.

Shapes: projection with duplicate elimination, selection with compound conditions, set
operators, joins (natural, many-to-many, outer), division, and nested expressions.
The right answer comes from a tiny evaluator; wrong choices are results of named
mistakes (keeping duplicates, swapping AND/OR, product instead of join, ...), padded with
single-element perturbations whose notes say why the element does / does not belong.
"""
from __future__ import annotations

from core import rng
from families._d02kit import q, table_block

SOURCES = ["sinagong-5-7", "itpasslab-2-9"]
NAMES = ["김하늘", "이도윤", "박서연", "최민준", "정지우", "한예린", "오세훈", "윤하준", "장서윤", "임지호", "강유진", "서태양"]
DEPTS = ["영업", "개발", "인사", "기획", "재무"]
RANKS = ["사원", "대리", "과장"]


def tbl(caption, cols, rows):
    return {"caption": caption, "columns": cols, "rows": [[str(v) for v in r] for r in rows]}


def uniq(rows):
    seen, out = set(), []
    for r in rows:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def num_choices(ans, mistakes, hi):
    """mistakes: [(value, note)]. Pad with nearby integers."""
    out, seen = [], {ans}
    for v, note in mistakes:
        if v in seen or v < 0:
            continue
        seen.add(v)
        out.append((str(v), note))
    for d in range(1, hi + 6):
        for v in (ans + d, ans - d):
            if v in seen or v < 0 or len(out) >= 14:
                continue
            seen.add(v)
            out.append((str(v), f"결과를 직접 세면 {ans}개이다. {v}개는 {'하나를 빠뜨리거나' if v < ans else '조건에 맞지 않는 행을 더 센'} 값으로, 어떤 연산 순서를 따라도 나오지 않는다."))
    return out


def set_choices(ans, universe, mistakes, why_in, why_not, fmt):
    """ans: frozenset; mistakes: [(frozenset, note)]."""
    out, seen = [], {ans}
    order = {u: i for i, u in enumerate(universe)}

    def add(S, note):
        S = frozenset(S)
        if S in seen:
            return
        seen.add(S)
        out.append((fmt(S, order), note))

    for S, note in mistakes:
        add(S, note)
    for e in universe:
        if e in ans:
            add(ans - {e}, f"{fmt_one(e)}을(를) 뺐다. {why_in[e]}")
        else:
            add(ans | {e}, f"{fmt_one(e)}을(를) 넣었다. {why_not[e]}")
    for e in universe:
        for f in universe:
            if e in ans and f not in ans:
                add((ans - {e}) | {f}, f"{fmt_one(e)}을(를) 빼고 {fmt_one(f)}을(를) 넣었다. {why_in[e]} {why_not[f]}")
    add(frozenset(), "공집합으로 보았다. 조건을 만족하는 행이 실제로 존재한다.")
    return out


def fmt_one(e):
    return "(" + ", ".join(e) + ")" if isinstance(e, tuple) else str(e)


def fmt_set(S, order):
    if not S:
        return "∅(결과 없음)"
    return "{" + ", ".join(fmt_one(e) for e in sorted(S, key=lambda x: order[x])) + "}"


def emp_table(r, n=8):
    names = r.sample(NAMES, n)
    depts = r.sample(DEPTS, r.choice([3, 4]))
    rows = []
    for i, nm in enumerate(names):
        rows.append((f"E{i + 1}", nm, r.choice(depts), r.choice(RANKS), r.choice([250, 300, 350, 400, 450])))
    return rows


EMP_COLS = ["사번", "이름", "부서", "직급", "급여"]


# ------------------------------------------------------------------ projection
def gen_proj():
    out = []
    for n in range(1, 5):
        r = rng(f"d02-ra-proj-{n}")
        for _ in range(200):
            rows = emp_table(r, r.choice([8, 9]))
            if len({x[2] for x in rows}) >= 3 and len(rows) - len({x[2] for x in rows}) >= 3:
                break
        N = len(rows)
        dist = lambda idx, rs=rows: len(uniq([tuple(x[i] for i in idx) for x in rs]))
        if n == 1:
            ans = dist([2])
            expr = "π<sub>부서</sub>(EMP)"
            mist = [(N, "중복 제거를 하지 않았다. 관계 대수의 프로젝션은 집합이므로 같은 부서 값은 한 번만 남는다."),
                    (dist([3]), "부서가 아니라 직급 열의 서로 다른 값 수를 셌다."),
                    (dist([2, 3]), "부서와 직급 두 열을 함께 투영한 조합의 수를 셌다."),
                    (dist([4]), "급여 열의 서로 다른 값 수를 셌다."),
                    (dist([1]), "이름의 서로 다른 값 수를 셌다. 이름은 모두 달라 행 수와 같다.")]
            ask_expr, deg = expr, 1
            hint = f"부서 열 값: {', '.join(x[2] for x in rows)} → 서로 다른 값 {ans}개"
        elif n == 2:
            ans = dist([2, 3])
            expr = "π<sub>부서, 직급</sub>(EMP)"
            mist = [(N, "중복 제거를 하지 않고 EMP의 행 수를 그대로 썼다."),
                    (dist([2]), "부서만 기준으로 중복을 제거했다. 두 열을 함께 보면 같은 부서 안에서도 직급이 다르면 별개 튜플이다."),
                    (dist([3]), "직급만 기준으로 중복을 제거했다."),
                    (dist([2]) * dist([3]), "부서 수와 직급 수의 곱(가능한 모든 조합)을 구했다. 실제로 존재하는 조합만 남는다."),
                    (dist([2]) + dist([3]), "열마다 서로 다른 값 수를 구해 더했다.")]
            hint = f"(부서, 직급) 쌍: {', '.join(x[2] + '/' + x[3] for x in rows)} → 서로 다른 쌍 {ans}개"
            ask_expr, deg = expr, 2
        elif n == 3:
            thr = 350
            sel = [x for x in rows if x[4] >= thr]
            ans = len(uniq([(x[2],) for x in sel]))
            expr = f"π<sub>부서</sub>(σ<sub>급여≥{thr}</sub>(EMP))"
            mist = [(len(sel), "선택된 행 수를 그대로 썼다. 투영 뒤 같은 부서가 여러 번 나오면 하나로 합쳐진다."),
                    (dist([2]), "선택을 하지 않고 모든 행에서 부서를 투영했다."),
                    (len(uniq([(x[2],) for x in rows if x[4] > thr])), "조건을 급여>350으로 읽어 350인 행을 제외했다."),
                    (len(uniq([(x[2],) for x in rows if x[4] <= thr])), "조건을 반대로 읽어 급여가 350 이하인 행을 골랐다."),
                    (N, "투영·선택을 모두 무시하고 EMP의 행 수를 썼다.")]
            hint = f"급여≥{thr}인 행의 부서: {', '.join(x[2] for x in sel) or '없음'} → 서로 다른 값 {ans}개"
            ask_expr, deg = expr, 1
        else:
            all_d = {x[2] for x in rows}
            has = {x[2] for x in rows if x[3] == "과장"}
            ans = len(all_d - has)
            expr = "π<sub>부서</sub>(EMP) − π<sub>부서</sub>(σ<sub>직급='과장'</sub>(EMP))"
            if ans == 0:
                r2 = rng(f"d02-ra-proj-retry-{n}")
                continue
            mist = [(len(has), "차집합을 하지 않고 과장이 있는 부서 수만 셌다."),
                    (len(all_d), "빼는 쪽(과장이 있는 부서)을 무시하고 전체 부서 수를 썼다."),
                    (len([x for x in rows if x[3] != "과장"]), "과장이 아닌 직원의 행 수를 셌다. 차집합의 단위는 직원이 아니라 부서 값이다."),
                    (len(uniq([(x[2],) for x in rows if x[3] != "과장"])), "과장이 아닌 직원이 속한 부서를 셌다. 과장이 있는 부서라도 다른 직급의 직원이 있으면 포함되어 버린다."),
                    (len(all_d) + len(has), "차집합을 합집합처럼 더했다.")]
            hint = f"전체 부서 {sorted(all_d)} − 과장이 있는 부서 {sorted(has)} = {sorted(all_d - has)}"
            ask_expr, deg = expr, 1
        out.append(q(
            id=f"d02-ra-proj-{n:02d}", label=2, difficulty=1 if n == 1 else 2 if n < 4 else 3,
            topic="관계 대수: 프로젝션과 중복 제거", tags=["관계 대수", "프로젝션", "카디널리티"],
            stem=f"다음 표 EMP에 대해 관계 대수식 {ask_expr.replace('<sub>', '_').replace('</sub>', '')}의 결과 릴레이션의 튜플(행) 수는?",
            tables=[tbl("EMP", EMP_COLS, rows)],
            answer=(str(ans), f"{hint}. 관계 대수의 결과는 집합이므로 중복 튜플은 하나만 남는다."),
            distractors=num_choices(ans, mist, N),
            ask="프로젝션은 지정한 열만 남기고 중복 튜플을 제거한다. 선택·차집합이 함께 있으면 안쪽 식부터 계산한다.",
            solve=[f"안쪽 식부터 순서대로 계산한다. {hint}.",
                   "SQL의 SELECT는 기본적으로 중복을 남기지만(DISTINCT를 써야 제거), 관계 대수의 π는 집합 연산이라 같은 값 조합을 하나로 합친다. 그래서 결과 행 수는 원본 행 수보다 작거나 같다.",
                   "조건에 쓰인 비교 연산자(≥, >)와 차집합의 방향을 읽을 때는 경계값과 앞뒤 순서를 다시 확인한다."],
            tip="π의 결과 행 수 = 지정 열 조합의 서로 다른 값 수. 선택(σ)이 먼저 나오면 선택된 행에서만 값을 모은다.",
            family="d02-ra-proj", source_ideas=SOURCES))
    return out


# ------------------------------------------------------------------- selection
def gen_sel():
    out = []
    forms = [
        ("and", "급여≥350 AND 부서='개발'", lambda x: x[4] >= 350 and x[2] == "개발"),
        ("or", "직급='과장' OR 급여≥400", lambda x: x[3] == "과장" or x[4] >= 400),
        ("not", "NOT(부서='영업') AND 직급≠'사원'", lambda x: not x[2] == "영업" and x[3] != "사원"),
        ("mix", "(부서='개발' OR 부서='기획') AND 급여>300", lambda x: x[2] in ("개발", "기획") and x[4] > 300),
    ]
    for n, (kind, cond, f) in enumerate(forms, 1):
        r = rng(f"d02-ra-sel-{n}")
        for _ in range(500):
            rows = emp_table(r, 9)
            if "개발" not in {x[2] for x in rows}:
                continue
            hit = [x for x in rows if f(x)]
            if 2 <= len(hit) <= 5:
                break
        ans = len(hit)
        mist = []
        if kind == "and":
            mist = [(len([x for x in rows if x[4] >= 350 or x[2] == "개발"]), "AND를 OR로 읽어 두 조건 중 하나만 만족해도 센 합집합 결과다."),
                    (len([x for x in rows if x[4] > 350 and x[2] == "개발"]), "급여≥350을 급여>350으로 읽어 경계값 350을 제외했다."),
                    (len([x for x in rows if x[2] == "개발"]), "급여 조건을 빠뜨리고 개발 부서만 셌다."),
                    (len([x for x in rows if x[4] >= 350]), "부서 조건을 빠뜨리고 급여 조건만 적용했다.")]
        elif kind == "or":
            mist = [(len([x for x in rows if x[3] == "과장" and x[4] >= 400]), "OR를 AND로 읽어 두 조건을 동시에 만족하는 행만 셌다."),
                    (len([x for x in rows if x[3] == "과장"]), "급여 조건을 빠뜨리고 과장만 셌다."),
                    (len([x for x in rows if x[4] >= 400]), "직급 조건을 빠뜨리고 급여 조건만 적용했다."),
                    (len([x for x in rows if x[3] == "과장"]) + len([x for x in rows if x[4] >= 400]), "두 조건의 해당 행 수를 그대로 더했다. 두 조건을 모두 만족하는 행이 두 번 세어진다.")]
        elif kind == "not":
            mist = [(len([x for x in rows if x[2] == "영업" and x[3] != "사원"]), "NOT을 부서 조건에 적용하지 않고 영업 부서를 골랐다."),
                    (len([x for x in rows if x[2] != "영업" or x[3] != "사원"]), "AND를 OR로 읽었다."),
                    (len([x for x in rows if x[2] != "영업"]), "직급 조건을 빠뜨리고 영업이 아닌 행만 셌다."),
                    (len([x for x in rows if x[2] != "영업" and x[3] == "사원"]), "직급≠'사원'을 직급='사원'으로 읽었다.")]
        else:
            mist = [(len([x for x in rows if x[2] == "개발" or (x[2] == "기획" and x[4] > 300)]), "괄호를 무시하고 AND가 OR보다 먼저 결합한다고 계산했다."),
                    (len([x for x in rows if x[2] in ("개발", "기획") and x[4] >= 300]), "급여>300을 급여≥300으로 읽어 경계값을 포함했다."),
                    (len([x for x in rows if x[2] in ("개발", "기획")]), "급여 조건을 빠뜨렸다."),
                    (len([x for x in rows if x[2] in ("개발", "기획") or x[4] > 300]), "괄호 밖 AND를 OR로 읽었다.")]
        mist.append((len(rows), "선택 조건을 적용하지 않고 EMP의 모든 행 수를 썼다."))
        out.append(q(
            id=f"d02-ra-sel-{n:02d}", label=2, difficulty=2 if kind in ("and", "or") else 3,
            topic="관계 대수: 셀렉션의 복합 조건", tags=["관계 대수", "셀렉션", "논리 연산"],
            stem=f"다음 표 EMP에서 σ_({cond})(EMP)의 결과 튜플 수는? (σ는 조건을 만족하는 행을 고르는 연산이다.)",
            tables=[tbl("EMP", EMP_COLS, rows)],
            answer=(str(ans), "조건을 행마다 평가해 참인 행만 센다: " + ", ".join(x[0] for x in hit) + f" → {ans}행."),
            distractors=num_choices(ans, mist, len(rows)),
            ask="복합 조건을 행마다 참/거짓으로 평가해 참인 행만 센다. AND/OR 결합 순서, 괄호, 경계값(≥ 대 >), NOT의 적용 범위가 함정이다.",
            solve=[f"행별 평가: " + "; ".join(f"{x[0]}({x[2]},{x[3]},{x[4]})={'참' if f(x) else '거짓'}" for x in rows) + ".",
                   f"참인 행은 {', '.join(x[0] for x in hit)}로 {ans}개이다. σ는 열을 줄이지 않고 행만 거르므로 차수는 EMP와 같고 카디널리티만 줄어든다.",
                   "AND는 모든 조건이 참일 때, OR는 하나라도 참일 때 참이다. 괄호가 있으면 괄호 안을 먼저 평가하고, 부등호의 경계(350이 포함되는가)를 값마다 확인한다."],
            tip="σ는 '행 단위로 조건 평가'. 행마다 참/거짓 표를 만들고, 경계값 행(예: 급여가 정확히 350)을 따로 표시해 두면 실수가 준다.",
            family="d02-ra-sel", source_ideas=SOURCES))
    return out


# --------------------------------------------------------------------- set ops
def gen_set():
    out = []
    ops = ["union", "inter", "diff", "diff_rev", "sym"]
    sym = {"union": "R ∪ S", "inter": "R ∩ S", "diff": "R − S", "diff_rev": "S − R", "sym": "(R ∪ S) − (R ∩ S)"}
    for n, op in enumerate(ops, 1):
        r = rng(f"d02-ra-set-{n}")
        for _ in range(500):
            pool = r.sample(NAMES, 8)
            R = sorted(r.sample(pool, r.choice([4, 5])), key=pool.index)
            S = sorted(r.sample(pool, r.choice([4, 5])), key=pool.index)
            a, b = set(R), set(S)
            if 1 <= len(a & b) <= 3 and len(a - b) >= 1 and len(b - a) >= 1 and len(a) != len(b):
                break
        res = {"union": a | b, "inter": a & b, "diff": a - b, "diff_rev": b - a, "sym": a ^ b}[op]
        ans = len(res)
        m = [(len(R) + len(S), "중복을 제거하지 않고 두 릴레이션의 행 수를 단순히 더했다. 집합 연산이므로 양쪽에 모두 있는 튜플은 한 번만 센다."),
             (len(a | b), "합집합 결과를 구했다."), (len(a & b), "교집합 결과를 구했다."),
             (len(a - b), "R − S를 구했다."), (len(b - a), "S − R을 구했다. 차집합은 앞 피연산자에서 뒤를 빼므로 순서가 바뀌면 값이 달라진다."),
             (len(a ^ b), "합집합에서 교집합을 뺀 대칭차를 구했다."), (len(R) - len(S) if len(R) > len(S) else len(S) - len(R), "행 수의 차이를 구했다. 차집합은 공통 튜플을 지우는 연산이지 행 수를 빼는 연산이 아니다.")]
        m = [(v, nt) for v, nt in m if v != ans]
        # rewrite notes for results that coincide with a differently named operation but equal numbers are dropped already
        out.append(q(
            id=f"d02-ra-set-{n:02d}", label=2, difficulty=1 if op in ("union", "inter") else 2 if op != "sym" else 3,
            topic="관계 대수: 합집합·교집합·차집합", tags=["관계 대수", "집합 연산", "합병 가능"],
            stem=f"동일한 스키마(학번)를 가진 두 릴레이션 R, S가 다음 표와 같다. {sym[op]}의 결과 튜플 수는?",
            tables=[tbl("R", ["학번"], [(x,) for x in R]), tbl("S", ["학번"], [(x,) for x in S])],
            answer=(str(ans), f"R = {{{', '.join(R)}}}, S = {{{', '.join(S)}}}에서 {sym[op]} = {{{', '.join(sorted(res, key=lambda x: NAMES.index(x))) or '없음'}}} → {ans}행."),
            distractors=num_choices(ans, m, len(R) + len(S)),
            ask="두 릴레이션이 합병 가능(차수가 같고 대응 속성의 도메인이 같음)할 때 집합 연산의 결과 튜플 수를 계산하는 문제다. 중복 제거와 차집합의 방향이 핵심이다.",
            solve=[f"R = {{{', '.join(R)}}}, S = {{{', '.join(S)}}}. 양쪽에 모두 있는 튜플은 {', '.join(sorted(a & b, key=lambda x: NAMES.index(x)))}이다.",
                   f"{sym[op]}를 적용하면 {{{', '.join(sorted(res, key=lambda x: NAMES.index(x))) or '없음'}}}으로 {ans}개이다.",
                   "합집합은 두 릴레이션의 튜플을 모으되 같은 튜플은 하나로 합치고, 교집합은 공통 튜플만, 차집합은 앞 릴레이션에만 있는 튜플만 남긴다. 차집합은 교환 법칙이 성립하지 않는다."],
            tip="합집합 크기 = |R| + |S| − |R∩S|. 차집합은 앞에서 공통 부분을 덜어낸 것(|R| − |R∩S|)이며 순서가 바뀌면 결과가 달라진다.",
            family="d02-ra-set", source_ideas=SOURCES))
    return out


# ------------------------------------------------------------------------ join
def gen_join():
    out = []
    cust = [("C1", "김하늘", "골드"), ("C2", "이도윤", "일반"), ("C3", "박서연", "골드"), ("C4", "최민준", "일반"), ("C5", "정지우", "골드")]
    for n in range(1, 6):
        r = rng(f"d02-ra-join-{n}")
        if n in (1, 2, 3):
            cs = r.sample(cust, 4)
            ids = [c[0] for c in cs]
            orders = [(f"O{i + 1}", r.choice(ids + ["C9"] * (1 if n == 3 else 0)), r.choice([12, 30, 45, 80])) for i in range(7)]
            orders = [(o, c, a) for o, c, a in orders]
            cs_t = tbl("CUSTOMER", ["고객번호", "이름", "등급"], cs)
            or_t = tbl("ORDERS", ["주문번호", "고객번호", "금액"], orders)
            matched = [o for o in orders if o[1] in ids]
            lonely = [c for c in cs if c[0] not in {o[1] for o in orders}]
            if n == 1:
                expr, ans = "ORDERS ⋈ CUSTOMER (자연 조인)", len(matched)
                nm = "고객번호가 같은 행끼리 짝지으며, CUSTOMER의 고객번호가 유일하므로 ORDERS의 각 행은 많아야 하나의 고객과 짝이 된다."
                m = [(len(orders) * len(cs), "자연 조인을 카티션 곱으로 계산했다. 공통 속성 값이 같은 쌍만 남아야 한다."),
                     (len(cs), "고객 수를 결과 행 수로 썼다. 결과 행은 주문마다 하나씩 생긴다."),
                     (len(orders) + len(cs), "두 릴레이션의 행 수를 더했다."),
                     (len({o[1] for o in matched}), "주문한 서로 다른 고객 수를 셌다. 주문이 여러 건이면 조인 결과도 여러 행이다."),
                     (len(orders) + len(lonely), "왼쪽 외부 조인처럼 주문이 없는 고객까지 센 값이다.")]
                diff = 2
            elif n == 2:
                expr, ans = "CUSTOMER ⟕ ORDERS (고객 기준 왼쪽 외부 조인)", len(matched) + len(lonely)
                nm = f"짝이 있는 주문 {len(matched)}행에 주문이 없는 고객 {len(lonely)}명이 NULL과 함께 추가된다."
                m = [(len(matched), "내부 조인 결과다. 외부 조인은 짝이 없는 고객 행도 NULL로 채워 남긴다."),
                     (len(orders) * len(cs), "카티션 곱 크기를 썼다."),
                     (len(cs), "고객 행 수를 그대로 썼다. 고객이 주문을 여러 건 하면 주문 수만큼 행이 생긴다."),
                     (len(matched) + len(cs), "짝이 있는 행에 고객 전체 수를 더했다."),
                     (len(orders) + len(lonely), "ORDERS 전체 행(고객번호 불일치 행 포함)에 주문 없는 고객을 더했다.")]
                diff = 3
            else:
                expr, ans = "ORDERS ⋈ CUSTOMER (자연 조인, ORDERS에는 CUSTOMER에 없는 고객번호 C9도 있음)", len(matched)
                nm = "C9처럼 상대 릴레이션에 짝이 없는 행은 내부 조인에서 사라진다."
                m = [(len(orders), "ORDERS의 모든 행이 결과에 남는다고 보았다. 짝이 없는 C9 주문은 내부 조인에서 제외된다."),
                     (len(orders) * len(cs), "카티션 곱 크기를 썼다."),
                     (len(cs), "고객 수를 썼다."),
                     (len(matched) + len([o for o in orders if o[1] not in ids]), "짝이 없는 주문을 NULL 고객과 함께 추가했다. 이는 외부 조인의 동작이다."),
                     (len({o[1] for o in matched}), "서로 다른 고객 수를 셌다.")]
                diff = 2
            tables = [or_t, cs_t]
            solve1 = f"ORDERS의 고객번호 {', '.join(o[1] for o in orders)} 중 CUSTOMER에 있는 {', '.join(ids)}와 같은 행이 {len(matched)}개이다."
        elif n == 4:
            # many-to-many: R(학생, 과목) ⋈ S(과목, 교수)
            courses = ["DB", "OS", "NET"]
            R = uniq([(r.choice(NAMES[:5]), r.choice(courses)) for _ in range(7)])
            S = uniq([(c, p) for c in courses for p in r.sample(["박교수", "최교수", "정교수"], r.choice([1, 2]))])
            res = [(a, b, p) for a, b in R for c, p in S if b == c]
            ans = len(res)
            tables = [tbl("ENROLL", ["학생", "과목"], R), tbl("TEACH", ["과목", "교수"], S)]
            expr = "ENROLL ⋈ TEACH (자연 조인)"
            per = {c: (sum(1 for a, b in R if b == c), sum(1 for x, p in S if x == c)) for c in courses}
            nm = "과목별로 (수강 행 수 × 담당 교수 행 수)를 구해 더한다: " + ", ".join(f"{c} {per[c][0]}×{per[c][1]}" for c in courses) + f" = {ans}."
            m = [(len(R) * len(S), "카티션 곱 크기를 썼다."), (len(R), "ENROLL의 각 행이 한 교수와만 짝이 된다고 보았다. 한 과목에 교수 행이 둘이면 그 수강 행은 둘로 늘어난다."),
                 (len(S), "TEACH의 행 수를 썼다."), (len(R) + len(S), "두 릴레이션의 행 수를 더했다."),
                 (len({(a, p) for a, b, p in res}), "결과에서 (학생, 교수) 쌍의 중복을 제거했다. 자연 조인의 결과는 과목 열을 포함하므로 과목이 다르면 다른 튜플이다.")]
            solve1 = nm
            diff = 3
            cust = cust
        else:
            cs = r.sample(cust, 5)
            orders = [(f"O{i + 1}", r.choice([c[0] for c in cs]), r.choice([12, 30, 45, 80])) for i in range(7)]
            matched = [(o, c) for o in orders for c in cs if o[1] == c[0] and c[2] == "골드" and o[2] >= 30]
            ans = len(matched)
            tables = [tbl("ORDERS", ["주문번호", "고객번호", "금액"], orders), tbl("CUSTOMER", ["고객번호", "이름", "등급"], cs)]
            expr = "σ_(등급='골드' AND 금액≥30)(ORDERS ⋈ CUSTOMER)"
            nm = "조인으로 고객 정보를 붙인 뒤 등급과 금액 조건을 만족하는 행만 센다."
            allj = [(o, c) for o in orders for c in cs if o[1] == c[0]]
            m = [(len(allj), "선택 조건을 적용하지 않고 조인 결과만 셌다."),
                 (len([1 for o, c in allj if c[2] == "골드"]), "금액 조건을 빠뜨렸다."),
                 (len([1 for o, c in allj if o[2] >= 30]), "등급 조건을 빠뜨렸다."),
                 (len([1 for o, c in allj if c[2] == "골드" or o[2] >= 30]), "AND를 OR로 읽었다."),
                 (len([1 for o, c in allj if c[2] == "골드" and o[2] > 30]), "금액≥30을 금액>30으로 읽어 경계값을 제외했다.")]
            solve1 = "조인 결과: " + ", ".join(f"{o[0]}({c[1]}·{c[2]}·{o[2]})" for o, c in allj) + f" 중 두 조건을 모두 만족하는 {ans}행."
            diff = 3
        out.append(q(
            id=f"d02-ra-join-{n:02d}", label=2, difficulty=diff, topic="관계 대수: 조인 결과 행 수",
            tags=["관계 대수", "조인", "카디널리티"],
            stem=f"다음 두 릴레이션에 대해 {expr}의 결과 튜플 수는?",
            tables=tables, answer=(str(ans), nm),
            distractors=num_choices(ans, m, 8),
            ask="조인은 공통 속성 값이 같은 튜플 쌍만 결합한다. 1:N인지 M:N인지, 짝이 없는 행이 사라지는지(내부) 남는지(외부)를 구분해 행 수를 센다.",
            solve=[solve1,
                   "카티션 곱은 모든 쌍(|R|×|S|)을 만들지만 조인은 조인 조건을 만족하는 쌍만 남긴다. 한쪽의 같은 값이 여러 번 나오면 그 값에서 (한쪽 개수 × 다른 쪽 개수)개의 결과가 나온다.",
                   "내부 조인은 짝이 없는 행이 결과에서 사라지고, 외부 조인은 NULL을 채워 남긴다. 조인 뒤의 셀렉션은 이미 만들어진 행에서 조건을 다시 거른다."],
            tip="조인 행 수는 공통 값마다 (왼쪽 개수 × 오른쪽 개수)를 더한다. 키로 조인하면 FK 쪽 행 수를 넘지 못하고, 외부 조인은 내부 조인 + 짝 없는 행이다.",
            family="d02-ra-join", source_ideas=SOURCES))
    return out


# -------------------------------------------------------------------- division
def gen_div():
    out = []
    studs = ["김하늘", "이도윤", "박서연", "최민준", "정지우"]
    for n in range(1, 4):
        r = rng(f"d02-ra-div-{n}")
        for _ in range(500):
            req = r.sample(["DB", "OS", "NET", "SW"], r.choice([2, 2, 3]))
            extra = [c for c in ["DB", "OS", "NET", "SW", "AI"] if c not in req]
            rows = []
            for st in studs:
                k = r.randint(1, len(req))
                got = r.sample(req, k) + r.sample(extra, r.randint(0, 1))
                rows += [(st, c) for c in got]
            full = {st for st in studs if all((st, c) in rows for c in req)}
            anyc = {st for st in studs if any((st, c) in rows for c in req)}
            if 1 <= len(full) <= 2 and len(anyc) > len(full):
                break
        why_in, why_not = {}, {}
        for st in studs:
            have = [c for c in req if (st, c) in rows]
            miss = [c for c in req if (st, c) not in rows]
            why_in[st] = f"{st}은(는) 필수 과목 {', '.join(req)}을(를) 모두 수강했으므로 나누기 결과에 들어간다."
            why_not[st] = f"{st}은(는) 필수 과목 중 {', '.join(miss) if miss else '일부'}을(를) 수강하지 않아 결과에 들어갈 수 없다."
        mist = [(frozenset(anyc), "필수 과목 중 하나라도 수강한 학생을 골랐다. 나누기(÷)는 나누는 릴레이션의 모든 튜플과 짝이 있는 값만 남기는 '모든'의 연산이다."),
                (frozenset(set(studs) - full), "조건을 반대로 읽어 모든 필수 과목을 수강하지 않은 학생을 골랐다."),
                (frozenset(studs), "수강 기록이 있는 모든 학생을 골랐다.")]
        choices = set_choices(frozenset(full), studs, mist, why_in, why_not, fmt_set)
        out.append(q(
            id=f"d02-ra-div-{n:02d}", label=2, difficulty=2 if n == 1 else 3,
            topic="관계 대수: 디비전(÷)", tags=["관계 대수", "나누기", "전칭 질의"],
            stem=f"다음 표에서 TAKE ÷ REQUIRED의 결과(학생 집합)로 옳은 것은? (TAKE(학생, 과목), REQUIRED(과목)이며 ÷는 관계 대수의 디비전이다.)",
            tables=[tbl("TAKE", ["학생", "과목"], rows), tbl("REQUIRED", ["과목"], [(c,) for c in req])],
            answer=(fmt_set(frozenset(full), {s_: i for i, s_ in enumerate(studs)}),
                    f"REQUIRED의 과목 {', '.join(req)}을(를) 모두 수강한 학생만 남는다."),
            distractors=choices,
            ask="나누기는 R(X, Y) ÷ S(Y)에서 S의 모든 Y 값과 짝을 이루는 X 값을 찾는다. '모든 ~을 수강한 학생'을 찾는 질의와 같다.",
            solve=["학생별로 수강한 필수 과목을 확인한다: " + "; ".join(f"{st}: {', '.join(c for c in req if (st, c) in rows) or '없음'}" for st in studs) + ".",
                   f"필수 과목 {', '.join(req)}을(를) 하나도 빠짐없이 가진 학생은 {', '.join(sorted(full, key=studs.index))}이다.",
                   "필수 과목 이외의 수강 기록(AI 같은 추가 과목)은 결과에 영향이 없다. 나누기는 SQL의 NOT EXISTS 이중 부정이나 GROUP BY HAVING COUNT 비교로 구현한다."],
            tip="÷는 '모든'. 학생마다 나누는 릴레이션의 모든 값을 갖고 있는지 체크하고, 하나라도 빠지면 제외한다. 하나라도 있으면 포함하는 것은 세미 조인에 가깝다.",
            family="d02-ra-div", source_ideas=SOURCES))
    return out


# ------------------------------------------------------------------ expression
def gen_expr():
    out = []
    for n in range(1, 4):
        r = rng(f"d02-ra-expr-{n}")
        cs = [("C1", "김하늘", "골드"), ("C2", "이도윤", "일반"), ("C3", "박서연", "골드"), ("C4", "최민준", "일반"), ("C5", "정지우", "골드")]
        for _ in range(500):
            orders = [(f"O{i + 1}", r.choice([c[0] for c in cs[:4]]), r.choice([12, 30, 45, 80])) for i in range(6)]
            if n == 1:
                f = lambda o, c: c[2] == "골드"
                cond = "등급='골드'"
            elif n == 2:
                f = lambda o, c: o[2] >= 45
                cond = "금액≥45"
            else:
                f = lambda o, c: c[2] == "골드" and o[2] < 45
                cond = "등급='골드' AND 금액<45"
            joined = [(o, c) for o in orders for c in cs if o[1] == c[0]]
            res = {c[1] for o, c in joined if f(o, c)}
            allc = {c[1] for o, c in joined}
            if 1 <= len(res) < len(allc) <= 4:
                break
        names = [c[1] for c in cs]
        why_in, why_not = {}, {}
        for nm in names:
            c = next(c for c in cs if c[1] == nm)
            os_ = [o for o in orders if o[1] == c[0]]
            why_in[nm] = f"{nm}은(는) 주문 {', '.join(o[0] for o in os_ if f(o, c))}이(가) 조건 {cond}을(를) 만족한다."
            why_not[nm] = (f"{nm}은(는) 주문이 없어 조인 결과에 나타나지 않는다." if not os_ else
                           f"{nm}의 주문({', '.join(str(o[2]) for o in os_)}원)은 등급 {c[2]}이어서 조건 {cond}을(를) 만족하지 못한다.")
        allnames = frozenset(allc)
        mist = [(allnames, "선택 조건을 무시하고 주문이 있는 모든 고객을 골랐다."),
                (frozenset(names), "CUSTOMER의 모든 고객을 골랐다. 내부 조인에는 주문이 없는 고객이 나타나지 않는다."),
                (frozenset(allnames - res), "조건을 만족하지 않는 고객을 골랐다.")]
        choices = set_choices(frozenset(res), names, mist, why_in, why_not, fmt_set)
        out.append(q(
            id=f"d02-ra-expr-{n:02d}", label=2, difficulty=3 if n == 3 else 2,
            topic="관계 대수: 복합식의 계산 순서", tags=["관계 대수", "조인", "셀렉션", "프로젝션"],
            stem=f"다음 표에 대해 π_이름(σ_({cond})(ORDERS ⋈ CUSTOMER))의 결과 집합으로 옳은 것은?",
            tables=[tbl("ORDERS", ["주문번호", "고객번호", "금액"], orders), tbl("CUSTOMER", ["고객번호", "이름", "등급"], cs)],
            answer=(fmt_set(frozenset(res), {s_: i for i, s_ in enumerate(names)}),
                    "조인 → 선택 → 투영 순서로 계산하면 남는 이름이다. 투영 뒤 같은 이름은 하나로 합쳐진다."),
            distractors=choices,
            ask="가장 안쪽 괄호부터 조인, 셀렉션, 프로젝션을 차례로 적용한 뒤 중복을 제거한 이름 집합을 구하는 문제다.",
            solve=["① 조인: " + ", ".join(f"{o[0]}→{c[1]}" for o, c in joined) + ".",
                   f"② 셀렉션({cond}): " + ", ".join(f"{o[0]}({c[1]})" for o, c in joined if f(o, c)) + ".",
                   f"③ 프로젝션: 이름만 남기고 중복을 제거하면 {fmt_set(frozenset(res), {s_: i for i, s_ in enumerate(names)})}.",
                   "주문이 없는 고객은 내부 조인에서 사라지고, 같은 고객의 여러 주문이 조건을 통과해도 투영 뒤에는 이름이 하나로 합쳐진다."],
            tip="안쪽 괄호부터 ⋈ → σ → π 순으로 중간 결과 표를 적는다. π는 마지막에 중복을 제거한다.",
            family="d02-ra-expr", source_ideas=SOURCES))
    return out


def generate():
    return gen_proj() + gen_sel() + gen_set() + gen_join() + gen_div() + gen_expr()
