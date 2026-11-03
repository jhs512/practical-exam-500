"""Java: method overriding and dynamic binding.

Template A (numeric): parent method run() calls f() and g(); the child overrides f
(maybe via super.f) and declares g (an override only when P.g is not private), and
may override run. Reasoning points: dynamic binding inside a parent method, private
methods are not virtual, super.f() goes to the parent body, casts do not change the
runtime method.

Template B (string chain): three-level hierarchy where each level may override m()
with or without super.m(), and a helper t() (maybe overridden in the middle class)
calls m(). Reasoning points: nearest override wins, super means the direct parent,
calls inside an inherited method still bind to the runtime class.
"""
from __future__ import annotations

from families.java_kit import jq, main_class, misconceptions, pick, rng, trace_table

FAM = "j-override"
SOURCES = ["itpasslab-2-10", "past-2024-2-14"]
TOPIC = "Java 오버라이딩과 동적 바인딩"


# ------------------------------------------------------------------ template A
def sim_a(v, bugs=frozenset()):
    a, b, d, e, k, n, m = v["a"], v["b"], v["d"], v["e"], v["k"], v["n"], v["m"]
    g_private = v["g_private"] ^ ("priv_flip" in bugs)
    rows = []

    def f(cls, x):
        if cls == "C" and "both_exec" in bugs:
            return f_real("C", x) + f_real("P", x)
        return f_real(cls, x)

    def f_real(cls, x):
        if cls == "C":
            if v["f_super"]:
                base = x if "no_super" in bugs else f_real("P", x)
                r = base * 2
            else:
                r = x - d
        else:
            r = x + a
        return r

    def g(cls, x):
        if cls == "C" and "both_exec" in bugs:
            return x * e + x * b
        return x * e if cls == "C" else x * b

    def run(cls, x, top=True):
        inner = "P" if "inner_static" in bugs else cls
        fv = f(inner, x)
        gv = g("P" if g_private else inner, x)
        r = fv + gv
        if top:
            rows.append([f"{'p' if cls == 'C' else 'q'}.run({x}) 안 f({x})", f"{inner}.f", fv])
            rows.append([f"{'p' if cls == 'C' else 'q'}.run({x}) 안 g({x})",
                         f"{'P' if g_private else inner}.g", gv])
        if cls == "C" and v["c_run"] and "run_skip" not in bugs:
            r += k
            if top:
                rows.append(["C.run의 super.run(...) + " + str(k), "C.run", r])
        return r

    p_cls = "P" if "static_bind" in bugs else "C"
    q_cls = "C" if "q_child" in bugs else "P"
    r1 = run(p_cls, n)
    r2 = run(q_cls, n)
    third = v["third"]
    if third == "q":
        t_cls = q_cls
    elif third == "cast":
        t_cls = "P" if ("cast_static" in bugs or "static_bind" in bugs) else "C"
    else:
        t_cls = p_cls
    r3 = f(t_cls, m)
    rows.append([{"p": f"p.f({m})", "cast": f"((P) p).f({m})", "q": f"q.f({m})"}[third],
                 f"{t_cls}.f", r3])
    return f"{r1} {r2} {r3}", rows


def render_a(v):
    a, b, d, e, k, n, m = v["a"], v["b"], v["d"], v["e"], v["k"], v["n"], v["m"]
    gmod = "private " if v["g_private"] else ""
    pcls = [
        "class P {",
        f"    int f(int x) {{ return x + {a}; }}",
        f"    {gmod}int g(int x) {{ return x * {b}; }}",
        "    int run(int x) { return f(x) + g(x); }",
        "}",
        "",
        "class C extends P {",
        (f"    int f(int x) {{ return super.f(x) * 2; }}" if v["f_super"]
         else f"    int f(int x) {{ return x - {d}; }}"),
        f"    int g(int x) {{ return x * {e}; }}",
    ]
    if v["c_run"]:
        pcls.append(f"    int run(int x) {{ return super.run(x) + {k}; }}")
    pcls.append("}")
    third = {"p": f"p.f({m})", "cast": f"((P) p).f({m})", "q": f"q.f({m})"}[v["third"]]
    body = [
        "P p = new C();",
        "P q = new P();",
        f'System.out.println(p.run({n}) + " " + q.run({n}) + " "',
        f"        + {third});",
    ]
    return main_class(body, before=pcls)


