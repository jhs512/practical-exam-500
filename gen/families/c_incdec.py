"""C: prefix/postfix ++/-- inside expressions, combined with operator precedence.

A program is 2-4 statements `x = ...;` / `x += ...;` whose operands are a, b, c with
++/-- in prefix or postfix form (each variable at most once per statement, so no
undefined behaviour). Every statement stores into its own result variable (or adds
to an earlier one), so a misreading anywhere shows in the output. Reasoning points
that vary: which occurrence is prefix or postfix, whether * or % changes evaluation
order, whether `+=` keeps the old value, and how a side effect in one statement feeds
the next. Wrong outputs re-run the program with one named misreading.
"""
from __future__ import annotations

from families.c_kit import cmod, emit, enough, program, search, trace_table

SOURCES = ["past-2020-1-12", "past-2022-2-15"]
FAM = "c-incdec"
KIND_TXT = {"pre++": "++{v}", "pre--": "--{v}", "post++": "{v}++", "post--": "{v}--", "": "{v}"}
FLIP = {"pre++": "post++", "post++": "pre++", "pre--": "post--", "post--": "pre--"}


def term_src(t):
    kind, v = t
    return str(v) if isinstance(v, int) else KIND_TXT[kind].format(v=v)


def stmt_src(st):
    terms, ops, mode, tgt = st
    parts = [term_src(terms[0])]
    for op, t in zip(ops, terms[1:]):
        parts += [op, term_src(t)]
    return f"{tgt} {mode} {' '.join(parts)};"


def apply(x, op, y):
    return {"+": x + y, "-": x - y, "*": x * y, "%": cmod(x, y) if y else 0}[op]


def eval_expr(vals, ops, ltr=False):
    if ltr:
        acc = vals[0]
        for op, v in zip(ops, vals[1:]):
            acc = apply(acc, op, v)
        return acc
    nums, pend = [vals[0]], []
    for op, v in zip(ops, vals[1:]):
        if op in "*%":
            nums[-1] = apply(nums[-1], op, v)
        else:
            pend.append(op)
            nums.append(v)
    acc = nums[0]
    for op, v in zip(pend, nums[1:]):
        acc = apply(acc, op, v)
    return acc


def targets(prog):
    tg = []
    for st in prog:
        if st[3] not in tg:
            tg.append(st[3])
    return tg


def simulate(prog, init, *bugs):
    """bugs: ("flip", occ) | ("allpost",) | ("allpre",) | ("ltr", s) | ("eq", s) | ("lost",) | ("stale",)"""
    env = dict(init)
    tg = targets(prog)
    for t in tg:
        env[t] = 0
    rows = []
    occ = 0
    start = dict(env)
    for s, (terms, ops, mode, tgt) in enumerate(prog):
        vals, effects, used = [], {}, []
        for kind, v in terms:
            if isinstance(v, int):
                vals.append(v)
                continue
            k = kind
            if kind:
                if ("flip", occ) in bugs or (("allpost",) in bugs and kind.startswith("pre")) or \
                        (("allpre",) in bugs and kind.startswith("post")):
                    k = FLIP[kind]
                occ += 1
            cur = start[v] if ("stale",) in bugs else env[v]
            step = 1 if k.endswith("++") else -1
            val = cur + step if k.startswith("pre") else cur
            if k:
                lost = ("lost",) in bugs and k.startswith("post")
                effects[v] = env[v] + (0 if lost else step)
            vals.append(val)
            used.append(f"{term_src((kind, v))}→{val}")
        e = eval_expr(vals, ops, ltr=("ltr", s) in bugs)
        env.update(effects)
        if mode == "+=" and ("eq", s) not in bugs:
            env[tgt] += e
        else:
            env[tgt] = e
        rows.append([stmt_src((terms, ops, mode, tgt)), ", ".join(used) + f" ⇒ 식 값 {e}",
                     env["a"], env["b"], env["c"]] + [env[t] for t in tg])
    return " ".join(str(env[k]) for k in ["a", "b", "c"] + tg) + "\n", rows


def occurrences(prog):
    occ = []
    for s, st in enumerate(prog):
        for kind, v in st[0]:
            if kind:
                occ.append((s, kind, v))
    return occ


