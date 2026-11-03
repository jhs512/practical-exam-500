"""Java: object creation order — static/instance initializers and constructor chaining.

Template A: parent/child each with a static block, an instance block (and in the
child a logged field initializer), constructors chained with this(...)/super(...).
Reasoning points: statics once per class (parent first), instance initializers run
in the constructor that (implicitly) calls super — not in one that delegates with
this(...) — before that constructor's body; explicit super(k) picks P(int).

Template B: a parent constructor calls an overridden method while the child's
fields still hold default values.
"""
from __future__ import annotations

from families.java_kit import jq, main_class, misconceptions, pick, trace_table

FAM = "j-ctor"
SOURCES = ["past-2024-1-10", "past-2025-3-12"]
TOPIC = "Java 생성자 호출 순서와 초기화 블록"

NAMES_A = [("Base", "Sub", "B", "S"), ("Top", "Down", "T", "D"), ("Parent", "Child", "P", "C"),
           ("Car", "Taxi", "R", "X"), ("Shape", "Box", "H", "O"), ("Home", "Room", "M", "N"),
           ("Unit", "Cell", "U", "L"), ("Tree", "Leaf", "E", "F"), ("Core", "Plug", "K", "G")]


# ------------------------------------------------------------------ template A
def sim_a(v, bugs=frozenset()):
    P, C, x, y = v["names"]
    out, rows = [], []
    done = set()

    def emit(tok, why):
        out.append(tok)
        rows.append([tok, why])

    def static(cls):
        if cls in done and "static_each" not in bugs:
            return
        done.add(cls)
        name, tag = (P, x) if cls == "P" else (C, y)
        emit(f"{tag}s", f"{name} 클래스 최초 사용 → static 블록 1회")

    def statics_first():
        if "static_late" in bugs:
            return
        for cls in (["C", "P"] if "static_child_first" in bugs else ["P", "C"]):
            static(cls)

    def p_inits():
        emit(f"{x}i", f"{P} 인스턴스 초기화 블록(super() 직후)")

    def c_inits():
        items = [(f"{y}f", f"{C} 필드 초기화식"), (f"{y}i", f"{C} 인스턴스 블록")]
        if not v["field_first"]:
            items.reverse()
        if "field_order" in bugs:
            items.reverse()
        for tok, why in items:
            emit(tok, why + "(작성 순서대로)")

    def body(tok, why, inits):
        if "init_after" in bugs:
            emit(tok, why)
            inits()
        else:
            inits()
            emit(tok, why)

    def p_noarg():
        if "static_late" in bugs:
            static("P")
        body(f"{x}c", f"{P}() 본문", p_inits)

    def p_int(k):
        if "static_late" in bugs:
            static("P")
        if v["p_kind"] == "this" and "ignore_this" not in bugs:
            p_noarg()
            if "init_twice" in bugs:
                p_inits()
            emit(f"{x}{k}", f"{P}(int) 본문(this() 복귀 후)")
        else:
            body(f"{x}{k}", f"{P}(int) 본문", p_inits)

    def parent_part():
        if v["c_super"] == "int" and "super_default" not in bugs:
            p_int(v["k"])
        else:
            p_noarg()

    def c_noarg():
        if "child_first" in bugs:
            if "static_late" in bugs:
                static("C")
            body(f"{y}c", f"{C}() 본문", c_inits)
            parent_part()
            return
        parent_part()
        if "static_late" in bugs:
            static("C")
        body(f"{y}c", f"{C}() 본문", c_inits)

    def c_int(n):
        if "ignore_this" in bugs:
            parent_part()
            body(f"{y}{n}", f"{C}(int) 본문", c_inits)
            return
        c_noarg()
        if "init_twice" in bugs:
            c_inits()
        emit(f"{y}{n}", f"{C}(int) 본문(this() 복귀 후)")

    for i, entry in enumerate(v["entries"]):
        if i == 0:
            statics_first()
        elif "static_each" in bugs:
            statics_first()
        if entry is None:
            c_noarg()
        else:
            c_int(entry)
    return " ".join(out), rows


