"""SQL NULL semantics, executed in sqlite.

Reasoning points: three-valued logic in WHERE (UNKNOWN rows are dropped), NULL in
arithmetic (sal + NULL = NULL), NOT IN against a list containing NULL vs NOT EXISTS,
and COALESCE. Wrong choices come from mutated queries that model each misreading.
"""
from __future__ import annotations

from families.sql_kit import (DB, DEPTS, FMT_RULE, NAMES, cond_block, eval_muts, q, search, sqlcode)

SRC = ["past-2021-2-6", "past-2023-1-16", "itpasslab-2-7"]
FAM = "sql-null"
TOPIC = "SQL NULL 처리"
COLS = ["id INTEGER", "name TEXT", "dept TEXT", "sal INTEGER", "bonus INTEGER"]


def rows_with_null(r, n):
    names = r.sample(NAMES, n)
    depts = r.sample(DEPTS, 3)
    out = []
    for i, nm in enumerate(names):
        bonus = r.choice([None, None, 0, 20, 30, 50, 50, 80])
        out.append((101 + i, nm, r.choice(depts), r.randrange(250, 560, 10), bonus))
    if sum(x[4] is None for x in out) < 2:
        return None
    return out


SHAPES = [  # (where, boundary/operator misreading, why)
    ("bonus <> {b} AND sal < {s}", "bonus = {b} AND sal < {s}", "<>(같지 않다)를 =로 읽었다."),
    ("NOT (bonus > {b}) OR dept = '{d}'", "NOT (bonus >= {b}) OR dept = '{d}'", ">를 >=로 읽어 경계값 {b}의 처리가 바뀌었다."),
    ("bonus <> {b} OR sal >= {s}", "bonus <> {b} OR sal > {s}", "sal >= {s}를 초과(>)로 읽어 경계값을 뺐다."),
    ("bonus < {b} OR sal >= {s}", "bonus <= {b} OR sal >= {s}", "bonus < {b}에 경계값 {b}를 포함했다."),
    ("NOT (bonus >= {b}) AND sal < {s}", "NOT (bonus > {b}) AND sal < {s}", ">=를 >로 읽어 경계값 {b}의 처리가 바뀌었다."),
    ("bonus <= {b} OR dept = '{d}'", "bonus < {b} OR dept = '{d}'", "bonus <= {b}에서 경계값 {b}를 뺐다."),
    ("NOT (bonus = {b} OR sal > {s})", "NOT (bonus = {b}) OR sal > {s}", "NOT이 괄호 전체가 아니라 첫 비교에만 걸린다고 보았다."),
    ("NOT (bonus < {b}) AND NOT (sal > {s})", "NOT (bonus < {b}) AND sal > {s}", "두 번째 조건 앞의 NOT을 놓쳤다."),
]


def t_tri(r, shape_i):
    rows = rows_with_null(r, r.randint(6, 8))
    if not rows:
        return None
    tmpl, alt, why = SHAPES[shape_i]
    b = r.choice([20, 30, 50])
    s_ = r.choice(sorted({x[3] for x in rows}))
    d = r.choice([x[2] for x in rows])
    w = tmpl.format(b=b, s=s_, d=d)
    db = DB([("emp", COLS, rows)])
    sel = "SELECT name FROM emp\nWHERE {w}\nORDER BY id;"
    query = sel.format(w=w)
    wz = w.replace("bonus", "COALESCE(bonus, 0)")
    muts = [
        (sel.format(w=f"({w}) OR bonus IS NULL"),
         "bonus가 NULL인 행의 비교 결과(UNKNOWN)를 참으로 보아 포함했다. WHERE는 TRUE인 행만 남긴다."),
        (sel.format(w=wz), "NULL을 0으로 취급해 비교했다. COALESCE/NVL 없이 NULL은 0이 아니다."),
        (sel.format(w=w.replace("bonus", "COALESCE(bonus, 9999)")),
         "NULL을 가장 큰 값처럼 비교했다. Oracle 정렬에서 NULL이 큰 값처럼 놓이는 것과 비교 연산을 혼동한 것이다."),
        (sel.format(w=f"NOT ({w})"), "조건을 거꾸로 적용했다(참·거짓 뒤집기)."),
        (sel.format(w=f"NOT ({w}) OR bonus IS NULL"),
         "조건을 거꾸로 적용하고 NULL 행까지 남겼다. UNKNOWN의 부정도 UNKNOWN이므로 NULL 행은 어느 쪽에도 남지 않는다."),
        (sel.format(w="bonus IS NULL"), "NULL 비교 자체를 '조건 만족'으로 오해해 NULL 행만 골랐다."),
        (sel.format(w=f"({w}) AND bonus IS NOT NULL"),
         "bonus가 NULL이면 다른 조건과 상관없이 무조건 탈락한다고 보았다. UNKNOWN OR TRUE는 TRUE이므로 OR의 다른 쪽이 참이면 남는다."),
        (sel.format(w=alt.format(b=b, s=s_, d=d)), why.format(b=b, s=s_)),
        (sel.format(w=w.replace(" OR ", " AND ") if " OR " in w else w.replace(" AND ", " OR ")),
         "OR와 AND를 바꿔 적용했다."),
        (f"SELECT name FROM emp\nWHERE {w}\nORDER BY id DESC;","행은 맞지만 ORDER BY id 오름차순을 내림차순으로 적었다."),
        ("SELECT name FROM emp ORDER BY id;", "WHERE 조건이 NULL 때문에 무시된다고 보아 모든 행을 골랐다."),
    ]
    ans = db.f(query)
    wrong = eval_muts(db.f, muts)
    if wrong[0][0] == ans or wrong[1][0] == ans or ans == "결과 없음":
        return None  # the NULL trap must change the result
    return dict(db=db, query=query, answer=ans, wrong=wrong, w=w)