BUGS_A = {
    "static_bind": "참조 변수 p의 선언 타입이 P라서 P의 메서드가 실행된다고 보았다(정적 바인딩 착각). "
                   "인스턴스 메서드는 실제 객체(new C())의 재정의 메서드가 실행된다.",
    "inner_static": "main에서 부른 p.run()은 동적 바인딩을 적용했지만, P.run() 본문 안의 f()·g() 호출은 "
                    "P 클래스 코드이므로 P의 것이 실행된다고 보았다. 본문 안의 호출도 this(실제 C 객체) 기준이다.",
    "priv_flip": "private 여부를 반대로 처리했다. private 메서드는 상속·재정의되지 않아 P.run 안의 g()는 "
                 "P.g로 고정되고, private이 아니면 C.g가 재정의로 실행된다.",
    "no_super": "super.f(x)를 부모 f의 결과가 아닌 인자 x 그대로로 계산했다. super.f(x)는 P.f 본문(x + a)을 실행한다.",
    "run_skip": "C에서 재정의한 run()을 놓치고 P.run 결과만 출력된다고 보았다. p.run()은 C.run이 먼저 실행된다.",
    "q_child": "q도 C 객체로 착각했다. q는 new P()로 만든 부모 객체라 재정의와 무관하게 P의 메서드만 실행된다.",
    "both_exec": "재정의된 메서드를 부르면 생성자처럼 부모 메서드도 함께 실행된다고 보고 부모·자식 결과를 더했다. "
                 "오버라이딩은 부모 구현을 대체하며, 부모 쪽은 super로 명시해야만 실행된다.",
    "cast_static": "(P) 캐스팅을 하면 부모 메서드가 호출된다고 보았다. 캐스팅은 참조 타입만 바꾸고 객체는 그대로 C라서 C.f가 실행된다.",
}


def variants_a():
    combos = []
    for g_private in (False, True):
        for f_super in (False, True):
            for c_run in (False, True):
                combos.append((g_private, f_super, c_run))
    thirds = ["p", "cast", "q", "cast", "p", "cast", "q", "p"]
    return [(i, c, thirds[i]) for i, c in enumerate(pick(combos, "j-ovr-a"))]


def build_a(idx, combo, third):
    g_private, f_super, c_run = combo
    seed = f"{FAM}-a-{idx}"
    r = rng(seed)
    for _ in range(5000):
        v = dict(g_private=g_private, f_super=f_super, c_run=c_run, third=third,
                 a=r.randint(1, 5), b=r.randint(2, 4), d=r.randint(1, 4), e=r.randint(2, 5),
                 k=r.randint(1, 9) * 10, n=r.randint(2, 6), m=r.randint(3, 9))
        if v["b"] == v["e"]:
            continue
        out, rows = sim_a(v)
        bugs = dict(BUGS_A)
        if not c_run:
            bugs.pop("run_skip")
        if third != "cast":
            bugs.pop("cast_static")
        wrong = misconceptions(lambda bs: sim_a(v, bs)[0], bugs, combos=True)
        if len({w for w, _ in wrong} - {out}) >= 9:
            break
    code = render_a(v)
    gp = ("P.g가 private이라 C의 g는 재정의가 아닌 별개 메서드이고, P.run 안의 g(x)는 P.g로 고정된다"
          if g_private else "P.g가 private이 아니므로 C.g가 P.g를 재정의한다")
    solve = [
        f"p는 선언 타입 P, 실제 객체 C다. 인스턴스 메서드는 실행 시점의 객체 타입으로 결정(동적 바인딩)되므로 "
        f"p.run()·p.f()는 C에 재정의가 있으면 C의 것을 쓴다. q는 new P()라 항상 P의 메서드다. "
        f"P.run 본문의 f(x)·g(x)는 this.f(x)·this.g(x)와 같아서 여기서도 실제 객체 기준으로 고른다. "
        f"단, {gp}.",
        trace_table(["호출", "실행 메서드", "값"], rows),
        f"따라서 출력은 {out}이다."
        + (" C.run은 super.run(x)로 P.run 본문을 실행한 뒤 상수를 더한다. super.run 안의 f·g 호출도 여전히 C 객체 기준이다."
           if c_run else "")
        + (" f는 super.f(x) * 2라서 P.f(x) = x + a를 먼저 구한 뒤 두 배 한다." if f_super else ""),
    ]
    if not g_private and not c_run:
        diff = 1
    elif g_private and c_run:
        diff = 3
    else:
        diff = 2
    return jq(
        id=f"j-override-{idx + 1:02d}", code=code, output=out, solve=solve,
        wrong=wrong, family=FAM, sources=SOURCES, topic=TOPIC, difficulty=diff,
        tags=["상속", "오버라이딩", "동적 바인딩"] + (["private"] if g_private else []) + (["super"] if f_super else []),
        ask=f"부모 타입 참조(P p = new C())로 호출할 때 어떤 클래스의 f·g·run이 실행되는지 묻는다. "
            f"g의 접근 제어자({'private' if g_private else '기본'}), C의 run 재정의 {'있음' if c_run else '없음'}, "
            f"마지막 호출 {'캐스팅' if third == 'cast' else ('q' if third == 'q' else 'p')}이 판단 지점이다.",
        tip="호출문마다 '실제 객체가 무엇인가'를 먼저 적고, 메서드 본문 안의 호출도 this 기준으로 다시 고른다. "
            "private·static 메서드는 재정의 대상이 아니므로 동적 바인딩이 적용되지 않는다.",
    )


