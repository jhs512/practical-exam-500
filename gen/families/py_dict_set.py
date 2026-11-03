"""Python: dict and set operations (counting, grouping, merge, inversion, set algebra).

Each variant is a short program whose key reasoning point differs: get-default
counting, setdefault grouping, update override order, comprehension key collisions,
literal duplicate keys, set algebra operators, set mutation methods, live keys views.
Misconceptions are source rewrites that are executed, so wrong outputs are real.
"""
from __future__ import annotations

from core import rng
from families._pykit import sub
from families._pyx import make_all

SOURCES = ["past-2023-2-14", "past-2024-1-15"]
T = "Python 딕셔너리·집합"
PFX = "py-dictset"


def count_words(r, k):
    ws = r.choice(["x y x z y x", "ab cd ab ab cd ef", "k j k k j"])
    if k == 0:
        code = f'''s = "{ws}"
d = {{}}
for w in s.split():
    d[w] = d.get(w, 0) + 1
print(d)'''
        wrong = [
            sub("매번 1을 대입하는 것으로 보아 모든 값이 1이라고 보았다.", ("d.get(w, 0) + 1", "1")),
            sub("get의 기본값을 1로 보아 처음 나온 단어부터 2가 된다고 보았다.", ("d.get(w, 0)", "d.get(w, 1)")),
            sub("s.split() 대신 문자 하나씩 순회한다고 보아 공백까지 센다.", ("s.split()", "s")),
            sub("값을 더하지 않고 get의 결과만 대입한다고 보아 모두 0이다.", ("d.get(w, 0) + 1", "d.get(w, 0)")),
            sub("처음 나온 단어만 등록하고 이후 반복은 무시한다고 보았다.", ("    d[w] = d.get(w, 0) + 1", "    if w not in d:\n        d[w] = 1")),
            sub("딕셔너리가 키를 정렬해 보관한다고 보아 키 역순으로 출력했다.", ("print(d)", "print(dict(sorted(d.items(), reverse=True)))")),
            sub("딕셔너리 출력이 나중에 들어온 키부터 보인다고 보았다.", ("print(d)", "print(dict(reversed(d.items())))")),
            sub("print(d)가 키 목록만 보여 준다고 보았다.", ("print(d)", "print(list(d))")),
            sub("값만 출력된다고 보았다.", ("print(d)", "print(list(d.values()))")),
            sub("서로 다른 단어 수만 센다고 보았다.", ("print(d)", "print(len(d))")),
            sub("값 대신 그 시점의 딕셔너리 크기가 저장된다고 보았다.", ("d.get(w, 0) + 1", "len(d) + 1")),
        ]
        pre = ["`d.get(w, 0)`은 키가 없으면 0을 돌려주므로, `d[w] = d.get(w, 0) + 1`은 처음 보는 단어를 1로 만들고 이미 있는 단어는 1씩 키운다. 딕셔너리는 키가 처음 삽입된 순서를 유지해 출력한다(Python 3.7+)."]
        return dict(code=code, wrong=wrong, pre=pre, difficulty=1, watch={"d", "w"},
                    ask="get의 기본값으로 횟수를 세는 딕셔너리의 최종 상태와 출력 순서를 묻는다.",
                    tip="d[k] = d.get(k, 0) + 1은 빈도 세기의 관용구다. 출력 순서는 키가 처음 삽입된 순서다.",
                    topic=T, tags=["dict", "get", "빈도"])
    code = f'''s = "{ws}"
d = {{}}
for w in s.split():
    d[w] = d.get(w, 0) + 1
m = max(d, key=d.get)
print(m, d[m], len(d))'''
    wrong = [
        sub("max(d)가 값이 아닌 키의 사전순 최댓값이라 보았다.", ("max(d, key=d.get)", "max(d)")),
        sub("가장 적게 나온 단어를 골랐다고 보았다.", ("max(d, key=d.get)", "min(d, key=d.get)")),
        sub("max가 마지막 키를 고른다고 보았다.", ("max(d, key=d.get)", "list(d)[-1]")),
        sub("max가 첫 키를 고른다고 보았다.", ("max(d, key=d.get)", "list(d)[0]")),
        sub("횟수 대신 단어 전체 개수를 센다고 보았다.", ("d[m]", "len(s.split())")),
        sub("서로 다른 단어 수 대신 전체 단어 수를 len으로 보았다.", ("len(d)", "len(s.split())")),
        sub("횟수 대신 단어 글자 수를 출력한다고 보았다.", ("d[m]", "len(m)")),
        sub("빈도 세기에서 get 기본값을 1로 오해했다.", ("d.get(w, 0)", "d.get(w, 1)")),
        sub("print가 튜플 형태로 출력한다고 보았다.", ("print(m, d[m], len(d))", "print((m, d[m], len(d)))")),
        sub("max가 값만 반환한다고 보았다.", ("m = max(d, key=d.get)", "m = max(d.values())")),
        sub("key 없이 값 비교 대신 정렬된 키의 마지막을 골랐다.", ("max(d, key=d.get)", "sorted(d)[-1]")),
        sub("횟수에 1을 더해 출력했다.", ("d[m],", "d[m] + 1,")),
        sub("횟수에서 1을 뺐다.", ("d[m],", "d[m] - 1,")),
        sub("종류 수를 하나 덜 세었다.", ("len(d))", "len(d) - 1)")),
        sub("종류 수를 하나 더 세었다.", ("len(d))", "len(d) + 1)")),
    ]
    pre = ["먼저 단어별 횟수 딕셔너리를 만든다. `max(d, key=d.get)`은 값(횟수)이 가장 큰 키를 돌려준다. 값이 같으면 먼저 삽입된 키가 선택된다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"d", "m"},
                ask="빈도 딕셔너리에서 key 함수를 이용해 최빈 단어를 찾고 그 횟수와 종류 수를 묻는다.",
                tip="max(딕셔너리, key=딕셔너리.get)은 값 기준 최대 키를 준다. key를 빼면 키 자체를 비교한다.",
                topic=T, tags=["dict", "max", "key"])


