"""Python: comprehensions and generator expressions.

Reasoning points differ per variant: filter vs conditional expression position,
nested-loop order, flatten/transpose, lazy generator evaluation, comprehension
variable scope, set/dict comprehension, zip truncation, and the list-multiplication
aliasing trap. Misconceptions are executed source rewrites.
"""
from __future__ import annotations

from families._pykit import sub
from families._pyx import make_all

SOURCES = ["past-2021-2-9", "past-2024-2-18"]
T = "Python 컴프리헨션·제너레이터 식"
PFX = "py-comp"


def filt(r):
    n = r.choice([8, 9, 10])
    code = f'''L = [x * x for x in range(1, {n}) if x % 2]
print(L, sum(L), len(L))'''
    wrong = [
        sub("if x % 2를 짝수 조건으로 보았다.", ("if x % 2]", "if x % 2 == 0]")),
        sub("range의 끝값을 포함한다고 보았다.", (f"range(1, {n})", f"range(1, {n + 1})")),
        sub("제곱을 두 배로 읽었다.", ("x * x", "x * 2")),
        sub("제곱을 하지 않고 x를 담는다고 보았다.", ("[x * x for", "[x for")),
        sub("sum 대신 len을 출력한다고 보았다.", ("sum(L)", "max(L)")),
        sub("조건 없이 모든 x를 쓴다고 보았다.", (" if x % 2", "")),
        sub("출력 순서를 거꾸로 읽었다.", ("print(L, sum(L), len(L))", "print(L[::-1], sum(L), len(L))")),
        sub("len을 하나 더 세었다.", ("len(L))", "len(L) + 1)")),
        sub("합계에서 마지막 항을 빼먹었다.", ("sum(L)", "sum(L[:-1])")),
        sub("x % 2 조건을 x > 2로 읽었다.", ("if x % 2]", "if x > 2]")),
        sub("range가 0부터 시작한다고 보고 0의 제곱까지 센다고 보았다.", (f"range(1, {n})", f"range({n})"), (" if x % 2", "")),
    ]
    pre = [f"`range(1, {n})`은 1부터 {n - 1}까지다. `if x % 2`는 나머지가 1(참)인 홀수만 통과시키고, 통과한 x마다 x*x를 리스트에 담는다. 합과 길이는 그 리스트에서 센다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=1, watch={"L"}, trace=False,
                ask="range의 끝값 제외, 홀수 필터, 제곱 표현식이 합쳐진 리스트 컴프리헨션 결과를 묻는다.",
                tip="컴프리헨션은 '앞의 표현식 · for · 뒤의 if' 순서로 읽는다. if는 값을 거르고 표현식은 담을 값을 만든다.",
                topic=T, tags=["컴프리헨션", "range", "필터"])


