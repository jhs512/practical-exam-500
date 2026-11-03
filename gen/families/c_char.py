"""C: char as integer (ASCII), letter shifting, digit chars, classification."""
from __future__ import annotations

from families.c_kit import run_family, subst

FAM = "c-char"


def _prog(body):
    return "\n".join(["#include <stdio.h>", "", "int main(void) {", *body,
                      "    return 0;", "}", ""])


def t_shift(r, k):
    up = r.random() < 0.5
    lo = ord("A" if up else "a")
    n = r.randint(3, 9)
    if k == 1:
        base = chr(lo + r.randint(n + 1, 25))
        op, s = "-=", -1
    else:
        base = chr(lo + r.randint(0, 25 - n))
        op, s = "+=", 1
    v = ord(base) + s * n
    if k == 2:
        body = [f"    char c = '{base}';",
                f'    printf("%c %d %c\\n", c + {n}, c + {n}, c);']
        out = f"{chr(v)} {v} {base}\n"
        tail = f" {base}"
        intro = (f"c는 변하지 않고 식 c + {n}만 int로 계산된다. '{base}'의 "
                 f"아스키(ASCII) 값은 {ord(base)}이다.")
        rows = [["c", base, ord(base)], [f"c + {n}", chr(v), v]]
    else:
        body = [f"    char c = '{base}';", f"    c {op} {n};",
                '    printf("%c %d\\n", c, c);']
        out = f"{chr(v)} {v}\n"
        tail = ""
        intro = (f"'{base}'의 아스키 값은 {ord(base)}이다. c {op} {n} 뒤 "
                 f"c의 값은 {v}이고 %c는 문자로, %d는 정수로 출력한다.")
        rows = [["초기", base, ord(base)], [f"c {op} {n}", chr(v), v]]
    f = lambda x: f"{chr(x)} {x}{tail}"
    wrong = [
        (f(v - s), f"{n}칸이 아니라 {n - 1}칸만 이동한다고 세었다(시작 글자를 1번째로 계산)."),
        (f(v + s), f"{n}칸보다 한 칸 더 이동했다고 잘못 셌다."),
        (f"{chr(v)} {n}{tail}", f"%d에 아스키 값 대신 이동량 {n}을 넣었다."),
        (f"{chr(v)} {v - lo + 1}{tail}", "%d를 알파벳 순번(첫 글자=1)으로 착각했다. %d는 아스키 값을 출력한다."),
        (f"{v} {chr(v)}{tail}", "출력 순서를 %c, %d의 반대로 적었다. 형식 지정자 순서대로 문자, 숫자 순이다."),
        (f"{base} {v}{tail}", "%c가 이동 전 문자를 출력한다고 보았다. 변경된 값의 문자가 출력된다."),
        (f"{chr(v)} {ord(base)}{tail}", "%d가 이동 전 아스키 값을 출력한다고 보았다."),
        (f(v ^ 32), "대문자와 소문자의 아스키 차(32)를 섞어 소문자(또는 대문자)로 바뀐다고 보았다."),
        (f"{chr(v)}{v}{tail}", "형식 문자열의 공백을 놓치고 두 값을 붙여 썼다."),
        (f(ord(base) - s * n), "이동 방향을 반대로 읽었다."),
        (f"{chr(v)} {v - 48}{tail}", "숫자 문자 '0'(48) 기준으로 %d 값을 뺀 것으로 착각했다."),
    ]
    return dict(code=_prog(body), out=out, intro=intro, cols=["단계", "문자", "정수값"],
                rows=rows, wrong=wrong, diff=1 if k < 2 else 2,
                end=(f"%c는 정수 값을 아스키 문자로 바꿔 출력하고 %d는 같은 값을 정수로 출력한다. "
                     f"최종 값 {v}은 문자 '{chr(v)}'이다."),
                ask="char 변수에 정수를 더하거나 빼면 문자 코드가 어떻게 변하는지와 %c, %d 출력 차이를 묻는다.",
                tip="char는 작은 정수형이다. 문자 ↔ 코드는 'A'=65, 'a'=97, '0'=48을 기준으로 계산하고, %c/%d를 구분해 읽는다.")