def group_len(r, k=0):
    ws = r.choice(["to be or not to be", "red sun sky moon sea", "an ox ate a big pear"])
    code = f'''g = {{}}
for w in "{ws}".split():
    g.setdefault(len(w), []).append(w)
print(g)'''
    wrong = [
        sub("키마다 마지막 단어 하나만 남는 리스트라고 보았다.", ("g.setdefault(len(w), []).append(w)", "g[len(w)] = [w]")),
        sub("키를 단어 자체로 보았다.", ("g.setdefault(len(w), [])", "g.setdefault(w, [])")),
        sub("키를 단어 길이 대신 첫 글자로 보았다.", ("setdefault(len(w), [])", "setdefault(w[0], [])")),
        sub("리스트가 아니라 단어 하나만 보관한다고 보았다.", ("g.setdefault(len(w), []).append(w)", "g[len(w)] = w")),
        sub("같은 길이 단어가 집합이 되어 중복 제거된다고 보았다.", ("g.setdefault(len(w), []).append(w)", "g.setdefault(len(w), set()).add(w)")),
        sub("같은 길이 단어를 앞쪽에 끼워 넣는다고 보았다.", ("append(w)", "insert(0, w)")),
        sub("출력이 키 내림차순으로 정렬된다고 보았다.", ("print(g)", "print(dict(sorted(g.items(), reverse=True)))")),
        sub("값 목록만 출력된다고 보았다.", ("print(g)", "print(list(g.values()))")),
        sub("키 목록만 출력된다고 보았다.", ("print(g)", "print(list(g))")),
        sub("그룹별 개수만 출력된다고 보았다.", ("print(g)", "print({n: len(v) for n, v in g.items()})")),
        sub("출력 순서가 나중에 생긴 키부터라고 보았다.", ("print(g)", "print(dict(reversed(g.items())))")),
    ]
    pre = ["`g.setdefault(key, [])`는 키가 없을 때만 빈 리스트를 넣고, 어느 쪽이든 그 키의 리스트를 돌려준다. 그래서 `.append(w)`가 바로 이어져 길이별 목록이 만들어진다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"g", "w"},
                ask="setdefault로 길이별 단어 목록을 만들 때 키 생성 시점과 각 목록의 내용을 묻는다.",
                tip="setdefault는 '없으면 넣고, 있든 없든 값을 돌려준다'. 반환된 리스트에 append가 이어지는 모양을 기억한다.",
                topic=T, tags=["dict", "setdefault", "그룹화"])


def dict_access(r, k=0):
    a, b = r.sample(range(2, 9), 2)
    code = f'''d = {{"a": {a}, "b": {b}}}
x = d.pop("a")
y = d.pop("z", {a + b})
d["c"] = x + y
z = d.get("q")
print(d, y, z)'''
    wrong = [
        sub("pop의 기본값을 0으로 보았다.", (f'd.pop("z", {a + b})', 'd.pop("z", 0)')),
        sub("pop이 키를 지우지 않고 값만 읽는다고 보았다.", ('x = d.pop("a")', 'x = d["a"]')),
        sub("get이 없는 키에 0을 돌려준다고 보았다.", ('d.get("q")', 'd.get("q", 0)')),
        sub("없는 키의 get이 키 이름 문자열을 돌려준다고 보았다.", ('z = d.get("q")', 'z = "q"')),
        sub("pop의 기본값이 딕셔너리에도 들어간다고 보았다.", (f'y = d.pop("z", {a + b})', f'y = d.setdefault("z", {a + b})')),
        sub("c의 값을 x만으로 보았다.", ('d["c"] = x + y', 'd["c"] = x')),
        sub("c의 값을 y만으로 보았다.", ('d["c"] = x + y', 'd["c"] = y')),
        sub("새 키가 맨 앞에 들어간다고 보았다.", ('d["c"] = x + y', 'd = {"c": x + y, **d}')),
        sub("pop한 키가 그대로 남는다고 보았다.", ('x = d.pop("a")', 'x = d.get("a")')),
        sub("get의 결과가 문자열 'None'이라 보았다.", ('z = d.get("q")', "z = 'None'")),
        sub("pop(\"a\")가 마지막 항목을 꺼낸다고 보았다.", ('x = d.pop("a")', 'x = d.popitem()[1]')),
    ]
    pre = ["pop은 키를 지우면서 값을 돌려주고, 키가 없으면 두 번째 인자(기본값)를 돌려줄 뿐 딕셔너리에 넣지 않는다. get은 없는 키에 대해 기본값이 없으면 None을 돌려준다. 딕셔너리에는 'b'와 새로 대입한 'c'가 남는다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"d", "x", "y", "z"},
                ask="pop, pop의 기본값, get, 새 키 대입이 딕셔너리를 어떻게 바꾸는지 묻는다.",
                tip="pop은 지우고 반환, get은 읽기만 한다. 둘 다 키가 없을 때 기본값을 딕셔너리에 넣지 않는다.",
                topic=T, tags=["dict", "pop", "get"])


