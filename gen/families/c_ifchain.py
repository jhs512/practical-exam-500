"""C: if / else-if chains, compound conditions, dangling else, short-circuit."""
from __future__ import annotations

import re

from families.c_kit import cev, run_family

FAM = "c-ifchain"


def _prog(body):
    return "\n".join(["#include <stdio.h>", "", "int main(void) {", *body,
                      "    return 0;", "}", ""])


def t_grade(r, k):
    t1, t2, t3 = r.choice([(90, 80, 70), (85, 70, 55), (80, 60, 40), (95, 85, 75)])
    s = r.choice([t1, t2, t3, t1 - 1, t2 - 1, t3 - 1, t1 + 4, t3 - 6, t2 + 3])
    if k == 1:
        s = r.choice([t1 + 3, t2 + 2, t3 + 4, t3 - 5])
    op = ">" if k == 2 else ">="
    if k == 1:
        body = [f"    int s = {s};",
                f"    if (s >= {t1}) printf(\"A\");",
                f"    if (s >= {t2}) printf(\"B\");",
                f"    if (s >= {t3}) printf(\"C\");",
                "    else printf(\"D\");", '    printf("\\n");']
        right = "ABC" if s >= t1 else "BC" if s >= t2 else "C" if s >= t3 else "D"
        intro = (f"s = {s}. 모두 독립된 if라 참인 조건마다 출력된다. 마지막 else는 바로 위 "
                 f"if (s >= {t3})에만 붙는다.")
        rows = [[f"s >= {t1}", "참" if s >= t1 else "거짓", "A" if s >= t1 else "-"],
                [f"s >= {t2}", "참" if s >= t2 else "거짓", "B" if s >= t2 else "-"],
                [f"s >= {t3}", "참" if s >= t3 else "거짓", "C" if s >= t3 else "D(else)"]]
    else:
        body = [f"    int s = {s};", "    char g;",
                f"    if (s {op} {t1}) g = 'A';",
                f"    else if (s {op} {t2}) g = 'B';",
                f"    else if (s {op} {t3}) g = 'C';",
                "    else g = 'D';", '    printf("%c\\n", g);']
        right = "A" if s > t1 - (op == ">=") else "B" if s > t2 - (op == ">=") else \
            "C" if s > t3 - (op == ">=") else "D"
        intro = (f"s = {s}. else if 사슬은 위에서부터 검사해 처음 참인 분기 하나만 실행한다. "
                 f"비교 연산자는 {op}이므로 경계값 {t1}, {t2}, {t3}에서의 판정에 주의한다.")
        rows = []
        done = False
        for th, ch in ((t1, "A"), (t2, "B"), (t3, "C")):
            ok = s >= th if op == ">=" else s > th
            rows.append([f"s {op} {th}", "참" if ok else "거짓",
                         ch if ok and not done else "검사 안 함" if done else "-"])
            done = done or ok
        rows.append(["else", "-", "D" if right == "D" else "검사 안 함"])
    subs = ["A", "B", "C", "D", "AB", "BC", "CD", "ABC", "BCD", "ABCD"]
    wrong = []
    for w in subs:
        if w == right:
            continue
        if k == 1:
            if len(w) == 1 and w != "D":
                note = "독립된 if를 else if 체인처럼 읽어 처음 참인 조건 하나만 출력된다고 보았다."
            elif "D" in w and len(w) > 1:
                note = "마지막 else가 바로 위 if에만 붙는 것을 놓쳐, 앞쪽 if의 거짓에도 D가 나온다고 보았다."
            elif w == "D":
                note = "참인 조건이 있어도 else가 실행된다고 보았다. else는 마지막 if의 거짓일 때만 실행된다."
            else:
                note = "각 if의 참/거짓 판정(≥)을 하나씩 잘못 읽어 출력되는 글자 수가 달라졌다."
        elif len(w) > 1:
            note = "else if를 독립된 if로 읽어, 참인 조건마다 연달아 출력된다고 보았다."
        elif abs(ord(w) - ord(right)) == 1:
            note = f"경계값 s = {s}에서 {op} 비교를 잘못 판단해 인접 등급 {w}를 골랐다."
        else:
            note = "위에서부터 순서대로 검사하는 규칙을 놓치고 조건 범위를 잘못 대응시켰다."
        wrong.append((w, note))
    return dict(code=_prog(body), out=right + "\n", intro=intro,
                cols=["조건", "판정", "출력"], rows=rows, wrong=wrong,
                diff=1 if k < 2 else 2,
                end=f"실행 결과 출력되는 문자열은 {right}이고 마지막 printf가 줄바꿈을 붙인다.",
                ask="점수 구간을 else if 사슬(또는 독립 if)로 판정할 때 경계값에서 어떤 분기가 실행되는지 묻는다.",
                tip="else if는 '처음 참인 하나', 독립 if는 '참인 것 모두'다. 경계값은 >= 와 > 의 차이를 먼저 확인한다.")


