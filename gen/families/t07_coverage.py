"""Coverage criteria on tiny programs: minimum test sets found by brute force (no short-circuit assumed)."""
from __future__ import annotations

from itertools import combinations, product

from families._t07kit import q

TOPIC = "구조 커버리지"
KO = {"stmt": "구문 커버리지", "branch": "결정(분기) 커버리지", "cond": "조건 커버리지",
      "cd": "조건/결정 커버리지", "mcdc": "변경 조건/결정 커버리지(MC/DC)", "mcc": "다중 조건 커버리지"}

# node: ("s", name) | ("if", expr, then_nodes, else_nodes)
PROGS = {
    "p1": [("if", "A and B", [("s", "S1")], [("s", "S2")])],
    "p1t": [("if", "A and B", [("s", "S1")], [])],
    "p2": [("if", "A or B", [("s", "S1")], [("s", "S2")])],
    "p3": [("if", "A and B", [("s", "S1")], []), ("if", "C", [("s", "S2")], [])],
    "p4": [("if", "A", [("if", "B", [("s", "S1")], [("s", "S2")])], [("s", "S3")])],
    "p5": [("if", "(A and B) or C", [("s", "S1")], [("s", "S2")])],
    "p6": [("if", "A and (B or C)", [("s", "S1")], [("s", "S2")])],
    "p8": [("if", "A or B", [("s", "S1")], [("s", "S2")]), ("if", "A and C", [("s", "S3")], [])],
    "p10": [("if", "(A or B) and (C or D)", [("s", "S1")], [("s", "S2")])],
}


def render(nodes, ind=0):
    pad = "    " * ind
    out = []
    for nd in nodes:
        if nd[0] == "s":
            out.append(f"{pad}{nd[1]};")
        else:
            e = nd[1].replace(" and ", " && ").replace(" or ", " || ")
            if nd[3]:
                out.append(f"{pad}if ({e}) {{")
                out += render(nd[2], ind + 1)
                out.append(f"{pad}}} else {{")
                out += render(nd[3], ind + 1)
                out.append(f"{pad}}}")
            else:
                out.append(f"{pad}if ({e}) {{")
                out += render(nd[2], ind + 1)
                out.append(f"{pad}}}")
    return out


def code_text(key):
    return "\n".join(render(PROGS[key]))


def varsof(expr):
    return sorted({c for c in expr if c.isalpha() and c.isupper()})


def decisions(nodes, acc=None):
    acc = [] if acc is None else acc
    for nd in nodes:
        if nd[0] == "if":
            acc.append(nd[1])
            decisions(nd[2], acc)
            decisions(nd[3], acc)
    return acc


def stmts(nodes, acc=None):
    acc = set() if acc is None else acc
    for nd in nodes:
        if nd[0] == "s":
            acc.add(nd[1])
        else:
            stmts(nd[2], acc)
            stmts(nd[3], acc)
    return acc


def run(nodes, env, trace):
    for nd in nodes:
        if nd[0] == "s":
            trace["stmts"].add(nd[1])
        else:
            res = bool(eval(nd[1].replace("and", " and ").replace("or", " or "), {}, dict(env)))
            vs = varsof(nd[1])
            trace["dec"].append((nd[1], res, tuple(env[v] for v in vs)))
            run(nd[2] if res else nd[3], env, trace)


def traces(prog, tests, names):
    out = []
    for t in tests:
        env = dict(zip(names, t))
        tr = {"stmts": set(), "dec": []}
        run(prog, env, tr)
        out.append((env, tr))
    return out


def satisfied(prog, tests, names):
    trs = traces(prog, tests, names)
    allst = stmts(prog)
    decs = decisions(prog)
    got = set().union(*[tr["stmts"] for _, tr in trs]) if trs else set()
    res = {}
    res["stmt"] = got == allst
    outcomes = {(d, o) for _, tr in trs for d, o, _ in tr["dec"]}
    res["branch"] = all((d, o) in outcomes for d in set(decs) for o in (True, False))
    cond_seen = set()
    for _, tr in trs:
        for d, o, vals in tr["dec"]:
            for v, val in zip(varsof(d), vals):
                cond_seen.add((d, v, val))
    res["cond"] = all((d, v, b) in cond_seen for d in set(decs) for v in varsof(d) for b in (True, False))
    res["cd"] = res["cond"] and res["branch"]
    combo = {(d, vals) for _, tr in trs for d, o, vals in tr["dec"]}
    res["mcc"] = all((d, vals) in combo for d in set(decs) for vals in product([True, False], repeat=len(varsof(d))))
    mc = True
    for d in set(decs):
        vs = varsof(d)
        rows = [(vals, o) for _, tr in trs for dd, o, vals in tr["dec"] if dd == d]
        for i in range(len(vs)):
            ok = False
            for (v1, o1), (v2, o2) in combinations(rows, 2):
                if o1 != o2 and all((a == b) == (j != i) for j, (a, b) in enumerate(zip(v1, v2))):
                    ok = True
                    break
            mc = mc and ok
    res["mcdc"] = mc
    return res