def dict_merge(r, k):
    a, b, c = r.sample(range(1, 9), 3)
    if k == 0:
        code = f'''p = {{"x": {a}, "y": {b}}}
q = {{"y": {c}, "z": {a + c}}}
m = {{**p, **q}}
p.update(q)
print(m == p, m["y"], len(m), list(m))'''
        wrong = [
            sub("뒤의 q가 아니라 앞의 p 값이 이긴다고 보았다.", ("{**p, **q}", "{**q, **p}")),
            sub("update가 같은 키를 무시한다고 보았다.", ("p.update(q)", "p.update({k: v for k, v in q.items() if k not in p})")),
            sub("update가 아무것도 하지 않는다고 보았다.", ("p.update(q)", "pass")),
            sub("키 개수를 겹치는 키까지 중복으로 센다고 보았다.", ("len(m)", "len(p) + len(q)")),
            sub("키 개수를 하나 더 세었다.", ("len(m)", "len(m) + 1")),
            sub("키 순서가 사전순 역순으로 정렬된다고 보았다.", ("list(m)", "sorted(m, reverse=True)")),
            sub("키 순서가 q의 키부터라고 보았다.", ("list(m)", "list({**q, **p})")),
            sub("m[\"y\"]를 두 값의 합으로 보았다.", ('m["y"]', f'{b + c}')),
            sub("m[\"y\"]를 p 쪽 값으로 보았다.", ('m["y"]', f'{b}')),
            sub("m과 p가 서로 다르다고 보았다.", ("m == p", "False")),
            sub("m[\"z\"]를 출력한다고 보았다.", ('m["y"]', 'm["z"]')),
        ]
        pre = ["`{**p, **q}`는 p를 펼친 뒤 q를 펼치므로 같은 키는 나중(q)의 값으로 덮인다. `p.update(q)`도 같은 규칙으로 p를 제자리에서 바꾼다. 따라서 m과 p는 키·값·순서가 같다. 키 순서는 x, y(처음 위치 유지), z다."]
        return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"m", "p"},
                    ask="딕셔너리 병합에서 같은 키의 값이 어느 쪽으로 정해지는지, update와 언패킹이 같은 결과인지 묻는다.",
                    tip="병합은 항상 '나중 것이 이긴다'. 이미 있던 키는 처음 삽입된 위치를 유지한 채 값만 바뀐다.",
                    topic=T, tags=["dict", "update", "병합"])
    code = f'''a = {{"k": {a}, "m": {b}}}
b = dict(a)
b["k"] = {c}
a.update(m={a + b + c}, n=0)
print(a, b)'''
    wrong = [
        sub("dict(a)가 별칭이라 b를 바꾸면 a도 바뀐다고 보았다.", ("b = dict(a)", "b = a")),
        sub("update(m=...)가 새 키만 추가한다고 보았다.", (f"a.update(m={a + b + c}, n=0)", "a.update(n=0)")),
        sub("update가 b에도 반영된다고 보았다.", ("b = dict(a)\n", "b = a\n"), ("b[\"k\"] = %d" % c, "b[\"k\"] = %d\nb = a" % c)),
        sub("b[\"k\"] 대입이 a를 바꾼다고 보았다.", ('b["k"] = %d' % c, 'a["k"] = %d' % c)),
        sub("update의 n=0이 무시된다고 보았다.", (", n=0)", ")")),
        sub("update가 아무 것도 하지 않는다고 보았다.", (f"a.update(m={a + b + c}, n=0)", "pass")),
        sub("출력 순서가 b, a라고 보았다.", ("print(a, b)", "print(b, a)")),
        sub("복사 시점이 update 이후라 b에 m, n이 보인다고 보았다.", ("b = dict(a)\nb[", f"a.update(m={a + b + c}, n=0)\nb = dict(a)\nb[")),
        sub("m의 값이 갱신되지 않고 n만 추가된다고 보았다.", (f"m={a + b + c}", f"m={b}")),
        sub("b에 k 갱신이 없다고 보았다.", ('b["k"] = %d' % c, "pass")),
        sub("b에서 m, n을 포함해 복사본도 갱신된다고 보았다.", ("print(a, b)", "print(a, {**b, 'm': %d, 'n': 0})" % (a + b + c))),
        sub("a의 k도 바뀐다고 보았다.", ("print(a, b)", "print({**a, 'k': %d}, b)" % c)),
        sub("b에 n만 보인다고 보았다.", ("print(a, b)", "print(a, {**b, 'n': 0})")),
    ]
    pre = ["`dict(a)`는 얕은 복사(shallow copy)로 새 딕셔너리를 만든다. 값이 정수라서 이후 b를 고치거나 a를 고쳐도 서로 영향이 없다. update는 키워드 인자로도 키를 추가·갱신한다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=1, watch={"a", "b"},
                ask="딕셔너리 복사(dict(a))와 update 이후 원본과 복사본이 각각 어떤 상태인지 묻는다.",
                tip="dict(a), a.copy(), {**a}는 새 객체, b = a는 같은 객체다. 복사 시점 이후의 변경은 서로 보이지 않는다.",
                topic=T, tags=["dict", "copy", "update"])


