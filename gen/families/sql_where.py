"""SQL WHERE: BETWEEN/IN/LIKE/AND-OR precedence, executed in sqlite.

Reasoning points: inclusive BETWEEN bounds, IN list membership vs NOT IN, AND binding
tighter than OR, LIKE wildcards (% any length, _ exactly one character), and combining
two conditions. Wrong choices are results of mutated WHERE clauses.
"""
from __future__ import annotations

from families.sql_kit import (DB, DEPTS, FMT_RULE, cond_block, q, query_spec, search, sqlcode)

SRC = ["past-2020-2-6", "past-2022-2-4", "sinagong-2-3"]
FAM = "sql-where"
TOPIC = "SQL WHERE 조건"
EMP_COLS = ["id INTEGER", "name TEXT", "dept TEXT", "sal INTEGER", "age INTEGER"]


def emp(r, n, depts):
    ids = list(range(101, 101 + n))
    from families.sql_kit import NAMES
    names = r.sample(NAMES, n)
    return [(i, nm, r.choice(depts), r.randrange(200, 610, 10), r.randint(24, 58))
            for i, nm in zip(ids, names)]


def t_between_in(r):
    depts = r.sample(DEPTS, 3)
    rows = emp(r, r.randint(6, 8), depts)
    sals = sorted({x[3] for x in rows})
    if len(sals) < 5:
        return None
    lo, hi = r.sample(sals[1:-1], 2) if len(sals) > 4 else (sals[1], sals[-2])
    lo, hi = min(lo, hi), max(lo, hi)
    if lo == hi:
        return None
    a, b = depts[0], depts[1]
    db = DB([("emp", EMP_COLS, rows)])
    w = f"dept IN ('{a}', '{b}') AND sal BETWEEN {lo} AND {hi}"
    sel = "SELECT name FROM emp\nWHERE {w}\nORDER BY id;"
    query = sel.format(w=w)
    muts = [
        (sel.format(w=f"dept IN ('{a}', '{b}') AND sal > {lo} AND sal < {hi}"),
         f"BETWEEN을 양 끝을 제외하는 범위로 보아 급여가 정확히 {lo}, {hi}인 행을 뺐다. BETWEEN은 양 끝을 포함한다."),
        (sel.format(w=f"dept IN ('{a}', '{b}') AND sal > {lo} AND sal <= {hi}"),
         f"하한 {lo}만 제외했다. BETWEEN {lo} AND {hi}는 sal >= {lo} AND sal <= {hi}와 같다."),
        (sel.format(w=f"dept IN ('{a}', '{b}') AND sal >= {lo} AND sal < {hi}"),
         f"상한 {hi}만 제외했다. BETWEEN의 상한도 포함된다."),
        (sel.format(w=f"dept NOT IN ('{a}', '{b}') AND sal BETWEEN {lo} AND {hi}"),
         f"IN 목록을 '제외할 부서'로 거꾸로 읽어 {a}·{b}가 아닌 부서를 골랐다."),
        (sel.format(w=f"dept IN ('{a}', '{b}') OR sal BETWEEN {lo} AND {hi}"),
         "AND를 OR처럼 적용해 두 조건 중 하나만 만족해도 포함했다."),
        (sel.format(w=f"sal BETWEEN {lo} AND {hi}"),
         "부서 조건(IN)을 빼먹고 급여 범위만 확인했다."),
        (sel.format(w=f"dept IN ('{a}', '{b}')"),
         "급여 범위 조건(BETWEEN)을 빼먹고 부서만 확인했다."),
        (sel.format(w=f"dept IN ('{a}', '{b}') AND sal NOT BETWEEN {lo} AND {hi}"),
         "급여 조건을 범위 밖(NOT BETWEEN)으로 반대로 해석했다."),
        (sel.format(w=f"dept = '{a}' AND sal BETWEEN {lo} AND {hi}"),
         f"IN 목록의 첫 값 '{a}'만 비교한다고 착각해 '{b}' 부서를 놓쳤다."),
        (sel.format(w=f"dept = '{b}' AND sal BETWEEN {lo} AND {hi}"),
         f"IN 목록의 마지막 값 '{b}'만 비교한다고 착각해 '{a}' 부서를 놓쳤다."),
        (f"SELECT name FROM emp\nWHERE {w}\nORDER BY id DESC;",
         "ORDER BY id는 오름차순(ASC 기본값)인데 내림차순으로 나열했다."),
    ]
    ans, wrong = query_spec(db, query, muts)
    if ans.count(" / ") < 1:
        return None
    return dict(db=db, query=query, answer=ans, wrong=wrong, lo=lo, hi=hi, a=a, b=b, w=w)