def nested_order(r):
    n = r.choice([3, 4])
    code = f'''p = [(i, j) for i in range({n}) for j in range(i)]
q = [i + j for j in range(i) for i in range({n})] if False else []
print(len(p), p[-1], sum(a * b for a, b in p))'''
    code = f'''p = [(i, j) for i in range({n}) for j in range(i)]
print(len(p), p[-1], sum(a * b for a, b in p))'''
    wrong = [
        sub("바깥 반복이 j라고 보았다.", ("for i in range(%d) for j in range(i)" % n, "for j in range(%d) for i in range(j)" % n)),
        sub("j의 범위를 range(i + 1)로 읽었다.", ("range(i)]", "range(i + 1)]")),
        sub("j의 범위를 range(%d)로 읽었다." % n, ("for j in range(i)]", "for j in range(%d)]" % n)),
        sub("i의 범위를 range(%d)로 읽었다." % (n - 1), ("for i in range(%d)" % n, "for i in range(%d)" % (n - 1))),
        sub("p[-1]을 첫 원소로 읽었다.", ("p[-1]", "p[0]")),
        sub("합을 a + b로 읽었다.", ("a * b", "a + b")),
        sub("len 대신 i의 최댓값을 센다고 보았다.", ("len(p)", "len(set(a for a, _ in p))")),
        sub("p[-1]을 (i, j)가 뒤바뀐 값으로 읽었다.", ("p[-1]", "p[-1][::-1]")),
        sub("합 대신 곱의 개수를 센다고 보았다.", ("sum(a * b for a, b in p)", "len([1 for a, b in p if a * b])")),
        sub("p의 길이를 n*n으로 읽었다.", ("len(p)", "%d" % (n * n))),
        sub("합을 a * b가 아닌 최댓값으로 읽었다.", ("sum(a * b for a, b in p)", "max(a * b for a, b in p)")),
    ]
    pre = [f"`for i ... for j ...`는 앞의 for가 바깥, 뒤의 for가 안쪽이다. i가 0, 1, ..., {n - 1}일 때 j는 `range(i)`이므로 i=0이면 비고, i=1이면 j=0, i=2면 j=0,1이 된다. 쌍의 개수는 0+1+...+{n - 1}이다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"p"},
                ask="이중 for 컴프리헨션에서 바깥·안쪽 반복의 순서와 안쪽 범위가 i에 의존하는 효과를 묻는다.",
                tip="컴프리헨션 안의 for는 쓴 순서대로 바깥에서 안쪽으로 중첩된다. 안쪽 범위가 바깥 변수에 의존하는지 먼저 본다.",
                topic=T, tags=["컴프리헨션", "중첩 반복"])


def cond_expr(r):
    L = [r.randint(1, 9) for _ in range(6)]
    code = f'''L = {L}
a = [x if x % 2 == 0 else -x for x in L]
b = [x for x in L if x % 2 == 0]
c = [x if x > 4 else 0 for x in L]
print(a, b, c)'''
    wrong = [
        sub("a를 b처럼 짝수만 거른다고 보았다.", ("[x if x % 2 == 0 else -x for x in L]", "[x for x in L if x % 2 == 0]")),
        sub("a에서 홀수를 0으로 바꾼다고 보았다.", ("else -x for", "else 0 for")),
        sub("a에서 짝수에 부호를 바꾼다고 보았다.", ("x if x % 2 == 0 else -x", "-x if x % 2 == 0 else x")),
        sub("b가 홀수를 거른다고 보았다.", ("[x for x in L if x % 2 == 0]", "[x for x in L if x % 2]")),
        sub("c가 4 이하를 남기고 큰 값을 0으로 바꾼다고 보았다.", ("x if x > 4 else 0", "x if x <= 4 else 0")),
        sub("c가 4 초과만 남기는 필터라 보았다.", ("[x if x > 4 else 0 for x in L]", "[x for x in L if x > 4]")),
        sub("c에서 4를 포함한다고 보았다.", ("x > 4", "x >= 4")),
        sub("a를 모두 음수로 읽었다.", ("[x if x % 2 == 0 else -x for x in L]", "[-x for x in L]")),
        sub("출력 순서를 거꾸로 읽었다.", ("print(a, b, c)", "print(c, b, a)")),
        sub("b가 짝수의 개수라 보았다.", ("print(a, b, c)", "print(a, len(b), c)")),
        sub("a와 b가 같은 결과라 보았다.", ("print(a, b, c)", "print(b, b, c)")),
    ]
    pre = ["`[식1 if 조건 else 식2 for x in L]`은 모든 원소를 변환하므로 길이가 같다. 반면 `[x for x in L if 조건]`은 조건을 통과한 원소만 남겨 길이가 줄어든다. a와 c는 변환형, b는 필터형이다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"a", "b", "c"},
                ask="컴프리헨션에서 if-else가 앞(변환)에 있을 때와 if가 뒤(필터)에 있을 때의 차이를 묻는다.",
                tip="else가 있으면 for 앞에 둔다(길이 유지). else 없는 if는 for 뒤에 둔다(길이 감소).",
                topic=T, tags=["컴프리헨션", "조건식", "필터"])