def minimum(key, crit):
    prog = PROGS[key]
    names = sorted({v for d in decisions(prog) for v in varsof(d)})
    universe = list(product([True, False], repeat=len(names)))
    for size in range(1, len(universe) + 1):
        for sub in combinations(universe, size):
            if satisfied(prog, sub, names)[crit]:
                return size
    raise ValueError


def min_q(n, key, crit, diff, note_extra=""):
    prog = PROGS[key]
    names = sorted({v for d in decisions(prog) for v in varsof(d)})
    vals = {c: minimum(key, c) for c in KO}
    right = vals[crit]
    k = len(names)
    wrong = []
    for c in KO:
        if c != crit:
            wrong.append((str(vals[c]), f"{KO[c]}의 최소 케이스 수({vals[c]})를 답했다. 문제가 묻는 기준은 {KO[crit]}이다."))
    wrong += [(str(2 ** k), f"조건 {k}개의 모든 조합 2^{k}를 답했다. 요구한 기준에 필요한 만큼만 고르면 된다."),
              (str(k + 1), "MC/DC의 일반식 n+1을 이 기준에도 적용했다."),
              (str(k), "조건 수를 케이스 수로 착각했다."),
              (str(2 * k), "조건마다 참/거짓 케이스를 따로 만든 값이다. 한 케이스가 여러 조건을 동시에 만족시킬 수 있다."),
              (str(len(decisions(prog)) * 2), "결정의 결과(참/거짓) 수를 케이스 수로 답했다. 한 케이스가 여러 결정을 동시에 지난다.")]
    code = code_text(key)
    dec_txt = "단락(short-circuit) 평가 없이 모든 조건이 평가된다고 가정한다. 조건 변수 " + ", ".join(names) + "는 독립적인 입력이다."
    assume = {"mcdc": " 각 조건이 결정 결과를 독립적으로 바꾸는 쌍이 시험 집합 안에 있어야 한다.",
              "mcc": " 결정마다 조건 값의 모든 조합이 나와야 한다.",
              "cond": " 각 조건이 참과 거짓을 한 번씩 갖기만 하면 되고 결정 결과는 따지지 않는다.",
              "cd": " 조건 커버리지와 결정 커버리지를 동시에 만족해야 한다.",
              "branch": " 결정마다 참과 거짓이 모두 나와야 한다.",
              "stmt": " 모든 문장이 한 번 이상 실행되어야 한다."}[crit]
    stem = f"다음 코드에서 {KO[crit]}를 만족하는 시험 케이스 집합의 최소 크기는? {dec_txt}"
    solve = [f"{KO[crit]}의 정의:{assume} 입력은 {', '.join(names)}의 참/거짓 조합이고 전체 조합은 {2 ** k}개다.",
             {"table": {"caption": "같은 코드에서 기준별 최소 케이스 수", "columns": ["기준", "최소 케이스 수"],
                        "rows": [[KO[c], vals[c]] for c in KO]}},
             f"가능한 조합을 부분집합으로 줄여 가며 확인하면 {KO[crit]}를 만족하는 최소 크기는 {right}이다. "
             f"기준이 강할수록 필요한 케이스 수가 늘거나 같다(구문 ≤ 결정 ≤ 조건/결정 ≤ MC/DC ≤ 다중 조건 순)."]
    return q(f"t07-cover-{n:02d}", TOPIC, stem,
             (str(right), f"{KO[crit]}를 만족하는 가장 작은 시험 집합의 크기가 {right}이다."),
             wrong, f"코드의 결정·조건 구조에서 {KO[crit]}의 최소 시험 케이스 수를 구한다.",
             solve, "구문은 문장, 결정은 결과, 조건은 개별 조건 값, MC/DC는 조건별 독립 영향 쌍, 다중 조건은 모든 조합을 본다. 먼저 어떤 기준인지부터 확정한다.",
             diff, tags=["커버리지", KO[crit]], code={"lang": "c", "text": code}, pad=right)


STRONG = ["stmt", "branch", "cond", "cd", "mcdc", "mcc"]