def b_between_in(n, s):
    db = s["db"]
    solve = [
        f"WHERE 절의 두 조건은 AND로 묶여 있으므로 둘 다 참인 행만 남는다. 조건 1은 부서가 '{s['a']}' 또는 '{s['b']}'인가(IN), "
        f"조건 2는 급여가 {s['lo']} 이상 {s['hi']} 이하인가(BETWEEN은 양 끝 포함)이다. 각 행을 표로 평가하면 다음과 같다.",
        cond_block(db, "emp", ["id", "name", "dept", "sal"],
                   [("IN", f"dept IN ('{s['a']}', '{s['b']}')"), ("BETWEEN", f"sal BETWEEN {s['lo']} AND {s['hi']}")]),
        f"두 열이 모두 O인 행을 id 오름차순으로 나열하면 {s['answer']}이다. 급여가 정확히 {s['lo']} 또는 {s['hi']}인 행이 있다면 "
        "BETWEEN에 포함된다는 점, IN은 목록 값 중 하나와 같으면 참이라는 점을 확인한다.",
    ]
    return q(id=f"{FAM}-{n:02d}", difficulty=1, topic=TOPIC, tags=["SQL", "WHERE", "BETWEEN", "IN"],
             stem=f"다음 emp 테이블에 SQL을 실행한 결과는? ({FMT_RULE})",
             spec=s, code=sqlcode(s["query"]), tables=[db.table("emp")],
             ask="IN 목록 조건과 BETWEEN 범위 조건이 AND로 결합된 WHERE 절을 통과하는 행을 id 순으로 묻는다. BETWEEN의 양 끝 포함 여부가 핵심이다.",
             solve=solve, tip="BETWEEN a AND b는 a <= x AND x <= b로 바꿔 읽고, IN (x, y)는 = x OR = y로 바꿔 읽으면 경계값과 목록 누락 실수가 줄어든다.",
             family=FAM, sources=SRC)


def t_precedence(r):
    depts = r.sample(DEPTS, 3)
    rows = emp(r, r.randint(6, 8), depts)
    a, b = depts[0], depts[1]
    x = r.choice(sorted({v[3] for v in rows}))
    db = DB([("emp", EMP_COLS, rows)])
    sel = "SELECT name FROM emp\nWHERE {w}\nORDER BY id;"
    w = f"dept = '{a}' OR dept = '{b}' AND sal >= {x}"
    query = sel.format(w=w)
    muts = [
        (sel.format(w=f"(dept = '{a}' OR dept = '{b}') AND sal >= {x}"),
         f"OR를 먼저 묶어 급여 조건이 '{a}' 부서에도 걸린다고 보았다. AND가 OR보다 우선하므로 급여 조건은 '{b}' 쪽에만 붙는다."),
        (sel.format(w=f"dept = '{a}' AND sal >= {x} OR dept = '{b}'"),
         f"급여 조건이 앞의 '{a}' 부서에 붙는다고 보았다. 실제로는 dept = '{b}' AND sal >= {x}가 한 덩어리다."),
        (sel.format(w=f"dept = '{a}' OR dept = '{b}'"),
         "AND 이하의 급여 조건을 무시하고 두 부서 전체를 골랐다."),
        (sel.format(w=f"dept = '{a}' OR dept = '{b}' AND sal > {x}"),
         f"sal >= {x}를 sal > {x}로 읽어 급여가 정확히 {x}인 행을 뺐다."),
        (sel.format(w=f"dept = '{a}' AND dept = '{b}' AND sal >= {x}"),
         "OR를 AND로 읽어 한 행이 두 부서에 동시에 속해야 한다고 보았다(불가능하므로 결과 없음)."),
        (sel.format(w=f"dept = '{a}' OR sal >= {x}"),
         f"dept = '{b}' 조건을 빠뜨려 급여만 만족하면 어느 부서든 포함했다."),
        (sel.format(w=f"dept = '{b}' AND sal >= {x}"),
         f"OR 앞의 dept = '{a}' 조건을 놓쳤다."),
        (sel.format(w=f"dept = '{a}' OR dept = '{b}' AND sal < {x}"),
         "급여 비교 방향을 반대로 읽었다."),
        (sel.format(w=f"dept <> '{a}' AND (dept = '{b}' AND sal >= {x} OR dept <> '{b}')"),
         f"첫 조건을 '{a}' 부서 제외로 오해하고 나머지 부서는 급여 조건 없이 포함했다."),
        (sel.format(w=f"sal >= {x}"),
         "부서 조건은 보지 않고 급여 조건만 적용했다."),
        (f"SELECT name FROM emp\nWHERE {w}\nORDER BY id DESC;",
         "행 집합은 맞지만 ORDER BY id(오름차순)를 내림차순으로 나열했다."),
    ]
    ans, wrong = query_spec(db, query, muts)
    # the trap must matter: the parenthesised reading must differ from the answer
    if wrong[0][0] == ans or ans.count(" / ") < 1:
        return None
    return dict(db=db, query=query, answer=ans, wrong=wrong, a=a, b=b, x=x)


