"""Python: indexing, negative indexes and slicing with steps (str and list).

Each variant prints three expressions chosen from different reasoning kinds (positive
index, negative index, plain slice, stepped slice, negative-bound slice, reversed step,
descending range slice, slice of a slice). Every misconception is a concrete rewrite of
one expression (1-based counting, inclusive stop, ignored step, ...), executed.
"""
from __future__ import annotations

from core import rng
from families._pykit import build, sub

SOURCES = ["past-2021-1-5", "itpasslab-1-13"]
WORDS = ["ALGORITHMS", "FREQUENCY", "BLACKSMITH", "DUPLICATE", "WORKSHOP", "PYTHONIC",
         "NIGHTCLUB", "COMPLEXITY", "LUMBERJACK", "TRAMPOLINE", "QUICKSORT"]


def kinds_text():
    return {
        "idx": "인덱스는 0부터",
        "neg": "-k는 끝에서 k번째(len-k)",
        "sl": "x[i:j]는 i부터 j-1까지, 끝 j는 제외",
        "step": "x[i:j:k]는 i에서 k칸씩 이동, j 직전까지",
        "negsl": "음수 경계는 len을 더해 읽는다",
        "rev": "음수 step + 시작 생략 → 맨 끝에서 출발",
        "down": "x[j:i:-1]은 j부터 i+1까지 내려온다",
        "chain": "슬라이스 결과는 새 시퀀스이므로 두 번째 인덱싱은 그 결과의 0번부터 다시 센다",
    }