def strongest_q(n, key, tests, answer_crit, diff):
    prog = PROGS[key]
    names = sorted({v for d in decisions(prog) for v in varsof(d)})
    sat = satisfied(prog, tests, names)
    labels = ["구문 커버리지", "결정(분기) 커버리지", "조건 커버리지", "조건/결정 커버리지", "변경 조건/결정 커버리지(MC/DC)",
              "다중 조건 커버리지", "데이터 흐름 커버리지", "함수 커버리지", "호출 커버리지", "루프 커버리지"]
    wrong = []
    for c in STRONG:
        if c == answer_crit:
            continue
        if sat[c]:
            note = f"이 시험 집합이 {KO[c]}도 만족하는 것은 맞지만, 문제는 만족하는 기준 중 가장 강한 것을 묻는다. 더 강한 {KO[answer_crit]}도 만족한다."
        else:
            note = f"이 시험 집합은 {KO[c]}의 요구를 채우지 못한다. 필요한 값 또는 조합이 집합에 없다."
        wrong.append((KO[c], note))
    wrong += [("데이터 흐름 커버리지", "변수의 정의-사용(def-use) 쌍을 덮는 기준이다. 이 코드에는 값을 정의하고 사용하는 변수 쌍이 없어 판단 대상이 아니며, 조건·결정 구성의 강도를 나타내지도 않는다."),
              ("함수 커버리지", "함수가 호출되었는지만 보는 기준이다. 코드 내부의 조건·결정 구성을 구분하지 않는다."),
              ("호출 커버리지", "함수/메서드 호출 지점의 실행을 보는 기준이다. 이 코드의 결정 구조와 관련이 없다."),
              ("루프 커버리지", "반복 횟수(0회·1회·여러 회)를 보는 기준이다. 이 코드에는 반복문이 없다.")]
    code = code_text(key)
    rows = [[f"T{i + 1}"] + ["참" if v else "거짓" for v in t] for i, t in enumerate(tests)]
    desc = "; ".join(f"T{i + 1}(" + ", ".join(f"{nm}={'참' if v else '거짓'}" for nm, v in zip(names, t)) + ")" for i, t in enumerate(tests))
    stem = (f"다음 코드를 {len(tests)}개의 시험 데이터 {desc}로 실행한다. 단락 평가 없이 모든 조건이 평가된다고 할 때, 이 집합이 만족하는 구조 커버리지 중 가장 강한 기준은?")
    solve = [f"각 시험 데이터를 코드에 대입해 실행 문장, 결정 결과, 조건 값을 기록한다. 입력 변수는 {', '.join(names)}이다.",
             {"table": {"caption": "기준별 만족 여부", "columns": ["기준", "만족"], "rows": [[KO[c], "예" if sat[c] else "아니오"] for c in STRONG]}},
             f"만족하는 기준 중 포함 관계(구문 < 결정 < 조건/결정 < MC/DC < 다중 조건)에서 가장 강한 것은 {KO[answer_crit]}이다. "
             "조건 커버리지와 결정 커버리지는 서로 포함하지 않으므로 둘 중 하나만 만족하는 경우도 있다."]
    return q(f"t07-cover-{n:02d}", TOPIC, stem,
             (KO[answer_crit], f"주어진 시험 집합을 실행해 보면 {KO[answer_crit]}까지 만족하고 그보다 강한 기준은 채우지 못한다."),
             wrong, "시험 집합을 코드에 대입해 만족하는 커버리지 기준 중 가장 강한 것을 판단한다.",
             solve, "시험 데이터를 코드에 직접 대입해 문장·결과·조건 값을 표로 적고, 기준별 요구(결과, 조건 값, 독립 영향 쌍, 전 조합)를 대조한다.",
             diff, tags=["커버리지"], code={"lang": "c", "text": code},
             tables=[{"caption": "시험 데이터", "columns": ["케이스"] + names, "rows": rows}])


def generate():
    T, F = True, False
    out = [
        min_q(1, "p1", "stmt", 1), min_q(2, "p2", "branch", 1), min_q(3, "p1", "cond", 2),
        min_q(4, "p1", "cd", 2), min_q(5, "p1", "mcdc", 2), min_q(6, "p1", "mcc", 1),
        min_q(7, "p4", "stmt", 2), min_q(8, "p4", "branch", 2), min_q(9, "p5", "mcdc", 3),
        min_q(10, "p6", "mcc", 2), min_q(11, "p3", "branch", 2), min_q(12, "p8", "mcdc", 3),
        min_q(13, "p10", "mcdc", 3),
        strongest_q(14, "p1", [(T, F), (F, T)], "cond", 3),
        strongest_q(15, "p1", [(T, T), (F, F)], "cd", 2),
        strongest_q(16, "p1", [(T, T), (T, F), (F, T)], "mcdc", 3),
        strongest_q(17, "p1t", [(T, T)], "stmt", 2),
    ]
    return out
