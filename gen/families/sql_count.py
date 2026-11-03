"""SQL aggregate functions over NULLs and empty sets, executed in sqlite.

Reasoning points: COUNT(*) counts rows while COUNT(col) skips NULL, COUNT(DISTINCT),
AVG/SUM/MAX/MIN ignore NULL (AVG is not divided by the row count), aggregates on an
empty set (COUNT = 0, the rest NULL), and COUNT(col) per group.
"""
from __future__ import annotations

from families.sql_kit import DB, DEPTS, FMT_RULE, NAMES
from families.sql_kit2 import differs, fin, run_plan, swap_muts

FAM = "sql-count"
TOPIC = "집계 함수와 NULL"
SRC = ["past-2021-1-8", "past-2022-2-11", "itpasslab-2-9"]
COLS = ["id INTEGER", "name TEXT", "dept TEXT", "sal INTEGER", "bonus INTEGER"]
STEM = f"emp 테이블에 대한 SQL의 실행 결과는? ({FMT_RULE})"


def rows(r, n, nulls=3):
    depts = r.sample(DEPTS, 3)
    out = []
    for i, nm in enumerate(r.sample(NAMES, n)):
        out.append([101 + i, nm, r.choice(depts), r.randrange(250, 560, 10), r.choice([10, 20, 20, 30, 40, 50])])
    for j in r.sample(range(n), nulls):
        out[j][4] = None
    return [tuple(x) for x in out]


CNT = {
    "COUNT(*)": "NULL 여부와 상관없이 조건을 통과한 행의 수를 센 값", "COUNT(bonus)": "bonus가 NULL이 아닌 행의 수를 센 값",
    "COUNT(DISTINCT bonus)": "bonus의 NULL이 아닌 서로 다른 값의 개수", "COUNT(DISTINCT dept)": "서로 다른 부서의 수",
    "COUNT(sal)": "sal이 NULL이 아닌 행의 수(이 열에는 NULL이 없다)", "COUNT(DISTINCT sal)": "서로 다른 급여 값의 개수",
    "COUNT(dept)": "dept가 NULL이 아닌 행의 수",
}


def t_count_forms(r, i):
    data = rows(r, r.randint(7, 9))
    db = DB([("emp", COLS, data)])
    x = r.choice([0, 0, 300, 350])
    exprs = [["COUNT(*)", "COUNT(bonus)", "COUNT(DISTINCT bonus)"],
             ["COUNT(bonus)", "COUNT(*)", "COUNT(DISTINCT dept)"],
             ["COUNT(DISTINCT bonus)", "COUNT(*)", "COUNT(bonus)"],
             ["COUNT(bonus)", "COUNT(DISTINCT bonus)", "COUNT(DISTINCT dept)"]][i % 4]
    where = f"\nWHERE sal >= {x}" if x else ""
    fm = "SELECT {e}\nFROM emp" + where + ";"
    query = fm.format(e=", ".join(exprs))
    muts = swap_muts(fm, exprs, CNT)
    if x:
        muts.append((fm.format(e=", ".join(exprs)).replace(f"WHERE sal >= {x}", ""), "WHERE 조건을 무시하고 전체 행을 세었다."))
        muts.append((query.replace(f">= {x}", f"> {x}"), f"sal >= {x}의 경계값을 제외했다."))
    s = fin(db, query, muts)
    if len(set(s["answer"].split(", "))) < len(exprs):
        return None
    inter = ("SELECT id, dept, bonus, CASE WHEN bonus IS NULL THEN 'NULL' ELSE 'O' END AS bonus_존재 FROM emp"
             + (f" WHERE sal >= {x}" if x else "") + " ORDER BY id")
    s.update(diff=1 if i % 4 < 2 else 2, tags=["COUNT", "NULL", "DISTINCT"], stem=STEM,
             ask="COUNT(*), COUNT(열), COUNT(DISTINCT 열)이 NULL과 중복을 각각 어떻게 다루는지 구별해 세 값을 구하는 문제다.",
             solve=["COUNT(*)는 NULL이 있어도 행 하나를 1로 센다. COUNT(열)은 그 열이 NULL인 행을 건너뛰고, COUNT(DISTINCT 열)은 NULL을 건너뛴 뒤 같은 값을 한 번만 센다. 조건을 통과한 행의 bonus 상태는 다음과 같다.",
                    db.block(inter, "대상 행의 bonus 상태"),
                    f"표에서 행 수, bonus가 NULL이 아닌 행 수, 중복을 제거한 값의 수, 서로 다른 부서 수를 각각 확인해 출력 순서대로 적으면 {s['answer']}이다."],
             tip="COUNT(*)는 '행', COUNT(열)은 '값이 있는 행', COUNT(DISTINCT 열)은 '값이 있는 서로 다른 값'이라고 구분해 읽는다.")
    return s