def make_expr(kind, n, r, name):
    """Returns (expr, [mutations of the expr text with notes], picked description)."""
    if kind == "idx":
        i = r.randint(2, n - 3)
        e = f"{name}[{i}]"
        return e, [(f"{name}[{i - 1}]", f"{e}를 1부터 세어 {i}번째 원소({name}[{i - 1}])로 읽었다. 파이썬 인덱스는 0부터 시작한다."),
                   (f"{name}[{i + 1}]", f"{e} 뒤 원소({name}[{i + 1}])를 골랐다. 인덱스 0이 첫 원소라는 점을 거꾸로 보정한 실수다.")]
    if kind == "neg":
        k = r.randint(2, 4)
        e = f"{name}[-{k}]"
        return e, [(f"{name}[-{k + 1}]", f"{e}에서 -1을 끝에서 두 번째로 보아 한 칸 더 앞({name}[-{k + 1}])을 골랐다. -1이 마지막 원소다."),
                   (f"{name}[{k}]", f"음수 부호를 무시하고 앞에서 {k}번 인덱스({name}[{k}])를 골랐다."),
                   (f"{name}[-{k - 1}]", f"끝에서 0번째부터 센다고 보아 {name}[-{k - 1}]를 골랐다.")]
    if kind == "sl":
        a = r.randint(1, 3)
        b = a + r.randint(3, 4)
        e = f"{name}[{a}:{b}]"
        return e, [(f"{name}[{a}:{b + 1}]", f"끝 인덱스 {b}까지 포함한다고 보았다({name}[{a}:{b + 1}]). 슬라이스 끝은 포함하지 않는다."),
                   (f"{name}[{a - 1}:{b - 1}]", f"인덱스를 1부터 세어 범위 전체를 한 칸 앞({name}[{a - 1}:{b - 1}])으로 잡았다."),
                   (f"{name}[{a}:{a + b}]", f"두 번째 수 {b}를 끝 위치가 아니라 가져올 개수로 읽었다({name}[{a}:{a + b}]).")]
    if kind == "step":
        a = r.randint(0, 2)
        b = n - r.randint(0, 2)
        c = r.choice([2, 3])
        e = f"{name}[{a}:{b}:{c}]"
        return e, [(f"{name}[{a}:{b}]", f"step {c}를 무시하고 인덱스 {a}부터 {b - 1}까지 모두 골랐다."),
                   (f"{name}[{a}:{b + 1}:{c}]" if b < n else f"{name}[{a + 1}:{b}:{c}]",
                    f"끝 {b}를 포함한다고 보거나 시작을 한 칸 밀어 고른 위치가 어긋났다." if b == n else f"끝 인덱스 {b}까지 포함한다고 보았다. step이 있어도 끝은 제외된다."),
                   (f"{name}[{a + c}:{b}:{c}]", f"시작 원소 {name}[{a}]는 건너뛰고 {c}칸 뒤부터 고른다고 보았다. 시작 인덱스는 결과에 포함된다.")]
    if kind == "negsl":
        k = r.randint(3, 5)
        if r.random() < 0.5:
            e = f"{name}[-{k}:]"
            return e, [(f"{name}[:-{k}]", f"{name}[-{k}:]와 {name}[:-{k}]를 바꿔 읽어 앞부분을 골랐다."),
                       (f"{name}[-{k + 1}:]", f"-{k}를 끝에서 {k + 1}번째로 보아 한 개 더 가져왔다."),
                       (f"{name}[-{k - 1}:]", f"-{k}부터가 아니라 그 다음 칸부터라고 보아 한 개 덜 가져왔다.")]
        e = f"{name}[:-{k}]"
        return e, [(f"{name}[-{k}:]", f"{name}[:-{k}]와 {name}[-{k}:]를 바꿔 읽어 뒷부분을 골랐다."),
                   (f"{name}[:-{k - 1}]", f"끝 경계 -{k}의 원소까지 포함한다고 보았다. 끝은 제외된다."),
                   (f"{name}[:{k}]", f"부호를 무시하고 앞에서 {k}개를 골랐다.")]
    if kind == "rev":
        c = r.choice([x for x in (2, 3) if (n - 1) % x] or [2])
        e = f"{name}[::-{c}]"
        return e, [(f"{name}[::{c}][::-1]", f"먼저 앞에서부터 {c}칸 간격으로 고른 뒤 뒤집었다. 음수 step은 마지막 원소에서 출발하므로 고르는 위치가 다르다."),
                   (f"{name}[::{c}]", f"음수 부호(방향)를 무시하고 앞에서부터 {c}칸 간격으로 골랐다."),
                   (f"{name}[-2::-{c}]", f"출발점을 마지막 원소가 아닌 끝에서 두 번째로 잡았다.")]
    if kind == "down":
        a = r.randint(1, 2)
        b = a + r.randint(4, 5)
        e = f"{name}[{b}:{a}:-1]"
        return e, [(f"{name}[{a}:{b}][::-1]", f"{name}[{a}:{b}]를 뒤집은 것으로 보아 인덱스 {b - 1}부터 {a}까지 골랐다. 실제로는 시작 인덱스 {b} 포함, 끝 인덱스 {a} 제외다."),
                   (f"{name}[{b}:{a - 1}:-1]", f"끝 인덱스 {a}까지 포함한다고 보았다."),
                   (f"{name}[{a}:{b}]", f"step -1을 무시하고 {a}부터 {b - 1}까지 정방향으로 골랐다.")]
    raise ValueError(kind)


COMBOS = [
    ("str", ["idx", "neg", "sl"], 1),
    ("str", ["idx", "step", "negsl"], 2),
    ("list", ["neg", "sl", "step"], 2),
    ("str", ["sl", "rev", "neg"], 2),
    ("list", ["idx", "negsl", "rev"], 2),
    ("str", ["neg", "down", "step"], 3),
    ("list", ["sl", "neg", "idx"], 1),
    ("str", ["negsl", "step", "down"], 3),
    ("str", ["chain"], 3),
    ("list", ["chain"], 3),
    ("str", ["idx", "negsl", "sl"], 1),
]


def describe(seq, expr_code, name):
    """Picked indices for an expression on a top-level sequence (no chaining)."""
    inner = expr_code[len(name) + 1:-1]
    n = len(seq)
    if ":" not in inner:
        i = int(inner)
        return f"인덱스 {i}" + (f" → {i + n}" if i < 0 else ""), [i % n]
    parts = [int(p) if p else None for p in inner.split(":")]
    while len(parts) < 3:
        parts.append(None)
    idx = list(range(*slice(*parts).indices(n)))
    return "인덱스 " + (", ".join(map(str, idx)) if idx else "(없음)"), idx


