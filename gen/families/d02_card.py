"""Area 02: degree/cardinality arithmetic and update/insert/delete anomalies on a shown table.

card: result degree and cardinality of relational operators (product, FK join, union
bounds, ...). anomaly: rows to update for a redundant fact, which fact disappears when
a row is deleted, and total rows after decomposition.
"""
from __future__ import annotations

from core import rng
from families._d02kit import q
from families.d02_ra import num_choices, tbl, uniq

SOURCES = ["sinagong-5-7", "itpasslab-2-3"]


def pair_choices(ans, deg_opts, card_opts):
    """deg_opts/card_opts: [(value, note)] with the right value first."""
    (dv, dn), (cv, cn) = deg_opts[0], card_opts[0]
    out = []
    for dv2, dn2 in deg_opts:
        for cv2, cn2 in card_opts:
            if (dv2, cv2) == (dv, cv):
                continue
            notes = []
            if dv2 != dv:
                notes.append(f"차수 {dv2}: {dn2}")
            if cv2 != cv:
                notes.append(f"카디널리티 {cv2}: {cn2}")
            out.append((f"차수 {dv2}, 카디널리티 {cv2}", " ".join(notes), (dv2 != dv) + (cv2 != cv)))
    out.sort(key=lambda t: (t[2], t[0]))
    return [(t, n) for t, n, _ in out]