CONDS = ["a > b && b > c", "a > b || c > 5", "a % 2 == 0", "b >= 5 && c < 5",
         "a + b > 10", "c == a || c == b", "a < b && c % 2 == 1", "b > a || c < 3"]
FORMS = ["a + b", "a * c", "b - c + 10", "a * 2 + b", "c * 3 + 1", "a + b + c"]


def _strict(c):
    return re.sub(r">=|<=|>|<", lambda m: {">=": ">", "<=": "<", ">": ">=", "<": "<="}[m.group()], c)


def _swap(c):
    return c.replace("&&", "@@").replace("||", "&&").replace("@@", "||")


def t_arms(r, k):
    a, b, c = r.randint(1, 9), r.randint(1, 9), r.randint(0, 9)
    env = dict(a=a, b=b, c=c)
    conds = r.sample(CONDS, 3)
    forms = r.sample(FORMS, 4)
    accum = k == 1
    ev = lambda cs: [bool(cev(x, env)) for x in cs]
    fv = [cev(f, env) for f in forms]
    t = ev(conds)
    if accum:
        tot = sum(fv[i] for i in range(2) if t[i]) + (fv[2] if t[2] else fv[3])
        right = tot
        asg = "r +="
    else:
        right = fv[0] if t[0] else fv[1] if t[1] else fv[2] if t[2] else fv[3]
        asg = "r ="
    if accum:
        lines = [f"    if ({conds[0]}) r += {forms[0]};", f"    if ({conds[1]}) r += {forms[1]};",
                 f"    if ({conds[2]}) r += {forms[2]};", f"    else r += {forms[3]};"]
    else:
        lines = [f"    if ({conds[0]}) r = {forms[0]};", f"    else if ({conds[1]}) r = {forms[1]};",
                 f"    else if ({conds[2]}) r = {forms[2]};", f"    else r = {forms[3]};"]
    body = [f"    int a = {a}, b = {b}, c = {c}, r = 0;", *lines, '    printf("%d\\n", r);']

    def chain(cs, order=(0, 1, 2)):
        tt = ev(cs)
        for i in order:
            if tt[i]:
                return fv[i]
        return fv[3]

    tl = [fv[i] for i in range(3) if t[i]]
    allv = tl + ([] if t[2] else [fv[3]])
    cand = [
        (chain([_swap(x) for x in conds]), "&&와 ||를 서로 바꿔 읽어 조건 판정이 달라졌다."),
        (chain([_strict(x) for x in conds]), "경계 비교(>, >=, <, <=)를 한 칸씩 바꿔 읽었다."),
        (chain(conds, (2, 1, 0)), "아래쪽 조건부터 검사했다. 사슬은 위에서부터 검사한다."),
        (sum(allv), "독립 if처럼 참인 분기의 값을 모두 더했다."),
        (allv[-1] if allv else 0, "독립 if처럼 마지막으로 참인 분기가 값을 덮어쓴다고 보았다."),
        (allv[0] if allv else 0, "else if 사슬 규칙(첫 참 분기만)을 += 코드에도 적용했다."),
        (0, "어느 분기도 실행되지 않아 r이 초기값 0으로 남는다고 보았다."),
    ]
    for i in range(3):
        cs = list(conds)
        cs[i] = _swap(cs[i])
        cand.append((chain(cs), f"{i + 1}번째 조건의 &&/||를 서로 바꿔 읽었다."))
        cs = list(conds)
        cs[i] = _strict(cs[i])
        cand.append((chain(cs), f"{i + 1}번째 조건의 경계(>, >=, <, <=)를 한 칸 잘못 읽었다."))
    for i in range(4):
        for j in range(i + 1, 4):
            cand.append((fv[i] + fv[j], f"{i + 1}번째와 {j + 1}번째 분기의 값을 모두 더했다(여러 분기가 실행된다고 착각)."))
    cand += [(right + 1, "마지막 산술에서 1을 더했다(계산 실수)."),
             (right - 1, "마지막 산술에서 1을 뺐다(계산 실수).")]
    for i in range(4):
        cand.append((fv[i], f"{'다른 ' if True else ''}분기({i + 1}번째 값 {forms[i]})가 실행된다고 보았다."))
    wrong = [(str(v), n) for v, n in cand]
    rows = [[f"{conds[i]}", "참" if t[i] else "거짓", forms[i] + f" = {fv[i]}"] for i in range(3)]
    rows.append(["else", "-", forms[3] + f" = {fv[3]}"])
    if accum:
        intro = (f"a={a}, b={b}, c={c}. 앞의 두 if와 세 번째 if는 모두 독립적으로 검사하며, 참이면 r에 값을 누적한다. "
                 "else는 세 번째 if의 거짓에만 붙는다.")
    else:
        intro = (f"a={a}, b={b}, c={c}. 조건 3개를 위에서부터 검사하고 처음 참인 분기만 실행한다. "
                 "모두 거짓이면 else가 실행된다.")
    return dict(code=_prog(body), out=f"{right}\n", intro=intro,
                cols=["조건", "판정", "값(참일 때)"], rows=rows, wrong=wrong,
                diff=3 if accum else 2,
                end=f"{'참인 분기의 값을 모두 더해' if accum else '처음 참인 분기의 값을 r에 넣어'} r = {right}이 출력된다.",
                ask="&&, || 가 섞인 조건을 else if 사슬(또는 독립 if 누적)로 평가했을 때 최종 r 값을 구하는 문제다.",
                tip="조건마다 변수 값을 대입해 참/거짓을 표로 먼저 적는다. else if는 처음 참인 곳에서 끝나고, 독립 if는 전부 검사한다.")