# ------------------------------------------------------------------ template B
NAMES = [
    ("Animal", "Dog", "Puppy", "sound", "A", "D", "P"),
    ("Shape", "Rect", "Square", "name", "S", "R", "Q"),
    ("Base", "Mid", "Leaf", "tag", "B", "M", "L"),
    ("Vehicle", "Car", "Taxi", "kind", "V", "C", "T"),
    ("Device", "Phone", "Smart", "id", "D", "P", "S"),
    ("Node", "Inner", "Tip", "mark", "N", "I", "T"),
    ("Item", "Book", "Comic", "code", "I", "B", "C"),
]


def sim_b(v, bugs=frozenset()):
    A, B, C, meth, la, lb, lc = v["names"]
    rows = []

    def m(cls):
        if cls == "A":
            return la
        if cls == "B":
            if v["b_super"] and "super_skip" not in bugs:
                return m("A") + lb
            return lb
        # C
        if v["c_mode"] == "none":
            return m("A") if "inherit_top" in bugs else m("B")
        if v["c_mode"] == "super" and "super_skip" not in bugs:
            base = m("A") if "super_top" in bugs else m("B")
            return base + lc
        return lc

    def t(cls):
        inner = "A" if "t_static" in bugs else cls
        core = "[" + m(inner) + "]"
        if cls != "A" and v["b_t"] and "t_skip" not in bugs:
            return "<" + core + ">"
        return core

    sb = "static_bind" in bugs
    x_cls = "A" if sb else "C"
    y_cls = "A" if sb else "B"
    z_cls = "B" if (sb or "z_static" in bugs) else "C"
    r1, r2, r3 = m(x_cls), m(y_cls), t(z_cls)
    rows.append([f"x.{meth}()", f"실제 객체 {C}", r1])
    rows.append([f"y.{meth}()", f"실제 객체 {B}", r2])
    rows.append([f"z.show()", f"실제 객체 {C}, show는 {B if v['b_t'] else A}의 것", r3])
    return f"{r1} {r2} {r3}", rows


def render_b(v):
    A, B, C, meth, la, lb, lc = v["names"]
    cls = [
        f"class {A} {{",
        f'    String {meth}() {{ return "{la}"; }}',
        f'    String show() {{ return "[" + {meth}() + "]"; }}',
        "}",
        "",
        f"class {B} extends {A} {{",
        (f'    String {meth}() {{ return super.{meth}() + "{lb}"; }}' if v["b_super"]
         else f'    String {meth}() {{ return "{lb}"; }}'),
    ]
    if v["b_t"]:
        cls.append('    String show() { return "<" + super.show() + ">"; }')
    cls += ["}", "", f"class {C} extends {B} {{"]
    if v["c_mode"] == "super":
        cls.append(f'    String {meth}() {{ return super.{meth}() + "{lc}"; }}')
    elif v["c_mode"] == "own":
        cls.append(f'    String {meth}() {{ return "{lc}"; }}')
    else:
        cls.append(f"    int level() {{ return 3; }}")
    cls.append("}")
    body = [
        f"{A} x = new {C}();",
        f"{A} y = new {B}();",
        f"{B} z = new {C}();",
        f'System.out.println(x.{meth}() + " " + y.{meth}() + " "',
        "        + z.show());",
    ]
    return main_class(body, before=cls)