def flatten_t(r):
    m = [[r.randint(1, 9) for _ in range(3)] for _ in range(2)]
    code = f'''m = {m}
flat = [v for row in m for v in row]
t = [[row[i] for row in m] for i in range(3)]
print(flat, t, [sum(c) for c in t])'''
    wrong = [
        sub("flat의 반복 순서를 열 우선으로 읽었다.", ("[v for row in m for v in row]", "[row[i] for i in range(3) for row in m]")),
        sub("t가 m과 같다고 보았다.", ("t = [[row[i] for row in m] for i in range(3)]", "t = [list(row) for row in m]")),
        sub("t의 안쪽·바깥쪽 반복을 뒤바꿨다.", ("[[row[i] for row in m] for i in range(3)]", "[[row[i] for i in range(3)] for row in m]")),
        sub("열 합 대신 행 합을 구한다고 보았다.", ("[sum(c) for c in t]", "[sum(row) for row in m]")),
        sub("flat이 중첩 리스트 그대로라고 보았다.", ("flat = [v for row in m for v in row]", "flat = [row for row in m]")),
        sub("flat이 역순이라 보았다.", ("print(flat,", "print(flat[::-1],")),
        sub("t를 행 개수 3으로 읽어 열 하나를 놓쳤다.", ("range(3)]\nprint", "range(2)]\nprint")),
        sub("합계 목록을 전체 합 하나로 보았다.", ("[sum(c) for c in t]", "sum(flat)")),
        sub("flat 길이만 출력된다고 보았다.", ("print(flat,", "print(len(flat),")),
        sub("전치한 t를 역순 행으로 읽었다.", ("print(flat, t,", "print(flat, t[::-1],")),
        sub("전치 결과를 한 줄로 평탄화해 읽었다.", ("print(flat, t,", "print(flat, [x for c in t for x in c],")),
    ]
    pre = ["`[v for row in m for v in row]`는 행을 차례로 꺼내 그 안의 원소를 이어 붙이는 평탄화다. 전치(transpose)는 열 번호 i를 바깥 반복으로, 각 행에서 i번째를 모으는 것을 안쪽 반복으로 둔다. 그래서 t의 i번째 리스트는 m의 i번째 열이다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"flat", "t"},
                ask="2차원 리스트를 평탄화하고 전치하는 컴프리헨션의 반복 순서를 구별하는 문제다.",
                tip="평탄화는 '행 → 원소', 전치는 '열 번호 바깥, 행 안쪽'이다. 바깥 for가 결과의 바깥 리스트를 만든다.",
                topic=T, tags=["컴프리헨션", "전치", "평탄화"])