def t_assign(r, k):
    a0, b0 = r.sample(range(2, 9), 2)
    if k == 0:
        cond, a1, truth = "(a = b)", b0, True
        cmpv = a0 == b0
    elif k == 1:
        cond, a1, truth = f"(a = b - {b0})", 0, False
        cmpv = a0 == b0 - b0
    else:
        th = r.choice([b0 - 1, b0 + 1])
        cond, a1, truth = f"((a = b) && a > {th})", b0, b0 > th
        cmpv = (a0 == b0) and a0 > th
    r1, r2 = 10, 20
    res = r1 if truth else r2
    body = [f"    int a = {a0}, b = {b0}, r = 0;",
            f"    if {cond if cond.startswith('((') else cond}" + " r = 10;",
            "    else r = 20;", '    printf("%d %d %d\\n", a, b, r);']
    out = f"{a1} {b0} {res}"
    rr = r1 if cmpv else r2
    cands = []
    for av in (a1, a0, b0, 0, a0 + b0):
        for rv in (r1, r2, 0):
            if (av, rv) == (a1, res):
                continue
            if av == a0 and rv == rr:
                note = "= 를 비교 연산 ==로 읽어 a가 바뀌지 않는다고 보았다. 조건 안의 =는 대입이다."
            elif av == a0:
                note = "대입 효과를 놓치고 a가 원래 값 그대로라고 보았다."
            elif av == a1:
                note = f"조건의 참/거짓 판정을 반대로 보아 r = {rv}로 읽었다(0이면 거짓, 0이 아니면 참)."
            elif av == 0:
                note = "대입 후 a 값이 0이 된다고 보았다(조건이 거짓이면 0이 된다는 착각)."
            elif av == b0:
                note = "대입 방향을 반대로 읽어 b의 값이 a에 들어간다고 보았다."
            else:
                note = "대입이 아니라 a에 b를 더한 값이 들어갔다고 보았다."
            cands.append((f"{av} {b0} {rv}", note))
    cands.append((f"{a1} {a0} {res}", "b 자리에 a의 원래 값이 출력된다고 보았다. b는 바뀌지 않는다."))
    cands.append((f"{a0} {b0} {rr}", "= 를 ==로 읽어 비교만 한다고 보았다."))
    rows = [["초기", a0, b0, "-"], ["조건의 a = b ..." if k != 1 else f"a = b - {b0}", a1, b0, "-"],
            ["분기 실행", a1, b0, res]]
    return dict(code=_prog(body), out=out + "\n",
                intro=(f"조건식 안의 =는 비교가 아니라 대입이다. 대입식의 값은 대입된 값이며, 0이면 거짓, "
                       f"0이 아니면 참으로 취급한다. 여기서는 a에 {a1}이 대입되어 조건이 {'참' if truth else '거짓'}이다."),
                cols=["단계", "a", "b", "r"], rows=rows, wrong=cands, diff=1 if k == 0 else 2,
                end=f"분기 결과 r = {res}이고 a는 {a1}으로 바뀐 채 남아 \"{out}\"가 출력된다.",
                ask="if 조건 안의 대입(=)이 변수 값과 참/거짓 판정에 미치는 영향을 묻는다.",
                tip="if 괄호 안의 = 는 대입이다. 대입된 값이 0이면 거짓이고 변수는 이미 바뀐 상태로 이후 코드에 쓰인다.")


