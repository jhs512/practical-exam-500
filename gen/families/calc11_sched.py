"""CPU scheduling: FCFS / SJF / SRT / RR / HRN / priority (non-preemptive, preemptive).

The real scheduler is simulated for the asked algorithm. Wrong choices re-run the
same input with a named mistake: another algorithm, the opposite RR queue order,
original burst instead of remaining time, reversed priority meaning, lowest ratio
for HRN, ignoring arrival times, or mixing up waiting/turnaround/response.
Reasoning points vary by arrival pattern (all at 0, staggered, idle gap), by
whether preemption happens, and by whether the RR queue convention matters.
"""
from __future__ import annotations

from fractions import Fraction

from core import rng
from families.calc11_common import enough, fmt, qbuild, table, tbl

SOURCES = {
    "srt": ["past-2024-2-12", "past-2026-2-8"],
    "rr": ["past-2025-2-13"],
    "hrn": ["past-2020-1-7"],
}
DEFAULT_SOURCES = ["past-2022-3-16", "past-2025-2-4"]

NAME = {
    "fcfs": "FCFS(First Come First Served)",
    "sjf": "SJF(Shortest Job First, 비선점)",
    "srt": "SRT(Shortest Remaining Time, 선점)",
    "rr": "RR(Round Robin)",
    "hrn": "HRN(Highest Response ratio Next)",
    "pri": "비선점 우선순위(Priority)",
    "prip": "선점 우선순위(Preemptive Priority)",
}
RULE = {
    "fcfs": "준비 큐에 먼저 도착한 프로세스부터 끝까지 실행한다.",
    "sjf": "CPU가 비는 시점에 도착해 있는 프로세스 중 실행 시간이 가장 짧은 것을 골라 끝까지 실행한다.",
    "srt": "매 시점 남은 실행 시간이 가장 짧은 프로세스를 실행하며, 더 짧은 프로세스가 도착하면 실행 중인 프로세스를 선점한다.",
    "rr": "준비 큐 앞의 프로세스를 타임 퀀텀만큼 실행하고, 끝나지 않으면 준비 큐 맨 뒤로 보낸다.",
    "hrn": "CPU가 비는 시점에 응답 비율 (대기 시간 + 실행 시간) / 실행 시간이 가장 큰 프로세스를 골라 끝까지 실행한다.",
    "pri": "CPU가 비는 시점에 도착해 있는 프로세스 중 우선순위 번호가 가장 작은(우선순위가 높은) 것을 골라 끝까지 실행한다.",
    "prip": "매 시점 우선순위 번호가 가장 작은 프로세스를 실행하며, 더 높은 우선순위가 도착하면 즉시 선점한다.",
}


# ---------------------------------------------------------------- simulators

def merge(units):
    seg = []
    for t, name in enumerate(units):
        if seg and seg[-1][0] == name:
            seg[-1] = (name, seg[-1][1], t + 1)
        else:
            seg.append((name, t, t + 1))
    return seg


def nonpre(P, key):
    t, fin, seg, log = 0, {}, [], []
    while len(fin) < len(P):
        ready = [p for p in P if p["name"] not in fin and p["arr"] <= t]
        if not ready:
            nt = min(p["arr"] for p in P if p["name"] not in fin)
            seg.append((None, t, nt))
            t = nt
            continue
        p = min(ready, key=lambda p: key(p, t))
        log.append((t, ready, p["name"]))
        seg.append((p["name"], t, t + p["burst"]))
        t += p["burst"]
        fin[p["name"]] = t
    return seg, fin, log


def pre(P, key):
    """Unit-time preemptive scheduler. Returns (seg, fin, tie) where tie flags an
    equal primary key between the best two ready processes."""
    t, fin, units, tie = 0, {}, [], False
    rem = {p["name"]: p["burst"] for p in P}
    while len(fin) < len(P):
        ready = [p for p in P if p["name"] not in fin and p["arr"] <= t]
        if not ready:
            units.append(None)
            t += 1
            continue
        ready.sort(key=lambda p: key(p, rem[p["name"]]))
        if len(ready) > 1 and key(ready[0], rem[ready[0]["name"]])[0] == key(ready[1], rem[ready[1]["name"]])[0]:
            tie = True
        p = ready[0]
        units.append(p["name"])
        rem[p["name"]] -= 1
        t += 1
        if rem[p["name"]] == 0:
            fin[p["name"]] = t
    return merge(units), fin, tie