def lazy_gen(r):
    code = '''L = [1, 2, 3]
g = (x * 10 for x in L)
h = [x * 10 for x in L]
L.append(4)
first = next(g)
print(list(g), h, first, sum(g))'''
    wrong = [
        sub("제너레이터도 생성 시점 L의 내용만 본다고 보았다(append가 안 보임).", ("L.append(4)", "pass")),
        sub("h도 append를 반영한다고 보았다.", ("h = [x * 10 for x in L]", "h = [x * 10 for x in L + [4]]")),
        sub("next가 소비하지 않는다고 보았다.", ("first = next(g)", "first = next(iter([10]))")),
        sub("list(g)가 첫 값도 포함한다고 보았다.", ("first = next(g)", "first = 10")),
        sub("sum(g)가 다시 처음부터 합한다고 보았다.", ("sum(g)", "sum(x * 10 for x in L)")),
        sub("제너레이터가 한 번 소비된 뒤에도 재사용된다고 보았다.", ("sum(g)", "sum(list(x * 10 for x in L))")),
        sub("first를 40으로 읽었다.", ("first = next(g)", "first = g.__next__() * 4")),
        sub("출력 순서를 바꿨다.", ("print(list(g), h, first, sum(g))", "print(h, list(g), first, sum(g))")),
        sub("sum을 list로 보았다.", ("sum(g))", "len(list(g)))")),
        sub("append가 제너레이터 생성 이후라 4가 빠진다고 보았다.", ("L.append(4)\nfirst", "L.append(4)\nfirst"), ("list(g)", "list(g)[:-1]")),
        sub("첫 값이 원소가 아니라 1이라 보았다.", ("print(list(g), h, first,", "print(list(g), h, first // 10,")),
        sub("h 대신 h의 길이를 출력한다고 보았다.", ("print(list(g), h,", "print(list(g), len(h),")),
        sub("h에서 마지막 값을 뺀 것으로 읽었다.", ("print(list(g), h,", "print(list(g), h[:-1],")),
        sub("sum(g)가 남은 값의 합 90이라 보았다.", ("sum(g))", "sum(list(x * 10 for x in L[1:])))")),
        sub("h가 제너레이터라 소비된다고 보았다.", ("h = [x * 10 for x in L]", "h = []")),
    ]
    pre = ["제너레이터 식은 값을 요청할 때 하나씩 계산하고, 바깥 iterable L은 만들 때 `iter(L)`로 잡아 두지만 같은 리스트 객체라 이후 append가 보인다(아직 소비하지 않은 위치에서). 리스트 컴프리헨션 h는 즉시 계산되어 4가 없다. 제너레이터는 한 번 소비하면 비어, 마지막 sum(g)는 0이다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"L", "h", "first"},
                ask="제너레이터 식의 지연 평가와 일회성 소비, 리스트 컴프리헨션의 즉시 평가 차이를 묻는다.",
                tip="제너레이터는 소비하면 줄어들고 재사용되지 않는다. 같은 리스트 객체를 수정하면 소비 전 제너레이터에는 보인다.",
                topic=T, tags=["제너레이터 식", "지연 평가", "next"])


def scope(r):
    x0, n = r.choice([10, 20, 5]), r.choice([3, 4])
    code = f'''x = {x0}
a = [x for x in range({n})]
b = [x + 1 for x in a]
for x in range(2):
    pass
print(x, a[-1], b[0], len(b))'''
    wrong = [
        sub("컴프리헨션 변수가 밖으로 새어 x가 마지막 값이 된다고 보았다.", ("for x in range(2):\n    pass\n", "x = a[-1]\n")),
        sub("for 문 변수가 x를 바꾸지 않는다고 보았다.", ("for x in range(2):\n    pass\n", "")),
        sub("for 뒤 x가 range(2)의 끝값 2라 보았다.", ("print(x,", "print(2,")),
        sub("a[-1]을 n으로 읽었다.", ("a[-1]", f"{n}")),
        sub("b[0]이 1이 아니라 0이라 보았다.", ("b[0]", "a[0]")),
        sub("len(b)를 하나 더 세었다.", ("len(b))", "len(b) + 1)")),
        sub("a의 마지막 원소를 첫 원소로 읽었다.", ("a[-1]", "a[0]")),
        sub("for 변수가 첫 값 0으로 남는다고 보았다.", ("print(x,", "print(0,")),
        sub("b[0]을 마지막 원소로 읽었다.", ("b[0]", "b[-1]")),
        sub("x가 처음 값으로 유지된다고 보았다.", ("print(x,", f"print({x0},")),
        sub("len(b)를 n+1로 읽었다.", ("len(b))", f"{n + 1})")),
    ]
    pre = [f"Python 3에서 컴프리헨션은 자기만의 스코프를 가져서 안쪽 변수 x가 밖의 x({x0})를 바꾸지 않는다. 그러나 일반 `for x in range(2)` 문은 같은 스코프의 x를 직접 대입하므로 반복이 끝난 뒤에도 마지막 값 1이 남는다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"x", "a", "b"},
                ask="컴프리헨션 변수의 스코프와 일반 for 문 변수가 반복 후 남는 값의 차이를 묻는다.",
                tip="컴프리헨션의 변수는 밖으로 새지 않지만 for 문의 변수는 반복이 끝난 뒤에도 마지막 값으로 남는다.",
                topic=T, tags=["컴프리헨션", "스코프", "for"])