def b_precedence(n, s):
    db, a, b, x = s["db"], s["a"], s["b"], s["x"]
    solve = [
        f"SQL 논리 연산자의 우선순위는 NOT > AND > OR이다. 따라서 WHERE 절은 dept = '{a}' OR (dept = '{b}' AND sal >= {x})로 묶인다. "
        f"즉 '{a}' 부서는 급여와 상관없이 모두 포함되고, '{b}' 부서는 급여가 {x} 이상일 때만 포함된다.",
        cond_block(db, "emp", ["id", "name", "dept", "sal"],
                   [(f"dept='{a}'", f"dept = '{a}'"), (f"dept='{b}' AND sal>={x}", f"dept = '{b}' AND sal >= {x}")]),
        f"두 덩어리 중 하나라도 O인 행을 id 순으로 나열하면 {s['answer']}이다. 괄호를 (dept = '{a}' OR dept = '{b}') AND sal >= {x}로 "
        f"잘못 묶으면 급여가 {x} 미만인 '{a}' 부서 직원이 빠져 결과가 달라진다.",
    ]
    return q(id=f"{FAM}-{n:02d}", difficulty=3, topic=TOPIC, tags=["SQL", "WHERE", "AND", "OR", "우선순위"],
             stem=f"다음 SQL의 실행 결과는? ({FMT_RULE})",
             spec=s, code=sqlcode(s["query"]), tables=[db.table("emp")],
             ask="괄호 없이 OR와 AND가 섞인 WHERE 절에서 연산자 우선순위에 따라 어떤 행이 선택되는지를 묻는다.",
             solve=solve, tip="괄호가 없으면 AND를 먼저 묶어 괄호를 직접 그려 넣는다. 의도와 다르게 읽힐 수 있는 조건은 실무에서도 괄호를 명시하는 것이 안전하다.",
             family=FAM, sources=SRC)


LIKE_PATS = ["%{c}%", "{c}%", "%{c}", "_{c}%", "%{c}_", "_{c}_"]


