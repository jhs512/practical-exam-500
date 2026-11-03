"""SQL GROUP BY / HAVING executed in sqlite.

Reasoning points: WHERE filters rows before grouping, HAVING filters groups after
aggregation, the grouping key decides what one output row means, multi-column
GROUP BY, and which aggregate function the select list asks for.
"""
from __future__ import annotations

from families.sql_kit import DB, DEPTS, FMT_RULE
from families.sql_kit2 import EMP_COLS, emp_rows, fin, differs, run_plan

FAM = "sql-group"
TOPIC = "GROUP BY와 HAVING"
SRC = ["past-2020-1-12", "past-2022-1-9", "sinagong-2-5"]
AGGS = [("COUNT(*)", "인원수"), ("SUM(sal)", "급여 합"), ("MAX(sal)", "최고 급여"), ("MIN(sal)", "최저 급여")]
STEM = f"emp 테이블에 대한 SQL의 실행 결과는? ({FMT_RULE})"


def t_where_having(r, i):
    rows = emp_rows(r, r.randint(8, 10))
    db = DB([("emp", EMP_COLS, rows)])
    agg, aname = AGGS[i % 4]
    x = r.choice([300, 350, 400, 450])
    k = r.choice([2, 2, 3])
    sel = "SELECT dept, {a}\nFROM emp\nWHERE sal >= {x}\nGROUP BY dept\nHAVING COUNT(*) >= {k}\nORDER BY dept;"
    query = sel.format(a=agg, x=x, k=k)
    muts = [
        (sel.format(a=agg, x=0, k=k), "WHERE 절의 급여 조건을 무시하고 전체 행으로 그룹을 만들었다. WHERE는 그룹을 만들기 전에 행을 거른다."),
        (query.replace("HAVING COUNT(*) >= %d\n" % k, ""), "HAVING 조건을 빼먹어 인원이 적은 부서도 출력했다."),
        (query.replace(">= %d\nORDER" % k, "> %d\nORDER" % k), f"HAVING COUNT(*) >= {k}를 초과(>)로 읽어 정확히 {k}명인 부서를 뺐다."),
        (query.replace(f"sal >= {x}", f"sal > {x}"), f"급여 조건 sal >= {x}에서 경계값 {x}를 제외했다."),
        (f"SELECT dept, {agg}\nFROM emp\nWHERE sal >= {x} AND dept IN (SELECT dept FROM emp GROUP BY dept HAVING COUNT(*) >= {k})\nGROUP BY dept\nORDER BY dept;",
         f"HAVING을 WHERE보다 먼저 적용해 전체 인원이 {k}명 이상인 부서를 고른 뒤 급여 조건을 걸었다. 실제 순서는 WHERE로 행을 거르고 그룹의 개수를 센다."),
        (query.replace(">= %d\nORDER" % k, "<= %d\nORDER" % k), "HAVING의 부등호 방향을 반대로 읽어 인원이 적은 부서를 골랐다."),
        (query.replace("ORDER BY dept", "ORDER BY dept DESC"), "ORDER BY dept의 기본 정렬은 오름차순인데 내림차순으로 나열했다."),
        (query.replace("HAVING COUNT(*)", "HAVING COUNT(DISTINCT pos)"), f"HAVING의 COUNT(*)를 서로 다른 직급의 수로 읽었다. COUNT(*)는 그룹의 행 수다."),
        (sel.format(a=agg, x=x, k=k + 1), f"HAVING 기준 인원을 {k + 1}명으로 잘못 읽어 {k}명인 부서를 뺐다."),
        (sel.format(a=agg, x=x, k=1), "HAVING 조건이 사실상 없는 것처럼 읽어 행이 하나라도 있는 부서를 모두 포함했다."),
        (sel.format(a=agg, x=x + 100, k=k), f"급여 기준을 {x + 100}으로 잘못 읽어 통과 행이 줄었다."),
    ] + [
        (sel.format(a=a2, x=x, k=k), f"집계 함수를 {a2}({n2})로 잘못 읽었다. 질문은 {aname}({agg})이다.")
        for a2, n2 in AGGS if a2 != agg
    ] + [
        (f"SELECT pos, {agg}\nFROM emp\nWHERE sal >= {x}\nGROUP BY pos\nHAVING COUNT(*) >= {k}\nORDER BY pos;",
         "그룹 기준을 부서가 아니라 직급(pos)으로 잘못 읽었다."),
    ]
    s = fin(db, query, muts)
    if not differs(s, 3) or s["answer"] == "결과 없음":
        return None
    g = (f"SELECT dept, COUNT(*) AS cnt, SUM(sal) AS sum_sal, MAX(sal) AS max_sal, MIN(sal) AS min_sal "
         f"FROM emp WHERE sal >= {x} GROUP BY dept ORDER BY dept")
    s.update(diff=[1, 2, 3, 2][i % 4], tags=["GROUP BY", "HAVING", "WHERE"], stem=STEM,
             ask=f"WHERE로 먼저 행을 거른 뒤 부서별로 묶고, HAVING으로 그룹을 다시 거르는 순서를 적용해 {aname} 값을 구하는 문제다.",
             solve=[f"실행 순서는 FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY이다. 먼저 WHERE sal >= {x}로 급여가 {x} 이상인 행만 남기고, 그 행들을 dept별로 묶는다. 묶은 그룹마다 COUNT(*)가 {k} 이상인지 HAVING으로 판단한다.",
                    db.block(g, f"WHERE 통과 행을 부서별로 집계한 중간 결과(sal >= {x})"),
                    f"위 표에서 cnt가 {k} 이상인 부서만 남기고 SELECT에 적힌 {agg}를 출력하면 {s['answer']}이다. 급여 조건이 없는 전체 인원으로 HAVING을 계산하면 다른 부서가 남을 수 있다."],
             tip="WHERE는 행, HAVING은 그룹에 대한 조건이다. 쿼리를 읽을 때 '행 거르기 → 묶기 → 그룹 거르기' 순서로 중간 표를 그려 보자.")
    return s