def setdict(r):
    n = r.choice([10, 11, 12])
    code = f'''s = {{x % 4 for x in range({n})}}
d = {{w: len(w) for w in ["ab", "cde", "ab", "f"]}}
e = {{k: v for k, v in d.items() if v > 1}}
print(sorted(s), len(d), e)'''
    wrong = [
        sub("집합 컴프리헨션이 중복을 유지한다고 보아 개수를 range 길이로 읽었다.", ("sorted(s),", f"len(list(range({n}))),")),
        sub("나머지가 4 이하의 값까지 나온다고 보았다.", ("x % 4", "x % 5")),
        sub("d의 길이를 원소 수 4로 보았다.", ("len(d)", "4")),
        sub("e에서 길이 1인 항목도 남는다고 보았다.", ("if v > 1", "if v >= 1")),
        sub("e에서 길이 2 이하만 남는다고 보았다.", ("if v > 1", "if v < 3")),
        sub("e의 조건을 v > 2로 읽었다.", ("if v > 1", "if v > 2")),
        sub("집합 정렬이 내림차순이라 보았다.", ("sorted(s)", "sorted(s, reverse=True)")),
        sub("s가 딕셔너리라 보았다.", ("print(sorted(s),", "print(len(s),")),
        sub("e가 키 목록이라 보았다.", (", e)", ", list(e))")),
        sub("e의 값이 길이가 아닌 첫 글자라 보았다.", ("print(sorted(s), len(d), e)", "print(sorted(s), len(d), {k: k[0] for k in e})")),
        sub("d의 길이를 중복 제거 후 하나 더 적게 읽었다.", ("len(d)", "len(d) - 1")),
    ]
    pre = [f"`{{x % 4 for x in range({n})}}`는 중괄호 안에 `키: 값`이 없어 집합 컴프리헨션이다. 나머지는 0~3뿐이라 중복이 합쳐진다. 딕셔너리 컴프리헨션의 \"ab\"는 같은 키가 두 번이라 한 항목만 남고, 이후 e는 값이 1보다 큰 항목만 거른다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=1, watch={"s", "d", "e"},
                ask="집합·딕셔너리 컴프리헨션의 중복 키 처리와 조건 필터를 묻는다.",
                tip="`{식 for}`는 집합, `{키: 값 for}`는 딕셔너리다. 중복 키는 하나로 합쳐진다.",
                topic=T, tags=["집합 컴프리헨션", "딕셔너리 컴프리헨션"])


def zipc(r):
    A = [r.randint(1, 5) for _ in range(4)]
    B = [r.randint(2, 6) for _ in range(3)]
    code = f'''A = {A}
B = {B}
p = [a * b for a, b in zip(A, B)]
q = [a for a in A if a in B]
print(p, sum(p), q, list(zip(A, B))[-1])'''
    wrong = [
        sub("zip이 긴 쪽 길이까지 이어진다고 보았다.", ("zip(A, B)]", "zip(A, B + [1])]")),
        sub("곱 대신 합이라 보았다.", ("a * b", "a + b")),
        sub("q가 B의 원소를 모은다고 보았다.", ("[a for a in A if a in B]", "[b for b in B if b in A]")),
        sub("q가 A에 없는 것만 남긴다고 보았다.", ("if a in B]", "if a not in B]")),
        sub("마지막 쌍을 A의 마지막과 B의 마지막으로 읽었다.", ("list(zip(A, B))[-1]", "(A[-1], B[-1])")),
        sub("sum을 평균으로 읽었다.", ("sum(p)", "sum(p) // len(p)")),
        sub("p의 길이를 A의 길이로 읽었다.", ("sum(p),", "len(A),")),
        sub("zip의 마지막 쌍을 첫 쌍으로 읽었다.", ("[-1])", "[0])")),
        sub("q에서 중복 원소를 한 번만 센다고 보았다.", ("[a for a in A if a in B]", "sorted({a for a in A if a in B})")),
        sub("p 대신 q를 먼저 출력한다고 보았다.", ("print(p, sum(p), q,", "print(q, sum(p), p,")),
        sub("sum(p)를 모든 쌍의 곱 합(전체 곱)으로 읽었다.", ("sum(p)", "sum(a * b for a in A for b in B)")),
    ]
    pre = [f"zip은 가장 짧은 쪽 길이({len(B)})에서 멈추므로 A의 마지막 원소는 쌍에 들어가지 못한다. p는 같은 위치끼리의 곱이다. q는 A의 원소 중 B에도 있는 것을 A의 순서와 중복 그대로 모은다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"p", "q"},
                ask="zip의 길이 절단과 두 리스트를 함께 도는 컴프리헨션, in 필터를 묻는다.",
                tip="zip은 짧은 쪽에서 끝난다. in 필터는 원래 리스트의 순서와 중복을 그대로 가져온다.",
                topic=T, tags=["zip", "컴프리헨션", "필터"])