def t_like(r):
    rows = emp(r, 8, r.sample(DEPTS, 3))
    names = set()
    while len(names) < 8:
        sur = r.choice(["김", "이", "박", "민", "남궁", "지"])
        names.add(sur + "".join(r.sample("민수지하준", r.choice([1, 2, 2, 2]))))
    names = sorted(names, key=lambda x: r.random())
    rows = [(x[0], nm) + x[2:] for x, nm in zip(rows, names)]
    chars = sorted({ch for nm in names for ch in nm if sum(ch in m for m in names) >= 2})
    if not chars:
        return None
    c = r.choice(chars)
    pat = r.choice(LIKE_PATS).format(c=c)
    age = r.choice([30, 35, 40])
    db = DB([("emp", EMP_COLS, rows)])
    sel = "SELECT name, age FROM emp\nWHERE {w}\nORDER BY id;"
    w = f"name LIKE '{pat}' AND age >= {age}"
    query = sel.format(w=w)
    alt = {
        "%" + c + "%": "%를 앞뒤에 붙여 '어디든 포함'으로 읽었다",
        c + "%": f"'{c}'로 시작하는 이름으로 읽었다",
        "%" + c: f"'{c}'로 끝나는 이름으로 읽었다",
        "_" + c + "%": f"둘째 글자가 '{c}'인 이름으로 읽었다",
        "%" + c + "_": f"끝에서 둘째 글자가 '{c}'인 이름으로 읽었다",
        "_" + c + "_": f"세 글자 이름의 가운데 글자가 '{c}'인 것으로 읽었다",
        "__" + c: f"셋째 글자가 '{c}'로 끝나는 세 글자 이름으로 읽었다",
        c + "__": f"'{c}'로 시작하는 정확히 세 글자 이름으로 읽었다",
    }
    muts = []
    for p, why in alt.items():
        if p == pat:
            continue
        muts.append((sel.format(w=f"name LIKE '{p}' AND age >= {age}"),
                     f"패턴 '{pat}'를 '{p}'처럼 해석했다. 즉 {why}. %는 0글자 이상, _는 정확히 한 글자다."))
    muts += [
        (sel.format(w=f"name NOT LIKE '{pat}' AND age >= {age}"), "LIKE를 NOT LIKE처럼 반대로 적용했다."),
        (sel.format(w=f"name LIKE '{pat}' AND age > {age}"), f"age >= {age}를 초과(>)로 읽어 나이가 정확히 {age}인 행을 뺐다."),
        (sel.format(w=f"name LIKE '{pat}'"), "나이 조건을 빼먹고 이름 패턴만 확인했다."),
        (sel.format(w=f"name LIKE '{pat}' OR age >= {age}"), "AND를 OR로 적용했다."),
        (sel.format(w=f"name = '{pat}' AND age >= {age}"), "LIKE 대신 = 비교로 보아 와일드카드를 문자 그대로 비교했다(일치하는 이름 없음)."),
    ]
    ans, wrong = query_spec(db, query, muts)
    if ans == "결과 없음":
        return None
    return dict(db=db, query=query, answer=ans, wrong=wrong, pat=pat, age=age)


def b_like(n, s):
    db = s["db"]
    solve = [
        f"LIKE 패턴 '{s['pat']}'에서 %는 0글자 이상의 임의 문자열, _는 정확히 한 글자를 뜻한다. 여기에 age >= {s['age']} 조건이 AND로 붙어 있으므로 "
        "두 조건을 모두 만족하는 행만 남는다.",
        cond_block(db, "emp", ["id", "name", "age"],
                   [("LIKE", f"name LIKE '{s['pat']}'"), (f"age>={s['age']}", f"age >= {s['age']}")]),
        f"두 열이 모두 O인 행을 id 순으로 적으면 {s['answer']}이다. 이름 길이가 두 글자에서 네 글자까지 섞여 있으므로 "
        "_가 몇 개인지와 %가 어느 쪽에 있는지에 따라 '몇 번째 글자'를 검사하는지, 길이가 제한되는지가 정해진다.",
    ]
    return q(id=f"{FAM}-{n:02d}", difficulty=2, topic=TOPIC, tags=["SQL", "WHERE", "LIKE", "와일드카드"],
             stem=f"다음 SQL의 실행 결과는? ({FMT_RULE})",
             spec=s, code=sqlcode(s["query"]), tables=[s["db"].table("emp")],
             ask="LIKE 와일드카드(%와 _)의 의미와 추가 비교 조건을 함께 적용한 결과 행을 묻는다.",
             solve=solve, tip="패턴을 글자 칸으로 그려 _는 한 칸, %는 '빈칸 포함 아무 길이'로 표시해 이름에 대어 본다.",
             family=FAM, sources=SRC)