AGG = {
    "AVG(bonus)": "NULL을 제외한 값들의 평균", "AVG(COALESCE(bonus, 0))": "NULL을 0으로 바꾼 뒤 모든 행으로 구한 평균",
    "SUM(bonus)": "NULL을 제외한 값의 합", "MAX(bonus)": "NULL을 제외한 최댓값", "MIN(bonus)": "NULL을 제외한 최솟값",
    "COUNT(bonus)": "NULL이 아닌 값의 개수", "COUNT(*)": "전체 행 수",
}


def t_avg_null(r, i):
    data = rows(r, r.randint(7, 9), nulls=r.choice([2, 3, 4]))
    db = DB([("emp", COLS, data)])
    exprs = [["AVG(bonus)", "AVG(COALESCE(bonus, 0))"], ["SUM(bonus)", "COUNT(bonus)", "AVG(bonus)"],
             ["AVG(COALESCE(bonus, 0))", "MAX(bonus)", "COUNT(*)"], ["AVG(bonus)", "MIN(bonus)", "SUM(bonus)"]][i % 4]
    fm = "SELECT {e}\nFROM emp;"
    query = fm.format(e=", ".join(exprs))
    muts = swap_muts(fm, exprs, AGG)
    muts.append((fm.format(e=", ".join(exprs)).replace("FROM emp", "FROM emp WHERE bonus IS NOT NULL"), "NULL 행을 먼저 제거한다고 보았다. 집계 함수 자체가 NULL을 건너뛰므로 WHERE 없이도 같은 값이 되는 식이 있고, 달라지는 식은 COALESCE/COUNT(*)뿐이다."))
    s = fin(db, query, muts)
    if len(set(s["answer"].split(", "))) < len(exprs):
        return None
    inter = "SELECT id, bonus, COALESCE(bonus, 0) AS coalesce_0 FROM emp ORDER BY id"
    s.update(diff=2 if i % 4 != 3 else 3, tags=["AVG", "SUM", "NULL", "COALESCE"], stem=STEM,
             ask="집계 함수가 NULL을 건너뛰는 규칙과 COALESCE로 NULL을 0으로 바꿨을 때 평균이 달라지는 점을 구별하는 문제다.",
             solve=["SUM, AVG, MAX, MIN, COUNT(열)은 NULL을 계산에서 제외한다. 특히 AVG(bonus)는 NULL이 아닌 값의 합을 NULL이 아닌 값의 개수로 나눈다. 반면 COALESCE(bonus, 0)은 NULL을 0으로 바꾸어 행 수가 분모에 들어간다. 원본과 변환 값을 나란히 놓으면 다음과 같다.",
                    db.block(inter, "bonus와 COALESCE(bonus, 0)"),
                    f"위 값으로 각 식을 계산해 출력 순서대로 적으면 {s['answer']}이다. NULL이 없는 열이면 두 평균이 같지만 NULL이 있으면 COALESCE 쪽이 작아진다."],
             tip="NULL이 섞인 열의 평균은 '값이 있는 행끼리의 평균'이다. 분모가 행 수인지 값이 있는 행 수인지가 AVG와 COALESCE 비교의 갈림길이다.")
    return s