def invert(r, k=0):
    vals = r.choice([[1, 2, 1], [3, 3, 4], [5, 6, 5]])
    items = ", ".join(f'"{c}": {v}' for c, v in zip("abc", vals))
    code = f'''d = {{{items}}}
inv = {{v: k for k, v in d.items()}}
cnt = {{v: 0 for v in d.values()}}
print(inv, len(inv), len(cnt))'''
    wrong = [
        sub("같은 값이 있어도 키가 모두 유지된다고 보아 개수를 3으로 봤다.", ("len(inv)", "len(d)")),
        sub("중복 값이면 먼저 나온 키가 남는다고 보았다.", ("{v: k for k, v in d.items()}", "dict(reversed([(v, k) for k, v in d.items()]))")),
        sub("역변환에서 값이 리스트로 모인다고 보았다.", ("{v: k for k, v in d.items()}", "{v: [k2 for k2, v2 in d.items() if v2 == v] for v in d.values()}")),
        sub("역변환이 키와 값을 바꾸지 않고 그대로 둔다고 보았다.", ("{v: k for k, v in d.items()}", "dict(d)")),
        sub("cnt의 길이를 값의 전체 개수로 보았다.", ("len(cnt)", "len(d.values())")),
        sub("inv의 순서가 반대라고 보았다.", ("inv = {v: k for k, v in d.items()}", "inv = dict(reversed({v: k for k, v in d.items()}.items()))")),
        sub("inv 길이를 값의 합으로 보았다.", ("len(inv)", "sum(d.values())")),
        sub("inv가 키 정렬된 채 출력된다고 보았다.", ("print(inv,", "print(dict(sorted(inv.items(), reverse=True)),")),
        sub("cnt가 중복도 따로 키로 둔다고 보았다.", ("len(cnt)", "len(d)")),
        sub("inv의 값에 같은 값을 가진 키 문자열이 모두 이어 붙는다고 보았다.", ("print(inv,", "print({v: ''.join(k for k in d if d[k] == v) for v in d.values()},")),
        sub("cnt 길이를 inv 길이에 1을 더한 값으로 보았다.", ("len(cnt))", "len(inv) + 1)")),
        sub("inv 길이를 하나 덜 세었다.", ("len(inv),", "len(inv) - 1,")),
        sub("inv에서 키 부분만 출력된다고 보았다.", ("print(inv,", "print(list(inv),")),
        sub("inv에서 값 부분만 출력된다고 보았다.", ("print(inv,", "print(list(inv.values()),")),
    ]
    pre = ["딕셔너리 컴프리헨션은 항목을 앞에서부터 차례로 대입한다. 같은 키가 다시 나오면 값이 덮어써지고, 키의 위치는 처음 삽입된 곳에 남는다. 그래서 값이 겹치면 역변환 결과는 원본보다 항목이 줄고, 겹친 값에는 마지막 키가 남는다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"inv", "cnt"},
                ask="값이 중복되는 딕셔너리를 키-값 반전할 때 충돌한 항목이 어떻게 되는지와 컴프리헨션 키 중복을 묻는다.",
                tip="딕셔너리의 키는 유일하다. 반전이나 컴프리헨션에서 키가 겹치면 항목 수가 줄고 마지막 값이 남는다.",
                topic=T, tags=["dict", "컴프리헨션", "반전"])


def literal_dup(r, k=0):
    a, b, c = r.sample(range(1, 9), 3)
    code = f'''d = {{"a": {a}, "b": {b}, "a": {c}}}
d["b"] += d["a"]
s = {{{a}, {b}, {a}, {c}}}
print(len(d), d["a"], d["b"], len(s))'''
    wrong = [
        sub("딕셔너리 리터럴의 중복 키가 모두 유지된다고 보아 길이를 3으로 봤다.", ("len(d)", "3")),
        sub("중복 키에서 먼저 쓴 값이 남는다고 보았다.", ('d["b"] += d["a"]', f'd["a"] = {a}\nd["b"] += d["a"]')),
        sub("집합의 중복 원소가 모두 유지된다고 보아 길이를 4로 봤다.", ("len(s))", "4)")),
        sub("b += a에서 a를 처음 값으로 더했다.", ('d["b"] += d["a"]', f'd["b"] += {a}')),
        sub("+=가 b를 덮어써 a 값만 남긴다고 보았다.", ('d["b"] += d["a"]', 'd["b"] = d["a"]')),
        sub("b에 변화가 없다고 보았다.", ('d["b"] += d["a"]', "pass")),
        sub("집합 길이를 원소 합으로 보았다.", ("len(s))", "sum(s))")),
        sub("a를 첫 값으로 출력했다.", ('d["a"], d["b"]', f'{a}, d["b"]')),
        sub("len(d)를 키와 값의 총 개수로 보았다.", ("len(d)", "len(d) * 2")),
        sub("집합 길이를 하나 더 세었다.", ("len(s))", "len(s) + 1)")),
        sub("집합 길이를 하나 덜 세었다.", ("len(s))", "len(s) - 1)")),
    ]
    pre = ["딕셔너리 리터럴에서 같은 키가 두 번 나오면 나중 값이 앞 값을 덮어쓰고 항목은 하나만 남는다(키 'a' → %d). 집합 리터럴도 같은 값은 하나로 합쳐진다. 그래서 길이는 서로 다른 값/키의 수다." % c]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"d", "s"},
                ask="리터럴에 중복 키·중복 원소가 있을 때 길이와 최종 값을 묻는다.",
                tip="중복 키는 마지막 값이 이긴다. 집합은 값이 같으면 하나다. 코드 위에서부터 한 줄씩 상태를 적는다.",
                topic=T, tags=["dict", "set", "중복"])