def t_notin_agg(r):
    depts = r.sample(DEPTS, 4)
    rows = emp(r, r.randint(6, 8), depts)
    a, b = depts[0], depts[1]
    age = r.choice(sorted({x[4] for x in rows})[1:-1] or [40])
    db = DB([("emp", EMP_COLS, rows)])
    sel = "SELECT COUNT(*), SUM(sal) FROM emp\nWHERE {w};"
    w = f"dept NOT IN ('{a}', '{b}') AND age < {age}"
    query = sel.format(w=w)
    muts = [
        (sel.format(w=f"dept IN ('{a}', '{b}') AND age < {age}"), "NOT을 놓쳐 목록에 있는 부서를 골랐다."),
        (sel.format(w=f"dept NOT IN ('{a}', '{b}') AND age <= {age}"), f"age < {age}에 경계값 {age}를 포함했다."),
        (sel.format(w=f"dept NOT IN ('{a}', '{b}') AND age > {age}"), "나이 비교 방향을 반대로 읽었다."),
        (sel.format(w=f"dept NOT IN ('{a}', '{b}') OR age < {age}"), "AND를 OR로 적용했다."),
        (sel.format(w=f"dept NOT IN ('{a}', '{b}')"), "나이 조건을 빼먹었다."),
        (sel.format(w=f"age < {age}"), "부서 제외 조건을 빼먹었다."),
        (sel.format(w=f"dept <> '{a}' AND age < {age}"), f"NOT IN 목록의 '{b}'를 놓쳐 '{a}'만 제외했다."),
        (sel.format(w=f"dept <> '{b}' AND age < {age}"), f"NOT IN 목록의 '{a}'를 놓쳐 '{b}'만 제외했다."),
        (sel.format(w=f"NOT (dept IN ('{a}', '{b}') AND age < {age})"),
         "NOT이 두 조건 전체에 걸린다고 보았다. NOT은 바로 뒤 IN 술어에만 붙는다."),
        ("SELECT COUNT(*), SUM(sal) FROM emp;", "WHERE 절을 무시하고 전체 행을 집계했다."),
    ]
    ans, wrong = query_spec(db, query, muts)
    if ans.startswith("0,") or ans.startswith("1,"):
        return None
    return dict(db=db, query=query, answer=ans, wrong=wrong, a=a, b=b, age=age)


def b_notin_agg(n, s):
    db, a, b, age = s["db"], s["a"], s["b"], s["age"]
    solve = [
        f"NOT IN ('{a}', '{b}')은 dept <> '{a}' AND dept <> '{b}'와 같다. 여기에 age < {age}가 AND로 결합되므로 두 부서가 아니면서 "
        f"나이가 {age} 미만인 행만 남고, 남은 행의 개수(COUNT(*))와 급여 합계(SUM(sal))를 한 행으로 출력한다.",
        cond_block(db, "emp", ["id", "name", "dept", "sal", "age"],
                   [("NOT IN", f"dept NOT IN ('{a}', '{b}')"), (f"age<{age}", f"age < {age}")]),
        db.block(f"SELECT id, name, sal FROM emp WHERE {s['query'].split('WHERE ')[1].rstrip(';')} ORDER BY id", "조건을 통과한 행"),
        f"통과한 행의 개수와 sal 합을 적으면 {s['answer']}이다.",
    ]
    return q(id=f"{FAM}-{n:02d}", difficulty=2, topic=TOPIC, tags=["SQL", "WHERE", "NOT IN", "집계"],
             stem="다음 SQL의 실행 결과(COUNT, SUM 순서로 ', ' 구분)는?",
             spec=s, code=sqlcode(s["query"]), tables=[db.table("emp")],
             ask="NOT IN과 비교 조건을 함께 만족하는 행의 개수와 급여 합계를 묻는다.",
             solve=solve, tip="NOT IN은 목록의 모든 값과 다를 때만 참이다. 조건을 통과한 행을 먼저 표시해 두고 나서 집계하면 계산 실수가 줄어든다.",
             family=FAM, sources=SRC)


PLAN = [(t_between_in, b_between_in, 6), (t_precedence, b_precedence, 5),
        (t_like, b_like, 5), (t_notin_agg, b_notin_agg, 4)]


def generate():
    out, n = [], 1
    for t, b, k in PLAN:
        for i in range(k):
            s = search(f"{FAM}-{t.__name__}-{i}", t)
            out.append(b(n, s))
            n += 1
    return out