def t_dangling(r, k):
    A, B = r.randint(2, 5), r.randint(2, 5)
    scen = r.choice([0, 1]) if k != 2 else 0
    if scen == 0:
        a, b = A + r.randint(1, 3), B - r.randint(0, 1)
    else:
        a, b = A - r.randint(0, 1), r.randint(1, 9)
    braces = k == 2
    if braces:
        code_if = [f"    if (a > {A}) {{", f"        if (b > {B})", "            x = a + b;",
                   "    } else", "        y = a - b;"]
    else:
        code_if = [f"    if (a > {A})", f"        if (b > {B})", "            x = a + b;",
                   "    else", "        y = a - b;"]
    body = [f"    int a = {a}, b = {b}, x = 0, y = 0, z;", *code_if,
            "    z = x * 2 + y;", '    printf("%d %d %d\\n", x, y, z);']
    xv, yv = a + b, a - b

    def run(bind_inner):
        x = y = 0
        if bind_inner:
            if a > A:
                if b > B:
                    x = xv
                else:
                    y = yv
        else:
            if a > A:
                if b > B:
                    x = xv
            else:
                y = yv
        return x, y

    rx, ry = run(not braces)
    ox, oy = run(braces)
    z = lambda x, y: x * 2 + y
    out = f"{rx} {ry} {z(rx, ry)}"
    cands = []
    for x in (xv, 0):
        for y in (yv, 0, -yv):
            for zf, zn in ((lambda x, y: x * 2 + y, ""), (lambda x, y: x + y, "z 식의 2배 계수를 놓쳐 ")):
                s = f"{x} {y} {zf(x, y)}"
                if s == out:
                    continue
                if (x, y) == (ox, oy) and not zn:
                    note = ("else가 바깥 if에 붙는다고 보았다. braces가 없으면 else는 가장 가까운 if에 붙는다."
                            if not braces else "else가 안쪽 if에 붙는다고 보았다. 중괄호가 바깥 if를 닫았으므로 else는 바깥 if의 것이다.")
                elif y == -yv and y != 0:
                    note = "y = a - b를 b - a로 계산해 부호가 뒤집혔다."
                elif x and y and (x, y) == (xv, yv):
                    note = "if 본문과 else 본문이 둘 다 실행된다고 보았다. 둘 중 하나만 실행된다."
                elif x == 0 and y == 0:
                    note = "두 대입 중 어느 것도 실행되지 않는다고 보았다."
                else:
                    note = zn + "if 중첩의 어느 분기가 실행되는지 잘못 골랐다."
                cands.append((s, note))
    cands.append((f"{ry} {rx} {z(ry, rx)}", "x와 y의 출력 위치를 바꿔 읽었다."))
    cands.append((f"{rx} {ry} {z(rx, ry) + 1}", "z 계산에서 1을 더했다고 착각했다."))
    path = ("바깥 if(a > %d)가 %s" % (A, "참" if a > A else "거짓"))
    if braces:
        intro = (f"중괄호가 바깥 if 본문을 닫았으므로 else는 바깥 if(a > {A})의 else이다. {path}. "
                 f"b > {B}는 {'참' if b > B else '거짓'}.")
    else:
        intro = (f"들여쓰기가 아니라 문법이 else의 짝을 정한다. else는 가장 가까운 if(b > {B})에 붙는다. "
                 f"{path}, b > {B}는 {'참' if b > B else '거짓'}.")
    rows = [["a > %d" % A, "참" if a > A else "거짓"], ["b > %d" % B, "참" if b > B else "거짓"],
            ["x, y", f"{rx}, {ry}"], ["z = x*2 + y", z(rx, ry)]]
    return dict(code=_prog(body), out=out + "\n", intro=intro, cols=["판정/변수", "값"], rows=rows,
                wrong=cands, diff=3 if k == 0 else 2,
                end=f"x = {rx}, y = {ry}, z = {z(rx, ry)} 이므로 \"{out}\"가 출력된다.",
                ask="중첩 if에서 else가 어느 if에 속하는지(dangling else)에 따라 어떤 대입이 실행되는지 묻는다.",
                tip="else는 항상 같은 블록 안에서 가장 가까운 앞의 if와 짝이다. 들여쓰기는 컴파일러가 무시하므로 중괄호부터 확인한다.")