def set_algebra(r, k=0):
    A = sorted(r.sample(range(1, 10), 5))
    B = sorted(set(r.sample(range(1, 10), 4)) | set(A[:2]))
    code = f'''a = {{{", ".join(map(str, A))}}}
b = {{{", ".join(map(str, B))}}}
print(sorted(a | b), sorted(a & b))
print(sorted(a - b), sorted(a ^ b))'''
    wrong = [
        sub("합집합을 교집합으로 보았다.", ("sorted(a | b)", "sorted(a & b)")),
        sub("교집합을 합집합으로 보았다.", ("sorted(a & b)", "sorted(a | b)")),
        sub("a - b를 b - a로 보았다.", ("sorted(a - b)", "sorted(b - a)")),
        sub("^를 합집합으로 보았다.", ("sorted(a ^ b)", "sorted(a | b)")),
        sub("^를 a - b로 보았다.", ("sorted(a ^ b)", "sorted(a - b)")),
        sub("^를 교집합으로 보았다.", ("sorted(a ^ b)", "sorted(a & b)")),
        sub("첫 줄의 두 결과 순서를 바꿨다.", ("print(sorted(a | b), sorted(a & b))", "print(sorted(a & b), sorted(a | b))")),
        sub("둘째 줄의 두 결과 순서를 바꿨다.", ("print(sorted(a - b), sorted(a ^ b))", "print(sorted(a ^ b), sorted(a - b))")),
        sub("합집합이 중복을 허용한다고 보았다.", ("sorted(a | b)", "sorted(list(a) + list(b))")),
        sub("a - b를 대칭차로 보았다.", ("sorted(a - b)", "sorted(a ^ b)")),
        sub("a - b를 합집합으로 보았다.", ("sorted(a - b)", "sorted(a | b)")),
    ]
    pre = ["| 합집합(둘 중 하나라도), & 교집합(둘 다), - 차집합(왼쪽에만), ^ 대칭차집합(한쪽에만)이다. 각 결과를 sorted로 정렬해 출력하므로 집합의 순서에 의존하지 않는다.",
           "a = %s, b = %s" % (A, B)]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=1, trace=False,
                ask="집합 연산자 네 가지(|, &, -, ^)의 의미를 구별해 결과를 구하는 문제다.",
                tip="-는 방향이 있고(a-b ≠ b-a), ^는 '한쪽에만 있는 것'(합집합 − 교집합)이다.",
                topic=T, tags=["set", "연산자"])


def set_mutate(r, k=0):
    a, b, c = r.sample(range(1, 9), 3)
    code = f'''s = {{{a}, {b}}}
s.add({c})
s.add({a})
s.discard({c + 10})
s.update([{c + 1}, {c + 1}, {b}])
s.remove({b})
print(sorted(s), len(s), max(s))'''
    wrong = [
        sub("update 후 b가 지워지지 않는다고 보았다.", (f"s.remove({b})", "pass")),
        sub("update의 중복이 모두 들어간다고 보고 길이를 1 크게 보았다.", ("len(s),", "len(s) + 1,")),
        sub("discard가 없는 값을 넣는다고 보았다.", (f"s.discard({c + 10})", f"s.add({c + 10})")),
        sub("add(c)가 없다고 보았다.", (f"s.add({c})\n", "")),
        sub("update 인자를 통째로 한 원소로 추가한다고 보았다.", (f"s.update([{c + 1}, {c + 1}, {b}])", f"s.add({c + 1})")),
        sub("remove 뒤 b가 다시 들어간다고 보았다.", (f"s.remove({b})", f"s.remove({b}); s.add({b})")),
        sub("길이를 처음 크기 2로 보았다.", ("len(s),", "2,")),
        sub("update가 새 원소를 넣지 못한다고 보았다.", (f"s.update([{c + 1}, {c + 1}, {b}])", "pass")),
        sub("discard가 최댓값을 지운다고 보았다.", (f"s.discard({c + 10})", "s.discard(max(s))")),
        sub("remove가 최솟값을 지운다고 보았다.", (f"s.remove({b})", "s.remove(min(s))")),
        sub("정렬이 내림차순이라 보았다.", ("sorted(s)", "sorted(s, reverse=True)")),
        sub("max(s)를 최솟값으로 보았다.", ("max(s))", "min(s))")),
        sub("max(s)를 원소 합으로 보았다.", ("max(s))", "sum(s))")),
        sub("add(a)가 값을 바꿔 a가 사라진다고 보았다.", (f"s.add({a})", f"s.discard({a})")),
    ]
    pre = ["집합은 중복을 허용하지 않으므로 add·update로 이미 있는 값을 넣어도 변화가 없다. discard는 없는 값이어도 오류가 없고, remove는 있어야 한다. update에 들어 있는 b도 이미 있어서 변화가 없으며 마지막 remove가 b를 지운다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"s"},
                ask="집합의 add·discard·update·remove가 중복과 없는 값을 어떻게 처리하는지 묻는다.",
                tip="add/update는 이미 있는 값을 무시하고, discard는 없는 값을 무시한다. remove만 없는 값에 오류다.",
                topic=T, tags=["set", "add", "remove"])


def set_dedupe(r, k=0):
    L = [r.randint(1, 6) for _ in range(8)]
    code = f'''L = {L}
u = list(set(L))
d = dict.fromkeys(L)
print(len(L), len(u), list(d), sorted(set(L), reverse=True)[:2])'''
    wrong = [
        sub("집합 변환이 중복을 줄이지 않는다고 보았다.", ("len(u)", "len(L)")),
        sub("dict.fromkeys가 정렬해 준다고 보았다.", ("list(d)", "sorted(d)")),
        sub("dict.fromkeys가 마지막 등장 순서를 따른다고 보았다.", ("list(d)", "list(dict.fromkeys(L[::-1]))")),
        sub("상위 2개가 가장 작은 값이라 보았다.", ("sorted(set(L), reverse=True)[:2]", "sorted(set(L))[:2]")),
        sub("중복을 포함해 상위 2개를 골랐다.", ("sorted(set(L), reverse=True)[:2]", "sorted(L, reverse=True)[:2]")),
        sub("두 길이를 서로 바꿔 읽었다.", ("len(L), len(u)", "len(u), len(L)")),
        sub("list(d)가 값(None)의 목록이라 보았다.", ("list(d)", "list(d.values())")),
        sub("슬라이스 [:2]를 [-2:]로 읽었다.", ("[:2]", "[-2:]")),
        sub("오름차순 마지막 2개로 읽었다.", ("sorted(set(L), reverse=True)[:2]", "sorted(set(L))[-2:]")),
        sub("len(u)를 최댓값으로 읽었다.", ("len(u)", "max(u)")),
        sub("fromkeys 결과의 키 순서를 set 순서(정렬)와 같다고 보았다.", ("list(d)", "sorted(set(L))")),
    ]
    pre = ["set(L)은 중복을 없애지만 순서를 보장하지 않으므로 sorted로 정렬해야 결과가 정해진다. `dict.fromkeys(L)`은 키로 L의 값을 넣고 중복은 첫 등장 위치만 남기므로 '순서를 지키는 중복 제거'로 쓰인다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"u", "d"},
                ask="중복 제거(set, dict.fromkeys)의 길이와 순서 보존 여부, 정렬 후 슬라이스를 묻는다.",
                tip="순서까지 지키며 중복을 없애려면 dict.fromkeys. set은 순서에 기대지 말고 sorted로 감싼다.",
                topic=T, tags=["set", "fromkeys", "중복 제거"])