def str_comp(r):
    s = r.choice(["programming", "education", "information"])
    code = f'''s = "{s}"
v = "aeiou"
a = "".join(c.upper() for c in s if c not in v)
b = [c for c in s if c in v]
c = {{ch: s.count(ch) for ch in s if s.count(ch) > 1}}
print(a, len(b), c)'''
    wrong = [
        sub("모음을 대문자로 바꾼다고 보았다.", ("if c not in v)", "if c in v)")),
        sub("upper를 하지 않는다고 보았다.", ("c.upper()", "c")),
        sub("b가 자음이라 보았다.", ("if c in v]", "if c not in v]")),
        sub("c가 두 번 이상이 아니라 한 번 이상이라 보았다.", ("> 1}", "> 0}")),
        sub("c의 값이 개수가 아니라 True라 보았다.", ("ch: s.count(ch)", "ch: True")),
        sub("a의 문자 순서가 뒤집힌다고 보았다.", ("a = \"\".join(c.upper()", "a = \"\".join(c.upper()"), ("print(a,", "print(a[::-1],")),
        sub("len(b)를 서로 다른 모음 수로 읽었다.", ("len(b)", "len(set(b))")),
        sub("a를 리스트 문자열로 읽었다.", ("print(a,", "print(list(a),")),
        sub("c를 정렬된 키 목록으로 읽었다.", (", c)", ", sorted(c))")),
        sub("모음 판단을 v가 아니라 'aeio'로 읽었다(u 누락).", ('v = "aeiou"', 'v = "aeio"')),
        sub("c에서 가장 많은 글자만 남긴다고 보았다.", (", c)", ", max(c.items(), key=lambda t: t[1]))")),
    ]
    pre = [f"문자열은 문자 단위로 순회된다. a는 모음이 아닌 문자를 대문자로 바꿔 이어 붙인 문자열이고, b는 모음만 모은 리스트다. c는 두 번 이상 나온 글자의 개수를 키별로 센 딕셔너리라 처음 등장한 순서로 출력된다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"a", "b", "c"},
                ask="문자열을 순회하는 세 가지 컴프리헨션(join, 리스트, 딕셔너리)의 조건과 결과를 묻는다.",
                tip="join에 제너레이터 식을 넘기면 조건을 통과한 문자만 이어 붙인다. 딕셔너리 컴프리헨션의 키 중복은 한 번만 남는다.",
                topic=T, tags=["문자열", "컴프리헨션", "join"])