def t_digits(r, k):
    s = "".join(str(r.randint(1, 9)) for _ in range(r.choice([4, 5])))
    d = [int(c) for c in s]
    head = [f'    char s[] = "{s}";', "    int v = 0;"]
    if k == 0:
        loop = ["    for (int i = 0; s[i] != '\\0'; i++)", "        v += s[i] - '0';"]
        right, intro = sum(d), "각 문자에서 '0'(48)을 빼 숫자로 바꾼 뒤 모두 더한다."
        rows = [[i, c, int(c), sum(d[:i + 1])] for i, c in enumerate(s)]
        wrong = [(sum(d) + 48 * len(d), "'0'을 빼지 않아 아스키 값(문자 코드)을 더했다."),
                 (len(d), "더한 값이 아니라 자릿수만 셌다."),
                 (max(d), "합이 아니라 최댓값을 구했다."),
                 (d[-1], "마지막 숫자만 남는다고 보았다(+= 를 = 로 읽음)."),
                 (d[0], "첫 숫자만 더했다고 보았다."),
                 (int(s), "문자열을 이어 붙인 십진수로 보았다. v += 는 자릿수 합이다."),
                 (sum(d) - d[0], "첫 문자(i=0)를 건너뛰었다."),
                 (sum(d) - d[-1], "마지막 문자를 건너뛰었다(경계 착오)."),
                 (sum(d) + 48, "'0'을 한 번만 더해 아스키 오프셋이 한 번 남았다고 보았다."),
                 (sum(x * x for x in d), "각 숫자를 제곱해 더했다.")]
    elif k == 1:
        loop = ["    for (int i = 0; s[i] != '\\0'; i++)",
                "        v = v * 10 + (s[i] - '0');", "    v = v + 1;"]
        right, intro = int(s) + 1, "자릿수를 왼쪽부터 v = v*10 + 숫자로 이어 붙여 정수를 만든 뒤 1을 더한다."
        rows, cur = [], 0
        for i, c in enumerate(s):
            cur = cur * 10 + int(c)
            rows.append([i, c, int(c), cur])
        wrong = [(int(s), "마지막 v = v + 1 문장을 놓쳤다."),
                 (int(s[::-1]) + 1, "자릿수가 거꾸로 쌓인다고 보았다."),
                 (sum(d) + 1, "이어 붙이기가 아니라 합으로 읽었다."),
                 (int(s) + 10, "마지막에 1이 아니라 10을 더한 것으로 보았다."),
                 (int(s) - 1, "+ 를 - 로 읽었다."),
                 (int(s) * 10 + 1, "v = v*10 + 1 형태로 마지막 문장을 읽었다."),
                 (int(s[:-1]) + 1, "마지막 자릿수를 처리하지 않았다(반복 경계 착오)."),
                 (int(s) + 49, "마지막에 '0'(48)을 더한 것으로 착각했다."),
                 (int(s[1:]) + 1, "첫 자릿수를 처리하지 않았다."),
                 (len(s) + 1, "자릿수 개수에 1을 더했다.")]
    else:
        loop = ["    for (int i = 0; s[i] != '\\0'; i++)",
                "        if (s[i] > '5') v += s[i] - '0';"]
        big = [x for x in d if x > 5]
        right, intro = sum(big), "문자끼리 비교해도 숫자 순서와 같다. '5'보다 큰 문자만 숫자로 바꿔 더한다."
        rows = [[i, c, "예" if c > "5" else "아니오", sum(x for x in d[:i + 1] if x > 5)]
                for i, c in enumerate(s)]
        wrong = [(sum(x for x in d if x >= 5), "> 를 >= 로 읽어 5도 더했다."),
                 (len(big), "더하지 않고 조건에 맞는 개수를 셌다."),
                 (sum(d), "조건 없이 모두 더했다."),
                 (sum(x for x in d if x <= 5), "조건을 반대로 읽었다."),
                 (sum(x + 48 for x in big), "'0'을 빼지 않고 아스키 값을 더했다."),
                 (max(d), "합 대신 최댓값을 구했다."),
                 (sum(x for x in d if x < 5), "조건을 < 로 바꿔 읽었다."),
                 (sum(x for x in d if x > 4), "경계를 5가 아니라 4로 보았다."),
                 (sum(d) - sum(big), "조건에 맞지 않는 값만 더했다."),
                 (sum(big) + 1, "누적 후 1을 더하는 문장을 잘못 상상했다."),
                 (sum(x - 1 for x in big), "'0' 대신 '1'을 빼는 것으로 보아 숫자값이 1씩 작아졌다."),
                 (sum(x + 1 for x in big), "'0'보다 하나 작은 문자를 뺀 것으로 보아 숫자값이 1씩 커졌다."),
                 (sum(i for i, x in enumerate(d) if x > 5), "더하는 값 대신 조건을 만족한 첨자 i를 더했다."),
                 (max(big) if big else 0, "합이 아니라 조건을 만족한 값 중 최댓값을 구했다."),
                 (sum(d[::-1][:len(big)]), "조건과 무관하게 뒤쪽 숫자를 개수만큼 더했다.")]
    code = _prog(head + loop + ['    printf("%d\\n", v);'])
    return dict(code=code, out=f"{right}\n", intro=intro,
                cols=["i", "s[i]", "숫자/판정", "v"], rows=rows,
                wrong=[(str(a), b) for a, b in wrong], diff=1 if k == 0 else 2,
                end=f"반복이 끝나면 v = {right}이며 printf가 이를 한 줄로 출력한다.",
                ask="숫자 문자열의 각 문자를 s[i] - '0'으로 정수화하며 누적하는 과정을 묻는다.",
                tip="숫자 문자는 '0'을 빼야 숫자값이 된다. 빼지 않으면 48씩 커진 아스키 값이 누적된다.")


