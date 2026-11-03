"""C: integer division, remainder, casts between int and double.

A program prints 3-5 expressions over int a, b, c, n (negative) and double x. Which
expressions appear is the reasoning knob: truncation of int/int, where a cast sits
(before or after the division), remainder sign with a negative dividend, (int) cast
truncation toward zero, left-to-right grouping of / and % at the same precedence.
Each expression carries its own misconceptions; a wrong choice changes exactly the
slot that the named misreading affects.
"""
from __future__ import annotations

import math

from families.c_kit import cdiv, cmod, emit, enough, program, search, trace_table

SOURCES = ["past-2021-2-16", "past-2022-1-14"]
FAM = "c-intdiv"


def f2(v):
    return f"{v:.2f}"


def tie(v):
    t = abs(v) * 100
    return abs(t - math.floor(t) - 0.5) < 1e-6


# key: (C expr, printf spec, true fn, explanation fn, [(wrong fn, note)])
def catalog(e):
    a, b, c, n, x, k = e["a"], e["b"], e["c"], e["n"], e["x"], e["k"]
    return {
        "div": ("a / b", "%d", cdiv(a, b), f"{a} / {b} → 정수끼리 나눗셈이라 소수부를 버림 → {cdiv(a, b)}",
                [(f2(a / b), "a / b를 실수 나눗셈으로 계산했다. 피연산자가 둘 다 int이면 결과도 int이며 소수부는 버려진다."),
                 (str(round(a / b)), "a / b의 몫을 반올림했다. C의 정수 나눗셈은 반올림하지 않고 0 쪽으로 잘라낸다.")]),
        "mod": ("a % b", "%d", cmod(a, b), f"{a} % {b} → {a} = {b}×{cdiv(a, b)} + {cmod(a, b)} → 나머지 {cmod(a, b)}",
                [(str(cdiv(a, b)), "%를 몫으로 읽었다. %는 나눗셈의 나머지를 구한다."),
                 (str(b - cmod(a, b)), "나머지를 '다음 배수까지 남은 양'(b - a % b)으로 계산했다.")]),
        "ndiv": ("n / b", "%d", cdiv(n, b), f"{n} / {b} → C99부터 0 쪽으로 잘라냄 → {cdiv(n, b)}",
                 [(str(n // b), "음수 나눗셈을 내림(바닥 함수)으로 처리했다(파이썬 // 방식). C는 0 쪽으로 잘라내므로 몫의 절댓값이 작아진다."),
                  (str(-cdiv(n, b)), "음수 부호를 놓쳐 |n| / b의 몫을 그대로 썼다.")]),
        "nmod": ("n % b", "%d", cmod(n, b), f"{n} % {b} → 나머지 부호는 피제수(n)를 따름 → {cmod(n, b)}",
                 [(str(n % b), "나머지를 항상 0 이상으로 보는 수학식(파이썬 %) 정의를 썼다. C의 %는 피제수 n의 부호를 따른다."),
                  (str(-cmod(n, b)), "나머지 부호가 제수 b를 따른다고 보아 부호를 뒤집었다.")]),
        "castdiv": ("(double)a / b", "%.2f", a / b, f"a를 먼저 double로 바꾼 뒤 나누므로 실수 나눗셈 → {f2(a / b)}",
                    [(f2(cdiv(a, b)), "캐스트가 나눗셈 결과에 적용된다고 보아 정수 몫을 double로 바꿨다. (double)은 바로 뒤 피연산자 a에만 붙는다.")]),
        "divcast": ("(double)(a / b)", "%.2f", float(cdiv(a, b)),
                    f"괄호 안 a / b가 먼저 정수 나눗셈 {cdiv(a, b)} → 그다음 double로 변환 → {f2(cdiv(a, b))}",
                    [(f2(a / b), "괄호 안 나눗셈이 실수로 계산된다고 보았다. 캐스트는 이미 잘린 정수 몫에 적용된다.")]),
        "mulback": ("a / b * b", "%d", cdiv(a, b) * b, f"(a / b) * b = {cdiv(a, b)} × {b} = {cdiv(a, b) * b}",
                    [(str(a), "a / b * b를 약분해서 a로 보았다. 정수 나눗셈에서 버린 나머지는 곱해도 돌아오지 않는다."),
                     (str(cdiv(a, b * b)), "a / (b * b)로 묶었다. /와 *는 우선순위가 같아 왼쪽부터 계산한다.")]),
        "half": ("1 / 2 * a", "%d", cdiv(1, 2) * a, f"1 / 2 = 0(정수 나눗셈) → 0 × {a} = 0",
                 [(str(cdiv(a, 2)), "1 / 2 * a를 a / 2로 바꿔 읽었다. 왼쪽부터 1 / 2가 먼저 계산되어 0이 된다."),
                  (f2(a / 2), "1 / 2를 0.5로 계산했다. 정수끼리 나누면 0이다.")]),
        "real2": ("a / 2.0", "%.2f", a / 2, f"2.0이 double이라 a가 double로 승격 → {f2(a / 2)}",
                  [(f2(cdiv(a, 2)), "2.0을 정수 2처럼 보아 정수 나눗셈 몫을 썼다. 한쪽이 double이면 실수 나눗셈이 된다.")]),
        "trunc": ("(int)x", "%d", int(x), f"(int){x} → 소수부를 버림 → {int(x)}",
                  [(str(round(x)), "(int) 변환을 반올림으로 보았다. 소수부는 그냥 잘린다.")]),
        "ntrunc": ("(int)-x", "%d", int(-x), f"(int)(-{x}) → 0 쪽으로 잘라냄 → {int(-x)}",
                   [(str(math.floor(-x)), "음수를 (int)로 바꿀 때 내림한다고 보았다. 변환은 0 쪽으로 잘라내므로 절댓값이 작아진다.")]),
        "scale": ("(int)x * k", "%d", int(x) * k, f"캐스트가 먼저: (int){x} = {int(x)} → × {k} = {int(x) * k}",
                  [(str(int(x * k)), "(int)가 x * k 전체에 적용된다고 보았다. 캐스트는 곱셈보다 우선순위가 높아 x에만 붙는다.")]),
        "scale2": ("(int)(x * k)", "%d", int(x * k), f"괄호 먼저: {x} × {k} = {x * k:g} → 소수부 버림 → {int(x * k)}",
                   [(str(int(x) * k), "x를 먼저 정수로 자른 뒤 곱했다. 괄호 때문에 곱셈 결과에 캐스트가 적용된다.")]),
        "divmod": ("a / b % c", "%d", cmod(cdiv(a, b), c),
                   f"/와 %는 같은 우선순위, 왼쪽부터: ({a} / {b}) % {c} = {cdiv(a, b)} % {c} = {cmod(cdiv(a, b), c)}",
                   [(str(cdiv(a, cmod(b, c))) if cmod(b, c) else "0",
                     "b % c를 먼저 계산했다. /와 %는 우선순위가 같으므로 왼쪽의 a / b가 먼저다.")]),
        "modmul": ("a % b * c", "%d", cmod(a, b) * c,
                   f"%와 *는 같은 우선순위, 왼쪽부터: ({a} % {b}) × {c} = {cmod(a, b) * c}",
                   [(str(cmod(a, b * c)), "b * c를 먼저 묶어 a % (b * c)로 계산했다. 같은 우선순위는 왼쪽부터 묶는다.")]),
    }


# (expression keys, difficulty)
SETS = [
    (["div", "mod", "castdiv"], 1), (["div", "real2", "trunc"], 1), (["mod", "divcast", "half"], 1),
    (["div", "mod", "mulback"], 1),
    (["castdiv", "divcast", "mulback", "trunc"], 2), (["ndiv", "nmod", "div", "mod"], 2),
    (["half", "real2", "scale", "scale2"], 2), (["divmod", "modmul", "div", "mod"], 2),
    (["trunc", "ntrunc", "scale2", "castdiv"], 2), (["div", "ndiv", "trunc", "ntrunc"], 2),
    (["ndiv", "nmod", "divcast", "scale", "half"], 3), (["divmod", "modmul", "nmod", "castdiv", "ntrunc"], 3),
    (["mulback", "ndiv", "scale", "scale2", "real2"], 3), (["divmod", "ntrunc", "nmod", "half", "divcast"], 3),
]


def fmt(spec, v):
    return f2(v) if spec == "%.2f" else str(v)


def generate():
    out = []
    for qn, (keys, diff) in enumerate(SETS):
        def attempt(r):
            b = r.randint(3, 7)
            a = r.randint(2 * b + 1, 6 * b)
            if a % b == 0:
                return None
            e = {"a": a, "b": b, "c": r.randint(2, 4), "n": -r.randint(b + 1, 5 * b), "k": r.randint(3, 6),
                 "x": r.randint(20, 99) / 10}
            if e["n"] % b == 0 or e["x"] == int(e["x"]) or e["b"] % e["c"] == 0:
                return None
            cat = catalog(e)
            xk = e["x"] * e["k"]
            if cat["scale"][2] == cat["scale2"][2] or abs(xk - round(xk)) < 1e-6:
                return None
            vals = [fmt(cat[k][1], cat[k][2]) for k in keys]
            if any(tie(cat[k][2]) for k in keys if cat[k][1] == "%.2f"):
                return None
            res = " ".join(vals) + "\n"
            w = []
            for i, k in enumerate(keys):
                for wv, note in cat[k][4]:
                    vv = list(vals)
                    vv[i] = wv
                    w.append((" ".join(vv) + "\n", f"{i + 1}번째 값({cat[k][0]}): {note}"))
            # global misreading: every int/int division treated as real division
            allreal = []
            for k in keys:
                spec = cat[k][1]
                if k in ("div", "divcast"):
                    allreal.append(f2(e["a"] / e["b"]))
                elif k == "ndiv":
                    allreal.append(f2(e["n"] / e["b"]))
                elif k == "half":
                    allreal.append(f2(e["a"] / 2))
                elif k == "mulback":
                    allreal.append(str(e["a"]))
                else:
                    allreal.append(fmt(spec, cat[k][2]))
            w.append((" ".join(allreal) + "\n", "정수끼리의 나눗셈을 모두 실수 나눗셈으로 계산했다(수학식처럼 계산). "
                                                 "int / int는 몫만 남기고 소수부를 버린다."))
            if len(keys) >= 3:
                for i in range(len(keys)):
                    for j in range(i + 1, len(keys)):
                        for wi, ni in cat[keys[i]][4]:
                            for wj, nj in cat[keys[j]][4]:
                                vv = list(vals)
                                vv[i], vv[j] = wi, wj
                                w.append((" ".join(vv) + "\n",
                                          f"두 곳을 함께 잘못 계산했다. {i + 1}번째 값: {ni} {j + 1}번째 값: {nj}"))
            if not enough(res, w):
                return None
            return e, cat, vals, res, w
        e, cat, vals, res, w = search(f"{FAM}-{qn}", attempt)
        uses = set("".join(cat[k][0] for k in keys))
        decl = []
        ints = [v for v in "abcnk" if v in uses]
        if ints:
            decl.append("    int " + ", ".join(f"{v} = {e[v]}" for v in ints) + ";")
        if "x" in uses:
            decl.append(f"    double x = {e['x']};")
        specs = " ".join(cat[k][1] for k in keys)
        args = ", ".join(cat[k][0] for k in keys)
        line = f'    printf("{specs}\\n", {args});'
        if len(line) > 80:
            line = f'    printf("{specs}\\n",\n           {args});'
        code = program(decl + [line])
        rows = [[i + 1, cat[k][0], cat[k][1], cat[k][3], vals[i]] for i, k in enumerate(keys)]
        solve = [
            "printf 인자를 하나씩 계산한다. 규칙은 세 가지다. ① int와 int의 연산 결과는 int이고 나눗셈은 0 쪽으로 잘라낸다. "
            "② 피연산자 중 하나라도 double이면 다른 쪽도 double로 바뀌어 실수 연산을 한다. ③ (자료형) 캐스트는 단항 연산자라 "
            "바로 뒤 피연산자 하나에만 먼저 적용되고, /·%·*는 같은 우선순위로 왼쪽부터 묶인다.",
            trace_table(["순서", "식", "형식", "계산", "출력"], rows, caption="인자별 계산"),
            f"각 값을 공백으로 이어 \"{res.strip()}\"가 출력된다.",
        ]
        out.append(emit(
            qid=f"{FAM}-{qn + 1:02d}", code=code, out=res, solve=solve, wrong=w,
            ask="정수 나눗셈·나머지·형 변환이 섞인 printf 인자 각각의 값을 묻는다. 어느 연산이 int끼리인지, 캐스트가 "
                "언제 적용되는지가 핵심이다.",
            tip="식을 볼 때 먼저 '두 피연산자의 자료형'을 표시한다. int/int면 몫만, 한쪽이 double이면 실수. 캐스트는 괄호가 "
                "없으면 바로 옆 하나에만 붙는다. 음수의 /와 %는 0 쪽 절삭, 나머지 부호는 피제수를 따른다.",
            topic="C 정수 나눗셈·나머지·형 변환", tags=["C", "정수나눗셈", "나머지", "형변환", "캐스트"],
            difficulty=diff, family=FAM, sources=SOURCES,
        ))
    return out
