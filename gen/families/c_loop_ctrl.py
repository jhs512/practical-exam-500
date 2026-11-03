"""C: for loop over an array with continue / break and an accumulator.

Reasoning points that vary across variants: which element triggers continue, whether
and where break fires (or never), the accumulator rule, and whether the break test
sits before or after the accumulation. Misconceptions are simulated, not guessed.
"""
from __future__ import annotations

from codekit import code_question, trace_table
from core import rng

SOURCES = ["sinagong-1-1"]

SKIP = {  # name: (C condition, python predicate, Korean)
    "even": ("a[i] % 2 == 0", lambda v: v % 2 == 0, "짝수"),
    "mul3": ("a[i] % 3 == 0", lambda v: v % 3 == 0, "3의 배수"),
    "lt4": ("a[i] < 4", lambda v: v < 4, "4보다 작은 값"),
}
STOP = {  # break condition on the running total s or the element
    "s_gt": ("s > {t}", "s", "누적값 s가 {t}를 넘으면"),
    "v_gt": ("a[i] > {t}", "v", "원소가 {t}보다 크면"),
}
ACC = {  # accumulator rule
    "sum": ("s += a[i];", lambda s, v, i: s + v, "s에 a[i]를 더한다"),
    "dbl": ("s = s * 2 + a[i];", lambda s, v, i: s * 2 + v, "s를 두 배 한 뒤 a[i]를 더한다"),
    "idx": ("s += a[i] * i;", lambda s, v, i: s + v * i, "s에 a[i]×i를 더한다"),
}


def simulate(a, skip, stop, t, acc, stop_after, bug=None):
    """Returns (s, rows). bug names a misconception to simulate."""
    pred = SKIP[skip][1]
    f = ACC[acc][1]
    s = 0
    rows = []
    start = 1 if bug == "start1" else 0
    end = len(a) - 1 if bug == "short" else len(a)
    for i in range(start, end):
        v = a[i]
        if bug == "ge":
            stop_hit = (lambda: (s >= t) if stop == "s_gt" else (v >= t))
        else:
            stop_hit = (lambda: (s > t) if stop == "s_gt" else (v > t))
        skipped = (not pred(v)) if bug == "invert_skip" else pred(v)
        if skipped and bug != "no_continue":
            if bug == "continue_is_break":
                rows.append([i, v, "continue를 break로 오해 → 종료", s])
                break
            rows.append([i, v, "continue(건너뜀)", s])
            continue
        if not stop_after and stop_hit() and bug != "no_break":
            if bug == "break_is_continue":
                rows.append([i, v, "break를 continue로 오해 → 건너뜀", s])
                continue
            if bug == "add_then_break":
                s = f(s, v, i)
                rows.append([i, v, "더한 뒤 break로 오해", s])
                break
            rows.append([i, v, "break(반복 종료)", s])
            break
        s = f(s, v, i) if bug != "count" else s + 1
        if stop_after and stop_hit() and bug != "no_break":
            if bug == "break_is_continue":
                rows.append([i, v, "누적 후 조건 참이지만 계속 진행으로 오해", s])
                continue
            rows.append([i, v, "누적 후 break", s])
            break
        rows.append([i, v, "누적", s])
    return s, rows


def render(a, skip, stop, t, acc, stop_after):
    cond_stop = STOP[stop][0].format(t=t)
    body = [f"        if ({SKIP[skip][0]}) continue;"]
    if stop_after:
        body += [f"        {ACC[acc][0]}", f"        if ({cond_stop}) break;"]
    else:
        body += [f"        if ({cond_stop}) break;", f"        {ACC[acc][0]}"]
    arr = ", ".join(map(str, a))
    return "\n".join([
        "#include <stdio.h>",
        "",
        "int main(void) {",
        f"    int a[] = {{{arr}}};",
        "    int s = 0;",
        f"    for (int i = 0; i < {len(a)}; i++) {{",
        *body,
        "    }",
        '    printf("%d\\n", s);',
        "    return 0;",
        "}",
        "",
    ])