def mult_alias(r):
    n = r.choice([2, 3])
    code = f'''a = [[0] * 2] * {n}
b = [[0] * 2 for _ in range({n})]
a[0][1] = 5
b[0][1] = 5
print(a, b, a[1] is a[0], b[1] is b[0])'''
    wrong = [
        sub("a의 행도 독립이라 첫 행만 바뀐다고 보았다.", ("a = [[0] * 2] * %d" % n, "a = [[0] * 2 for _ in range(%d)]" % n)),
        sub("b의 행이 같은 객체라 모두 바뀐다고 보았다.", ("b = [[0] * 2 for _ in range(%d)]" % n, "b = [[0] * 2] * %d" % n)),
        sub("is 결과가 모두 False라 보았다.", ("a[1] is a[0]", "False")),
        sub("is 결과가 모두 True라 보았다.", ("b[1] is b[0]", "True")),
        sub("[0] * 2가 [0, 0, 0]이 된다고 보았다.", ("a[0][1] = 5", "a[0][1] = 5\na[0].append(0)")),
        sub("대입 인덱스를 [0]으로 읽었다.", ("a[0][1] = 5", "a[0][0] = 5")),
        sub("두 대입이 열 방향으로 반영된다고 보았다.", ("b[0][1] = 5", "[r.__setitem__(1, 5) for r in b]")),
        sub("두 리스트 모두 첫 행만 바뀐다고 보았다.", ("a = [[0] * 2] * %d" % n, "a = [[0] * 2 for _ in range(%d)]" % n), ("a[1] is a[0]", "False")),
        sub("두 리스트 모두 모든 행이 바뀐다고 보았다.", ("b = [[0] * 2 for _ in range(%d)]" % n, "b = [[0] * 2] * %d" % n), ("b[1] is b[0]", "True")),
        sub("a만 변하고 b는 변하지 않는다고 보았다.", ("b[0][1] = 5", "pass")),
        sub("출력 순서를 바꿨다.", ("print(a, b, a[1] is a[0], b[1] is b[0])", "print(b, a, a[1] is a[0], b[1] is b[0])")),
    ]
    pre = [f"`[[0] * 2] * {n}`은 안쪽 리스트 하나를 {n}번 참조하는 리스트다. 행이 모두 같은 객체라 `a[0][1] = 5`가 모든 행에 보이고 `a[1] is a[0]`는 True다. 컴프리헨션은 반복마다 새 리스트를 만들어 행이 독립이다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"a", "b"},
                ask="리스트 곱셈(*)이 안쪽 리스트를 복사하지 않고 같은 객체를 반복 참조한다는 점을 묻는다.",
                tip="`[x] * n`은 x가 가변 객체이면 같은 객체를 n번 가리킨다. 2차원 배열은 컴프리헨션으로 만든다.",
                topic=T, tags=["리스트 곱셈", "별칭", "2차원 리스트"])


def idx_prev(r):
    L = [r.randint(1, 9) for _ in range(6)]
    code = f'''L = {L}
up = [i for i, v in enumerate(L) if v > L[i - 1]]
d = [L[i] - L[i - 1] for i in range(1, len(L))]
print(up, d, max(d), sum(1 for x in d if x > 0))'''
    wrong = [
        sub("i=0에서 L[-1]이 마지막 원소가 아닌 오류/빈 값이라 보아 0을 제외했다.", ("enumerate(L)", "enumerate(L) if False else enumerate(L[:0])")),
        sub("i - 1이 이전 원소가 아니라 다음 원소라 보았다.", ("L[i - 1]) ]", "L[i - 1]]"), ),
        sub("v > L[i - 1]를 v >= L[i - 1]로 읽었다.", ("v > L[i - 1]", "v >= L[i - 1]")),
        sub("차이를 앞에서 뒤를 뺀 값으로 읽었다.", ("L[i] - L[i - 1]", "L[i - 1] - L[i]")),
        sub("range(1, len(L))를 range(len(L))로 읽었다.", ("range(1, len(L))", "range(len(L))")),
        sub("max(d)를 min(d)로 읽었다.", ("max(d)", "min(d)")),
        sub("양수 개수를 음수 개수로 읽었다.", ("if x > 0", "if x < 0")),
        sub("up이 값 목록이라 보았다.", ("[i for i, v in", "[v for i, v in")),
        sub("up이 증가 구간 수라 보았다.", ("print(up,", "print(len(up),")),
        sub("enumerate가 1부터 번호를 매긴다고 보았다.", ("enumerate(L)", "enumerate(L, 1)")),
        sub("d의 길이를 len(L)로 읽었다.", ("max(d), sum", "len(L), sum")),
    ]
    wrong = [w for w in wrong if w[1][0] != ("L[i - 1]) ]", "L[i - 1]]")]
    pre = ["파이썬의 음수 인덱스 때문에 `L[i - 1]`은 i=0일 때 `L[-1]`, 즉 마지막 원소다. 오류가 나지 않고 첫 원소를 마지막 원소와 비교하게 된다. 반면 d는 range(1, ...)로 시작해 이런 순환 비교가 없다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"up", "d"},
                ask="인덱스 i-1이 i=0에서 음수 인덱스로 순환해 마지막 원소를 가리키는 점을 포함한 비교 결과를 묻는다.",
                tip="L[i-1]은 i=0일 때 L[-1]이다. 이전 원소와 비교하려면 반복을 1부터 시작해야 안전하다.",
                topic=T, tags=["enumerate", "음수 인덱스", "컴프리헨션"])