def subset(r, k=0):
    code = '''a = {1, 2, 3}
b = {1, 2, 3, 4}
c = {3, 2, 1}
print(a < b, a <= c, a < c, b >= a)
print(a == c, a is c, a.isdisjoint({5}), 4 in b)'''
    wrong = [
        sub("a < c도 참이라 보았다(같은 집합은 진부분집합이 아니다).", ("a < c", "a <= c")),
        sub("a <= c가 거짓이라 보았다.", ("a <= c", "a < c")),
        sub("a == c가 순서 때문에 거짓이라 보았다.", ("a == c", "list(a) == [3, 2, 1]")),
        sub("a is c가 값이 같으니 참이라 보았다.", ("a is c", "a == c")),
        sub("isdisjoint({5})가 거짓이라 보았다.", ("a.isdisjoint({5})", "a.isdisjoint({3})")),
        sub("b >= a가 거짓이라 보았다.", ("b >= a", "b <= a")),
        sub("a < b가 거짓이라 보았다.", ("a < b", "b < a")),
        sub("4 in b가 거짓이라 보았다.", ("4 in b", "4 in a")),
        sub("a == c와 a is c를 서로 바꿔 읽었다.", ("a == c, a is c", "a is c, a == c")),
        sub("a < b와 a <= c 두 개를 모두 반대로 읽었다.", ("a < b, a <= c", "b < a, a < c")),
        sub("isdisjoint를 겹치는 원소가 있으면 참이라고 읽었다.", ("a.isdisjoint({5})", "not a.isdisjoint({5})")),
    ]
    pre = ["집합에서 `<`는 진부분집합, `<=`는 부분집합(같아도 참)이다. 집합의 동등 비교 `==`는 원소만 보고 순서는 무시하므로 {3, 2, 1}과 같다. `is`는 같은 객체인지 묻기 때문에 값이 같아도 다른 객체면 거짓이다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, trace=False,
                ask="집합의 부분집합 비교(<, <=), 동등(==)과 동일성(is), isdisjoint, in의 결과를 묻는다.",
                tip="< 는 '진'부분집합(같으면 거짓), <= 는 같아도 참. ==는 값 비교, is는 같은 객체 비교다.",
                topic=T, tags=["set", "부분집합", "is"])


def sort_by_value(r, k=0):
    vs = r.sample(range(1, 9), 4)
    code = f'''d = {{"w": {vs[0]}, "x": {vs[1]}, "y": {vs[2]}, "z": {vs[3]}}}
a = sorted(d, key=d.get)
b = sorted(d.items(), key=lambda t: -t[1])[0]
c = sorted(d, key=lambda k: (d[k] % 2, k))
print(a, b, c)'''
    wrong = [
        sub("sorted(d)처럼 키를 사전순으로 정렬한다고 보았다.", ("sorted(d, key=d.get)", "sorted(d)")),
        sub("key=d.get 정렬이 내림차순이라 보았다.", ("sorted(d, key=d.get)", "sorted(d, key=d.get, reverse=True)")),
        sub("b가 값이 가장 작은 항목이라 보았다.", ("-t[1]", "t[1]")),
        sub("b가 키만 나온다고 보았다.", ("[0]\n", "[0][0]\n")),
        sub("b가 값만 나온다고 보았다.", ("[0]\n", "[0][1]\n")),
        sub("c의 정렬 기준을 값 크기로 보았다.", ("(d[k] % 2, k)", "d[k]")),
        sub("c에서 홀수가 먼저 온다고 보았다.", ("(d[k] % 2, k)", "(1 - d[k] % 2, k)")),
        sub("c에서 같은 홀짝일 때 키 역순이라 보았다.", ("(d[k] % 2, k)", "(d[k] % 2, -ord(k))")),
        sub("a가 정렬된 값 목록이라 보았다.", ("a = sorted(d, key=d.get)", "a = sorted(d.values())")),
        sub("c가 키 사전순 단순 정렬이라 보았다.", ("sorted(d, key=lambda k: (d[k] % 2, k))", "sorted(d)")),
        sub("c의 key가 홀짝 하나뿐이라 같은 홀짝은 원래 순서를 유지한다고 보았다.", ("(d[k] % 2, k)", "d[k] % 2")),
    ]
    pre = ["key 함수는 각 원소에서 정렬 기준값을 뽑는 함수다. sorted(d, key=d.get)은 값 오름차순으로 키를 나열하고, `-t[1]`은 부호를 뒤집어 값이 큰 항목이 앞에 오게 한다. c는 (홀짝, 키) 튜플로 비교하므로 짝수(0)가 먼저, 같은 홀짝이면 키 순서다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"a", "b", "c"},
                ask="key 인자로 값·부호·튜플을 써서 딕셔너리를 정렬한 결과 세 가지를 묻는다.",
                tip="key는 정렬 기준값을 만드는 함수다. 튜플 key는 앞 요소가 같을 때만 뒤 요소를 비교한다.",
                topic=T, tags=["sorted", "key", "dict"])