POOL = ["Hi 5Go 2024!", "aB3 dE4 Fg!", "C99 Prog_Ex 1", "x1Y2 z3, W4", "Ab-12 Cd 9Z",
        "Kd 3 Rt-77 a", "9Lives ok? 2B", "m4Rs T1ps!!", "Q7 w8 E9 r0 u"]


def t_count(r, k):
    s = r.choice(POOL) + r.choice(["", "x", "7", "#"])
    c = dict(u=0, l=0, d=0, o=0)
    for ch in s:
        c["u" if ch.isupper() else "l" if ch.islower() else "d" if ch.isdigit() else "o"] += 1
    orders = [("u", "l", "d"), ("d", "u", "l"), ("l", "d", "u")]
    od = list(orders[k % 3]) + (["o"] if k == 2 else [])
    cond = {"u": "s[i] >= 'A' && s[i] <= 'Z'", "l": "s[i] >= 'a' && s[i] <= 'z'",
            "d": "s[i] >= '0' && s[i] <= '9'"}
    body = [f'    char s[] = "{s}";', "    int u = 0, l = 0, d = 0, o = 0;",
            "    for (int i = 0; s[i] != '\\0'; i++) {",
            f"        if ({cond['u']}) u++;",
            f"        else if ({cond['l']}) l++;",
            f"        else if ({cond['d']}) d++;",
            "        else o++;", "    }"]
    fmt = " ".join(["%d"] * len(od))
    body.append(f'    printf("{fmt}\\n", {", ".join(od)});')
    pr = lambda m: " ".join(str(m[x]) for x in od)
    M = lambda **kw: {**c, **kw}
    wrong = [
        (pr(M(u=c["l"], l=c["u"])), "대문자와 소문자 판정 범위를 서로 바꿔 읽었다."),
        (pr(M(u=c["u"] + c["l"], l=0)), "알파벳이면 모두 대문자로 센다고 보았다(isalpha와 혼동)."),
        (pr(M(d=c["d"] + c["o"])), "공백·기호도 숫자 쪽에 센다고 보았다. 마지막 else는 o++ 이다."),
        (pr(M(l=c["l"] + c["o"])), "공백·기호를 소문자에 포함했다."),
        (pr(M(u=c["u"] + c["o"])), "공백·기호를 대문자에 포함했다."),
        (pr(M(l=len(s))), "l에 문자열 전체 길이를 넣었다."),
        (pr(M(d=sum(int(x) for x in s if x.isdigit()))), "숫자 문자의 개수가 아니라 숫자 값의 합을 셌다."),
        (pr(M(u=c["u"] - 1)), "대문자 하나를 놓쳤다(마지막/첫 문자 경계)."),
        (pr(M(l=c["l"] + 1)), "소문자를 하나 더 센 것으로 착각했다."),
        (" ".join(str(c[x]) for x in od[1:] + od[:1]), "printf 인수 순서를 한 칸씩 밀어 읽었다."),
        (pr(M(d=c["d"] - 1)), "숫자 하나를 빠뜨렸다."),
    ]
    rows = [[n, str(v)] for n, v in zip(["대문자 u", "소문자 l", "숫자 d", "기타 o"],
                                          [c["u"], c["l"], c["d"], c["o"]])]
    return dict(code=_prog(body), out=pr(c) + "\n",
                intro=(f"문자열 \"{s}\"를 한 글자씩 보며 else if 사슬로 분류한다. 대문자 A~Z, 소문자 a~z, "
                       "숫자 0~9는 아스키 범위 비교로, 나머지는 기타(o)로 센다."),
                cols=["분류", "개수"], rows=rows, wrong=wrong, diff=2,
                end=f"출력 순서는 printf 인수 순서({', '.join(od)})를 따라 {pr(c)}이다.",
                ask="문자 범위 비교(else if 사슬)로 대문자·소문자·숫자 개수를 세고, printf 인수 순서대로 읽는 문제다.",
                tip="범위 비교 사슬은 위에서부터 한 글자당 한 분기만 실행된다. 공백·기호는 마지막 else로 간다. 출력 순서는 변수 선언이 아니라 printf 인수 순서다.")