def gen_card():
    out = []
    plan = [
        ("product", 4, 3, 5, 6), ("product", 3, 6, 4, 5), ("product", 5, 8, 2, 4),
        ("fkjoin", 4, 9, 3, 5), ("fkjoin", 5, 12, 4, 6),
        ("union_max", 3, 7, 3, 5), ("union_min", 4, 6, 4, 9),
        ("inter_max", 3, 8, 3, 5), ("diff_max", 4, 7, 4, 3), ("proj_max", 6, 10, 2, 0),
    ]
    for n, (kind, d1, c1, d2, c2) in enumerate(plan, 1):
        if kind == "product":
            tgt = "R × S의 차수와 카디널리티"
            deg = [(d1 + d2, f"카티션 곱의 차수는 속성 수의 합이다."), (d1 * d2, "차수를 곱했다. 곱해지는 것은 튜플 수이고 속성 수는 더한다."),
                   (max(d1, d2), "더 큰 쪽 차수만 썼다."), (d1 + d2 - 1, "공통 속성이 하나 겹친다고 보고 1을 뺐다. 곱에서는 속성을 합치지 않는다.")]
            card = [(c1 * c2, "카티션 곱의 카디널리티는 튜플 수의 곱이다."), (c1 + c2, "튜플 수를 더했다. 곱은 모든 쌍을 만든다."),
                    (max(c1, c2), "더 큰 쪽 튜플 수만 썼다."), (c1 * c2 - c1, "일부 쌍이 제외된다고 보았다.")]
            tcond = f"R은 차수 {d1}, 카디널리티 {c1}이고 S는 차수 {d2}, 카디널리티 {c2}이다."
            why = f"차수 = {d1}+{d2} = {d1 + d2}, 카디널리티 = {c1}×{c2} = {c1 * c2}"
            diff = 1 if n == 1 else 2
        elif kind == "fkjoin":
            tgt = "R ⋈ S의 차수와 카디널리티"
            tcond = (f"R(주문)은 차수 {d1}, 카디널리티 {c1}이고 S(고객)는 차수 {d2}, 카디널리티 {c2}이다. 두 릴레이션의 공통 속성은 고객번호 하나이고, "
                     "S의 기본키이며 R의 외래키(NOT NULL, 참조 무결성 유지)이다.")
            deg = [(d1 + d2 - 1, "자연 조인은 공통 속성을 한 번만 남기므로 속성 수의 합에서 공통 속성 수를 뺀다."), (d1 + d2, "공통 속성이 결과에 두 번 나온다고 보았다. 자연 조인은 한 번만 남긴다."),
                   (max(d1, d2), "더 큰 차수만 썼다."), (d1 * d2, "차수를 곱했다.")]
            card = [(c1, "외래키가 NOT NULL이고 참조 무결성이 유지되므로 R의 각 튜플은 S의 기본키 값 하나와 정확히 짝이 된다. 결과는 R의 튜플 수와 같다."), (c1 * c2, "카티션 곱 크기다. 조인은 값이 같은 쌍만 남긴다."),
                    (c2, "S의 튜플 수를 썼다. 결과 행은 주문(R)마다 하나씩 생긴다."), (c1 + c2, "튜플 수를 더했다.")]
            why = f"차수 = {d1}+{d2}−1 = {d1 + d2 - 1}, 카디널리티 = R의 튜플 수 {c1}"
            diff = 2
        elif kind == "union_max":
            tgt = "R ∪ S의 차수와 가능한 최대 카디널리티"
            tcond = f"R과 S는 합병 가능하며 차수는 {d1}이다. R의 카디널리티는 {c1}, S는 {c2}이다."
            deg = [(d1, "합병 가능한 릴레이션의 합집합은 스키마가 같아 차수가 그대로다."), (d1 * 2, "차수가 두 배가 된다고 보았다. 합집합은 열을 늘리지 않고 행을 합친다."), (d1 + 1, "결과에 식별 열이 추가된다고 보았다.")]
            card = [(c1 + c2, "공통 튜플이 전혀 없을 때 최대가 된다."), (max(c1, c2), "공통 튜플이 최대로 겹칠 때의 최솟값이다."), (c1 * c2, "곱했다."), (c1 + c2 - 1, "한 튜플은 반드시 겹친다고 보았다. 겹침이 없는 경우도 가능하다.")]
            why = f"차수는 {d1} 그대로, 카디널리티 최댓값은 겹침이 없을 때 {c1}+{c2} = {c1 + c2}"
            diff = 2
        elif kind == "union_min":
            tgt = "R ∪ S의 차수와 가능한 최소 카디널리티"
            tcond = f"R과 S는 합병 가능하며 차수는 {d1}이다. R의 카디널리티는 {c1}, S는 {c2}이다."
            deg = [(d1, "합병 가능한 릴레이션의 합집합은 스키마가 같아 차수가 그대로다."), (d1 * 2, "차수가 두 배가 된다고 보았다."), (d1 + 1, "결과에 식별 열이 추가된다고 보았다.")]
            card = [(max(c1, c2), "작은 쪽이 큰 쪽에 완전히 포함될 때 최소가 된다."), (min(c1, c2), "작은 쪽만 남는다고 보았다. 합집합은 큰 쪽 튜플을 모두 포함하므로 큰 쪽보다 작아질 수 없다."), (c1 + c2, "겹침이 없을 때의 최댓값이다."), (c1 * c2, "튜플 수를 곱했다. 합집합은 쌍을 만들지 않는다.")]
            why = f"차수 {d1}, 카디널리티 최솟값은 작은 쪽이 큰 쪽의 부분집합일 때 max({c1},{c2}) = {max(c1, c2)}"
            diff = 3
        elif kind == "inter_max":
            tgt = "R ∩ S의 차수와 가능한 최대 카디널리티"
            tcond = f"R과 S는 합병 가능하며 차수는 {d1}이다. R의 카디널리티는 {c1}, S는 {c2}이다."
            deg = [(d1, "교집합도 스키마가 같아 차수가 그대로다."), (d1 * 2, "차수가 늘어난다고 보았다."), (d1 + 1, "열이 하나 추가된다고 보았다.")]
            card = [(min(c1, c2), "작은 쪽이 큰 쪽에 완전히 포함될 때 최대가 된다."), (max(c1, c2), "큰 쪽 튜플 수는 교집합보다 클 수 있다."), (c1 + c2, "합집합의 최댓값이다."), (0, "겹침이 없을 때의 최솟값이다.")]
            why = f"차수 {d1}, 교집합 최대는 작은 쪽 전체가 겹칠 때 min({c1},{c2}) = {min(c1, c2)}"
            diff = 2
        elif kind == "diff_max":
            tgt = "R − S의 차수와 가능한 최대 카디널리티"
            tcond = f"R과 S는 합병 가능하며 차수는 {d1}이다. R의 카디널리티는 {c1}, S는 {c2}이다."
            deg = [(d1, "차집합도 스키마가 같아 차수가 그대로다."), (d1 * 2, "차수가 늘어난다고 보았다."), (d1 + 1, "열이 하나 추가된다고 보았다.")]
            card = [(c1, "S와 겹치는 튜플이 없을 때 R의 튜플이 모두 남아 최대가 된다."), (c1 - c2, "S의 튜플이 모두 R에 있다고 가정한 최솟값이다."), (c2, "S의 튜플 수를 썼다. 결과는 R에서 나온다."), (c1 + c2, "합집합의 최댓값을 썼다.")]
            why = f"차수 {d1}, R−S의 최댓값은 겹침이 없을 때 R 전체인 {c1}"
            diff = 2
        else:
            tgt = "π_(R의 앞 2개 열)(R)"
            tcond = f"R은 차수 {d1}, 카디널리티 {c1}이다."
            deg = [(2, "두 열만 남기므로 차수는 2다."), (d1, "원래 차수를 그대로 썼다."), (d1 - 2, "남기는 열이 아니라 버리는 열의 수를 썼다."), (d1 + 2, "열이 늘어난다고 보았다.")]
            card = [(c1, "중복이 전혀 없을 때 최대 카디널리티는 원래와 같다."), (1, "중복이 모두 합쳐질 때의 최솟값이다."), (c1 * 2, "행이 늘어난다고 보았다."), (c1 - 2, "행이 줄어든다고 단정해 둘을 뺐다.")]
            why = f"차수는 2, 카디널리티 최댓값은 중복이 없을 때 {c1}"
            diff = 3
            tgt = "R의 앞 두 열만 투영한 결과의 차수와 가능한 최대 카디널리티"
        if len(deg) < 4:
            deg.append((d1 - 1, "연산 과정에서 열이 하나 사라진다고 보았다. 집합 연산은 열을 줄이지 않는다."))
        d0, c0 = deg[0][0], card[0][0]
        ans = f"차수 {d0}, 카디널리티 {c0}"
        cands = pair_choices(ans, deg, card)
        if len(cands) < 9:
            raise RuntimeError(f"card {n}")
        out.append(q(
            id=f"d02-card-{n:02d}", label=2, difficulty=diff, topic="차수(degree)와 카디널리티(cardinality)",
            tags=["관계형 모델", "차수", "카디널리티", "관계 대수"],
            stem=f"{tcond} {tgt}를 (차수, 카디널리티) 순서로 구한 것은?",
            answer=(ans, why + "이다."),
            distractors=cands[:11],
            ask="차수는 속성(열) 수, 카디널리티는 튜플(행) 수이다. 연산이 열을 합치는지, 행을 늘리는지 줄이는지로 두 값을 따로 계산한다.",
            solve=[f"{tcond}", f"계산: {why}.",
                   "카티션 곱은 열을 이어 붙이고 모든 쌍을 만들기에 차수는 합, 카디널리티는 곱이다. 자연 조인은 공통 속성을 한 번만 남기고 값이 같은 쌍만 남긴다. 집합 연산은 스키마가 같아 차수가 변하지 않고 겹침 정도에 따라 카디널리티가 범위를 가진다.",
                   "범위를 묻는 문제는 겹침이 전혀 없는 경우와 완전히 포함되는 경우, 두 극단을 각각 계산해 최댓값·최솟값을 고른다."],
            tip="차수 = 열 수(스키마), 카디널리티 = 행 수(인스턴스). 연산이 스키마를 바꾸는지와 행 수를 바꾸는지를 분리해서 계산한다.",
            family="d02-card", source_ideas=SOURCES))
    return out