def rr(P, q, new_first=True):
    if q <= 0:
        raise ValueError("Round-robin quantum must be positive")
    order = sorted(P, key=lambda p: (p["arr"], p["i"]))
    rem = {p["name"]: p["burst"] for p in P}
    t, fin, seg, log, queue, k = 0, {}, [], [], [], 0
    coincide = []
    while k < len(order) and order[k]["arr"] <= t:
        queue.append(order[k]["name"]); k += 1
    while len(fin) < len(P):
        if not queue:
            nt = order[k]["arr"]
            seg.append((None, t, nt))
            t = nt
            while k < len(order) and order[k]["arr"] <= t:
                queue.append(order[k]["name"]); k += 1
            continue
        name = queue.pop(0)
        run = min(q, rem[name])
        s = t
        t += run
        rem[name] -= run
        before, at = [], []
        while k < len(order) and order[k]["arr"] <= t:
            (at if order[k]["arr"] == t else before).append(order[k]["name"]); k += 1
        queue += before
        if rem[name] > 0:
            if at:
                coincide.append((t, at, name))
            queue += (at + [name]) if new_first else ([name] + at)
        else:
            fin[name] = t
            queue += at
        seg.append((name, s, t))
        log.append([f"{s}~{t}", name, run, rem[name], ", ".join(queue) or "(비어 있음)"])
    return seg, fin, log, coincide


def sjf_noarr(P):
    """Mistake: sort by burst first and ignore that a job may not have arrived."""
    t, fin, seg = 0, {}, []
    for p in sorted(P, key=lambda p: (p["burst"], p["arr"], p["i"])):
        if p["arr"] > t:
            seg.append((None, t, p["arr"]))
            t = p["arr"]
        seg.append((p["name"], t, t + p["burst"]))
        t += p["burst"]
        fin[p["name"]] = t
    return seg, fin


KEYS = {
    "fcfs": lambda p, t: (p["arr"], p["i"]),
    "sjf": lambda p, t: (p["burst"], p["arr"], p["i"]),
    "hrn": lambda p, t: (-Fraction(t - p["arr"] + p["burst"], p["burst"]), p["arr"], p["i"]),
    "hrn_low": lambda p, t: (Fraction(t - p["arr"] + p["burst"], p["burst"]), p["arr"], p["i"]),
    "pri": lambda p, t: (p["pri"], p["arr"], p["i"]),
    "pri_rev": lambda p, t: (-p["pri"], p["arr"], p["i"]),
}
PKEYS = {
    "srt": lambda p, r: (r, p["arr"], p["i"]),
    "srt_orig": lambda p, r: (p["burst"], p["arr"], p["i"]),
    "prip": lambda p, r: (p["pri"], p["arr"], p["i"]),
    "prip_rev": lambda p, r: (-p["pri"], p["arr"], p["i"]),
}


def run(P, algo, q=2):
    """Returns (seg, fin) for algorithm or named mistake."""
    if algo in KEYS:
        s, f, _ = nonpre(P, KEYS[algo])
        return s, f
    if algo in PKEYS:
        s, f, _ = pre(P, PKEYS[algo])
        return s, f
    if algo == "rr":
        s, f, _, _ = rr(P, q, True)
        return s, f
    if algo == "rr_old":
        s, f, _, _ = rr(P, q, False)
        return s, f
    if algo == "sjf_noarr":
        return sjf_noarr(P)
    raise KeyError(algo)


def zeroed(P):
    return [dict(p, arr=0) for p in P]


def first_start(seg):
    st = {}
    for name, s, _ in seg:
        if name and name not in st:
            st[name] = s
    return st