def t_short(r, k):
    a, b = r.randint(1, 6), r.randint(1, 6)
    t1, t2 = r.randint(2, 5), r.randint(2, 6)
    if k == 0:
        c1, c2 = f"a > {t1} && ++b > {t2}", f"a > {t1} || b++ < {t2}"
    else:
        c1, c2 = f"a < {t1} || ++b > {t2}", f"a < {t1} && b++ < {t2}"
    body = [f"    int a = {a}, b = {b}, c = 0;", f"    if ({c1}) c += 1;",
            f"    if ({c2}) c += 10;", '    printf("%d %d %d\\n", a, b, c)' + ";"]

    def sim(sc=True, post=False):
        bb, cc = b, 0
        # first condition
        def pre(bb):
            return (bb + 1, bb) if post else (bb + 1, bb + 1)
        if k == 0:
            l1 = a > t1
            nb, val = pre(bb)
            if l1 or not sc:
                bb = nb
            r1 = l1 and val > t2
            if r1:
                cc += 1
            l2 = a > t1
            v2 = bb < t2
            if (not l2) or not sc:
                bb += 1
            r2 = l2 or v2
        else:
            l1 = a < t1
            nb, val = pre(bb)
            if (not l1) or not sc:
                bb = nb
            r1 = l1 or val > t2
            if r1:
                cc += 1
            l2 = a < t1
            v2 = bb < t2
            if l2 or not sc:
                bb += 1
            r2 = l2 and v2
        if r2:
            cc += 10
        return bb, cc

    rb, rc = sim()
    out = f"{a} {rb} {rc}"
    nb, nc = sim(sc=False)
    pb, pc = sim(post=True)
    toks = [a, rb, rc]
    cands = [
        (f"{a} {nb} {nc}", "&&, ||의 두 번째 피연산자가 항상 실행된다고 보았다. 앞 결과로 값이 정해지면 뒤는 평가되지 않는다(단락 평가)."),
        (f"{a} {pb} {pc}", "++b를 b++처럼 읽어 비교에 증가 전 값을 썼다."),
        (f"{a} {b} {rc}", "단락 평가 때문에 b가 한 번도 증가하지 않는다고 보았다."),
        (f"{a} {b + 2} {rc}", "두 조건의 b 증가가 모두 실행된다고 보았다."),
        (f"{a} {rb} {rc ^ 1 if rc & 1 else rc + 1}", "첫 번째 if의 참/거짓을 반대로 판정했다."),
        (f"{a} {rb} {rc ^ 10 if rc >= 10 else rc + 10}", "두 번째 if의 참/거짓을 반대로 판정했다."),
        (f"{a} {rb} {11 if rc != 11 else 0}", "두 if가 모두 참이라고 (또는 모두 거짓이라고) 가정했다."),
        (f"{rb} {a} {rc}", "a와 b의 출력 위치를 바꿔 읽었다."),
        (f"{a} {rb + 1} {rc}", "b가 한 번 더 증가한다고 보았다."),
        (f"{a} {rb - 1} {rc}", "b의 증가를 한 번 놓쳤다."),
        (f"{a + 1} {rb} {rc}", "조건에 a도 증가한다고 착각했다."),
        (f"{a} {rb} {rc + 1}", "c에 1이 한 번 더 더해진다고 보았다."),
        (f"{a} {rb} {rc + 10}", "c에 10이 한 번 더 더해진다고 보았다."),
    ]
    rows = [["초기", a, b, 0]]
    return dict(code=_prog(body), out=out + "\n",
                intro=(f"a={a}, b={b}. &&는 왼쪽이 거짓이면, ||는 왼쪽이 참이면 오른쪽을 평가하지 않는다(단락 평가). "
                       "따라서 오른쪽의 ++b, b++ 같은 부수 효과가 실행되는지부터 따져야 한다."),
                cols=["단계", "a", "b", "c"], rows=rows + [["두 if 실행 후", a, rb, rc]], wrong=cands,
                diff=3 if k == 0 else 2,
                end=f"두 if를 차례로 평가하면 b = {rb}, c = {rc}이 되어 \"{out}\"가 출력된다.",
                ask="&&, ||의 단락 평가(short-circuit) 때문에 오른쪽 피연산자의 증가 연산이 실행되는지를 묻는다.",
                tip="&&는 왼쪽이 거짓, ||는 왼쪽이 참이면 오른쪽을 건너뛴다. ++b, b++ 같은 부수 효과가 오른쪽에 있으면 실행 여부를 먼저 판정한다.")