def keys_view(r, k=0):
    code = '''d = {"a": 1, "b": 2}
ks = d.keys()
vs = list(d.values())
d["c"] = 3
d["a"] = 9
del d["b"]
print(list(ks), vs, len(ks), "b" in ks)'''
    wrong = [
        sub("keys()가 호출 시점의 스냅샷이라 변경이 반영되지 않는다고 보았다.", ("ks = d.keys()", "ks = list(d.keys())")),
        sub("vs도 실시간으로 반영된다고 보았다.", ("vs = list(d.values())", "vs = d.values()")),
        sub("del d[\"b\"]가 일어나지 않았다고 보았다.", ('del d["b"]', "pass")),
        sub("c가 추가되지 않는다고 보았다.", ('d["c"] = 3', "pass")),
        sub("len(ks)가 스냅샷 시점 길이 2라 보았다.", ("len(ks)", "2")),
        sub("\"b\" in ks가 참이라 보았다.", ('"b" in ks', "True")),
        sub("list(ks)가 항목 전체를 보여 준다고 보았다.", ("list(ks)", "list(d.items())")),
        sub("vs가 갱신된 값이라 보았다.", ("vs, ", "[9, 3], ")),
        sub("del이 마지막 키를 지운다고 보았다.", ('del d["b"]', "del d[list(d)[-1]]")),
        sub("키 순서가 역순으로 바뀐다고 보았다.", ("list(ks)", "sorted(ks, reverse=True)")),
        sub("keys 뷰도 스냅샷이고 vs도 실시간이라고 서로 바꿔 보았다.", ("ks = d.keys()", "ks = list(d.keys())"), ("vs = list(d.values())", "vs = d.values()")),
    ]
    pre = ["`d.keys()`는 복사본이 아니라 딕셔너리와 연결된 뷰(view)다. 이후 d에 일어난 추가·삭제가 그대로 비친다. 반면 `list(d.values())`는 그 순간의 값으로 만든 독립된 리스트라 이후 변경이 반영되지 않는다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"d", "vs"},
                ask="keys() 뷰의 실시간 반영과 list(...) 스냅샷의 차이를 묻는다.",
                tip="keys/values/items는 뷰라서 원본 변경을 따라간다. 고정하려면 list()로 감싼다.",
                topic=T, tags=["dict", "keys", "view"])


def popitem(r, k=0):
    code = '''d = {}
for i, ch in enumerate("pqrs"):
    d[ch] = i * 2
a = d.popitem()
b = d.popitem()
d["p"] += 5
d.pop("q")
print(a, b, d)'''
    wrong = [
        sub("popitem이 첫 항목을 꺼낸다고 보았다(FIFO).", ("a = d.popitem()", "a = ('p', 0); del d['p']")),
        sub("popitem이 키만 돌려준다고 보았다.", ("a = d.popitem()", "a = d.popitem()[0]")),
        sub("popitem이 값만 돌려준다고 보았다.", ("b = d.popitem()", "b = d.popitem()[1]")),
        sub("두 번째 popitem이 같은 항목을 반복한다고 보았다.", ("b = d.popitem()", "b = a")),
        sub("enumerate의 i를 1부터 센다고 보았다.", ('enumerate("pqrs")', 'enumerate("pqrs", 1)')),
        sub("+= 5가 값을 5로 덮어쓴다고 보았다.", ('d["p"] += 5', 'd["p"] = 5')),
        sub("pop(\"q\")가 지우지 않는다고 보았다.", ('d.pop("q")', "d.get('q')")),
        sub("i * 2를 i로 보았다.", ("i * 2", "i")),
        sub("두 번째 popitem이 첫 항목을 꺼낸다고 보았다.", ("b = d.popitem()", "b = ('p', 0); del d['p']")),
        sub("마지막 print가 d만 출력한다고 보았다.", ("print(a, b, d)", "print(d)")),
        sub("d 대신 남은 키 목록을 출력한다고 보았다.", ("print(a, b, d)", "print(a, b, list(d))")),
        sub("d 대신 남은 항목 수를 출력한다고 보았다.", ("print(a, b, d)", "print(a, b, len(d))")),
        sub("a와 b의 출력 순서가 뒤바뀐다고 보았다.", ("print(a, b, d)", "print(b, a, d)")),
        sub("pop 대상을 p로 읽었다.", ('d.pop("q")', 'd.pop("p")')),
    ]
    pre = ["Python 3.7부터 `popitem()`은 가장 나중에 삽입된 항목부터 (키, 값) 튜플로 꺼낸다(LIFO). s, r 순으로 꺼내고 남은 p, q 중 p의 값이 5 늘고 q가 삭제된다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"d", "a", "b"},
                ask="popitem의 꺼내는 순서(후입선출)와 이후 +=, pop의 반영을 묻는다.",
                tip="popitem은 마지막 삽입 항목부터 (키, 값) 튜플로 꺼낸다. pop(key)와 헷갈리지 않는다.",
                topic=T, tags=["dict", "popitem", "enumerate"])