def measure(P, seg, fin, metric):
    n = len(P)
    if metric == "wait":
        return Fraction(sum(fin[p["name"]] - p["arr"] - p["burst"] for p in P), n)
    if metric == "tat":
        return Fraction(sum(fin[p["name"]] - p["arr"] for p in P), n)
    if metric == "order":
        return sorted(P, key=lambda p: (fin[p["name"]], p["i"]))
    raise KeyError(metric)


def show(val, metric):
    if metric == "order":
        return " → ".join(p["name"] for p in val)
    return fmt(val)


# ------------------------------------------------------------- distractors

def alt_note(algo, q):
    return {
        "fcfs": "도착 순서대로만 처리하는 FCFS로 계산한 값이다.",
        "sjf": "실행 시간이 짧은 작업을 고르되 한 번 시작하면 끝까지 실행하는 SJF(비선점)로 계산한 값이다.",
        "srt": "남은 시간이 더 짧은 프로세스가 오면 선점하는 SRT로 계산한 값이다.",
        "rr": f"퀀텀 {q}의 RR로 돌아가며 실행했다고 보고 계산한 값이다.",
        "hrn": "응답 비율이 가장 큰 작업을 고르는 HRN으로 계산한 값이다.",
        "pri": "우선순위 번호가 작은 작업부터 비선점으로 실행해 계산한 값이다.",
        "prip": "더 높은 우선순위가 도착하면 선점하는 방식으로 계산한 값이다.",
    }[algo]


def preempt_events(P, seg):
    rem = {p["name"]: p["burst"] for p in P}
    ev = []
    for idx, (name, s, e) in enumerate(seg):
        if name is None:
            continue
        rem[name] -= e - s
        if rem[name] > 0 and idx + 1 < len(seg) and seg[idx + 1][0]:
            ev.append((e, name, rem[name], seg[idx + 1][0]))
    return ev