def t_group_key(r, i):
    rows = emp_rows(r, r.randint(8, 10))
    db = DB([("emp", EMP_COLS, rows)])
    key = ["dept", "pos"][i % 2]
    other = "pos" if key == "dept" else "dept"
    fn, fname = [("AVG(sal)", "평균 급여"), ("SUM(sal)", "급여 합"), ("COUNT(*)", "인원수"), ("MAX(sal)", "최고 급여")][(i // 2) % 4]
    sel = "SELECT {g}, " + fn + "\nFROM emp\nGROUP BY {g}\nORDER BY {g};"
    query = sel.format(g=key)
    muts = [
        (sel.format(g=other), f"그룹 기준을 {key}가 아니라 {other}로 읽었다. 출력 행의 의미가 달라진다."),
        (f"SELECT dept, pos, {fn}\nFROM emp\nGROUP BY dept, pos\nORDER BY dept, pos;", "두 열 모두를 그룹 키로 삼아 더 잘게 나누었다. 질문의 그룹 기준은 한 열뿐이다."),
        (f"SELECT {key}, {fn}\nFROM emp\nGROUP BY {key}\nORDER BY {key} DESC;", "ORDER BY의 기본 정렬(ASC)을 내림차순으로 읽었다."),
        (f"SELECT {key}, {fn}\nFROM emp\nGROUP BY {key}\nORDER BY 2, 1;", "정렬 기준을 집계값 먼저로 읽어 행 순서가 바뀌었다."),
        (f"SELECT {key}, COUNT(DISTINCT {other})\nFROM emp\nGROUP BY {key}\nORDER BY {key};", "다른 열의 서로 다른 값 개수를 구한다고 잘못 읽었다."),
    ]
    for a2, n2 in [("AVG(sal)", "평균"), ("SUM(sal)", "합계"), ("COUNT(*)", "개수"), ("MAX(sal)", "최댓값"), ("MIN(sal)", "최솟값")]:
        if a2 != fn:
            muts.append((sel.format(g=key).replace(fn, a2), f"집계 함수를 {a2}({n2})로 읽었다. 질문은 {fname}({fn})이다."))
    if fn == "AVG(sal)":
        muts.append((f"SELECT {key}, (MAX(sal) + MIN(sal)) / 2\nFROM emp\nGROUP BY {key}\nORDER BY {key};",
                     "평균을 (최댓값+최솟값)/2로 계산했다. 평균은 합계를 개수로 나눈 값이다."))
    s = fin(db, query, muts)
    if not differs(s, 3):
        return None
    inter = f"SELECT {key}, COUNT(*) AS cnt, SUM(sal) AS sum_sal, MAX(sal) AS max_sal, MIN(sal) AS min_sal FROM emp GROUP BY {key} ORDER BY {key}"
    s.update(diff=1 if i % 3 == 0 else 2, tags=["GROUP BY", "집계 함수"], stem=STEM,
             ask=f"{key}를 기준으로 그룹을 만들고 그룹별 {fname}을 구한 뒤 {key} 순으로 나열하는 문제다.",
             solve=[f"GROUP BY {key}는 {key} 값이 같은 행끼리 하나의 그룹으로 묶는다. SELECT 목록의 {fn}는 그룹마다 한 번씩 계산되고, 출력 행 수는 {key}의 서로 다른 값의 개수와 같다. 중간 결과를 그룹별로 정리하면 다음과 같다.",
                    db.block(inter, f"{key}별 집계 중간 결과"),
                    f"이 표에서 요청한 값만 골라 {key} 오름차순으로 적으면 {s['answer']}이다. 같은 데이터를 {other}로 묶으면 행 수와 값이 모두 달라지므로 그룹 기준 열을 먼저 확인한다."],
             tip="GROUP BY 뒤의 열이 곧 '출력 행 하나의 의미'다. SELECT의 일반 열은 그룹 키여야 하고 나머지는 집계 함수로 계산된다.")
    return s


def t_multi_key(r, i):
    rows = emp_rows(r, r.randint(9, 11), depts=r.sample(DEPTS, 2))
    db = DB([("emp", EMP_COLS, rows)])
    fn = ["COUNT(*)", "SUM(sal)", "MAX(sal)"][i % 3]
    hv = {"COUNT(*)": "COUNT(*) >= 2", "SUM(sal)": "SUM(sal) >= 600", "MAX(sal)": "MAX(sal) >= 400"}[fn]
    sel = "SELECT dept, pos, {f}\nFROM emp\nGROUP BY dept, pos\nHAVING {h}\nORDER BY dept, pos;"
    query = sel.format(f=fn, h=hv)
    nohv = f"SELECT dept, pos, {fn}\nFROM emp\nGROUP BY dept, pos\nORDER BY dept, pos;"
    muts = [
        (nohv, "HAVING 조건을 빠뜨려 모든 (부서, 직급) 조합을 출력했다."),
        (f"SELECT dept, {fn}\nFROM emp\nGROUP BY dept\nHAVING {hv}\nORDER BY dept;", "두 열 GROUP BY를 부서 하나로만 묶었다. 직급까지 같은 행끼리가 한 그룹이다."),
        (f"SELECT pos, {fn}\nFROM emp\nGROUP BY pos\nHAVING {hv}\nORDER BY pos;", "두 열 GROUP BY를 직급 하나로만 묶었다."),
        (query.replace("ORDER BY dept, pos", "ORDER BY pos, dept"), "ORDER BY의 열 순서를 바꾸어 직급을 먼저 정렬했다."),
        (query.replace("ORDER BY dept, pos", "ORDER BY dept DESC, pos"), "dept만 내림차순으로 읽었다."),
        (query.replace("ORDER BY dept, pos", "ORDER BY dept, pos DESC"), "pos만 내림차순으로 읽었다."),
        (sel.format(f=fn, h=hv.replace(">=", ">")), "HAVING의 경계값을 제외했다(>= 를 > 로 읽음)."),
        (sel.format(f=fn, h=hv.replace(">=", "<")), "HAVING 부등호 방향을 반대로 읽었다."),
    ]
    for a2 in ["COUNT(*)", "SUM(sal)", "MAX(sal)", "MIN(sal)"]:
        if a2 != fn:
            muts.append((sel.format(f=a2, h=hv), f"SELECT의 집계를 {a2}로 읽었다. HAVING의 조건은 {hv}이고 출력은 {fn}이다."))
    s = fin(db, query, muts)
    if not differs(s, 3) or s["answer"] == "결과 없음":
        return None
    g = "SELECT dept, pos, COUNT(*) AS cnt, SUM(sal) AS sum_sal, MAX(sal) AS max_sal FROM emp GROUP BY dept, pos ORDER BY dept, pos"
    s.update(diff=2 if i % 3 else 3, tags=["GROUP BY", "HAVING", "복수 열"], stem=STEM,
             ask="두 열(dept, pos)의 값 조합마다 그룹을 만들고, HAVING으로 그룹을 걸러 지정한 집계값과 정렬 순서까지 맞히는 문제다.",
             solve=["GROUP BY dept, pos는 두 열의 값이 모두 같은 행을 하나의 그룹으로 묶는다. 같은 부서라도 직급이 다르면 다른 그룹이 된다. 먼저 모든 조합의 집계를 구한다.",
                    db.block(g, "(dept, pos) 조합별 집계"),
                    f"HAVING {hv}를 만족하는 그룹만 남기고 SELECT의 {fn}만 출력하며, ORDER BY dept, pos이므로 부서 순으로 먼저 정렬하고 같은 부서 안에서 직급 순으로 정렬한다. 결과는 {s['answer']}이다."],
             tip="GROUP BY 열이 여러 개이면 모든 열이 같아야 한 그룹이다. 조합표를 먼저 만들고 HAVING으로 지우면 된다.")
    return s


def t_having_other(r, i):
    rows = emp_rows(r, r.randint(8, 10))
    db = DB([("emp", EMP_COLS, rows)])
    kind = i % 3
    hv, nm = [("MAX(sal) - MIN(sal) >= 150", "급여 최대와 최소의 차이"),
              ("COUNT(DISTINCT pos) >= 2", "서로 다른 직급 수"),
              ("AVG(sal) >= 400", "평균 급여")][kind]
    sel = "SELECT dept, {f}\nFROM emp\nGROUP BY dept\nHAVING {h}\nORDER BY dept;"
    fsel = ["MAX(sal) - MIN(sal)", "COUNT(DISTINCT pos)", "AVG(sal)"][kind]
    query = sel.format(f=fsel, h=hv)
    muts = [
        (sel.format(f=fsel, h="1 = 1"), "HAVING 조건을 무시하고 모든 부서를 출력했다."),
        (sel.format(f=fsel, h=hv.replace(">=", ">")), "HAVING 경계값을 제외했다."),
        (sel.format(f=fsel, h=hv.replace(">=", "<")), "HAVING 부등호 방향을 반대로 읽었다."),
        (query.replace("ORDER BY dept", "ORDER BY dept DESC"), "정렬 방향을 반대로 읽었다."),
        (sel.format(f=fsel, h="NOT (" + hv + ")"), "HAVING 조건 전체를 부정으로 읽었다."),
    ]
    for f2, n2 in [("COUNT(*)", "인원수"), ("SUM(sal)", "급여 합"), ("MAX(sal)", "최고 급여"), ("MIN(sal)", "최저 급여"),
                   ("COUNT(DISTINCT pos)", "서로 다른 직급 수"), ("AVG(sal)", "평균 급여"), ("MAX(sal) - MIN(sal)", "급여 범위")]:
        if f2 != fsel:
            muts.append((sel.format(f=f2, h=hv), f"SELECT의 출력을 {n2}({f2})로 잘못 읽었다. HAVING 조건과 출력 값은 서로 다른 식일 수 있다."))
    s = fin(db, query, muts)
    if not differs(s, 3) or s["answer"] == "결과 없음":
        return None
    g = ("SELECT dept, COUNT(*) AS cnt, COUNT(DISTINCT pos) AS pos_kinds, MAX(sal) AS max_sal, MIN(sal) AS min_sal, AVG(sal) AS avg_sal "
         "FROM emp GROUP BY dept ORDER BY dept")
    s.update(diff=2 if kind != 1 else 3, tags=["HAVING", "집계 함수"], stem=STEM,
             ask=f"HAVING에서 {nm}를 기준으로 그룹을 거르고, SELECT에는 같은 값을 출력하는 문제다.",
             solve=[f"HAVING은 그룹 단위로 계산한 값에 조건을 건다. 이 문제의 조건은 {hv}이다. 부서별로 필요한 집계를 먼저 계산해 둔다.",
                    db.block(g, "부서별 집계 중간 결과"),
                    f"조건 {hv}를 통과하는 부서만 남기고 SELECT의 값을 출력하면 {s['answer']}이다. WHERE에는 집계 함수를 쓸 수 없으므로 그룹 조건은 HAVING에서 처리한다."],
             tip="HAVING의 식과 SELECT의 식이 같은 함수인지 먼저 확인하고, 부서별 집계표 하나로 둘 다 읽는다.")
    return s


PLAN = [(t_where_having, 4), (t_group_key, 4), (t_multi_key, 3), (t_having_other, 3)]


def generate():
    return run_plan(FAM, TOPIC, SRC, PLAN)