def wrongs(prog, init):
    w = [
        (simulate(prog, init, ("allpre",))[0],
         "후위 증감(a++, b--)도 전위처럼 읽어 바뀐 값을 식에 넣었다. 후위형은 현재 값을 먼저 식에 쓰고 증감은 그 뒤에 일어난다."),
        (simulate(prog, init, ("allpost",))[0],
         "전위 증감(++a, --b)도 후위처럼 읽어 바뀌기 전 값을 식에 넣었다. 전위형은 먼저 증감하고 바뀐 값을 식에 쓴다."),
    ]
    for s, st in enumerate(prog):
        ops = st[1]
        if any(o in "*%" for o in ops) and any(o in "+-" for o in ops):
            w.append((simulate(prog, init, ("ltr", s))[0],
                      f"{s + 1}번째 문장을 왼쪽부터 차례로 계산했다. *와 %는 +, -보다 우선순위가 높아 먼저 계산된다."))
    occ = occurrences(prog)
    for i, (s, kind, v) in enumerate(occ):
        src = term_src((kind, v))
        if kind.startswith("post"):
            note = f"{s + 1}번째 문장의 {src}만 전위처럼 읽어 {v}가 바뀐 값으로 계산했다. 후위형은 바뀌기 전 값을 식에 쓴다."
        else:
            note = f"{s + 1}번째 문장의 {src}만 후위처럼 읽어 {v}가 바뀌기 전 값으로 계산했다. 전위형은 먼저 증감한 값을 쓴다."
        w.append((simulate(prog, init, ("flip", i))[0], note))
    for s, st in enumerate(prog):
        if st[2] == "+=":
            t = st[3]
            w.append((simulate(prog, init, ("eq", s))[0],
                      f"{s + 1}번째 문장의 {t} += 를 {t} = 처럼 읽어 이전 {t} 값을 버렸다. +=는 기존 {t}에 식 값을 더한다."))
    w.append((simulate(prog, init, ("lost",))[0],
              "후위 증감은 식 안에서만 의미가 있고 변수에는 남지 않는다고 보아 후위형 변수를 그대로 두었다. "
              "후위형도 그 문장이 끝나기 전에 변수 값을 바꾼다."))
    w.append((simulate(prog, init, ("stale",))[0],
              "앞 문장에서 바뀐 a, b, c를 다음 문장에 반영하지 않고 처음 값으로 계산했다. "
              "증감 결과는 즉시 변수에 저장되어 다음 문장이 그 값을 읽는다."))
    for i in range(len(occ)):
        for j in range(i + 1, len(occ)):
            (s1, k1, v1), (s2, k2, v2) = occ[i], occ[j]
            if k1[:3] != k2[:3]:
                a1, a2 = term_src((k1, v1)), term_src((k2, v2))
                w.append((simulate(prog, init, ("flip", i), ("flip", j))[0],
                          f"{s1 + 1}번째 문장의 {a1}와 {s2 + 1}번째 문장의 {a2}를 둘 다 반대 형태(전위↔후위)로 읽었다. "
                          "두 형태가 섞여 있으면 하나씩 '쓰고 바꾸는지, 바꾸고 쓰는지'를 따로 확인해야 한다."))
    return w


# (statements, ops pool, allow +=, difficulty)
SHAPES = [
    (2, "+-", False, 1), (3, "+-", False, 1), (2, "+-*", False, 1), (2, "+-", False, 1), (2, "+-*", True, 1),
    (3, "+-*", False, 2), (3, "+-*", True, 2), (3, "+-%", True, 2), (3, "+-*", True, 2), (3, "+-*%", False, 2),
    (3, "+-*", True, 2),
    (4, "+-*", True, 3), (4, "+-*%", True, 3), (4, "+-*", True, 3), (4, "+-*%", True, 3),
]