def b_tri(n, s, diff):
    db, w = s["db"], s["w"]
    parts = [("WHERE 조건", w)]
    if " OR " in w or " AND " in w or "NOT" in w:
        for piece in w.replace("NOT (", "(").replace("(", "").replace(")", "").replace(" AND ", " OR ").split(" OR "):
            parts.insert(0, (piece.strip(), piece.strip()))
    solve = [
        "NULL과의 비교(=, <>, <, > 등)는 TRUE도 FALSE도 아닌 UNKNOWN이다. NOT UNKNOWN은 UNKNOWN, UNKNOWN OR TRUE는 TRUE, "
        "UNKNOWN OR FALSE는 UNKNOWN, UNKNOWN AND FALSE는 FALSE다. WHERE 절은 결과가 TRUE인 행만 남기고 FALSE와 UNKNOWN은 모두 버린다.",
        cond_block(db, "emp", ["id", "name", "sal", "bonus"], parts, caption="행별 3값 논리 평가", tri=True),
        f"'WHERE 조건' 열이 TRUE인 행만 id 순으로 적으면 {s['answer']}이다. bonus가 NULL인 행은 다른 쪽 조건이 OR로 TRUE를 만들어 주지 않는 한 "
        "결과에서 빠진다. NULL을 0으로 보거나 UNKNOWN을 참으로 보면 다른 보기가 나온다.",
    ]
    return q(id=f"{FAM}-{n:02d}", difficulty=diff, topic=TOPIC, tags=["SQL", "NULL", "3값 논리", "WHERE"],
             stem=f"bonus 열에 NULL이 있는 다음 emp 테이블에 SQL을 실행한 결과는? ({FMT_RULE})",
             spec=s, code=sqlcode(s["query"]), tables=[db.table("emp")],
             answer_note="UNKNOWN이 된 NULL 행을 버리고 TRUE인 행만 남긴 실제 실행 결과다.",
             ask="NULL이 섞인 열을 비교할 때 3값 논리(TRUE/FALSE/UNKNOWN)에 따라 WHERE 절을 통과하는 행을 묻는다.",
             solve=solve, tip="NULL 행에는 'U'를 적어 두고 NOT·AND·OR 진리표로 계산한다. NULL을 찾을 때는 = NULL이 아니라 IS NULL을 써야 한다.",
             family=FAM, sources=SRC)