def candidates(P, algo, metric, q, has_pri):
    """[(value_text, note)] most relevant first."""
    seg, fin = run(P, algo, q)
    out = []
    target = NAME[algo]

    def add(alg, note):
        s, f = run(P, alg, q or 2)
        out.append((show(measure(P, s, f, metric), metric), note))

    ev = preempt_events(P, seg)
    ev_txt = (f"t={ev[0][0]}에 {ev[0][1]}가 중단되고 {ev[0][3]}가 실행되는 선점을 반영해야 한다."
              if ev else "")
    if algo == "srt":
        add("srt_orig", "새로 도착한 프로세스와 비교할 때 실행 중인 프로세스의 남은 시간이 아니라 처음 실행 시간을 사용했다. SRT는 남은 시간끼리 비교한다.")
        add("sjf", alt_note("sjf", q) + " " + ev_txt)
    if algo == "prip":
        add("pri", "선점을 하지 않는 비선점 우선순위로 계산했다. " + ev_txt)
        add("prip_rev", "우선순위 번호가 클수록 우선순위가 높다고 거꾸로 읽고 선점 방식으로 계산했다. 문제 조건은 번호가 작을수록 높다.")
    if algo == "pri":
        add("pri_rev", "우선순위 번호가 클수록 먼저 실행한다고 거꾸로 읽었다. 문제 조건은 번호가 작을수록 우선순위가 높다.")
        add("prip", "비선점 조건을 무시하고, 더 높은 우선순위가 도착하면 선점한다고 보고 계산했다.")
    if algo == "hrn":
        add("hrn_low", "응답 비율이 가장 작은 프로세스를 골랐다. HRN은 오래 기다린 작업의 비율이 커지도록 해 가장 큰 값을 선택한다.")
        add("sjf", "대기 시간을 반영하지 않고 실행 시간만 비교하는 SJF로 계산했다. HRN은 (대기+실행)/실행으로 기다린 시간을 보상한다.")
    if algo == "sjf":
        add("sjf_noarr", "도착 시간을 무시하고 실행 시간이 짧은 순서로 먼저 줄 세운 뒤 처리했다. SJF는 CPU가 비는 시점에 이미 도착한 프로세스 중에서만 고른다.")
        add("srt", "비선점인 SJF를 선점형 SRT처럼 계산했다. SJF는 시작한 작업을 끝까지 실행한다.")
    if algo == "rr":
        _, _, _, co = rr(P, q, True)
        if co:
            t, at, name = co[0]
            note = (f"t={t}에 {', '.join(at)} 도착과 {name}의 퀀텀 종료가 겹칠 때 {name}를 먼저 큐에 넣었다. "
                    "문제 조건은 새로 도착한 프로세스가 먼저 준비 큐에 들어간다.")
        else:
            note = "큐 순서 규칙을 잘못 적용해 계산한 값이다."
        add("rr_old", note)
        for qq in (q + 1, q - 1):
            if qq >= 1 and qq != q:
                s, f = run(P, "rr", qq)
                out.append((show(measure(P, s, f, metric), metric),
                            f"타임 퀀텀을 {q}가 아니라 {qq}로 적용해 계산한 값이다."))
    if algo == "fcfs":
        idx = sorted(P, key=lambda p: p["i"])
        if [p["name"] for p in idx] != [p["name"] for p in sorted(P, key=lambda p: (p["arr"], p["i"]))]:
            t, fin2, seg2 = 0, {}, []
            for p in idx:
                t = max(t, p["arr"]) + p["burst"]
                fin2[p["name"]] = t
            out.append((show(measure(P, seg2, fin2, metric), metric),
                        "도착 시간이 아니라 표의 프로세스 번호 순서대로 실행했다. FCFS의 기준은 도착 시각이다."))

    if metric in ("wait", "tat"):
        n = len(P)
        tat = measure(P, seg, fin, "tat")
        wait = measure(P, seg, fin, "wait")
        if metric == "wait":
            out.append((fmt(tat), "대기 시간이 아니라 반환 시간(종료 - 도착)의 평균을 구했다. 대기 시간은 반환 시간에서 실행 시간을 뺀 값이다."))
            out.append((fmt(Fraction(sum(fin[p["name"]] - p["burst"] for p in P), n)),
                        "대기 시간을 '종료 시각 - 실행 시간'으로 계산해 도착 시각을 빼지 않았다."))
            st = first_start(seg)
            resp = Fraction(sum(st[p["name"]] - p["arr"] for p in P), n)
            if algo in ("srt", "prip", "rr"):
                out.append((fmt(resp), "처음 CPU를 받은 시각까지만 대기로 셌다(응답 시간). 선점·퀀텀 만료 뒤 다시 기다린 시간도 대기 시간에 포함된다."))
            out.append((fmt(wait * n), "평균이 아니라 대기 시간의 합계를 답했다."))
        else:
            out.append((fmt(wait), "반환 시간이 아니라 대기 시간(반환 - 실행)의 평균을 구했다."))
            out.append((fmt(Fraction(sum(fin[p["name"]] for p in P), n)),
                        "반환 시간을 종료 시각 그대로 보고 도착 시각을 빼지 않았다."))
            out.append((fmt(tat * n), "평균이 아니라 반환 시간의 합계를 답했다."))
    else:
        st = first_start(seg)
        start_order = sorted(P, key=lambda p: (st[p["name"]], p["i"]))
        if algo in ("srt", "prip", "rr"):
            out.append((show(start_order, "order"),
                        "완료 순서가 아니라 처음 CPU를 받은 순서를 적었다. 선점이나 퀀텀 만료로 먼저 시작한 프로세스가 늦게 끝날 수 있다."))
        out.append((show(sorted(P, key=lambda p: (p["burst"], p["i"])), "order"),
                    "도착 시각을 보지 않고 실행 시간이 짧은 순서대로 나열했다."))
        out.append((show(sorted(P, key=lambda p: -p["i"]), "order"),
                    "번호 역순으로 나열했다. 완료 순서는 스케줄 결과의 종료 시각으로 정해진다."))
        out.append((show(sorted(P, key=lambda p: (-p["burst"], p["i"])), "order"),
                    "실행 시간이 긴 순서대로 나열했다. 긴 작업이 먼저 끝나는 것은 FCFS에서 먼저 도착했을 때뿐이다."))

    if any(p["arr"] for p in P):
        z = zeroed(P)
        s, f = run(z, algo, q)
        out.append((show(measure(z, s, f, metric), metric),
                    f"모든 프로세스가 0에 도착했다고 보고 {target} 규칙을 적용했다. 표의 도착 시각을 반영해야 한다."))
    if metric in ("wait", "tat"):
        base = measure(P, seg, fin, metric)
        for p in P:
            for sign in (1, -1):
                value = base + sign * Fraction(p["burst"], len(P))
                if value >= 0:
                    action = "한 번 더 더했다" if sign > 0 else "한 번 더 뺐다"
                    out.append((fmt(value), f"{p['name']}의 실행 시간 {p['burst']}을 합계에서 {action}. 각 프로세스의 종료·도착·실행 시간을 표로 구분한 뒤 평균을 계산해야 한다."))
    else:
        ordered = list(measure(P, seg, fin, metric))
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                swapped = list(ordered)
                swapped[i], swapped[j] = swapped[j], swapped[i]
                out.append((show(swapped, "order"), f"종료 시각으로 정렬했을 때 {i + 1}번째와 {j + 1}번째 프로세스의 위치를 서로 바꾼 결과다. 시작 순서나 중간 실행 구간이 아니라 각 작업의 마지막 구간 끝을 비교한다."))
    pool = ["fcfs", "sjf", "srt", "hrn", "rr"] + (["pri", "prip"] if has_pri else [])
    for alt in pool:
        if alt != algo:
            add(alt, alt_note(alt, q or 2) + f" 문제는 {target} 방식이다.")
    return out


