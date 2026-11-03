"""Python: list methods (append/extend/insert/pop/remove/sort/reverse/del) and
sort() vs sorted().

Each variant applies a different operation sequence (chosen to hit different
reasoning points) to a random list. Each misconception is a rewrite of one line into
what a confused reader believes it does (append vs extend, pop() vs pop(0), remove by
index, insert after the position, sort() returning the list, ...), then executed.
"""
from __future__ import annotations

from core import rng
from families._pykit import build_retry, josa, sub

SOURCES = ["past-2022-1-7", "past-2023-1-15"]


def op(kind, r, a):
    """Return (line, desc, [(new_line, note)]). `a` is the current list (simulated
    only to pick sensible arguments; the real output comes from execution)."""
    n = len(a)
    if kind == "append_list":
        x = [r.randint(1, 9), r.randint(1, 9)]
        line = f"a.append({x})"
        a.append(x)
        return line, f"`{line}`은 리스트 {x} 자체를 원소 하나로 끝에 붙인다(길이 +1).", [
            (f"a.extend({x})", "append에 리스트를 넘기면 그 원소들이 낱개로 펼쳐진다고 보았다. 펼치는 것은 extend다."),
            (f"a.insert(0, {x})", "append가 맨 앞에 붙인다고 보았다.")]
    if kind == "extend":
        x = [r.randint(1, 9), r.randint(1, 9)]
        line = f"a.extend({x})"
        a.extend(x)
        return line, f"`{line}`은 {x}의 원소를 하나씩 끝에 이어 붙인다(길이 +{len(x)}).", [
            (f"a.append({x})", "extend가 리스트를 통째로 한 원소로 넣는다고 보았다. 그것은 append의 동작이다."),
            (f"a[:0] = {x}", "extend가 앞쪽에 이어 붙인다고 보았다.")]
    if kind == "append":
        x = r.randint(10, 19)
        line = f"a.append({x})"
        a.append(x)
        return line, f"`{line}`은 {x}를 맨 끝에 추가한다.", [
            (f"a.insert(0, {x})", "append가 맨 앞에 추가한다고 보았다."),
            ("pass", "append가 새 리스트를 반환할 뿐 a를 바꾸지 않는다고 보았다. 리스트 메서드는 제자리에서 수정한다.")]
    if kind == "insert":
        i = r.randint(1, max(1, n - 2))
        x = r.randint(20, 29)
        line = f"a.insert({i}, {x})"
        a.insert(i, x)
        return line, f"`{line}`은 인덱스 {i} 자리에 {josa(x, "을/를")} 넣고, 원래 그 자리부터의 원소를 한 칸씩 뒤로 민다.", [
            (f"a.insert({i + 1}, {x})", f"인덱스 {i}의 원소 '뒤'에 끼워 넣는다고 보았다. insert는 그 위치 '앞'에 넣어 새 원소가 인덱스 {i}가 된다."),
            (f"a[{i}] = {x}", f"insert가 인덱스 {i}의 값을 덮어쓴다고 보았다. insert는 기존 원소를 밀어낸다.")]
    if kind == "pop_end":
        line = "x = a.pop()"
        a.pop()
        return line, "`x = a.pop()`은 마지막 원소를 꺼내 x에 담고 리스트에서 지운다.", [
            ("x = a.pop(0)", "인자 없는 pop()이 맨 앞 원소를 꺼낸다고 보았다(큐처럼 생각). 기본값은 마지막 원소다."),
            ("x = a[-1]", "pop이 값을 읽기만 하고 리스트에서 지우지 않는다고 보았다.")]
    if kind == "pop_idx":
        i = r.randint(1, n - 2)
        line = f"x = a.pop({i})"
        v = a.pop(i)
        alt = [(f"x = a.pop({i - 1})", f"pop({i})의 인덱스를 1부터 세어 {i}번째 원소(인덱스 {i - 1})를 꺼냈다.")]
        if v != i and i in a:
            alt.append((f"a.remove({i}); x = {i}", f"pop의 인자 {i}를 위치가 아닌 값으로 보아 값 {i}를 지웠다."))
        else:
            alt.append((f"x = a[{i}]", "pop이 값을 읽기만 하고 리스트에서 지우지 않는다고 보았다."))
        return line, f"`{line}`은 인덱스 {i}의 원소를 꺼내 x에 담고 리스트에서 지운다. 뒤 원소들은 한 칸씩 당겨진다.", alt
    if kind == "remove":
        dup = [v for v in a if isinstance(v, int) and a.count(v) >= 2]
        cand = dup or [v for v in a if isinstance(v, int)]
        v = cand[0]
        line = f"a.remove({v})"
        idx = a.index(v)
        a.remove(v)
        alts = [(f"a = [e for e in a if e != {v}]",
                 f"remove가 값 {v}를 모두 지운다고 보았다. remove는 처음 만나는 하나만 지운다.")] if dup else []
        if v < n + 1:
            alts.append((f"del a[{v}]", f"remove({v})의 {v}를 인덱스로 보아 a[{v}]를 지웠다. remove의 인자는 값이다."))
        alts.append((f"a.pop()", f"remove가 마지막 원소를 지운다고 보았다. remove는 값 {v}를 찾아 지운다."))
        return line, f"`{line}`은 앞에서부터 찾아 처음 나오는 값 {v}(인덱스 {idx}) 하나만 지운다.", alts
    if kind == "sort":
        line = "a.sort()"
        a.sort()
        return line, "`a.sort()`는 a 자체를 오름차순으로 바꾸고 None을 반환한다.", [
            ("a.sort(reverse=True)", "sort()가 큰 값부터(내림차순) 정렬한다고 보았다. 기본은 오름차순이다."),
            ("pass", "sort()가 정렬된 새 리스트를 돌려줄 뿐 a는 그대로라고 보았다. 그것은 sorted()의 동작이다.")]
    if kind == "reverse":
        line = "a.reverse()"
        a.reverse()
        return line, "`a.reverse()`는 a의 순서를 제자리에서 뒤집는다(정렬이 아니다).", [
            ("a.sort(reverse=True)", "reverse()를 내림차순 정렬로 보았다. reverse는 현재 순서를 거꾸로 할 뿐이다."),
            ("pass", "reverse()가 새 리스트만 만들고 a는 그대로라고 보았다.")]
    if kind == "del_slice":
        i = r.randint(0, 1)
        j = i + 2
        line = f"del a[{i}:{j}]"
        del a[i:j]
        return line, f"`{line}`은 인덱스 {i}부터 {j - 1}까지 두 원소를 지운다(끝 {j}는 제외).", [
            (f"del a[{i}:{j + 1}]", f"끝 인덱스 {j}까지 포함해 세 원소를 지웠다고 보았다."),
            (f"del a[{i}]", "슬라이스 범위를 첫 인덱스 하나로 보았다.")]
    raise ValueError(kind)