def make(k):
    typ, kinds, diff = COMBOS[k]
    r = rng(f"py-index-slice-{k}")
    word = WORDS[k]
    n = len(word)
    if typ == "str":
        name, decl = "s", f's = "{word}"'
        seq = list(word)
    else:
        name = "a"
        seq = [r.randint(1, 9) * 10 + j for j in range(r.choice([8, 9]))]
        n = len(seq)
        decl = f"a = {seq}"
    kt = kinds_text()
    if kinds == ["chain"]:
        a, c = 1, 2
        b = a + c * 3
        i2 = -1 if k % 2 == 0 else 1
        lines = [decl, f"t = {name}[{a}:{b}:{c}]", f"print(t, t[{i2}], len(t))"]
        code = "\n".join(lines)
        t_idx = list(range(a, b, c))
        wrong = [
            sub(f"step {c}를 무시해 t를 {name}[{a}:{b}] 전체로 보았다.", (f"[{a}:{b}:{c}]", f"[{a}:{b}]")),
            sub(f"끝 인덱스 {b}까지 포함한다고 보았다.", (f"[{a}:{b}:{c}]", f"[{a}:{b + 1}:{c}]")),
            sub("시작 인덱스를 1부터 세어 첫 원소부터 골랐다.", (f"[{a}:{b}:{c}]", f"[{a - 1}:{b}:{c}]")),
            sub(f"t[{i2}]를 원래 {name}의 인덱스로 읽었다. t는 새 시퀀스라 자기 0번부터 센다.", (f"t[{i2}]", f"{name}[{i2}]")),
            sub("t[-1]을 첫 원소 t[0]로 읽었다. -1은 마지막 원소다." if i2 < 0 else "t[1]을 한 칸 뒤 원소 t[2]로 읽었다(인덱스 경계 착오).", (f"t[{i2}]", f"t[{i2 + 1 if i2 > 0 else 0}]")),
            sub("len(t)를 원래 시퀀스 길이로 보았다.", ("len(t)", f"len({name})")),
            sub(f"step {c}를 무시하고, t[{i2}]도 원래 시퀀스 기준으로 읽었다.", (f"[{a}:{b}:{c}]", f"[{a}:{b}]"), (f"t[{i2}]", f"{name}[{i2}]")),
            sub(f"끝 인덱스 {b}까지 포함해 t의 길이가 하나 늘었고, " + ("마지막 원소를 끝에서 두 번째로 읽는 실수까지 겹쳤다." if i2 < 0 else "t[1]을 첫 원소로 읽는 실수까지 겹쳤다."), (f"[{a}:{b}:{c}]", f"[{a}:{b + 1}:{c}]"), (f"t[{i2}]", f"t[{i2 - 1}]")),
            sub("step 2를 '두 개를 버리고 다음 것을 고른다'로 해석해 3칸 간격으로 골랐다. step은 다음 인덱스까지의 거리다.", (f"[{a}:{b}:{c}]", f"[{a}:{b}:3]")),
            sub("음수 인덱스 -1을 끝에서 두 번째로 읽었다." if i2 < 0 else "t[1]을 t의 첫 원소로 읽었다.", (f"t[{i2}]", "t[-2]" if i2 < 0 else "t[0]")),
        ]
        pre = [
            f"{name}[{a}:{b}:{c}]는 인덱스 {a}에서 시작해 {c}칸씩 건너뛰며 {b} 직전까지 고른다. 고른 인덱스는 {', '.join(map(str, t_idx))}이고, 그 원소들로 만든 새 {'문자열' if typ == 'str' else '리스트'} t의 길이는 {len(t_idx)}이다.",
            f"t[{i2}]는 원래 {name}가 아니라 t 안에서의 위치다. {kt['chain']}. len(t)도 t의 길이다.",
        ]
        spec = dict(code=code, wrong=wrong, pre=pre, trace=True, difficulty=diff,
                    ask=f"슬라이스로 만든 새 시퀀스 t에 다시 인덱스를 적용할 때, 두 번째 인덱스가 어느 시퀀스 기준인지 묻는다.",
                    post="print는 t, t의 원소, t의 길이를 공백으로 구분해 출력하므로 결과는 {OUT}이다.",
                    tip="슬라이스 결과를 변수에 담으면 인덱스가 0부터 새로 매겨진다. 원본 인덱스와 새 인덱스를 표 두 줄로 나눠 적으면 헷갈리지 않는다.",
                    topic="Python 인덱싱·슬라이싱", tags=["슬라이싱", "step", "인덱스"])
        return spec
    exprs = []
    muts = []
    for kd in kinds:
        e, ms = make_expr(kd, n, r, name)
        exprs.append(e)
        muts.append(ms)
    code = "\n".join([decl, f"print({', '.join(exprs)})"])
    wrong = []
    for e, ms in zip(exprs, muts):
        for new, note in ms:
            wrong.append(sub(note, (e, new)))
    # Two simultaneous slips on the first two expressions.
    wrong.append(sub("두 식에서 함께 실수했다: " + muts[0][0][1] + " 또한 " + muts[1][0][1],
                     (exprs[0], muts[0][0][0]), (exprs[1], muts[1][0][0])))
    wrong.append(sub("세 번째 식에서 실수했다: " + muts[2][0][1] + " 첫 식도 " + muts[0][-1][1],
                     (exprs[0], muts[0][-1][0]), (exprs[2], muts[2][0][0])))
    rows = []
    for e, kd in zip(exprs, kinds):
        d, idx = describe(seq, e, name)
        vals = [seq[i] for i in idx]
        res = "".join(vals) if typ == "str" else (str(vals[0]) if ":" not in e else str(vals))
        rows.append([e, d, res, kt[kd]])
    table = {"table": {"caption": "인덱스 대응표", "columns": ["구분"] + [str(x) for x in seq],
                       "rows": [["양수"] + [str(i) for i in range(n)], ["음수"] + [str(i - n) for i in range(n)]]}}
    pick_table = {"table": {"caption": "식마다 고른 위치", "columns": ["식", "고른 위치", "결과", "규칙"], "rows": rows}}
    pre = [
        f"먼저 {name}의 각 원소에 양수 인덱스(0~{n - 1})와 음수 인덱스(-{n}~-1)를 함께 적는다. 음수 인덱스 -k는 len({name})={n}을 더한 {n}-k와 같다.",
        table,
        "각 식이 고르는 위치를 규칙대로 구하면 다음과 같다. 슬라이스는 시작은 포함, 끝은 제외이며 step만큼 건너뛴다.",
    ]
    spec = dict(code=code, wrong=wrong, pre=pre, table=pick_table, trace=False, difficulty=diff,
                post=f"print는 세 값을 공백 하나로 구분해 한 줄에 출력한다{' (리스트 슬라이스는 대괄호 형태로 출력)' if typ == 'list' else ''}. 따라서 출력은 {{OUT}}이다.",
                ask=f"{'문자열' if typ == 'str' else '리스트'}에 대한 세 식({', '.join(exprs)})이 각각 어떤 원소를 고르는지 묻는다. 0부터 세는 인덱스, 끝 제외 규칙, step과 음수 인덱스가 핵심 조건이다.",
                tip="인덱스 문제는 원소 아래에 양수·음수 인덱스를 두 줄로 써 놓고, 슬라이스는 range(시작, 끝, step)처럼 실제 인덱스 목록을 뽑아 보면 실수가 사라진다.",
                topic="Python 인덱싱·슬라이싱", tags=["슬라이싱", "음수 인덱스", "step"])
    return spec


def generate():
    return [build(id=f"py-index-slice-{k + 1:02d}", spec=make(k), family="py-index-slice", sources=SOURCES)
            for k in range(len(COMBOS))]