YEARS = [1900, 2000, 2100, 2023, 2024, 1996, 2400, 1800, 2019, 2012, 2200, 1600]


def t_leap(r, k):
    if k == 2:
        lo = r.choice([11, 12, 13])
        hi = lo + r.choice([4, 5])
        code = _prog([f"    for (int i = {lo}; i <= {hi}; i++) {{",
                      '        if (i % 3 == 0) printf("F ");',
                      '        else if (i % 5 == 0) printf("B ");',
                      '        else if (i % 15 == 0) printf("FB ");',
                      '        else printf("%d ", i);', "    }", '    printf("\\n");'])
        tok = lambda i, fb="FB": "F" if i % 3 == 0 else "B" if i % 5 == 0 else str(i)
        seq = list(range(lo, hi + 1))
        out = " ".join(tok(i) for i in seq)
        rows = [[i, "i%3==0" if i % 3 == 0 else "i%5==0" if i % 5 == 0 else "-", tok(i)] for i in seq]
        sw = lambda t: {"F": "B", "B": "F"}.get(t, t)
        cands = [
            (" ".join("FB" if i % 15 == 0 else tok(i) for i in seq), "15의 배수를 FB로 출력한다고 보았다. i % 3 == 0이 먼저 참이라 FB 분기에는 도달하지 못한다."),
            (" ".join("B" if i % 15 == 0 else tok(i) for i in seq), "15에서 i % 5 == 0이 먼저 검사된다고 보았다. 3의 배수 검사가 먼저이다."),
            (" ".join(sw(tok(i)) for i in seq), "F와 B를 서로 바꿔 읽었다."),
            (" ".join(tok(i) for i in seq[1:]), "첫 값(i = %d)을 출력하지 않았다." % lo),
            (" ".join(tok(i) for i in seq[:-1]), "i <= %d의 등호를 놓쳐 마지막 값을 빼먹었다." % hi),
            (" ".join(str(i) if i % 3 else "F" for i in seq), "5의 배수 분기(B)가 없다고 보았다."),
            (" ".join(str(i) if i % 5 else "B" for i in seq), "3의 배수 분기(F)가 없다고 보았다."),
            (" ".join("F B" if i % 15 == 0 else tok(i) for i in seq), "15에서 F와 B가 둘 다 출력된다고 보았다. else if라 한 분기만 실행된다."),
            (" ".join(str(i) if i % 15 == 0 else tok(i) for i in seq), "15의 배수는 숫자를 그대로 출력한다고 보았다."),
            (" ".join(tok(i + 1) for i in seq), "i 값을 1 크게 읽었다."),
            (" ".join("F" if i % 3 == 0 and i % 5 else "B" if i % 5 == 0 and i % 3 else tok(i) for i in seq), "3과 5의 공배수는 출력 없이 지나간다고 보았다."),
            (" ".join(tok(i) for i in seq[::-1]), "순서를 거꾸로 출력했다."),
        ]
        if not any(i % 15 == 0 for i in seq):
            return None
        return dict(code=code, out=out + " \n", intro=(f"i = {lo}부터 {hi}까지 else if 사슬을 위에서부터 검사한다. "
                    "15의 배수는 3의 배수이기도 하므로 첫 분기(i % 3 == 0)에서 끝나고, 세 번째 분기(FB)는 도달할 수 없다."),
                    cols=["i", "처음 참인 조건", "출력"], rows=rows, wrong=cands, diff=3,
                    end=f"각 값 뒤에 공백이 붙고 마지막에 줄바꿈이 출력된다. 결과는 \"{out}\"이다.",
                    ask="else if 조건의 배치 순서 때문에 더 구체적인 조건(i % 15 == 0)이 실행되지 못하는 상황을 묻는다.",
                    tip="else if 사슬은 위에서부터 첫 참에서 끝난다. 포함 관계가 있는 조건(15의 배수 ⊂ 3의 배수)은 더 좁은 조건을 먼저 둬야 한다.")
    ys = r.sample(YEARS, 5)
    preds = {
        "p": lambda y: (y % 4 == 0 and y % 100 != 0) or y % 400 == 0,
        "4": lambda y: y % 4 == 0,
        "no400": lambda y: y % 4 == 0 and y % 100 != 0,
        "no4": lambda y: y % 100 != 0 or y % 400 == 0,
        "400": lambda y: y % 400 == 0,
        "andall": lambda y: y % 4 == 0 and y % 100 != 0 and y % 400 == 0,
        "100": lambda y: y % 4 == 0 and y % 100 == 0,
        "or": lambda y: y % 4 == 0 or y % 100 != 0 or y % 400 == 0,
        "inv": lambda y: not ((y % 4 == 0 and y % 100 != 0) or y % 400 == 0),
    }
    f = preds["p"]
    arr = ", ".join(map(str, ys))
    if k == 0:
        test = ["        if ((y[i] % 4 == 0 && y[i] % 100 != 0) || y[i] % 400 == 0)",
                '            printf("Y");', "        else", '            printf("N");']
    else:
        test = ["        if (y[i] % 400 == 0) printf(\"Y\");",
                "        else if (y[i] % 100 == 0) printf(\"N\");",
                "        else if (y[i] % 4 == 0) printf(\"Y\");", "        else printf(\"N\");"]
    code = _prog([f"    int y[] = {{{arr}}};", f"    for (int i = 0; i < {len(ys)}; i++) {{", *test, "    }",
                  '    printf("\\n");'])
    yn = lambda p, seq=ys: "".join("Y" if p(v) else "N" for v in seq)
    out = yn(f)
    notes = {
        "4": "4의 배수이면 모두 윤년이라고 보았다. 100의 배수는 400의 배수일 때만 윤년이다.",
        "no400": "400의 배수 예외를 놓쳤다. 400으로 나누어떨어지면 100의 배수여도 윤년이다.",
        "no4": "4의 배수 조건을 빼고 100의 배수가 아니면 모두 윤년으로 보았다.",
        "400": "400의 배수만 윤년이라고 보았다.",
        "andall": "세 조건을 모두 AND로 묶어 읽었다.",
        "100": "100의 배수이면 윤년이라고 거꾸로 이해했다.",
        "or": "세 조건 중 하나만 맞으면 윤년으로 보았다.",
        "inv": "판정 결과 Y와 N을 서로 바꿔 읽었다.",
    }
    cands = [(yn(preds[n]), notes[n]) for n in notes]
    cands += [(out[::-1], "배열을 거꾸로 순회했다고 보았다."),
              (out.replace("Y", "y"), "대소문자만 다른 출력은 오답이다.") if False else (out[1:], "첫 원소를 처리하지 않았다."),
              (out[:-1], "마지막 원소를 처리하지 않았다."),
              (str(out.count("Y")), "윤년 개수를 출력한다고 보았다.")]
    rows = [[v, "Y" if f(v) else "N"] for v in ys]
    if k == 1:
        rows = [[v, "400의 배수→Y" if v % 400 == 0 else "100의 배수→N" if v % 100 == 0 else "4의 배수→Y" if v % 4 == 0 else "N"] for v in ys]
    return dict(code=code, out=out + "\n",
                intro=("윤년은 4의 배수이면서 100의 배수가 아니거나, 400의 배수인 해이다. 각 해를 조건에 대입해 "
                       "Y/N을 차례로 이어 붙인다."),
                cols=["연도", "판정"], rows=rows, wrong=cands, diff=2,
                end=f"배열 순서대로 판정 문자를 붙이면 {out}이고, 마지막 printf가 줄바꿈을 출력한다.",
                ask="&&, || 가 섞인 윤년 판정 조건(또는 같은 의미의 else if 사슬)을 여러 연도에 적용한 결과를 묻는다.",
                tip="100·400의 배수가 예외 처리의 핵심이다. 1900 같은 100의 배수와 2000 같은 400의 배수를 따로 검사해 보자.")


def generate():
    return run_family(FAM, 14, [t_grade, t_arms, t_assign, t_dangling, t_short, t_leap],
                      "C 조건문(if·else if)", ["C", "if", "조건문"])