PLANS = [
    # (ops, final print, difficulty)
    (["append_list", "extend", "pop_end"], "print(a, len(a), x)", 1),
    (["insert", "remove", "append"], "print(a)", 1),
    (["extend", "pop_idx", "insert", "reverse"], "print(a, x)", 2),
    (["remove", "append_list", "pop_idx"], "print(a, len(a), x)", 2),
    (["sort", "insert", "pop_end", "extend"], "print(a, x)", 2),
    (["del_slice", "sort", "append", "pop_idx"], "print(a, x)", 2),
    (["reverse", "remove", "insert", "pop_end"], "print(a, x)", 2),
    (["append", "extend", "del_slice", "reverse"], "print(a)", 1),
    ("sorted", None, 2),
    ("sort_none", None, 3),
    (["insert", "extend", "remove", "pop_idx", "sort"], "print(a, x)", 3),
]


def plan_ops(k, r):
    ops, final, diff = PLANS[k]
    for _ in range(200):
        base = [r.randint(1, 9) for _ in range(r.choice([5, 6]))]
        if "remove" in ops:
            j = r.randrange(len(base) - 1)
            base[j + 1:j + 1] = [base[j]] if r.random() < 0.7 else []
        a = list(base)
        lines, descs, muts = [], [], []
        ok = True
        for kd in ops:
            if kd == "sort" and any(isinstance(v, list) for v in a):
                ok = False
                break
            line, d, m = op(kd, r, a)
            lines.append(line)
            descs.append(d)
            muts.append(m)
        if ok and len(set(lines)) == len(lines) and "a.remove" not in final:
            return base, lines, descs, muts, final, diff
    raise RuntimeError(k)