# --------------------------------------------------------------------- anomaly
DEPT_HEAD = {"컴퓨터": "정교수", "경영": "한교수", "디자인": "오교수", "수학": "서교수"}
STUDENTS = ["김하늘", "이도윤", "박서연", "최민준", "정지우", "한예린", "오세훈", "윤하준"]
COURSES = {"DB": 3, "OS": 3, "통계": 2, "회계": 3, "드로잉": 2}
HOME = {"컴퓨터": ["DB", "OS"], "경영": ["회계", "통계"], "디자인": ["드로잉", "통계"], "수학": ["통계", "DB"]}


def reg_rows(r, n):
    depts = r.sample(list(DEPT_HEAD), 3)
    studs = r.sample(STUDENTS, 5)
    sd = {s_: r.choice(depts) for s_ in studs}
    rows = []
    for s_ in studs:
        for c in r.sample(HOME[sd[s_]], r.choice([1, 2])):
            rows.append((s_, sd[s_], DEPT_HEAD[sd[s_]], c, COURSES[c]))
    return rows


REG_COLS = ["학생", "학과", "학과장", "과목", "학점"]


def gen_anomaly():
    out = []
    # (a) update anomaly: number of rows to change
    for n in range(1, 4):
        r = rng(f"d02-anomaly-upd-{n}")
        for _ in range(300):
            rows = reg_rows(r, 9)
            cnt = {}
            for x in rows:
                cnt[x[1]] = cnt.get(x[1], 0) + 1
            d = max(cnt, key=lambda k: (cnt[k], k))
            if cnt[d] >= 3 and len(rows) >= 7:
                break
        ans = cnt[d]
        n_stu = len({x[0] for x in rows if x[1] == d})
        mist = [(1, "학과장 정보가 학과 테이블에 한 번만 저장되어 있다고 보았다. 이 표에서는 수강 행마다 학과장이 반복 저장되어 있다."),
                (n_stu, "학과 학생 수를 셌다. 학생이 두 과목을 들으면 행이 두 개라 학생 수만큼만 고치면 일부 행이 옛 값으로 남는다."),
                (len(rows), "모든 행을 고쳐야 한다고 보았다. 다른 학과의 행은 학과장이 달라 건드릴 필요가 없다."),
                (len({x[3] for x in rows if x[1] == d}), "그 학과 학생이 듣는 서로 다른 과목 수를 셌다."),
                (len(rows) - cnt[d], "다른 학과 행의 수를 셌다.")]
        out.append(q(
            id=f"d02-anomaly-upd-{n:02d}", label=2, difficulty=2 if n < 3 else 3,
            topic="이상 현상: 갱신 이상", tags=["정규화", "이상 현상", "갱신 이상"],
            stem=f"다음 표는 학생의 수강 정보를 하나의 릴레이션 REG(학생, 과목)에 저장한 것이다. {d}학과의 학과장이 '{DEPT_HEAD[d]}'에서 '신임교수'로 바뀌어 데이터를 일관되게 수정하려면, UPDATE로 고쳐야 하는 행은 최소 몇 개인가?",
            tables=[tbl("REG", REG_COLS, rows)],
            answer=(str(ans), f"{d}학과 행은 {ans}개이고 모두 같은 학과장 값을 반복 저장하고 있어 전부 고쳐야 일관성이 유지된다."),
            distractors=num_choices(ans, mist, len(rows)),
            ask="학과장 같은 학과의 속성이 수강 행마다 중복 저장된 구조에서, 값 하나를 바꿀 때 영향받는 행 수를 센다. 일부만 고치면 모순이 생기는 갱신 이상을 확인하는 문제다.",
            solve=[f"학과가 '{d}'인 행: " + ", ".join(f"({x[0]},{x[3]})" for x in rows if x[1] == d) + f" → {ans}행.",
                   "학과장은 학과에 종속되는 속성(학과→학과장)인데, 학생·과목이 키인 릴레이션 안에 있어 이행적으로 중복된다. 그래서 값 하나를 바꾸려면 그 학과의 모든 행을 고쳐야 한다.",
                   "일부만 고치면 같은 학과에 학과장이 두 명 기록되는 불일치가 생긴다. 학과 정보를 별도 릴레이션으로 분리하면 한 행만 고치면 된다."],
            tip="중복 저장된 사실의 변경 비용 = 그 사실이 반복된 행 수. 한 곳만 고치면 불일치가 생기는 것이 갱신 이상이다.",
            family="d02-anomaly-upd", source_ideas=SOURCES))
    # (b) delete anomaly: which fact is lost
    for n in range(1, 5):
        r = rng(f"d02-anomaly-del-{n}")
        for _ in range(500):
            rows = reg_rows(r, 9)
            for victim in r.sample(rows, len(rows)):
                s_, d, h, c, cr = victim
                rest = [x for x in rows if x != victim]
                lost = []
                if not any(x[1] == d for x in rest):
                    lost.append(f"{d}학과의 학과장 {h}")
                if not any(x[3] == c for x in rest):
                    lost.append(f"{c} 과목의 학점 {cr}")
                if not any(x[0] == s_ for x in rest):
                    lost.append(f"학생 {s_}의 소속 학과")
                if len(lost) == 1:
                    break
            else:
                continue
            break
        ans = lost[0]
        facts = []
        for x in rows:
            for f, col in ((f"{x[1]}학과의 학과장 {x[2]}", "학과"), (f"{x[3]} 과목의 학점 {x[4]}", "과목"), (f"학생 {x[0]}의 소속 학과", "학생")):
                if f not in facts:
                    facts.append(f)
        cands = []
        for f in facts:
            if f == ans:
                continue
            kept = []
            for x in rest:
                if f in (f"{x[1]}학과의 학과장 {x[2]}", f"{x[3]} 과목의 학점 {x[4]}", f"학생 {x[0]}의 소속 학과"):
                    kept.append(x)
            if kept:
                cands.append((f, f"이 사실은 삭제 뒤에도 남은 행 ({kept[0][0]}, {kept[0][3]})에 다시 저장되어 있어 사라지지 않는다."))
            else:
                cands.append((f, f"삭제하는 행과 무관한 사실이라 이번 삭제의 영향을 받지 않는다."))
        out.append(q(
            id=f"d02-anomaly-del-{n:02d}", label=2, difficulty=2 if n < 3 else 3,
            topic="이상 현상: 삭제 이상", tags=["정규화", "이상 현상", "삭제 이상"],
            stem=f"다음 표 REG에서 학생 '{s_}'의 '{c}' 수강 행 하나를 삭제했다. 이 삭제로 표 전체에서 더 이상 확인할 수 없게 되는 사실은?",
            tables=[tbl("REG", REG_COLS, rows)],
            answer=(ans, f"삭제한 행이 이 사실을 담은 유일한 행이었다. 같은 정보가 다른 행에 없으므로 의도하지 않은 정보 손실이 생긴다."),
            distractors=cands[:11],
            ask="한 행을 지울 때 그 행에만 들어 있던 다른 종류의 사실까지 사라지는 삭제 이상을 찾는 문제다. 각 사실이 다른 행에 중복 저장되어 있는지 확인한다.",
            solve=[f"삭제 대상 행: ({s_}, {d}, {h}, {c}, {cr}). 이 행이 담은 사실은 학생의 소속, 학과장, 과목 학점 세 가지다.",
                   f"남은 행에서 각 사실을 찾아보면 {ans}만 어느 행에도 남지 않는다. 학과·과목·학생 정보를 하나의 표에 섞어 두면 수강 한 건을 지우다 학과나 과목 정보까지 잃는 구조가 된다.",
                   "학생, 학과, 과목을 별도 릴레이션으로 분리하면 수강 기록을 지워도 학과·과목 정보는 그대로 남는다."],
            tip="삭제 이상은 '이 행에만 있던 다른 사실'을 찾는 문제다. 행의 각 속성 조합이 다른 행에도 있는지 하나씩 확인한다.",
            family="d02-anomaly-del", source_ideas=SOURCES))
    # (c) rows after decomposition
    for n in range(1, 4):
        r = rng(f"d02-anomaly-dec-{n}")
        rows = reg_rows(r, 9)
        stu = uniq([(x[0], x[1]) for x in rows])
        dep = uniq([(x[1], x[2]) for x in rows])
        crs = uniq([(x[3], x[4]) for x in rows])
        enr = uniq([(x[0], x[3]) for x in rows])
        total = len(stu) + len(dep) + len(crs) + len(enr)
        mist = [(len(rows), "분해 전 행 수를 그대로 썼다. 분해하면 릴레이션마다 중복이 제거되어 행 수가 달라진다."),
                (len(stu) + len(dep) + len(crs), "수강(학생, 과목) 릴레이션을 빠뜨리고 세 개만 합했다."),
                (len(rows) * 4, "릴레이션 4개가 각각 원래 행 수를 가진다고 보았다."),
                (len(stu) + len(dep) + len(crs) + len(rows) + len(stu), "수강 릴레이션 행 수를 학생 수로 더하는 등 중복 제거 대상을 잘못 골랐다."),
                (len(dep) + len(crs) + len(enr), "학생(학번, 학과) 릴레이션을 빠뜨렸다."),
                (len(stu) + len(dep) + len(crs) + len(enr) + 1, "하나를 더 센 값이다.")]
        out.append(q(
            id=f"d02-anomaly-dec-{n:02d}", label=2, difficulty=3,
            topic="정규화 후 릴레이션 행 수", tags=["정규화", "릴레이션 분해", "카디널리티"],
            stem=("다음 표 REG(학생, 학과, 학과장, 과목, 학점)에는 함수 종속 학생→학과, 학과→학과장, 과목→학점이 성립하고 (학생, 과목)이 기본키이다. "
                  "이를 제3정규형으로 분해해 STUDENT(학생, 학과), DEPT(학과, 학과장), COURSE(과목, 학점), ENROLL(학생, 과목) 네 릴레이션으로 만들 때 네 릴레이션의 튜플 수 합계는?"),
            tables=[tbl("REG", REG_COLS, rows)],
            answer=(str(total), f"STUDENT {len(stu)} + DEPT {len(dep)} + COURSE {len(crs)} + ENROLL {len(enr)} = {total}. 각 릴레이션은 프로젝션으로 만들어지므로 중복이 제거된다."),
            distractors=num_choices(total, mist, len(rows)),
            ask="분해는 각 릴레이션으로의 프로젝션이다. 프로젝션은 중복을 제거하므로, 릴레이션별로 서로 다른 행 수를 세어 합하는 문제다.",
            solve=[f"STUDENT: " + ", ".join(f"{a}/{b}" for a, b in stu) + f" → {len(stu)}행", f"DEPT: " + ", ".join(f"{a}/{b}" for a, b in dep) + f" → {len(dep)}행",
                   f"COURSE: " + ", ".join(f"{a}/{b}" for a, b in crs) + f" → {len(crs)}행", f"ENROLL: {len(enr)}행(원래 수강 행과 같다). 합계 {total}행.",
                   "분해 후 총 행 수가 원본보다 많을 수도 적을 수도 있다. 중복 저장되던 학과·과목 정보는 줄어들지만 릴레이션이 늘면서 수강 행은 그대로 남기 때문이다. 저장 공간과 이상 현상 제거를 맞바꾸는 것이 정규화다."],
            tip="분해 = 프로젝션 여러 번. 릴레이션마다 중복을 제거한 뒤 합산한다. 키 쪽(수강) 릴레이션은 행 수가 변하지 않는다.",
            family="d02-anomaly-dec", source_ideas=SOURCES))
    return out


def generate():
    return gen_card() + gen_anomaly()