def render_a(v):
    P, C, x, y = v["names"]
    pc = [
        f"class {P} {{",
        f'    static {{ System.out.print("{x}s "); }}',
        f'    {{ System.out.print("{x}i "); }}',
        "",
        f'    {P}() {{ System.out.print("{x}c "); }}',
    ]
    if v["p_kind"] == "this":
        pc.append(f"    {P}(int k) {{")
        pc.append("        this();")
        pc.append(f'        System.out.print("{x}" + k + " ");')
        pc.append("    }")
    else:
        pc.append(f'    {P}(int k) {{ System.out.print("{x}" + k + " "); }}')
    pc += [
        "",
        "    static int log(String s) {",
        '        System.out.print(s + " ");',
        "        return 1;",
        "    }",
        "}",
        "",
        f"class {C} extends {P} {{",
    ]
    fld = f'    int f = log("{y}f");'
    blk = f'    {{ System.out.print("{y}i "); }}'
    pc.append(f'    static {{ System.out.print("{y}s "); }}')
    pc += [fld, blk] if v["field_first"] else [blk, fld]
    pc.append("")
    if v["c_super"] == "int":
        pc += [f"    {C}() {{", f"        super({v['k']});", f'        System.out.print("{y}c ");', "    }"]
    else:
        pc.append(f'    {C}() {{ System.out.print("{y}c "); }}')
    pc += [f"    {C}(int n) {{", "        this();", f'        System.out.print("{y}" + n + " ");', "    }", "}"]
    body = []
    for e in v["entries"]:
        body.append(f"new {C}();" if e is None else f"new {C}({e});")
    body.append("System.out.println();")
    return main_class(body, before=pc)


def bugs_a(v):
    P, C, *_ = v["names"]
    b = {
        "init_after": "인스턴스 초기화 블록이 생성자 본문 뒤에 실행된다고 보았다. 초기화 블록·필드 초기화식은 super() 호출 직후, 본문보다 먼저 실행된다.",
        "child_first": f"자식 {C}의 생성자 본문이 먼저 끝나고 부모 {P}가 나중에 초기화된다고 보았다. 생성자 첫 줄의 super(...)가 먼저 부모를 완성한다.",
        "static_late": "static 블록이 각 클래스 생성자 직전에 실행된다고 보았다. 클래스 로딩 시 부모·자식 static 블록이 객체 초기화보다 먼저 모두 실행된다.",
        "static_child_first": f"자식 클래스 {C}의 static 블록이 부모보다 먼저라고 보았다. 자식 클래스를 초기화하기 전에 부모 클래스 초기화가 먼저 일어난다.",
        "field_order": f"{C}의 필드 초기화식과 인스턴스 블록의 순서를 반대로 보았다. 둘은 소스에 적힌 순서대로 실행된다.",
    }
    if len(v["entries"]) > 1:
        b["static_each"] = "객체를 만들 때마다 static 블록이 다시 실행된다고 보았다. static 블록은 클래스당 처음 한 번만 실행된다."
    if v["c_super"] == "int":
        b["super_default"] = f"super({v['k']}) 호출을 무시하고 기본 생성자 {P}()가 호출된다고 보았다. 명시한 super(인수)에 맞는 {P}(int)가 실행된다."
    if v["p_kind"] == "this" and v["c_super"] == "int" or any(e is not None for e in v["entries"]):
        b["init_twice"] = "this(...)로 위임하는 생성자에서도 인스턴스 초기화가 한 번 더 실행된다고 보았다. 초기화 블록은 super를 호출하는 생성자에서 객체당 한 번만 실행된다."
        b["ignore_this"] = "this() 위임 호출을 무시하고 해당 생성자 본문만 실행된다고 보았다. this()가 같은 클래스의 다른 생성자를 먼저 끝까지 실행한다."
    return b


A_COMBOS = [
    # p_kind, c_super, entries, field_first
    ("plain", "default", [None], True),
    ("plain", "default", [None, None], False),
    ("plain", "int", [None], True),
    ("this", "int", [None], False),
    ("plain", "default", [5], True),
    ("this", "int", [7], True),
    ("this", "default", [3, None], False),
    ("plain", "int", [None, 4], True),
    ("this", "int", [2, 6], False),
]