# --------------------------------------------------------------- variants

# (algo, metric, pattern, n, difficulty, q)
VARIANTS = [
    ("fcfs", "wait", "zero", 4, 1, 0), ("fcfs", "tat", "stagger", 4, 1, 0), ("fcfs", "wait", "gap", 5, 2, 0),
    ("fcfs", "tat", "shuffled", 5, 1, 0),
    ("sjf", "wait", "zero", 5, 1, 0), ("sjf", "wait", "stagger", 4, 2, 0), ("sjf", "tat", "stagger", 5, 2, 0),
    ("sjf", "order", "stagger", 5, 2, 0), ("sjf", "wait", "gap", 5, 2, 0), ("sjf", "tat", "shuffled", 4, 1, 0),
    ("srt", "wait", "preempt1", 4, 2, 0), ("srt", "tat", "preempt1", 4, 3, 0), ("srt", "wait", "preempt2", 5, 3, 0),
    ("srt", "order", "preempt2", 5, 3, 0), ("srt", "wait", "gap", 4, 3, 0), ("srt", "tat", "preempt2", 5, 3, 0),
    ("srt", "wait", "preempt2", 4, 3, 0),
    ("rr", "wait", "zero", 4, 2, 2), ("rr", "wait", "zero", 4, 2, 3), ("rr", "tat", "conv", 4, 3, 2),
    ("rr", "wait", "conv", 5, 3, 3), ("rr", "order", "conv", 4, 3, 2), ("rr", "tat", "zero", 5, 2, 4),
    ("rr", "wait", "noconv", 4, 2, 2),
    ("hrn", "wait", "stagger", 4, 2, 0), ("hrn", "tat", "stagger", 5, 2, 0), ("hrn", "order", "stagger", 5, 2, 0),
    ("hrn", "wait", "diff", 5, 3, 0), ("hrn", "order", "diff", 4, 3, 0),
    ("pri", "wait", "zero", 5, 1, 0), ("pri", "tat", "stagger", 4, 2, 0), ("pri", "order", "stagger", 5, 2, 0),
    ("prip", "wait", "preempt1", 4, 2, 0), ("prip", "tat", "preempt2", 5, 3, 0),
    ("prip", "order", "preempt1", 5, 2, 0), ("prip", "wait", "gap", 4, 3, 0),
]
METRIC = {"wait": "평균 대기 시간", "tat": "평균 반환 시간(turnaround time)", "order": "프로세스가 완료되는 순서"}