def bugs_b(v):
    A, B, C, meth, *_ = v["names"]
    b = {
        "static_bind": f"참조 변수의 선언 타입({A}, {B})으로 메서드를 골랐다. 재정의된 인스턴스 메서드는 실제 객체 타입으로 결정된다.",
        "super_skip": f"super.{meth}() 호출 결과를 빼고 자기 문자열만 반환한다고 보았다. super 호출 결과가 앞에 붙는다.",
        "z_static": f"z의 선언 타입이 {B}라서 z.show()와 그 안의 {meth}()가 {B} 기준으로 실행된다고 보았다. "
                    f"z가 가리키는 객체는 new {C}()이다.",
        "t_static": f"show()가 {A} 클래스에 정의돼 있으니 그 안의 {meth}()도 {A}의 것이 실행된다고 보았다. 본문 안 호출도 실제 객체 기준이다.",
    }
    if v["c_mode"] == "none":
        b["inherit_top"] = (f"{C}에 {meth}() 재정의가 없으면 최상위 {A}의 메서드가 실행된다고 보았다. "
                            f"가장 가까운 조상인 {B}의 재정의가 상속된다.")
    if v["c_mode"] == "super":
        b["super_top"] = (f"{C}의 super.{meth}()가 최상위 {A}의 메서드를 부른다고 보았다. "
                          f"super는 직계 부모 {B}를 가리키며, {B}의 메서드가 다시 자기 규칙대로 실행된다.")
    if v["b_t"]:
        b["t_skip"] = f"{B}에서 재정의한 show()를 놓쳤다. z의 실제 객체 {C}는 {B}.show()를 상속하므로 <...>가 붙는다."
    return b


def build_b(idx, combo):
    b_super, c_mode, b_t = combo
    v = dict(b_super=b_super, c_mode=c_mode, b_t=b_t, names=NAMES[idx])
    out, rows = sim_b(v)
    bugs = bugs_b(v)
    wrong = misconceptions(lambda bs: sim_b(v, bs)[0], bugs, combos=True)
    A, B, C, meth, *_ = v["names"]
    # extra plausible slips that are still named misconceptions
    r1, r2, r3 = out.split(" ")
    wrong.append((f"{r1} {r2} {r3.strip('[]<>')}",
                  f"show()가 붙이는 괄호 문자를 빼고 {meth}() 결과만 출력된다고 보았다. show는 결과를 [ ]로 감싼다."))
    wrong.append((f"{r1} {r1} {r3}", f"y도 {C} 객체라고 착각했다. y는 new {B}()이므로 {B}의 {meth}()가 실행된다."))
    code = render_b(v)
    cdesc = {"none": f"{C}는 {meth}()를 재정의하지 않아 {B}의 것을 물려받고",
             "own": f"{C}는 {meth}()를 super 없이 재정의해 자기 문자열만 반환하고",
             "super": f"{C}는 super.{meth}()로 {B}의 결과 뒤에 문자를 붙이고"}[c_mode]
    solve = [
        f"메서드 선택 규칙: 실제 객체의 클래스부터 위로 올라가며 처음 만나는 정의를 실행한다. {cdesc}, "
        f"{B}는 {meth}()를 {'super 호출 후 덧붙이는' if b_super else '자기 문자열만 반환하는'} 방식으로 재정의했다. "
        f"show()는 {A}에 있고 {('이를 ' + B + '가 <...>로 감싸 재정의했다' if b_t else '아무도 재정의하지 않았다')}. "
        f"show() 본문의 {meth}() 호출은 this.{meth}()이므로 실제 객체({C})의 메서드를 다시 고른다.",
        trace_table(["식", "판단", "결과"], rows),
        f"세 결과를 공백으로 이어 붙이면 {out}이다.",
    ]
    if c_mode == "own" and not b_t:
        diff = 1
    elif c_mode == "super" and b_super and b_t:
        diff = 3
    else:
        diff = 2
    return jq(
        id=f"j-override-{idx + 9:02d}", code=code, output=out, solve=solve, wrong=wrong,
        family=FAM, sources=SOURCES, topic=TOPIC, difficulty=diff,
        tags=["상속", "오버라이딩", "super", "다단계 상속"],
        ask=f"3단계 상속({A} → {B} → {C})에서 부모 타입 참조로 {meth}()와 show()를 호출할 때 실제로 실행되는 "
            f"메서드 체인을 묻는다. {C}의 재정의 방식과 super 호출 여부가 핵심이다.",
        tip="super.메서드()는 '직계 부모의 구현'을 실행하고, 그 구현 안의 다른 호출은 다시 실제 객체 기준으로 "
            "고른다. 각 클래스에 어떤 메서드가 정의돼 있는지 표로 먼저 정리하면 실수가 줄어든다.",
    )


def variants_b():
    combos = [(bs, cm, bt) for bs in (False, True) for cm in ("none", "own", "super") for bt in (False, True)]
    return pick(combos, "j-ovr-b", 7)


def generate():
    out = [build_a(i, c, t) for i, c, t in variants_a()]
    out += [build_b(i, c) for i, c in enumerate(variants_b())]
    return out