def build_a(i, combo):
    p_kind, c_super, entries, field_first = combo
    v = dict(names=NAMES_A[i], p_kind=p_kind, c_super=c_super, entries=entries,
             field_first=field_first, k=[8, 9, 1, 3, 4, 5, 7, 2, 6][i])
    out, rows = sim_a(v)
    bugs = bugs_a(v)
    wrong = misconceptions(lambda bs: sim_a(v, bs)[0], bugs, combos=True)
    P, C, *_ = v["names"]
    code = render_a(v)
    first = "new " + C + ("()" if entries[0] is None else f"({entries[0]})")
    solve = [
        f"{first}가 처음 실행되면 클래스 초기화가 먼저 일어난다. 부모 {P}의 static 블록, 이어서 {C}의 static 블록이 "
        f"한 번씩 실행된다. 그다음 객체 생성: 생성자 첫 줄이 this(...)이면 같은 클래스의 다른 생성자로 위임하고, "
        f"super(...)(생략 시 super())이면 부모 생성자를 끝까지 실행한다. super 호출이 돌아온 직후에 그 클래스의 "
        f"필드 초기화식과 인스턴스 블록이 작성 순서대로 실행되고, 마지막으로 생성자 본문이 실행된다.",
        trace_table(["출력", "이유"], rows),
        f"출력을 이어 붙이면 {out}이다."
        + (" 두 번째 객체부터는 static 블록이 다시 실행되지 않는다." if len(entries) > 1 else "")
        + (f" {P}(int)는 this()로 {P}()에 위임하므로, {P}의 인스턴스 블록은 {P}() 쪽에서 한 번만 실행된다."
           if p_kind == "this" and c_super == "int" else ""),
    ]
    complexity = (p_kind == "this") + (c_super == "int") + (len(entries) > 1) + any(e is not None for e in entries)
    diff = 1 if complexity <= 1 else (2 if complexity == 2 else 3)
    return jq(
        id=f"j-ctor-{i + 1:02d}", code=code, output=out, solve=solve, wrong=wrong, family=FAM,
        sources=SOURCES, topic=TOPIC, difficulty=diff, trail=True,
        tags=["생성자", "초기화 블록", "static 블록", "super", "this()"],
        ask=f"{C} 객체를 {len(entries)}번 생성할 때 static 블록, 인스턴스 초기화(필드 초기화식·블록), "
            f"생성자 본문이 출력되는 순서를 묻는다. this()/super(...) 위임 경로가 판단 지점이다.",
        tip="순서는 ① 클래스 static(부모→자식, 최초 1회) ② 부모 생성자 완료 ③ 자식 필드·인스턴스 블록(작성 순) "
            "④ 자식 생성자 본문이다. this(...)로 위임하는 생성자는 초기화를 하지 않고 위임받은 생성자가 한다.",
    )


# ------------------------------------------------------------------ template B
B_SPECS = [
    # names, field kind, child overrides, parent calls, init style
    dict(names=("Widget", "Button", "draw"), ftype="int", init="field", override=True, val=7),
    dict(names=("Animal", "Cat", "speak"), ftype="String", init="field", override=True, val="meow"),
    dict(names=("Account", "Saving", "info"), ftype="int", init="ctor", override=True, val=30),
    dict(names=("Engine", "Turbo", "report"), ftype="int", init="static", override=True, val=5),
    dict(names=("Logger", "FileLog", "label"), ftype="int", init="field", override="private", val=9),
    dict(names=("Sensor", "Thermo", "read"), ftype="String", init="ctor", override=True, val="hot"),
]


def sim_b(s, bugs=frozenset()):
    P, C, m = s["names"]
    val = s["val"]
    default = "null" if s["ftype"] == "String" else "0"
    rows = []
    # parent ctor call of m()
    if s["override"] == "private" and "private_dyn" in bugs:
        first = f"{C[0]}{default}"
        rows.append([f"{P}() 안의 {m}()", f"{C}.{m}", first])
    elif s["override"] is True and "no_dynamic" not in bugs:
        ready = s["init"] == "static" or "field_ready" in bugs
        if s["init"] == "static" and "static_default" in bugs:
            ready = False
        first = f"{C[0]}{val if ready else default}"
        rows.append([f"{P}() 안의 {m}()", f"{C}.{m} (동적 바인딩)", first])
    else:
        first = f"{P[0]}{s['pv']}"
        rows.append([f"{P}() 안의 {m}()", f"{P}.{m}", first])
    # child ctor body call of m()
    second = f"{C[0]}{val}"
    rows.append([f"{C}() 본문의 {m}()", f"{C}.{m}", second])
    toks = [first, second]
    if "child_first" in bugs:
        toks = [second, first]
    if "once" in bugs:
        toks = [second]
    return " ".join(toks), rows


