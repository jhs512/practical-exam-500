"""Java: static (class) members vs instance members.

Mode 0: constructor counter (static total, per-object copy); mode 1: methods called
through references (static field shared, instance field per object, static method
called via an instance); mode 2: static block / instance block / constructor order and
the class-initialization trigger (a compile-time constant does not trigger it).
"""
from __future__ import annotations

from families.java_lib import family, pr, trace_table

FAM = "j-static"
TOPIC = "Java static 멤버와 인스턴스 멤버"
SRC = ["itpasslab-2-10"]

V0 = [("Ticket", "issued", "no", "step"), ("Order", "placed", "seq", "qty"),
      ("Member", "joined", "rank", "gain"), ("Task", "created", "pos", "weight"),
      ("Seat", "booked", "num", "span")]
V1 = [("Box", "total", "count", "add", "reset"), ("Cart", "sum", "items", "put", "clear"),
      ("Wallet", "bank", "cash", "save", "empty"), ("Tank", "pool", "level", "fill", "drain"),
      ("Meter", "grand", "local", "tick", "zero")]
V2 = [("Log", "hi", "MAX"), ("Boot", "go", "LIMIT"), ("Unit", "run", "SIZE"),
      ("Node", "ping", "DEPTH"), ("Cell", "tap", "WIDTH")]