FORMS = {
    "notin": ("SELECT COUNT(*) FROM emp\nWHERE id NOT IN (SELECT emp_id FROM proj);",
              "NOT IN 목록(서브쿼리 결과)에 NULL이 하나라도 있으면 id <> NULL이 UNKNOWN이 되어 어떤 행도 TRUE가 될 수 없다."),
    "notin_nn": ("SELECT COUNT(*) FROM emp\nWHERE id NOT IN (SELECT emp_id FROM proj\n                 WHERE emp_id IS NOT NULL);",
                 "서브쿼리에서 NULL을 걸러냈으므로 NOT IN이 정상적으로 '목록에 없는 직원'을 센다."),
    "notexists": ("SELECT COUNT(*) FROM emp e\nWHERE NOT EXISTS (SELECT 1 FROM proj p\n                  WHERE p.emp_id = e.id);",
                  "NOT EXISTS는 일치하는 행이 있는지만 보므로 proj의 NULL 행은 어느 직원과도 일치하지 않을 뿐 결과를 막지 않는다."),
    "in": ("SELECT COUNT(*) FROM emp\nWHERE id IN (SELECT emp_id FROM proj);",
           "IN은 목록 값 중 하나와 같으면 TRUE이므로 NULL이 있어도 일치하는 직원은 그대로 센다. 중복된 emp_id가 있어도 직원은 한 번만 센다."),
    "exists": ("SELECT COUNT(*) FROM emp e\nWHERE EXISTS (SELECT 1 FROM proj p\n              WHERE p.emp_id = e.id);",
               "EXISTS는 일치하는 proj 행이 하나라도 있으면 그 직원을 한 번 센다."),
}
JOIN_CNT = "SELECT COUNT(*) FROM emp e JOIN proj p ON p.emp_id = e.id"
MISREAD = {
    "notin": [("SELECT COUNT(*) FROM emp WHERE id NOT IN (SELECT emp_id FROM proj WHERE emp_id IS NOT NULL)",
               "NULL을 무시하고 목록에 없는 직원을 셌다"),
              ("SELECT COUNT(*) FROM emp", "NULL과의 비교가 모두 참이 된다고 보아 전 직원을 셌다"),
              ("SELECT COUNT(*) FROM emp WHERE id IN (SELECT emp_id FROM proj)", "NOT을 놓쳐 IN으로 셌다")],
    "notin_nn": [("SELECT COUNT(*) FROM emp WHERE id NOT IN (SELECT emp_id FROM proj)",
                  "IS NOT NULL 필터를 놓치고 NULL 때문에 0행이라고 보았다"),
                 ("SELECT COUNT(*) FROM emp WHERE id IN (SELECT emp_id FROM proj)", "NOT을 놓쳐 IN으로 셌다")],
    "notexists": [("SELECT COUNT(*) FROM emp WHERE id NOT IN (SELECT emp_id FROM proj)",
                   "NOT IN처럼 NULL이 결과를 막는다고 보아 0행으로 셌다"),
                  ("SELECT COUNT(*) FROM emp e WHERE EXISTS (SELECT 1 FROM proj p WHERE p.emp_id = e.id)",
                   "NOT을 놓쳐 EXISTS로 셌다"),
                  ("SELECT COUNT(*) FROM emp", "상관 조건을 무시해 전 직원을 셌다")],
    "in": [(JOIN_CNT, "중복된 emp_id만큼 직원을 여러 번 셌다(조인 행 수와 혼동)"),
           ("SELECT 0", "목록에 NULL이 있으면 IN도 실패한다고 보아 0으로 셌다"),
           ("SELECT COUNT(*) FROM emp WHERE id NOT IN (SELECT emp_id FROM proj WHERE emp_id IS NOT NULL)",
            "IN과 NOT IN을 바꿔 읽었다")],
    "exists": [(JOIN_CNT, "일치하는 proj 행 수만큼 직원을 여러 번 셌다"),
               ("SELECT COUNT(*) FROM emp", "EXISTS 서브쿼리가 항상 행을 돌려준다고 보아 전 직원을 셌다"),
               ("SELECT COUNT(*) FROM emp e WHERE NOT EXISTS (SELECT 1 FROM proj p WHERE p.emp_id = e.id)",
                "EXISTS를 NOT EXISTS로 읽었다")],
}
PAIRS = [("notin", "notexists"), ("notin", "in"), ("in", "notexists"), ("notin_nn", "notin"), ("exists", "notin")]


def t_pair(r, pi):
    fa, fb = PAIRS[pi]
    n = r.randint(5, 7)
    names = r.sample(NAMES, n)
    emp = [(101 + i, nm) for i, nm in enumerate(names)]
    m = r.randint(4, 6)
    ids = [r.choice(emp)[0] for _ in range(m - 1)] + [None]
    r.shuffle(ids)
    proj = [(f"P{i + 1}", e) for i, e in enumerate(ids)]
    db = DB([("emp", ["id INTEGER", "name TEXT"], emp), ("proj", ["pid TEXT", "emp_id INTEGER"], proj)])
    va, vb = db.f(FORMS[fa][0]), db.f(FORMS[fb][0])
    alts_a = [(va, None)] + [(db.f(sq), why) for sq, why in MISREAD[fa]]
    alts_b = [(vb, None)] + [(db.f(sq), why) for sq, why in MISREAD[fb]]
    if len({va, vb}) < 2 or any(len(set(x for x, _ in alts)) < len(alts) for alts in (alts_a, alts_b)):
        return None
    wrong = []
    for xa, wa in alts_a:
        for xb, wb in alts_b:
            if wa is None and wb is None:
                continue
            note = " ".join([f"(가): {wa}." if wa else "(가)는 맞다.", f"(나): {wb}." if wb else "(나)는 맞다."])
            wrong.append((f"(가) {xa}, (나) {xb}", note))
    wrong.append((f"(가) {vb}, (나) {va}", "두 쿼리의 결과를 서로 바꿔 적었다. NULL이 영향을 주는 쪽이 어느 것인지 혼동했다."))
    return dict(db=db, answer=f"(가) {va}, (나) {vb}", wrong=wrong, fa=fa, fb=fb, va=va, vb=vb)