def nested_acc(r, k=0):
    code = '''rows = [("a", 3), ("b", 5), ("a", 4), ("c", 1), ("b", 2)]
tot = {}
for name, n in rows:
    tot[name] = tot.get(name, []) + [n]
res = {k: sum(v) for k, v in tot.items() if len(v) > 1}
print(tot["a"], res)'''
    wrong = [
        sub("get 기본값 리스트에 값이 누적되지 않고 덮어쓰기라 보았다.", ("tot.get(name, []) + [n]", "[n]")),
        sub("조건 len(v) > 1을 무시하고 모든 키를 포함했다.", (" if len(v) > 1", "")),
        sub("합계 대신 개수를 구했다.", ("sum(v)", "len(v)")),
        sub("조건을 len(v) == 1로 보았다.", ("len(v) > 1", "len(v) == 1")),
        sub("tot['a']가 첫 값만이라 보았다.", ('tot["a"]', 'tot["a"][:1]')),
        sub("tot['a']가 합이라 보았다.", ('tot["a"]', 'sum(tot["a"])')),
        sub("튜플 언패킹이 name과 n을 바꿔 받는다고 보았다.", ("for name, n in rows:", "for n, name in rows:")),
        sub("리스트에 값이 앞쪽에 쌓인다고 보았다.", ("tot.get(name, []) + [n]", "[n] + tot.get(name, [])")),
        sub("res의 합계에 최댓값을 사용한다고 보았다.", ("sum(v)", "max(v)")),
        sub("res가 항목 리스트라 보았다.", ('print(tot["a"], res)', 'print(tot["a"], sorted(res.items()))')),
        sub("res에 c도 포함된다고 보았다.", (" if len(v) > 1", " if len(v) >= 1")),
    ]
    pre = ["`tot.get(name, []) + [n]`은 기존 리스트(또는 빈 리스트) 뒤에 n을 붙인 새 리스트를 만들어 대입한다. 그래서 a는 [3, 4], b는 [5, 2], c는 [1]이 된다. 컴프리헨션의 if는 원소가 둘 이상인 키만 남긴다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=2, watch={"tot", "res"},
                ask="튜플 언패킹 반복과 get 기본값 리스트 누적, 조건부 딕셔너리 컴프리헨션을 함께 묻는다.",
                tip="누적형 딕셔너리는 반복마다 '기존 값 + 새 값'을 다시 대입한다. 컴프리헨션의 if는 항목 필터다.",
                topic=T, tags=["dict", "컴프리헨션", "누적"])


def anagram(r, k=0):
    code = '''w = ["tea", "eat", "ate", "tan", "nat", "bat"]
g = {}
for s in w:
    g.setdefault("".join(sorted(s)), set()).add(s)
n = sorted(len(v) for v in g.values())
print(len(g), n, sorted(g["aet"]))'''
    wrong = [
        sub("그룹 키를 정렬하지 않은 단어 자체로 보았다.", ('"".join(sorted(s))', "s")),
        sub("그룹 키를 단어의 길이로 보았다.", ('"".join(sorted(s))', "len(s)")),
        sub("그룹 키를 첫 글자로 보았다.", ('"".join(sorted(s))', "s[0]")),
        sub("개수 목록을 내림차순으로 보았다.", ("n = sorted(len(v) for v in g.values())", "n = sorted((len(v) for v in g.values()), reverse=True)")),
        sub("g[\"aet\"]에 첫 단어만 있다고 보았다.", ('sorted(g["aet"])', '[w[0]]')),
        sub("그룹 수를 단어 수로 보았다.", ("len(g)", "len(w)")),
        sub("개수 목록을 단어 수 하나로 보았다.", ("n = sorted(len(v) for v in g.values())", "n = [len(w)]")),
        sub("sorted(g['aet'])가 역순이라 보았다.", ('sorted(g["aet"])', 'sorted(g["aet"], reverse=True)')),
        sub("그룹 수를 하나 덜 세었다.", ("len(g)", "len(g) - 1")),
        sub("개수 목록을 합계 하나로 보았다.", ("n = sorted(len(v) for v in g.values())", "n = sum(len(v) for v in g.values())")),
        sub("출력 키를 다른 그룹 ant로 읽었다.", ('sorted(g["aet"])', 'sorted(g["ant"])')),
        sub("그룹 수를 하나 더 세었다.", ("len(g)", "len(g) + 1")),
        sub("개수 목록이 그룹별 첫 단어 목록이라 보았다.", ("n = sorted(len(v) for v in g.values())", "n = [min(v) for v in g.values()]")),
        sub("g['aet']가 비어 있다고 보았다.", ('sorted(g["aet"])', "[]")),
    ]
    pre = ["단어의 글자를 정렬한 문자열은 애너그램(anagram)끼리 같은 키가 된다. tea, eat, ate는 'aet', tan, nat는 'ant', bat는 'abt'다. setdefault로 키마다 집합을 만들어 단어를 담으므로 그룹은 3개이고 크기는 1, 2, 3이다."]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=3, watch={"g", "n"},
                ask="정렬한 글자를 키로 쓰는 그룹화(setdefault + set)의 결과를 묻는다.",
                tip="'정렬한 글자'는 애너그램 판별용 정규화 키다. 키를 만드는 식을 먼저 값으로 바꿔 본다.",
                topic=T, tags=["dict", "set", "애너그램"])


FUNCS = [
    lambda r: count_words(r, 0), lambda r: count_words(r, 1), group_len, dict_access,
    lambda r: dict_merge(r, 0), lambda r: dict_merge(r, 1), invert, literal_dup,
    set_algebra, set_mutate, set_dedupe, subset, sort_by_value, keys_view, popitem,
    nested_acc, anagram,
]


def generate():
    return make_all(PFX, FUNCS, "py-dictset", SOURCES)