def mode0(i, r):
    C, S, N, P = V0[(i // 3) % 5]
    n = r.choice([3, 3, 4])
    steps = [r.randint(1, 4) for _ in range(n)]
    pre = r.random() < 0.5
    names = "abcd"[:n]
    first, second = (f"{N} = {S};", f"{S} += {P};")
    ctor = [first, second] if pre else [second, first]
    code = "\n".join([
        f"class {C} {{",
        f"    static int {S} = 0;",
        f"    int {N};",
        f"    int {P};",
        f"    {C}(int {P}) {{",
        f"        this.{P} = {P};",
        *[f"        {x}" for x in ctor],
        "    }",
        "}",
        "",
        "public class Main {",
        "    public static void main(String[] args) {",
        *[f"        {C} {c} = new {C}({s});" for c, s in zip(names, steps)],
        *pr([f"{c}.{N}" for c in names] + [f"{C}.{S}"]),
        "    }",
        "}", ""])
    last = names[-1]
    muts = [
        ([(f"    static int {S} = 0;", f"    int {S} = 0;"), (f"{C}.{S}", f"{last}.{S}")],
         f"static 필드 {S}를 객체마다 따로 있는 인스턴스 필드로 보았다. static은 클래스에 하나뿐이라 모든 객체가 같은 {S}를 누적한다."),
        ([(f"        this.{P} = {P};\n", f"        this.{P} = {P};\n        {S} = 0;\n")],
         "static 초기화(= 0)가 생성자 호출 때마다 다시 실행된다고 보았다. 초기화는 클래스 로딩 때 한 번뿐이다."),
        ([(f"    int {N};", f"    static int {N};")],
         f"{N}도 모든 객체가 공유한다고 보았다. {N}은 인스턴스 필드라 객체마다 생성 시점의 값이 따로 저장된다."),
        ([(f"{S} += {P};", f"{S}++;")],
         f"생성자가 {P}만큼이 아니라 1씩 올린다고 읽었다. {S} += {P}는 인자를 누적한다."),
        ([(f"    static int {S} = 0;", f"    static int {S} = 1;")],
         f"{S}의 초기값을 1로 잘못 읽었다. 코드의 초기값은 0이다."),
        ([(f"{C}.{S}", f"{last}.{N}")],
         f"마지막 줄의 {C}.{S}를 마지막 객체의 {N}과 같은 값으로 보았다. {N}은 복사 시점의 값이고 {S}는 최종 누적값이다."),
        ([(ctor[0], "TMP"), (ctor[1], ctor[0]), ("TMP", ctor[1])],
         "생성자 안 두 문장의 순서를 반대로 읽었다. 복사되는 값이 증가 전/후로 달라진다."),
        ([(f"{C}.{S}", f"a.{P}")],
         f"static 필드 {S} 자리에 첫 객체의 {P}를 읽었다. {C}.{S}는 모든 생성자의 누적 결과다."),
        ([(f"{S} += {P};", f"{S} += {P} * 2;")],
         f"생성자에서 {P}를 두 번 더한다고 읽었다. 한 번만 더한다."),
        ([(f"{C}.{S}", f"{names[0]}.{N}")],
         f"{C}.{S}가 첫 객체가 받은 {N}과 같다고 보았다. 첫 번호는 첫 생성 직후(또는 직전) 값이고 {S}는 마지막 생성 뒤 값이다."),
    ]
    run, rows = 0, []
    for c, s in zip(names, steps):
        if pre:
            no, run = run, run + s
        else:
            run += s
            no = run
        rows.append([f"new {C}({s})", c, no, run])
    para = (f"{S}는 static 필드라 클래스에 하나뿐이고 모든 {C} 객체가 공유한다. 생성자가 호출될 때마다 {P}만큼 누적되며, "
            f"{N}은 인스턴스 필드라 생성 시점에 읽은 {S} 값이 객체별로 따로 저장된다. "
            + (f"이 코드는 {N}에 먼저 현재 {S}를 복사한 뒤 누적하므로 {N}은 증가 전 값이다." if pre
               else f"이 코드는 먼저 누적한 뒤 {N}에 복사하므로 {N}은 증가 후 값이다."))
    return dict(code=code, muts=muts,
                solve=lambda out: [para, trace_table(["생성", "변수", f"{N} 저장값", f"{S} 누적"], rows),
                                   f"마지막 줄은 각 객체의 {N}을 순서대로 읽고 {C}.{S}의 최종 값을 붙이므로 출력은 {out}이다."],
                ask=f"static 필드 하나를 여러 객체가 공유하는 방식과, 생성자 안 문장 순서({'복사 후 누적' if pre else '누적 후 복사'})가 "
                    "인스턴스 필드 값에 미치는 영향을 묻는다.",
                tip="static 필드는 객체 수와 무관하게 한 칸이다. 생성자 안에서는 문장 순서대로 값이 변한다는 점과, "
                    "각 객체에 복사된 값은 그 뒤 static이 바뀌어도 그대로라는 점을 표로 확인한다.",
                diff=2 if pre else 1, tags=["static", "생성자", "카운터"])


def mode1(i, r):
    C, T, K, A, R = V1[(i // 3) % 5]
    a, b, c = r.randint(1, 6), r.randint(2, 7), r.randint(1, 5)
    via = r.choice(["y", "x", C])
    reset_at = r.choice(["mid", "end"])
    rcall = f"{via}.{R}();"
    pre = [f"x.{A}({a});", f"y.{A}({b});"]
    post = [f"x.{A}({c});"]
    seq = pre + [rcall] + post if reset_at == "mid" else pre + post + [rcall]
    code = "\n".join([
        f"class {C} {{",
        f"    static int {T} = 0;",
        f"    int {K} = 0;",
        f"    void {A}(int v) {{",
        f"        {K} += v;",
        f"        {T} += v;",
        "    }",
        f"    static void {R}() {{",
        f"        {T} = 0;",
        "    }",
        "}",
        "",
        "public class Main {",
        "    public static void main(String[] args) {",
        f"        {C} x = new {C}();",
        f"        {C} y = new {C}();",
        *[f"        {s}" for s in seq],
        *pr([f"x.{K}", f"y.{K}", f"{C}.{T}"]),
        "    }",
        "}", ""])
    other = f"y.{R}();" if via != "y" else f"x.{R}();"
    muts = [
        ([(f"    static int {T} = 0;", f"    int {T} = 0;"), (f"{C}.{T}", f"x.{T}"),
          (f"    static void {R}()", f"    void {R}()")]
        + ([(rcall, f"x.{R}();")] if via == C else []),
         f"{T}를 인스턴스 필드로 보아 x와 y가 각자 합계를 가진다고 계산했다. static이라 한 칸을 공유한다."),
        ([(f"    int {K} = 0;", f"    static int {K} = 0;")],
         f"{K}도 공유된다고 보았다. {K}는 인스턴스 필드라 x와 y가 각각 가진다."),
        ([(rcall, "")],
         f"{R}() 호출을 무시했다. static 메서드도 참조로 호출하면 실행되고 {T}를 0으로 만든다."),
        ([(rcall, other)],
         f"{R}()를 호출한 참조가 가리키는 객체만 초기화된다고 보았다. static 메서드는 참조와 무관하게 클래스 전체의 {T}를 바꾼다."),
        ([(f"        {T} += v;", f"        {T} = v;")],
         f"{T} += v를 대입으로 읽어 마지막 값만 남는다고 보았다. +=는 누적한다."),
        ([(f"{C}.{T}", f"y.{K}")],
         f"{C}.{T} 자리에 y.{K}를 읽었다. {T}는 x와 y의 호출을 모두 합친 static 값이다."),
        ([(f"        {K} += v;", f"        {K} = v;")],
         f"{K} += v를 대입으로 읽어 마지막으로 더한 값만 남는다고 보았다."),
        ([(f"x.{K}", "TMP"), (f"y.{K}", f"x.{K}"), ("TMP", f"y.{K}")],
         "출력 순서를 y, x로 읽었다. 코드는 x가 먼저다."),
        ([(f"        {T} += v;", f"        {T} += v * 2;")],
         f"{A}가 {T}에 두 배를 더한다고 읽었다."),
        ([(f"    int {K} = 0;", f"    int {K} = 1;")],
         f"{K}의 초기값을 1로 읽었다."),
        ([(f"x.{A}({a});", f"x.{A}({a});\n        x.{A}({a});")],
         "첫 호출을 두 번 실행한다고 읽었다."),
    ]
    cx = cy = run = 0
    rows = []
    for s in seq:
        if s.startswith(f"x.{A}"):
            v = int(s.split("(")[1][:-2]); cx += v; run += v
            rows.append([s, f"x.{K}={cx}, y.{K}={cy}", run])
        elif s.startswith(f"y.{A}"):
            v = int(s.split("(")[1][:-2]); cy += v; run += v
            rows.append([s, f"x.{K}={cx}, y.{K}={cy}", run])
        else:
            run = 0
            rows.append([s, f"x.{K}={cx}, y.{K}={cy}", f"0 ({R} 실행)"])
    para = (f"{K}는 인스턴스 필드라 x와 y가 각자 가지고, {T}는 static 필드라 {C} 클래스에 한 칸만 있다. {A}는 두 필드를 함께 올리므로 "
            f"어느 참조로 불러도 {T}에는 합쳐진다. {R}()는 static 메서드라 {via}.{R}()처럼 불러도 참조 객체와 상관없이 {C}.{T}를 0으로 만든다.")
    return dict(code=code, muts=muts,
                solve=lambda out: [para, trace_table(["실행 문장", f"{K} 값", T], rows),
                                   f"마지막 줄은 x.{K}, y.{K}, {C}.{T} 순서로 읽으므로 출력은 {out}이다."],
                ask=f"static 필드는 공유되고 인스턴스 필드는 객체별이라는 점, 그리고 static 메서드 {R}()를 "
                    f"{via} 쪽으로 호출한 시점({'중간' if reset_at == 'mid' else '마지막'})의 영향을 묻는다.",
                tip="필드마다 'static이면 한 칸, 아니면 객체마다 한 칸'을 먼저 그린다. static 메서드는 호출 표기가 "
                    "참조든 클래스명이든 같은 메서드다.",
                diff=2 if reset_at == "mid" else 1, tags=["static", "static 메서드", "참조"])


def mode2(i, r):
    C, H, M = V2[(i // 3) % 5]
    flavour = ["new2", "const", "call", "chain"][(i // 3) % 4]
    S, I, K = r.choice([("S", "I", "C"), ("s", "i", "c"), ("St", "In", "Ct")])
    lines = [
        f"class {C} {{",
        f'    static {{ System.out.print("{S} "); }}',
        f'    {{ System.out.print("{I} "); }}',
        f'    {C}() {{ System.out.print("{K} "); }}',
        f"    static final int {M} = 3;",
        f'    static void {H}() {{ System.out.print("H "); }}',
        "}",
        "",
        "public class Main {",
        "    public static void main(String[] args) {",
        '        System.out.print("M ");',
    ]
    body = {
        "new2": [f"        new {C}();", f"        new {C}();"],
        "const": [f"        int k = {C}.{M};", '        System.out.print(k + " ");', f"        new {C}();"],
        "call": [f"        {C}.{H}();", f"        new {C}();"],
        "chain": [f"        {C} g = null;", '        System.out.print("N ");',
                  f"        g = new {C}();", f"        {C}.{H}();"],
    }[flavour]
    code = "\n".join(lines + body + ["        System.out.println();", "    }", "}", ""])
    sb = f'    static {{ System.out.print("{S} "); }}'
    ib = f'    {{ System.out.print("{I} "); }}'
    ct = f'    {C}() {{ System.out.print("{K} "); }}'
    muts = [
        ([(sb, sb.replace("static ", ""))],
         "static 블록도 객체를 만들 때마다 실행된다고 보았다. static 초기화 블록은 클래스 로딩 때 한 번만 실행된다."),
        ([('System.out.print("M ");', f'System.out.print("{S} M ");'), (sb + "\n", "")],
         f"static 블록이 main보다 먼저, 프로그램 시작 시 실행된다고 보았다. {C}는 처음 사용될 때 로딩·초기화된다."),
        ([(ib + "\n", ""), (ct, f'    {C}() {{ System.out.print("{K} {I} "); }}')],
         "인스턴스 초기화 블록이 생성자 본문 뒤에 실행된다고 보았다. 블록은 생성자 본문보다 먼저 실행된다."),
        ([(sb + "\n", "")], "static 블록을 건너뛴다고 보았다. 클래스가 처음 쓰일 때 한 번은 반드시 실행된다."),
        ([(ib + "\n", "")], "인스턴스 초기화 블록은 실행되지 않는다고 보았다. 객체를 만들 때마다 생성자 본문 앞에서 실행된다."),
        ([(ct, f"    {C}() {{ }}")], "생성자가 출력을 하지 않는다고 읽었다."),
        ([('        System.out.print("M ");\n', "")], "main의 첫 출력 M을 빠뜨렸다."),
        ([('"H "', '"H H "')], f"{H}() 메서드가 두 번 출력한다고 읽었다."),
        ([(sb, sb.replace(f'"{S} "', f'"{S} {S} "'))], "static 블록 출력을 두 번으로 읽었다."),
        ([(ib, ib.replace(f'"{I} "', f'"{I} {I} "'))], "인스턴스 초기화 블록 출력을 두 번으로 읽었다."),
        ([(sb, sb + f'\n    static {{ System.out.print("{S}2 "); }}')], "static 블록이 하나 더 있다고 읽었다."),
    ]
    if flavour == "const":
        muts += [([(f"        int k = {C}.{M};", f"        int k = {C}.{M};\n        {C}.{H}();")],
                  "상수를 읽어도 클래스 초기화가 일어난다고 보았다. 컴파일 시점 상수는 읽어도 클래스를 초기화하지 않는다."),
                 ([('System.out.print(k + " ");', f'System.out.print("{S} " + k + " ");')],
                  f"{C}.{M} 접근이 static 블록을 실행시킨다고 보았다. 상수는 컴파일 때 값이 치환되어 {C}가 로딩되지 않는다.")]
    if flavour == "chain":
        muts += [([(f"{C} g = null;", f"{C} g = new {C}();")],
                  f"{C} g = null; 선언도 클래스 초기화와 생성자를 일으킨다고 보았다. 참조 변수 선언만으로는 로딩·생성이 없다.")]
    steps = {
        "new2": [["M 출력", "main 시작"], [f"첫 new {C}()", f"{C} 로딩 → {S}, 그다음 {I} {K}"],
                 [f"둘째 new {C}()", f"{I} {K} ({S}는 이미 실행됨)"]],
        "const": [["M 출력", "main 시작"], [f"{C}.{M} 읽기", "컴파일 시점 상수라 초기화 없음 → 3 출력"],
                  [f"new {C}()", f"처음 사용 → {S}, 그다음 {I} {K}"]],
        "call": [["M 출력", "main 시작"], [f"{C}.{H}()", f"static 호출이 클래스 초기화 유발 → {S}, 그다음 H"],
                 [f"new {C}()", f"{I} {K} ({S} 없음)"]],
        "chain": [["M 출력", "main 시작"], [f"{C} g = null", "참조만 선언, 로딩 없음 → N 출력"],
                  [f"g = new {C}()", f"처음 사용 → {S}, 그다음 {I} {K}"], [f"{C}.{H}()", "H"]],
    }[flavour]
    para = ("클래스 초기화(static 블록 실행)는 클래스를 처음 능동적으로 사용할 때 한 번만 일어난다. 객체를 만들면 생성자 본문보다 "
            f"인스턴스 초기화 블록이 먼저 실행되어 {I} 다음에 {K}가 나온다. "
            + (f"{C}.{M}은 static final 컴파일 시점 상수라 읽어도 초기화가 일어나지 않는다." if flavour == "const"
               else f"참조 변수 선언({C} g = null)만으로는 클래스가 초기화되지 않는다." if flavour == "chain"
               else "static 메서드 호출도 클래스 초기화를 일으킨다." if flavour == "call"
               else "두 번째 생성부터는 static 블록 없이 블록과 생성자 출력만 반복된다."))
    return dict(code=code, muts=muts, trail=True,
                solve=lambda out: [para, trace_table(["실행", "결과"], steps),
                                   f"출력은 한 줄에 공백으로 이어져 {out}이다."],
                ask="클래스 초기화(static 블록)가 언제, 몇 번 실행되는지와 인스턴스 초기화 블록·생성자 순서를 묻는다. 핵심 조건은 "
                    + {"new2": "객체를 두 번 생성", "const": "상수 접근 후 생성", "call": "static 메서드 호출 후 생성",
                       "chain": "null 참조 선언 후 생성"}[flavour] + "이다.",
                tip="static 블록은 클래스당 한 번(처음 능동 사용 시), 인스턴스 블록과 생성자는 객체마다 '블록 → 생성자' 순서다. "
                    "main이 이미 출력한 문자는 클래스 초기화보다 앞선다.",
                diff={"new2": 1, "const": 3, "call": 2, "chain": 3}[flavour],
                tags=["static 블록", "초기화 순서", "클래스 로딩"])


def make(i, r):
    return [mode0, mode1, mode2][i % 3](i, r)


def generate():
    return family(FAM, "static", TOPIC, 15, make, sources=SRC)