def make_procs(r, n, pattern, algo):
    names = [f"P{i + 1}" for i in range(n)]
    hi = 9 if algo != "rr" else 8
    burst = [r.randint(1, hi) for _ in range(n)]
    if pattern == "zero":
        arr = [0] * n
    elif pattern == "shuffled":
        arr = [0] + [r.randint(0, 6) for _ in range(n - 1)]
        r.shuffle(arr)
    elif pattern == "gap":
        arr = sorted([0] + [r.randint(0, 14) for _ in range(n - 1)])
    else:
        arr = sorted([0] + [r.randint(0, 8) for _ in range(n - 1)])
    pri = r.sample(range(1, n + 2), n)
    return [{"name": names[i], "i": i, "arr": arr[i], "burst": burst[i], "pri": pri[i]} for i in range(n)]


def pattern_ok(P, algo, pattern, q, metric):
    if algo == "rr":
        seg, fin, log, co = rr(P, q, True)
        idle = any(s[0] is None for s in seg)
        if idle:
            return False
        if pattern == "conv":
            s2, f2 = run(P, "rr_old", q)
            return bool(co) and measure(P, seg, fin, metric) != measure(P, s2, f2, metric) \
                and (metric != "order" or show(measure(P, seg, fin, metric), metric) != show(measure(P, s2, f2, metric), metric))
        if pattern == "noconv":
            return not co and any(p["arr"] for p in P) and len(seg) >= len(P) + 3
        return len(seg) >= len(P) + 3
    if algo in ("srt", "prip"):
        seg, fin, tie = pre(P, PKEYS[algo])
        if tie and algo == "srt":
            return False
        npre = len(preempt_events(P, seg))
        idle = any(s[0] is None for s in seg)
        if pattern == "gap":
            return idle and npre >= 1
        if idle:
            return False
        return npre >= (2 if pattern == "preempt2" else 1)
    seg, fin = run(P, algo)
    idle = any(s[0] is None for s in seg)
    if pattern == "gap":
        return idle
    if idle:
        return False
    if pattern == "diff":
        s2, f2 = run(P, "sjf")
        return show(measure(P, seg, fin, "order"), "order") != show(measure(P, s2, f2, "order"), "order")
    if algo in ("sjf", "hrn", "pri") and pattern != "zero":
        # the chosen job must differ from plain arrival order at least once
        s2, f2 = run(P, "fcfs")
        return show(measure(P, seg, fin, "order"), "order") != show(measure(P, s2, f2, "order"), "order")
    return True


def gantt(seg):
    return tbl("간트 차트(Gantt chart)", ["구간", "실행"], [[f"{s}~{e}", n or "유휴(idle)"] for n, s, e in seg])


def result_table(P, fin):
    rows = []
    for p in P:
        f = fin[p["name"]]
        rows.append([p["name"], p["arr"], p["burst"], f, f"{f}-{p['arr']}={f - p['arr']}",
                     f"{f - p['arr']}-{p['burst']}={f - p['arr'] - p['burst']}"])
    return tbl("프로세스별 결과", ["프로세스", "도착", "실행", "종료", "반환", "대기"], rows)