def make_prog(r, n_st, pool, allow_pe):
    prog = []
    for s in range(n_st):
        vs = r.sample(["a", "b", "c"], r.choice([2, 3]))
        terms = [(r.choice(["pre++", "pre--", "post++", "post--", "", "post++", "pre++"]), v) for v in vs]
        if all(k == "" for k, _ in terms):
            terms[0] = (r.choice(["pre++", "post--"]), terms[0][1])
        if r.random() < 0.25:
            terms.append(("", r.randint(2, 4)))
        ops = [r.choice(pool) for _ in terms[1:]]
        for i, op in enumerate(ops):
            if op == "%" and not isinstance(terms[i + 1][1], int):
                ops[i] = "*" if "*" in pool else "+"
        used = targets(prog)
        if allow_pe and s > 0 and r.random() < 0.5:
            mode, tgt = "+=", r.choice(used)
        else:
            mode, tgt = "=", "xyzw"[len(used)]
        prog.append((terms, ops, mode, tgt))
    return prog


def generate():
    out = []
    for n, (n_st, pool, allow_pe, diff) in enumerate(SHAPES):
        def attempt(r):
            init = {"a": r.randint(2, 9), "b": r.randint(2, 9), "c": r.randint(2, 9)}
            prog = make_prog(r, n_st, pool, allow_pe)
            if "%" in pool and not any("%" in st[1] for st in prog):
                return None
            mixed = any(any(o in "*%" for o in st[1]) and any(o in "+-" for o in st[1]) for st in prog)
            if diff == 3 and not mixed:
                return None
            if allow_pe and not any(st[2] == "+=" for st in prog):
                return None
            res, rows = simulate(prog, init)
            if any(int(x) < 0 for x in res.split()[:3]):
                return None
            w = wrongs(prog, init)
            if not enough(res, w):
                return None
            return init, prog, res, rows, w
        init, prog, res, rows, w = search(f"{FAM}-{n}", attempt)
        tg = targets(prog)
        fmt = " ".join(["%d"] * (3 + len(tg)))
        body = [f"    int a = {init['a']}, b = {init['b']}, c = {init['c']};",
                "    int " + ", ".join(f"{t} = 0" for t in tg) + ";"]
        body += ["    " + stmt_src(st) for st in prog]
        body += [f'    printf("{fmt}\\n", a, b, c, {", ".join(tg)});']
        code = program(body)
        has_mul = any(any(o in "*%" for o in st[1]) for st in prog)
        has_pe = any(st[2] == "+=" for st in prog)
        names = ["a", "b", "c"] + tg
        solve = [
            "각 문장은 ① 피연산자 값을 정하고(전위형은 증감한 뒤의 값, 후위형은 증감 전 값) ② 연산자 우선순위대로 식을 계산한 다음 "
            "③ 증감 결과를 변수에 남기는 순서로 추적한다. 한 문장 안에서 같은 변수는 한 번만 쓰였으므로 결과가 하나로 정해진다.",
            trace_table(["문장", "피연산자 값 → 식 값", "a", "b", "c"] + tg, rows),
            "마지막 상태는 " + ", ".join(f"{k}={v}" for k, v in zip(names, res.split())) +
            f"이고 printf가 \"{res.strip()}\"를 출력한다.",
        ]
        if has_mul:
            solve.append("*와 %는 +, -보다 먼저 묶인다. 예를 들어 p + q * 2는 q * 2를 먼저 구한 뒤 p를 더한다.")
        if has_pe:
            solve.append("x += 식은 x = x + (식)이므로 앞 문장에서 저장한 값에 이어서 더한다. = 문장은 이전 값을 덮어쓴다.")
        out.append(emit(
            qid=f"{FAM}-{n + 1:02d}", code=code, out=res, solve=solve, wrong=w,
            ask=f"{n_st}개 문장에 섞인 전위·후위 증감 연산자를 따라가 최종 a, b, c와 결과 변수({', '.join(tg)}) 값을 묻는다. "
                "각 피연산자가 증감 전 값과 후 값 중 무엇으로 쓰이는지와, 증감이 다음 문장에 반영되는지가 핵심이다.",
            tip="++x는 '바꾸고 쓴다', x++는 '쓰고 바꾼다'. 문장마다 식에 들어간 값과 문장 끝 변수 값을 한 줄씩 표로 적으면 "
                "두 가지를 섞지 않는다.",
            topic="C 증감 연산자·우선순위", tags=["C", "증감연산자", "전위", "후위", "우선순위"],
            difficulty=diff, family=FAM, sources=SOURCES,
        ))
    return out