def b_pair(n, s):
    db, fa, fb = s["db"], s["fa"], s["fb"]
    code = "-- (가)\n" + FORMS[fa][0] + "\n\n-- (나)\n" + FORMS[fb][0]
    solve = [
        "proj.emp_id에는 NULL이 한 행 있다. 각 직원 id가 서브쿼리 결과에 들어 있는지, 그리고 NULL과의 비교가 어떤 값이 되는지를 따로 본다.",
        db.block("SELECT e.id, e.name, (SELECT COUNT(*) FROM proj p WHERE p.emp_id = e.id) AS 일치_proj_수 FROM emp e ORDER BY e.id",
                 "직원별 proj 일치 행 수"),
        f"(가) {FORMS[fa][1]} 따라서 결과는 {s['va']}이다.",
        f"(나) {FORMS[fb][1]} 따라서 결과는 {s['vb']}이다.",
        "NOT IN (a, b, NULL)은 id <> a AND id <> b AND id <> NULL로 펼쳐지는데, 마지막 항이 UNKNOWN이라 전체가 TRUE가 될 수 없다. "
        "반면 IN은 OR로 펼쳐지므로 일치하는 값이 하나라도 있으면 TRUE가 된다.",
    ]
    return q(id=f"{FAM}-{n:02d}", difficulty=3, topic=TOPIC, tags=["SQL", "NULL", "NOT IN", "EXISTS", "서브쿼리"],
             stem="다음 두 테이블에 SQL (가), (나)를 각각 실행했을 때 결과값으로 옳은 것은?",
             spec=s, code=sqlcode(code), tables=[db.table("emp"), db.table("proj")],
             answer_note="(가)와 (나)를 실제로 실행한 COUNT 값이다.",
             ask="서브쿼리 결과에 NULL이 있을 때 IN/NOT IN과 EXISTS/NOT EXISTS가 어떻게 달라지는지 두 쿼리의 결과로 묻는다.",
             solve=solve, tip="'목록에 없는 행'을 찾을 때 서브쿼리 열에 NULL이 들어갈 수 있으면 NOT EXISTS를 쓰거나 IS NOT NULL로 걸러야 한다.",
             family=FAM, sources=SRC)