def sorted_slice(r):
    w = r.choice([["pear", "fig", "apple", "kiwi", "date"], ["tea", "milk", "jam", "bread", "egg"]])
    code = f'''w = {w}
a = sorted(w, key=len)
b = sorted(w, key=lambda s: (-len(s), s))[:2]
c = [s[::-1] for s in a][::2]
print(a, b, c)'''
    wrong = [
        sub("key=len 정렬이 사전순이라 보았다.", ("sorted(w, key=len)", "sorted(w)")),
        sub("key=len이 내림차순이라 보았다.", ("sorted(w, key=len)", "sorted(w, key=len, reverse=True)")),
        sub("b에서 길이가 짧은 것부터 2개라 보았다.", ("(-len(s), s)", "(len(s), s)")),
        sub("b의 동률을 사전 역순으로 읽었다.", ("(-len(s), s)", "(-len(s), [-ord(x) for x in s])")),
        sub("c의 [::2]를 [:2]로 읽었다.", ("[::2]", "[:2]")),
        sub("c의 문자열을 뒤집지 않는다고 보았다.", ("s[::-1]", "s")),
        sub("c가 두 번째부터 한 칸씩이라 보았다.", ("[::2]", "[1::2]")),
        sub("a의 동률이 입력 순서를 뒤집는다고 보았다.", ("sorted(w, key=len)", "sorted(w, key=len)[::-1]")),
        sub("b의 슬라이스를 [:3]으로 읽었다.", ("[:2]", "[:3]")),
        sub("c가 a의 원본 단어 중 짝수 번째라 보았다.", ("[s[::-1] for s in a][::2]", "a[::2]")),
        sub("b를 길이만으로 정렬해 동률은 입력 순서라 보았다.", ("(-len(s), s)", "-len(s)")),
    ]
    pre = ["sorted의 key=len은 길이로 비교하며 동률이면 원래 순서를 유지하는 안정 정렬(stable sort)이다. b는 (-길이, 단어) 튜플이라 긴 것부터, 길이가 같으면 사전순이다. c는 a의 각 단어를 뒤집은 뒤 0, 2, 4번째를 고른다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"a", "b", "c"},
                ask="key 정렬의 안정성, 음수 길이를 쓴 내림차순, 컴프리헨션 뒤 슬라이스 간격을 묻는다.",
                tip="key가 같으면 입력 순서가 유지된다(안정 정렬). 튜플 key의 -len은 길이 내림차순을 뜻한다.",
                topic=T, tags=["sorted", "key", "슬라이스"])


FUNCS = [filt, nested_order, cond_expr, flatten_t, lazy_gen, scope, setdict, zipc, str_comp, mult_alias, idx_prev, sorted_slice]


def generate():
    return make_all(PFX, FUNCS, "py-comp", SOURCES)