def t_empty_set(r, i):
    data = rows(r, r.randint(6, 8))
    db = DB([("emp", COLS, data)])
    depts = sorted({d[2] for d in data})
    absent = "인사" if "인사" not in depts else "법무"
    kind = i % 3
    if kind == 0:
        exprs, cond = ["COUNT(*)", "SUM(sal)", "MAX(sal)"], f"dept = '{absent}'"
    elif kind == 1:
        exprs, cond = ["COUNT(bonus)", "AVG(bonus)", "MIN(sal)"], f"dept = '{absent}' OR sal > 9999"
    else:
        exprs, cond = ["COUNT(*)", "SUM(bonus)", "COUNT(DISTINCT dept)"], f"sal < 0"
    fm = "SELECT {e}\nFROM emp\nWHERE " + cond + ";"
    query = fm.format(e=", ".join(exprs))
    cands = {"COUNT(*)": "행 수", "SUM(sal)": "급여 합", "MAX(sal)": "최고 급여", "COUNT(bonus)": "보너스 있는 행 수", "AVG(bonus)": "보너스 평균",
             "MIN(sal)": "최저 급여", "SUM(bonus)": "보너스 합", "COUNT(DISTINCT dept)": "부서 종류 수", "AVG(sal)": "급여 평균", "MIN(bonus)": "최저 보너스"}
    muts = swap_muts(fm, exprs, cands)
    zero = [e if e.startswith("COUNT") else f"COALESCE({e}, 0)" for e in exprs]
    allnull = ["MAX(id)" if e.startswith("COUNT") else e for e in exprs]
    allzero = [f"COALESCE({e}, 0)" for e in exprs]
    muts += [
        (fm.format(e=", ".join(["1" if e.startswith("COUNT") else e for e in exprs])), "결과 한 행이 있으므로 COUNT가 1이라고 보았다. COUNT는 집계 대상 행의 수라서 0이다."),
        (fm.format(e=", ".join(allzero)), "모든 집계 결과가 0이라고 보았다. COUNT만 0이고 나머지 집계는 NULL이다."),
        (fm.format(e=", ".join(zero)), "합계·평균·최댓값이 0이라고 보았다. 빈 집합에서 SUM·AVG·MAX·MIN은 0이 아니라 NULL이다."),
        (fm.format(e=", ".join(allnull)), "COUNT도 NULL이라고 보았다. 빈 집합에서도 COUNT는 0을 반환한다."),
        (fm.format(e=", ".join(exprs)).replace("FROM emp", "FROM emp GROUP BY dept"), "집계 질의는 조건에 맞는 행이 없으면 결과 행도 없다고 보았다. GROUP BY가 없으면 빈 집합에서도 1행이 나온다."),
        ("SELECT " + ", ".join(exprs) + " FROM emp WHERE " + cond + " HAVING COUNT(*) > 0;", "결과를 한 행도 반환하지 않는다고 보았다."),
    ] + [(fm.format(e=", ".join(exprs)).replace(cond, "1 = 1"), "WHERE 조건을 무시하고 전체 행을 집계했다."),
             (fm.format(e=", ".join(exprs)).replace("WHERE " + cond, "WHERE " + cond.replace(absent, depts[0]).replace("sal > 9999", "sal > 0").replace("sal < 0", "sal > 0")), "조건에 해당하는 행이 있다고 보고 계산했다.")]
    s = fin(db, query, muts)
    if "NULL" not in s["answer"]:
        return None
    s.update(diff=[2, 3, 3][kind], tags=["집계 함수", "NULL", "빈 집합"], stem=STEM,
             ask="조건에 맞는 행이 하나도 없을 때 COUNT는 0이고 SUM/AVG/MAX/MIN은 NULL이 되는 규칙을 묻는다.",
             solve=[f"WHERE {cond}을 통과하는 행이 없으므로 집계 대상이 빈 집합이다. 집계 함수만 있는 SELECT는 GROUP BY가 없으면 항상 한 행을 반환한다. 그 한 행에서 COUNT 계열은 0이고, SUM·AVG·MAX·MIN은 계산할 값이 없어 NULL이다.",
                    db.block(f"SELECT COUNT(*) AS 통과_행수 FROM emp WHERE {cond}", "조건 통과 행 수"),
                    f"따라서 출력 순서대로 {s['answer']}이다. 행이 0개인 것과 결과 행이 0개인 것은 다르다. 이 질의는 집계 결과 한 행을 반환한다."],
             tip="집계만 있는 SELECT는 대상이 비어도 결과가 1행이다. COUNT는 0, 나머지는 NULL로 읽는다.")
    return s