def render_b(s):
    P, C, m = s["names"]
    t = s["ftype"]
    lit = f'"{s["val"]}"' if t == "String" else str(s["val"])
    pc = [
        f"class {P} {{",
        f"    int pv = {s['pv']};",
        f"    {P}() {{ {m}(); }}",
        f'    {"private " if s["override"] == "private" else ""}void {m}() {{ System.out.print("{P[0]}" + pv + " "); }}',
        "}",
        "",
        f"class {C} extends {P} {{",
    ]
    if s["init"] == "field":
        pc.append(f"    {t} w = {lit};")
    elif s["init"] == "static":
        pc.append(f"    static {t} w = {lit};")
    else:
        pc.append(f"    {t} w;")
    if s["init"] == "ctor":
        pc += [f"    {C}() {{", f"        w = {lit};", f"        {m}();", "    }"]
    else:
        pc.append(f"    {C}() {{ {m}(); }}")
    pc.append(f'    void {m}() {{ System.out.print("{C[0]}" + w + " "); }}')
    pc.append("}")
    body = [f"new {C}();", "System.out.println();"]
    return main_class(body, before=pc)


def build_b(j, s):
    s = dict(s, pv=[4, 6, 2, 8, 3, 1][j])
    P, C, m = s["names"]
    out, rows = sim_b(s)
    default = "null" if s["ftype"] == "String" else "0"
    bugs = {
        "no_dynamic": f"부모 생성자 안의 {m}() 호출은 부모 클래스 코드라서 {P}.{m}()가 실행된다고 보았다. 생성 중인 객체는 이미 {C}이므로 재정의 메서드가 호출된다.",
        "child_first": f"자식 생성자 본문이 먼저, 부모 생성자가 나중에 실행된다고 보았다. {C}()의 첫 줄에 숨은 super()가 먼저 실행된다.",
        "once": f"부모 생성자에서 호출된 {m}()는 출력되지 않는다고 보고 자식 본문의 호출만 셌다. 부모 생성자도 실제로 {m}()를 호출해 출력한다.",
    }
    if s["override"] == "private":
        del bugs["no_dynamic"]
        bugs["private_dyn"] = (f"{P}.{m}()가 private인데도 {C}의 {m}()로 재정의돼 동적 바인딩된다고 보았다. "
                               f"private 메서드는 재정의되지 않아 {P}() 안의 호출은 {P}.{m}()로 고정된다.")
    if s["override"] is True and s["init"] != "static":
        bugs["field_ready"] = (f"부모 생성자가 실행될 때 {C}의 필드 w가 이미 초기화돼 있다고 보았다. 자식 필드 초기화는 "
                               f"super() 이후에 일어나므로 그 시점 w는 기본값 {default}이다.")
    if s["init"] == "static":
        bugs["static_default"] = ("static 필드도 인스턴스 필드처럼 부모 생성자 시점에 기본값이라고 보았다. static 필드는 "
                                  "클래스 초기화 때 이미 값이 들어가 있다.")
    wrong = misconceptions(lambda bs: sim_b(s, bs)[0], bugs, combos=True)
    f, sec = out.split(" ")
    other_default = "0" if default == "null" else "null"
    extra = [
        (f"{f[0]}{other_default} {sec}", f"참조형/기본형 기본값을 혼동했다. {s['ftype']} 필드의 기본값은 {default}이다."),
        (f"{f[0]} {sec}", f"아직 대입되지 않은 필드는 빈 문자열로 출력된다고 보았다. 기본값 {default}가 문자열로 붙는다."),
        (f"{P[0]}{s['pv']} {P[0]}{s['pv']}", f"{C}가 {P}를 상속하니 {m}()는 모두 부모 버전이 실행된다고 보았다. "
                                         + "자식 본문의 호출은 생성 중인 객체의 클래스 기준으로 고른다."),
        (f"{C[0]}{s['val']}", f"객체를 한 번 생성하면 메서드도 한 번만 호출된다고 보았다. 부모 생성자와 자식 생성자가 각각 {m}()를 호출한다."),
        (f"{P[0]}{s['pv']} {C[0]}{default}", f"부모 생성자는 부모 메서드를, 자식 본문은 아직 초기화되지 않은 w를 출력한다고 거꾸로 보았다."),
        (f"{C[0]}{default} {C[0]}{default}", f"w가 생성자 끝날 때까지 기본값으로 남는다고 보았다. 필드 초기화는 자식 생성자 본문 실행 전에 끝난다."),
        (f"{P[0]}0 {sec}", f"부모 필드 pv도 생성자 실행 시점에 기본값 0이라고 보았다. {P}의 필드 초기화는 {P}() 본문 전에 끝난다."),
    ]
    wrong += extra
    code = render_b(s)
    if s["override"] is True:
        if s["init"] == "static":
            core = f"w는 static 필드라 클래스 초기화 때 이미 {s['val']}이 들어가 있으므로, 부모 생성자에서 호출된 {C}.{m}()도 {s['val']}을 출력한다."
        else:
            core = (f"부모 생성자 {P}()가 실행되는 시점에는 {C}의 필드 w가 아직 초기화 전이라 기본값 {default}이다. "
                    f"그런데 {m}()는 재정의되어 있어 생성 중인 객체({C}) 기준으로 {C}.{m}()가 호출되므로 {C[0]}{default}가 찍힌다.")
    else:
        core = (f"{P}.{m}()는 private이라 {C}의 {m}()는 재정의가 아닌 별개 메서드다. 그래서 {P}() 안의 호출은 "
                f"{P}.{m}()로 고정되어 {P[0]}{s['pv']}를 찍고, {C}() 본문의 호출은 {C}.{m}()로 이미 초기화된 w를 찍는다.")
    solve = [
        f"new {C}()의 순서: {C}() 첫 줄의 숨은 super() → {P}의 필드 초기화(pv = {s['pv']}) → {P}() 본문의 {m}() → "
        f"{C}의 필드 초기화 → {C}() 본문. {core}",
        trace_table(["호출 위치", "실행 메서드", "출력"], rows),
        f"따라서 출력은 {out}이다. 생성자에서 재정의 가능한 메서드를 부르면 자식 필드가 준비되기 전에 자식 코드가 실행될 수 있어 실무에서도 피하는 패턴이다.",
    ]
    diff = {("field", True): 3, ("ctor", True): 3, ("static", True): 3, ("field", "private"): 2}[(s["init"], s["override"])]
    if s["ftype"] == "String" and s["init"] == "field":
        diff = 2
    if j == 2:
        diff = 2
    return jq(
        id=f"j-ctor-{j + 10:02d}", code=code, output=out, solve=solve, wrong=wrong, family=FAM,
        sources=SOURCES, topic=TOPIC, difficulty=diff, trail=True,
        tags=["생성자", "동적 바인딩", "필드 기본값", "초기화 순서"],
        ask=f"부모 생성자 안에서 {m}()를 호출할 때 어떤 메서드가 실행되고, 그 순간 자식 필드 w가 어떤 값인지 묻는다. "
            f"w의 선언 방식({ {'field': '필드 초기화식', 'ctor': '생성자 본문 대입', 'static': 'static 초기화'}[s['init']] })이 핵심 조건이다.",
        tip="생성자 안의 메서드 호출도 동적 바인딩된다. 자식 인스턴스 필드는 부모 생성자가 끝난 뒤 초기화되므로 그 전에는 "
            "0/false/null 같은 기본값이다. static 필드는 이와 달리 객체 생성 전에 이미 초기화된다.",
    )


def generate():
    out = [build_a(i, c) for i, c in enumerate(A_COMBOS)]
    out += [build_b(j, s) for j, s in enumerate(B_SPECS)]
    return out