WORDS = ["xylophone", "jazz box", "lazy fox 2 day", "wizard xyz", "zebra yak", "crazy fly ox", "xyz zoo 7 box", "max zone buzz", "quiz yes 42 zip", "wax by jazz"]


def t_caesar(r, k):
    s = r.choice(WORDS)
    n = r.randint(2, 4)
    fwd = k != 1
    upper = k == 2
    base = "A" if upper else "a"
    if upper:
        s = s.upper()
    sg = n if fwd else -n
    expr = (f"(c - '{base}' + {n}) % 26 + '{base}'" if fwd
            else f"(c - '{base}' - {n} + 26) % 26 + '{base}'")
    code = _prog([f'    char s[] = "{s}";',
                  "    for (int i = 0; s[i] != '\\0'; i++) {",
                  "        char c = s[i];",
                  f"        if (c >= '{base}' && c <= '{chr(ord(base) + 25)}')",
                  f"            c = {expr};",
                  "        putchar(c);", "    }", "    putchar('\\n');"])
    isl = lambda ch: base <= ch <= chr(ord(base) + 25)

    def sh(ch, m, wrap=True):
        if not isl(ch):
            return ch
        if wrap:
            return chr((ord(ch) - ord(base) + m) % 26 + ord(base))
        return chr(ord(ch) + m)

    right = "".join(sh(ch, sg) for ch in s)
    rows = [[ch, ord(ch), sh(ch, sg) if isl(ch) else "그대로"] for ch in s[:6]]
    wrong = [
        ("".join(sh(ch, sg, False) for ch in s), "% 26 으로 알파벳 끝에서 처음으로 돌아가는 과정을 빼고 코드값만 더했다."),
        ("".join(sh(ch, -sg) for ch in s), "이동 방향을 반대로 읽었다."),
        ("".join(sh(ch, sg + 1) for ch in s), f"이동량을 {abs(sg) + 1}로 잘못 읽었다."),
        ("".join(sh(ch, sg - 1) for ch in s), f"이동량을 {abs(sg) - 1}로 잘못 읽었다."),
        ("".join(chr(ord(ch) + sg) if not isl(ch) and 32 <= ord(ch) + sg < 127 else sh(ch, sg) for ch in s),
         "if 조건 밖의 공백·숫자도 이동한다고 보았다."),
        (right[::-1], "putchar를 역순으로 출력한다고 보았다."),
        (s[0] + right[1:], "첫 글자는 변환하지 않는다고 보았다."),
        ("".join(ch if ch in "aeiouAEIOU" else sh(ch, sg) for ch in s), "모음은 변환하지 않는다고 보았다."),
        ("".join(sh(ch, sg) if i % 2 == 0 else ch for i, ch in enumerate(s)), "짝수 번째 글자만 변환한다고 보았다."),
        ("".join(chr((ord(ch) - ord(base) + sg) % 25 + ord(base)) if isl(ch) else ch for ch in s),
         "% 26 을 % 25 로 잘못 읽었다."),
        ("".join(sh(ch, 2 * sg) for ch in s), "이동을 두 번 적용한다고 보았다."),
        (s, "조건을 만족하는 문자가 없다고 보고 입력을 그대로 출력했다."),
    ]
    d = "앞으로" if fwd else "뒤로"
    return dict(code=code, out=right + "\n",
                intro=(f"알파벳 {'대' if upper else '소'}문자만 {n}칸 {d} 이동(시저 암호)하고, 끝을 넘어가면 % 26 으로 "
                       f"돌아온다. 그 밖의 문자(공백, 숫자)는 if 조건 밖이라 그대로 출력된다."),
                cols=["문자", "코드", "변환 결과"], rows=rows, wrong=wrong, diff=3,
                end=f"문자열 전체를 같은 규칙으로 변환하면 \"{right}\"가 되고 putchar('\\n')으로 줄이 끝난다.",
                ask="알파벳 범위만 골라 (c - 기준 ± 이동) % 26 + 기준 으로 순환 이동하는 코드의 결과를 묻는다.",
                tip="'z' 다음은 'a'로 돌아와야 한다. 기준 문자를 빼 0~25로 만든 뒤 % 26, 다시 기준을 더하는 3단계로 쪼개 계산한다.")