def t_group_count(r, i):
    data = rows(r, r.randint(8, 10), nulls=r.choice([3, 4]))
    db = DB([("emp", COLS, data)])
    exprs = [["COUNT(*)", "COUNT(bonus)"], ["COUNT(bonus)", "SUM(bonus)"], ["COUNT(*) - COUNT(bonus)", "COUNT(DISTINCT bonus)"]][i % 3]
    fm = "SELECT dept, {e}\nFROM emp\nGROUP BY dept\nORDER BY dept;"
    query = fm.format(e=", ".join(exprs))
    cands = {"COUNT(*)": "그룹의 행 수", "COUNT(bonus)": "bonus가 NULL이 아닌 행의 수", "SUM(bonus)": "NULL을 제외한 bonus 합",
             "COUNT(DISTINCT bonus)": "bonus의 서로 다른 값 수", "COUNT(*) - COUNT(bonus)": "bonus가 NULL인 행의 수", "AVG(bonus)": "NULL을 제외한 bonus 평균",
             "MAX(bonus)": "bonus 최댓값", "COUNT(DISTINCT sal)": "급여의 서로 다른 값 수"}
    muts = swap_muts(fm, exprs, cands)
    muts.append((query.replace("ORDER BY dept", "ORDER BY dept DESC"), "정렬을 내림차순으로 읽었다."))
    s = fin(db, query, muts)
    if not differs(s, 1) or s["answer"] == s["wrong"][0][0]:
        return None
    g = "SELECT dept, COUNT(*) AS rows_cnt, COUNT(bonus) AS bonus_cnt, SUM(bonus) AS bonus_sum, COUNT(DISTINCT bonus) AS bonus_kinds FROM emp GROUP BY dept ORDER BY dept"
    s.update(diff=2 if i % 3 != 2 else 3, tags=["GROUP BY", "COUNT", "NULL"], stem=STEM,
             ask="부서별로 묶은 뒤 COUNT(*)와 COUNT(열)이 NULL 때문에 달라지는 값을 구하는 문제다.",
             solve=["부서별 그룹 안에서 COUNT(*)는 모든 행을, COUNT(bonus)와 SUM(bonus)는 NULL이 아닌 값만 대상으로 한다. 아래 표는 그룹별 기본 집계다.",
                    db.block(g, "부서별 집계 중간 결과"),
                    f"SELECT 목록의 식을 이 표에서 골라 적으면 {s['answer']}이다. COUNT(*) − COUNT(bonus)는 bonus가 NULL인 행의 수를 간접적으로 구하는 관용구다."],
             tip="그룹 안의 NULL 개수는 COUNT(*) − COUNT(열)로 구한다. 표에서 NULL 칸을 직접 세어 검산하면 된다.")
    return s


PLAN = [(t_count_forms, 4), (t_avg_null, 4), (t_empty_set, 3), (t_group_count, 3)]


def generate():
    return run_plan(FAM, TOPIC, SRC, PLAN)