def build(n_idx, variant):
    algo, metric, pattern, n, diff, q = variant
    seed = f"calc11-sched-{n_idx}"
    r = rng(seed)
    has_pri = algo in ("pri", "prip")
    for _ in range(50000):
        P = make_procs(r, n, pattern, algo)
        if not pattern_ok(P, algo, pattern, q, metric):
            continue
        seg, fin = run(P, algo, q)
        ans = show(measure(P, seg, fin, metric), metric)
        wrong = candidates(P, algo, metric, q, has_pri)
        if enough(ans, wrong):
            break
    else:
        raise RuntimeError(f"no instance for {variant}")

    cols = ["프로세스", "도착 시간", "실행 시간"] + (["우선순위"] if has_pri else [])
    rows = [[p["name"], p["arr"], p["burst"]] + ([p["pri"]] if has_pri else []) for p in P]
    conv = ["조건이 같으면 먼저 도착한 프로세스, 도착 시각도 같으면 번호가 작은 프로세스를 먼저 선택한다."]
    if has_pri:
        conv.append("우선순위는 번호가 작을수록 높다.")
    if algo == "rr":
        conv.append(f"타임 퀀텀은 {q}이다. 같은 시각에 새로 도착한 프로세스와 퀀텀이 끝난 프로세스가 겹치면 "
                    "새로 도착한 프로세스가 먼저 준비 큐에 들어간다.")
    if algo in ("srt", "prip", "rr"):
        conv.append("문맥 교환 시간은 무시한다.")
    stem = (f"다음 표의 프로세스를 {NAME[algo]} 방식으로 스케줄링할 때 {METRIC[metric]}{'는' if metric == 'order' else '은'}? "
            + " ".join(conv))

    solve = [f"{NAME[algo]}: {RULE[algo]}"]
    if algo == "rr":
        _, _, log, co = rr(P, q, True)
        solve.append(tbl("RR 진행(퀀텀 단위)", ["구간", "실행", "실행량", "남은 시간", "실행 후 준비 큐"], log))
        if co:
            t, at, name = co[0]
            solve.append(f"t={t}에는 {', '.join(at)}의 도착과 {name}의 퀀텀 종료가 겹친다. 조건에 따라 "
                         f"{', '.join(at)}를 먼저 큐에 넣고 {name}를 그 뒤에 넣는다. 이 순서가 이후 실행 순서를 바꾼다.")
    elif algo == "hrn":
        _, _, log = nonpre(P, KEYS["hrn"])
        hrows = []
        for t, ready, chosen in log:
            if len(ready) == 1:
                cand = f"{ready[0]['name']}만 대기"
            else:
                cand = ", ".join(f"{p['name']} ({t - p['arr']}+{p['burst']})/{p['burst']}="
                                 f"{fmt(Fraction(t - p['arr'] + p['burst'], p['burst']))}" for p in ready)
            hrows.append([f"t={t}", cand, chosen])
        solve.append(tbl("선택 시점별 응답 비율", ["시점", "후보와 응답 비율", "선택"], hrows))
    elif algo in ("srt", "prip"):
        ev = preempt_events(P, seg)
        if ev:
            what = "남은 시간" if algo == "srt" else "우선순위"
            solve.append("선점이 일어나는 시점: " + "; ".join(
                f"t={t}에 {a}(남은 {rm})가 중단되고 {b}가 실행된다" for t, a, rm, b in ev)
                + f". 각 시점에 새로 도착한 프로세스와 실행 중인 프로세스의 {what}을 비교해야 한다.")
    elif algo in ("sjf", "pri", "fcfs"):
        _, _, log = nonpre(P, KEYS[algo])
        picks = [f"t={t}: {', '.join(p['name'] for p in ready)} 중 {c}" for t, ready, c in log if len(ready) > 1]
        if picks:
            solve.append("CPU가 빌 때 도착해 있는 후보와 선택: " + "; ".join(picks) + ".")
    solve.append(gantt(seg))
    solve.append(result_table(P, fin))
    nn = len(P)
    if metric == "wait":
        vals = [fin[p["name"]] - p["arr"] - p["burst"] for p in P]
        solve.append(f"평균 대기 시간 = ({' + '.join(map(str, vals))}) / {nn} = {sum(vals)} / {nn} = {ans}. "
                     "대기 시간은 반환 시간(종료 - 도착)에서 실행 시간을 뺀 값이다.")
    elif metric == "tat":
        vals = [fin[p["name"]] - p["arr"] for p in P]
        solve.append(f"평균 반환 시간 = ({' + '.join(map(str, vals))}) / {nn} = {sum(vals)} / {nn} = {ans}. "
                     "반환 시간은 도착부터 종료까지 걸린 시간이다.")
    else:
        solve.append(f"종료 시각이 빠른 순서로 나열하면 {ans}이다. 간트 차트의 마지막 실행 구간 끝이 각 프로세스의 종료 시각이다.")

    tips = {
        "fcfs": "FCFS는 도착 시각만 보면 된다. 도착 사이에 CPU가 비는 구간(유휴)이 있으면 다음 시작 시각이 도착 시각으로 밀린다는 점만 주의한다.",
        "sjf": "SJF는 'CPU가 비는 순간 이미 도착한 후보'만 비교한다. 짧지만 아직 도착하지 않은 작업을 끌어오는 실수가 가장 흔하다.",
        "srt": "SRT는 새 프로세스가 도착하는 시각마다 남은 시간끼리 비교한다. 중단된 프로세스의 대기 시간은 여러 구간으로 나뉘므로 '반환 - 실행'으로 한 번에 구하면 안전하다.",
        "rr": "RR은 준비 큐 상태를 구간마다 적어야 틀리지 않는다. 퀀텀 종료와 도착이 같은 시각이면 문제에 주어진 큐 삽입 순서를 먼저 확인한다.",
        "hrn": "HRN은 선택 시점마다 대기 시간이 달라지므로 비율을 매번 다시 계산한다. 비율 = 1 + 대기/실행이라 오래 기다린 짧은 작업이 유리하다.",
        "pri": "우선순위 문제는 번호의 의미(작을수록 높음/클수록 높음)와 선점 여부를 먼저 확인한다. 비선점이면 실행 중인 작업은 끝까지 간다.",
        "prip": "선점 우선순위는 도착 시각마다 실행 중인 프로세스와 우선순위를 비교한다. 대기 시간은 '반환 - 실행'으로 구하면 중단 구간을 빠뜨리지 않는다.",
    }
    ask = (f"{NAME[algo]}로 스케줄링한 결과의 {METRIC[metric]}을 묻는다. "
           + {"zero": "모든 프로세스가 0에 도착하므로 선택 규칙만으로 순서가 정해진다.",
              "stagger": "도착 시각이 서로 달라 선택 시점마다 후보가 바뀐다.",
              "shuffled": "표의 번호 순서와 도착 순서가 다르다는 점이 함정이다.",
              "gap": "도중에 CPU가 비는 유휴 구간이 생긴다는 점이 핵심 조건이다.",
              "preempt1": "도착 시점에 선점이 일어나는지 판단해야 한다.",
              "preempt2": "선점이 여러 번 일어나 실행이 쪼개진다.",
              "conv": "퀀텀 종료와 새 도착이 같은 시각에 겹쳐 큐 삽입 순서 규칙이 결과를 좌우한다.",
              "noconv": "도착이 퀀텀 경계와 겹치지 않으므로 준비 큐를 차례대로 따라가면 된다.",
              "diff": "대기 시간이 쌓인 긴 작업이 짧은 작업보다 먼저 선택되는 순간이 있다.",
              }[pattern])
    fam = f"calc11-sched-{algo}"
    count = sum(1 for v in VARIANTS[:n_idx] if v[0] == algo) + 1
    return qbuild(
        id=f"calc11-sched-{algo}-{count:02d}", family=fam, topic=f"CPU 스케줄링 {algo.upper()} 계산",
        tags=["운영체제", "CPU 스케줄링", NAME[algo].split("(")[0], METRIC[metric].split("(")[0]],
        stem=stem, answer=ans,
        answer_note=f"{NAME[algo]} 규칙대로 간트 차트를 그리고 {METRIC[metric]}을 구한 값이다.",
        wrong=wrong, ask=ask, solve=solve, tip=tips[algo], difficulty=diff,
        tables=[table("프로세스 정보", cols, rows)], sources=SOURCES.get(algo, DEFAULT_SOURCES))


def generate():
    return [build(i, v) for i, v in enumerate(VARIANTS)]