def t_arith(r, variant):
    rows = rows_with_null(r, r.randint(5, 7))
    if not rows:
        return None
    db = DB([("emp", COLS, rows)])
    d = r.choice([x[2] for x in rows])
    where = f"\nWHERE dept = '{d}'" if variant % 2 else ""
    cols = ["SUM(sal + bonus)", "SUM(sal) + SUM(bonus)", "SUM(sal + COALESCE(bonus, 0))"]
    if variant >= 2:
        cols = ["COUNT(sal + bonus)", "SUM(sal + bonus)", "MAX(sal + COALESCE(bonus, 0))"]
    query = f"SELECT {', '.join(cols)}\nFROM emp{where};"
    def mq(cs):
        return f"SELECT {', '.join(cs)} FROM emp{where}"
    nz = [c.replace("sal + bonus", "sal + COALESCE(bonus, 0)").replace("SUM(bonus)", "SUM(COALESCE(bonus, 0))") for c in cols]
    muts = []
    for i in range(3):
        alt = list(cols)
        alt[i] = nz[i]
        if alt != cols:
            muts.append((mq(alt), f"{i + 1}번째 식에서 NULL을 0처럼 더했다. sal + NULL은 NULL이고, 집계 함수는 그 NULL 행을 건너뛴다."))
    muts.append((mq(nz), "모든 식에서 NULL을 0으로 보았다."))
    alt = [c.replace("sal + bonus", "sal") for c in cols]
    muts.append((mq(alt), "sal + bonus가 NULL이면 sal만 남는다고 보았다(NULL을 무시하는 덧셈으로 오해)."))
    if variant < 2:
        muts.append((mq(["NULL", cols[1], cols[2]]), "SUM 안에 NULL이 하나라도 있으면 전체가 NULL이 된다고 보았다. 집계 함수는 NULL을 제외하고 계산한다."))
        muts.append((mq(["NULL", "NULL", cols[2]]), "SUM(bonus)도 NULL이 섞이면 NULL이 된다고 보아 앞의 두 식을 모두 NULL로 적었다."))
        muts.append((mq([cols[1], cols[0], cols[2]]), "1번째와 2번째 식의 결과를 바꿔 적었다. 행 단위로 먼저 더하는 식과 열마다 따로 합한 뒤 더하는 식을 혼동했다."))
        muts.append((mq([cols[0], "SUM(sal)", cols[2]]), "SUM(bonus)가 NULL 때문에 무시된다고 보아 SUM(sal)만 적었다."))
    else:
        muts.append((mq(["COUNT(*)", cols[1], cols[2]]), "COUNT(식)이 NULL 행도 센다고 보아 전체 행 수를 적었다."))
        muts.append((mq(["COUNT(*)", nz[1], cols[2]]), "COUNT와 SUM 모두에서 NULL 행을 포함했다."))
        muts.append((mq([cols[0], cols[1], "MAX(sal + bonus)"]), "MAX 안의 COALESCE를 무시해 NULL 행을 제외하고 최댓값을 구했다."))
        muts.append((mq([cols[0], cols[1], "MAX(sal)"]), "MAX에서 bonus를 더하지 않고 sal 최댓값만 보았다."))
        muts.append((mq([cols[0], "NULL", cols[2]]), "SUM 안에 NULL 행이 있으면 합계 전체가 NULL이 된다고 보았다."))
    muts.append((mq([c.replace("bonus", "0") for c in cols]), "bonus 값을 모두 0으로 착각했다."))
    ans = db.f(query)
    wrong = eval_muts(db.f, muts)
    if variant % 2 and sum(1 for x in rows if x[2] == d and x[4] is None) == 0:
        return None
    if "NULL" in ans:
        return None
    return dict(db=db, query=query, answer=ans, wrong=wrong, where=where, d=d, variant=variant)


def b_arith(n, s):
    db = s["db"]
    w = s["where"].strip()
    solve = [
        "산술 연산에 NULL이 끼면 결과는 NULL이다(sal + NULL = NULL). 집계 함수(SUM, COUNT(식), MAX 등)는 NULL 값을 건너뛰고 나머지로 계산한다. "
        "COALESCE(bonus, 0)은 bonus가 NULL이면 0을 대신 쓴다(Oracle의 NVL과 같은 역할)." + (f" 먼저 {w} 조건으로 행을 거른다." if w else ""),
        db.block(f"SELECT id, name, sal, bonus, sal + bonus AS \"sal+bonus\", sal + COALESCE(bonus, 0) AS \"sal+COALESCE\" FROM emp "
                 f"{w} ORDER BY id", "행별 식 값"),
        f"위 표의 열을 집계하면 결과는 {s['answer']}이다. 행 단위로 먼저 더한 뒤 합하면 NULL 행 전체(sal 포함)가 빠지고, "
        "열마다 따로 합한 뒤 더하면 NULL 행의 sal은 합계에 남는다는 차이가 핵심이다.",
    ]
    return q(id=f"{FAM}-{n:02d}", difficulty=2 if s["variant"] < 2 else 3, topic=TOPIC,
             tags=["SQL", "NULL", "산술", "COALESCE", "집계"],
             stem="다음 SQL의 실행 결과(SELECT 목록 순서대로 ', ' 구분)는?",
             spec=s, code=sqlcode(s["query"]), tables=[db.table("emp")],
             answer_note="행마다 NULL 전파를 적용한 뒤 집계 함수가 NULL을 건너뛴 실제 결과다.",
             ask="NULL이 섞인 열을 산술식과 집계 함수에 넣을 때 NULL 전파와 NULL 제외가 각각 어디서 일어나는지 묻는다.",
             solve=solve, tip="'식 안의 NULL은 전파, 집계 함수는 NULL 제외' 두 규칙을 순서대로 적용한다. NULL을 0으로 바꾸려면 COALESCE(Oracle은 NVL)를 명시해야 한다.",
             family=FAM, sources=SRC)


def generate():
    out, n = [], 1
    for i in range(7):
        s = search(f"{FAM}-tri-{i}", lambda r, i=i: t_tri(r, i))
        out.append(b_tri(n, s, 2 if i < 2 else 3)); n += 1
    for i in range(5):
        s = search(f"{FAM}-pair-{i}", lambda r, i=i: t_pair(r, i))
        out.append(b_pair(n, s)); n += 1
    return out