def t_expr(r, k):
    x, y = r.sample(range(2, 8), 2)
    n = r.randint(1, 2)
    X, Y = str(x), str(y)
    if k == 0:
        exprs = ["y - x", f"x + {n}", "x + y - '0'"]
        v = [y - x, chr(48 + x + n), 48 + x + y]
        naive = [y - x, x + n, x + y]
        diff = 2
    elif k == 1:
        exprs = ["(x - '0') * (y - '0')", f"y - {n}", "x + y"]
        v = [x * y, chr(48 + y - n), 96 + x + y]
        naive = [x * y, y - n, x + y]
        diff = 3
    else:
        exprs = ["x < y", f"'0' + (x - '0') + {n}", "y - '0' + 1"]
        v = [int(x < y), chr(48 + x + n), y + 1]
        naive = [int(x < y), x + n, y + 1]
        diff = 2
    fm = ["%d", "%c", "%d"]
    out = " ".join(str(a) for a in v)
    code = _prog([f"    char x = '{X}', y = '{Y}';",
                  f'    printf("{" ".join(fm)}\\n", {", ".join(exprs)});'])
    toks = [str(a) for a in v]
    alts = {0: [(naive[0] + 1, "첫 식의 비교/연산 결과를 잘못 계산했다."),
                (naive[0] - 1, "첫 식의 연산 결과를 한 단계 낮게 계산했다.")],
            1: [(chr(ord(v[1]) + 1), "코드값을 한 칸 더 이동한 문자로 계산했다."),
                (naive[1], "%c인데 숫자 값 그대로 정수로 출력했다."),
                (chr(48 + (x if k != 1 else y)), "더하거나 뺀 뒤 값이 아니라 원래 문자를 출력했다.")],
            2: [(naive[2], "숫자 문자를 아스키 값이 아닌 숫자 값으로 계산했다."),
                (v[2] + 48, "'0'(48)을 한 번 더 더했다."),
                (v[2] - 48, "'0'(48)을 한 번 더 뺐다.")]}
    wrong = subst(toks, alts)
    wrong += [(" ".join(str(a) for a in naive), "세 식 모두 문자 코드를 무시하고 숫자 값으로만 계산했다."),
              (f"{toks[1]} {toks[0]} {toks[2]}", "출력 순서를 바꿔 읽었다."),
              (f"{toks[0]} {toks[1]}", "세 번째 인수를 빠뜨렸다."),
              (f"{toks[0]} {toks[2]} {toks[1]}", "%c와 %d의 위치를 바꿔 읽었다."),
              (f"{48 + x} {toks[1]} {toks[2]}", "첫 식을 변수 x의 아스키 값으로 읽었다.")]
    return dict(code=code, out=out + "\n",
                intro=(f"x = '{X}'({48 + x}), y = '{Y}'({48 + y}). 문자는 int로 승격되어 코드값끼리 계산된다. "
                       "%c는 결과를 문자로, %d는 정수로 출력한다."),
                cols=["식", "계산", "출력"],
                rows=[[exprs[0], "코드값 연산", toks[0]], [exprs[1], "코드값 연산", toks[1]],
                      [exprs[2], "코드값 연산", toks[2]]],
                wrong=wrong, diff=diff,
                end=f"세 값을 순서대로 공백으로 이어 \"{out}\"가 출력된다.",
                ask="숫자 문자(x, y)를 포함한 식이 숫자값이 아니라 문자 코드로 계산됨을 이용해 %c, %d 결과를 구하는 문제다.",
                tip="'0'을 뺀 부분만 숫자값이고, 빼지 않은 문자 연산은 코드값(48~57)으로 계산된다. %c에는 코드값이 문자로 바뀌어 출력된다.")


def generate():
    return run_family(FAM, 14, [t_shift, t_digits, t_count, t_caesar, t_expr],
                      "C 문자(char)와 아스키 코드", ["C", "char", "ASCII"])