def wrong_outputs(a, skip, stop, t, acc, stop_after, s, rows):
    bugs = {
        "continue_is_break": "continue를 break처럼 읽어 첫 번째 건너뛰기에서 반복을 끝냈다. continue는 이번 회차의 나머지만 건너뛰고 i++로 다음 회차를 계속한다.",
        "break_is_continue": "break를 continue처럼 읽어 조건을 만족한 원소만 건너뛰고 끝까지 돌았다. break는 for 문 전체를 즉시 빠져나간다.",
        "no_break": "break 조건을 무시하고 배열 끝까지 누적했다.",
        "no_continue": "continue 조건을 무시해서 건너뛰어야 할 원소까지 누적했다.",
        "start1": "배열 첨자를 1부터 센다고 착각해 a[0]을 처리하지 않았다. C 배열은 0부터 시작한다.",
        "short": f"i < {len(a)}를 i < {len(a) - 1}처럼 읽어 마지막 원소를 처리하지 않았다(반복 경계 착오).",
        "count": "누적식 대신 누적한 원소의 개수를 셌다.",
        "invert_skip": "continue 조건을 반대로 읽어, 조건을 만족하지 않는 원소를 건너뛰었다.",
        "ge": "break 조건의 >를 >=로 읽어 경계값과 같을 때도 종료된다고 보았다.",
    }
    if not stop_after:
        bugs["add_then_break"] = "break 조건이 누적문보다 위에 있는데도, break를 만난 원소를 먼저 더한 뒤 종료했다고 보았다."
    wrong = []
    for bug, note in bugs.items():
        v, _ = simulate(a, skip, stop, t, acc, stop_after, bug)
        wrong.append((f"{v}\n", note))
    # Two-error combinations are realistic for hurried tracing.
    for b1, b2, note in [
        ("no_continue", "no_break", "continue와 break를 모두 무시하고 모든 원소를 누적했다."),
    ]:
        s2 = 0
        for i, v in enumerate(a):
            s2 = ACC[acc][1](s2, v, i)
        wrong.append((f"{s2}\n", note))
    wrong.append((f"{rows[-1][1]}\n", "누적값이 아니라 반복이 끝난 시점의 원소 a[i]를 출력한다고 착각했다."))
    return wrong



VARIANTS = []
for skip in SKIP:
    for stop in STOP:
        for acc in ACC:
            VARIANTS.append((skip, stop, acc))


def generate():
    out = []
    for n, (skip, stop, acc) in enumerate(VARIANTS):
        for k in range(1):
            seed = f"c-loop-ctrl-{n}-{k}"
            r = rng(seed)
            for attempt in range(20000):
                stop_after = r.random() < 0.5
                a = [r.randint(1, 12) for _ in range(r.choice([6, 7, 8]))]
                if stop == "v_gt":
                    t = r.choice([8, 9, 10])
                else:
                    t = r.choice([10, 15, 20, 25])
                s, rows = simulate(a, skip, stop, t, acc, stop_after)
                acts = [row[2] for row in rows]
                # Need a real continue and a real break that fires before the end,
                # and misconceptions that all lead to different outputs.
                if not (any("continue" in x for x in acts) and any("break" in x for x in acts) and len(rows) >= 3):
                    continue
                wrong = wrong_outputs(a, skip, stop, t, acc, stop_after, s, rows)
                if len({w for w, _ in wrong} - {f"{s}\n"}) >= 9:
                    break
            code = render(a, skip, stop, t, acc, stop_after)
            stop_desc = STOP[stop][2].format(t=t)
            order = "누적한 다음 break 조건을 검사" if stop_after else "break 조건을 먼저 검사한 다음 누적"
            solve = [
                f"반복 한 회차의 순서: ① {SKIP[skip][2]}이면 continue로 이번 회차를 건너뛴다 → ② {order}한다. 누적 규칙은 '{ACC[acc][2]}'이다.",
                trace_table(["i", "a[i]", "동작", "s"], rows),
                f"break가 실행되는 순간 for 문을 빠져나가므로 그 뒤 원소는 보지 않는다. 최종 s = {s}이고 printf가 이 값을 출력한다.",
            ]
            if acc == "dbl":
                solve.append("s = s * 2 + a[i]는 이전 누적값이 매번 두 배가 되므로, 앞에서 더한 원소일수록 결과에 크게 반영된다. 회차마다 s를 새로 적어야 실수가 줄어든다.")
            if acc == "idx":
                solve.append("a[i] * i는 i = 0일 때 0이 되므로, 첫 원소는 누적되어도 s에 영향을 주지 않는다.")
            out.append(code_question(
                id=f"c-loop-ctrl-{n + 1:02d}", lang="c", code=code, output=f"{s}\n", solve=solve, wrong=wrong,
                ask=f"for 문 안에서 continue({SKIP[skip][2]} 건너뛰기)와 break({stop_desc} 종료)가 섞여 있을 때 최종 누적값 s를 묻는다. break 검사가 누적 {'뒤' if stop_after else '앞'}에 있다는 점이 핵심 조건이다.",
                tip="continue는 '이번 회차만 생략', break는 '반복 전체 종료'다. 검사문과 누적문의 위아래 순서에 따라 경계 원소가 포함되는지가 바뀌므로, i·a[i]·s를 표로 적으며 추적한다.",
                topic="C 반복 제어(continue·break)", tags=["C", "for", "continue", "break", "누적"],
                difficulty=2 if acc == "sum" else 3, family="c-loop-ctrl", sources=SOURCES,
            ))
    return out