def make(k, t=0):
    r = rng(f"py-list-methods-{k}-{t}")
    plan = PLANS[k][0]
    if plan == "sorted":
        base = [r.randint(1, 30) for _ in range(5)]
        code = "\n".join([f"a = {base}", "b = sorted(a)", "a.append(min(b) - 1)", "c = sorted(a, reverse=True)",
                          "print(a, b[0], c[0], b[-1])"])
        wrong = [
            sub("sorted(a)가 a 자체도 정렬한다고 보았다. sorted는 새 리스트를 반환하고 원본은 그대로다.", ("b = sorted(a)", "a.sort(); b = a")),
            sub("b = sorted(a) 이후 b와 a가 같은 리스트라고 보아 a.append가 b에도 반영된다고 보았다.", ("b = sorted(a)", "b = a; b.sort()")),
            sub("reverse=True를 무시하고 c도 오름차순으로 보았다.", ("sorted(a, reverse=True)", "sorted(a)")),
            sub("sorted(a)가 원래 순서를 뒤집는다고 보았다.", ("b = sorted(a)", "b = a[::-1]")),
            sub("min(b) - 1 대신 min(b)를 추가한다고 보아 -1을 놓쳤다.", ("min(b) - 1", "min(b)")),
            sub("append가 맨 앞에 넣는다고 보았다.", ("a.append(min(b) - 1)", "a.insert(0, min(b) - 1)")),
            sub("b[-1]을 b의 첫 원소로 읽었다.", ("b[-1])", "b[0])")),
            sub("c를 원본 a의 역순으로 보았다. reverse=True는 정렬 후 내림차순이다.", ("sorted(a, reverse=True)", "a[::-1]")),
            sub("sorted(a)가 a를 바꾸고, reverse=True도 무시했다.", ("b = sorted(a)", "a.sort(); b = a"), ("sorted(a, reverse=True)", "sorted(a)")),
            sub("b가 a의 별칭이라 append가 b에도 반영되고, 정렬도 되지 않는다고 보았다.", ("b = sorted(a)", "b = a")),
            sub("sorted(a, reverse=True)가 a 자체를 내림차순으로 바꾼다고 보았다. sorted는 원본을 바꾸지 않는다.",
                ("c = sorted(a, reverse=True)", "a.sort(reverse=True); c = a")),
        ]
        pre = [
            "sorted(a)는 a를 건드리지 않고 정렬된 새 리스트를 만든다. 그래서 b는 정렬본, a는 원래 순서 그대로다.",
            "a.append(min(b) - 1)은 원본 a의 끝에 최솟값보다 1 작은 값을 붙인다. b는 별개의 리스트이므로 바뀌지 않는다. c는 바뀐 a를 내림차순으로 정렬한 또 다른 새 리스트다.",
        ]
        return dict(code=code, wrong=wrong, pre=pre, difficulty=2,
                    ask="sorted()가 새 리스트를 만드는지, 원본 리스트를 바꾸는지, 이후 append가 어느 리스트에 반영되는지를 묻는다.",
                    post="a는 원래 순서에 새 값이 하나 붙은 상태이고, b[0]과 b[-1]은 처음 a의 최솟값과 최댓값, c[0]은 새 값이 포함된 a의 최댓값이다. 출력은 {OUT}이다.",
                    tip="list.sort()는 제자리 정렬 후 None 반환, sorted()는 새 리스트 반환이다. 정렬 뒤 원본을 수정하는 코드가 나오면 두 리스트를 따로 적어 추적한다.",
                    topic="Python 리스트 메서드", tags=["sorted", "sort", "리스트"])
    if plan == "sort_none":
        base = [r.randint(1, 30) for _ in range(5)]
        code = "\n".join([f"a = {base}", "b = a.sort()", "c = a", "c.append(0)", "print(b, a, len(c))"])
        wrong = [
            sub("a.sort()가 정렬된 리스트를 반환한다고 보았다. sort()는 None을 반환한다.", ("b = a.sort()", "a.sort(); b = list(a)")),
            sub("a.sort()가 a를 바꾸지 않는다고 보았다(None 반환과 제자리 정렬을 함께 오해).", ("b = a.sort()", "b = None")),
            sub("c = a를 복사로 보아 c.append(0)이 a에 반영되지 않는다고 보았다.", ("c = a\n", "c = a[:]\n")),
            sub("sort()가 정렬된 리스트를 반환하며 b가 a와 같은 객체라고 보았다.", ("b = a.sort()", "a.sort(); b = a")),
            sub("sort()가 내림차순 정렬이라고 보았다.", ("b = a.sort()", "b = a.sort(reverse=True)")),
            sub("c = a를 복사로 보았고, sort()가 None을 반환한다는 점도 놓쳤다.", ("b = a.sort()", "a.sort(); b = list(a)"), ("c = a\n", "c = a[:]\n")),
            sub("append(0)이 맨 앞에 들어간다고 보았다.", ("c.append(0)", "c.insert(0, 0)")),
            sub("append(0) 뒤에 정렬이 다시 적용된다고 보아 0이 앞에 온다고 보았다.", ("c.append(0)", "c.append(0); c.sort()")),
            sub("c = a를 복사로 보고, sort()도 a를 바꾸지 않는다고 보았다.", ("b = a.sort()", "b = None"), ("c = a\n", "c = a[:]\n")),
            sub("len(c)가 append 전 길이라고 보았다.", ("len(c)", "len(c) - 1")),
        ]
        pre = [
            "a.sort()는 a를 제자리에서 오름차순으로 바꾸고 반환값은 None이다. 따라서 b에는 None이 들어간다.",
            "c = a는 복사가 아니라 같은 리스트 객체에 이름을 하나 더 붙이는 대입이다. c.append(0)은 그 하나뿐인 리스트를 바꾸므로 a를 출력해도 0이 보인다.",
        ]
        return dict(code=code, wrong=wrong, pre=pre, difficulty=3,
                    ask="sort()의 반환값, 제자리 정렬 여부, c = a 대입이 별칭(alias)인지 복사인지를 함께 묻는다.",
                    post="b는 None, a는 정렬 후 끝에 0이 붙은 리스트, len(c)는 같은 리스트의 길이다. 출력은 {OUT}이다.",
                    tip="'변수 = 리스트.메서드()' 형태가 보이면 그 메서드의 반환값부터 확인한다. sort, reverse, append, extend, insert는 모두 None을 반환한다.",
                    topic="Python 리스트 메서드", tags=["sort", "None", "별칭"])
    base, lines, descs, muts, final, diff = plan_ops(k, r)
    code = "\n".join([f"a = {base}"] + lines + [final])
    wrong = []
    for line, ms in zip(lines, muts):
        for new, note in ms:
            wrong.append(sub(note, (line, new)))
    if len(lines) >= 2:
        wrong.append(sub("두 줄에서 함께 실수했다. " + muts[0][0][1] + " " + muts[1][0][1],
                         (lines[0], muts[0][0][0]), (lines[1], muts[1][0][0])))
        wrong.append(sub("두 줄에서 함께 실수했다. " + muts[-1][0][1] + " " + muts[1][-1][1],
                         (lines[-1], muts[-1][0][0]), (lines[1], muts[1][-1][0])))
    if "len(a)" in final:
        wrong.append(sub(f"len(a)를 처음 리스트 길이({len(base)})로 보았다. len은 print 시점의 길이를 센다.",
                         ("len(a)", str(len(base)))))
    pre = ["각 메서드는 a를 제자리에서(in-place) 바꾼다. 줄마다 동작은 다음과 같다.\n" +
           "\n".join(f"{n + 1}) {d}" for n, d in enumerate(descs))]
    return dict(code=code, wrong=wrong, pre=pre, difficulty=diff, watch={"a", "x"},
                ask="리스트에 메서드를 차례로 적용한 뒤의 최종 상태(와 꺼낸 값)를 묻는다. 메서드마다 위치·값·원소 단위 중 무엇을 다루는지가 핵심 조건이다.",
                post="마지막 print가 출력하는 값은 {OUT}이다.",
                tip="append/extend는 '하나 vs 펼쳐서', pop/remove는 '인덱스 vs 값', insert는 '그 위치 앞'으로 기억하고, 줄마다 리스트 전체를 다시 적어 둔다.",
                topic="Python 리스트 메서드", tags=["리스트", "append", "pop", "remove"])


def generate():
    return [build_retry(id=f"py-list-methods-{k + 1:02d}", make=lambda t, k=k: make(k, t),
                        family="py-list-methods", sources=SOURCES) for k in range(len(PLANS))]
