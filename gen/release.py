"""The 500-question release: explicit sources and balanced, stable selection."""
from collections import defaultdict, deque

from core import pick

TOTAL = 500
# Editorial allocation, not an assertion about official examination weighting.
QUOTA = {"01": 21, "02": 43, "03": 6, "04": 30, "05": 11, "06": 9,
         "07": 41, "08": 47, "09": 51, "10": 149, "11": 84, "12": 8}
LANGUAGES = {"c": 65, "java": 45, "python": 39}
MODULES = {
    "c_char", "c_ifchain", "c_incdec", "c_intdiv", "c_loop_ctrl", "calc11_sched",
    "d02_card", "d02_fd_keys", "d02_fd_nf", "d02_ra",
    "java_ctor_chain", "java_override", "java_static", "kb_knowledge",
    "py_comp", "py_dict_set", "py_index_slice", "py_list_methods",
    "sql_count", "sql_group", "sql_null", "sql_where",
    "t07_bva", "t07_coverage", "t07_cyclo", "t07_dtable", "t07_ep", "release_cases",
}
BANKS = {"b09-dos", "b09-net", "b09-sol", "b09-web", "b11-dead", "b11-dr",
         "b11-mem", "b11-proc", "b11-raid", "d02-model", "if05-data", "s04-gof"}
assert sum(QUOTA.values()) == TOTAL
assert sum(LANGUAGES.values()) == QUOTA["10"]


def balanced(pool: list[dict], count: int, seed: str) -> list[dict]:
    if len(pool) < count:
        raise ValueError(f"{seed}: {len(pool)} candidates for {count} required questions")
    groups = defaultdict(list)
    for q in pool:
        groups[q["_family"]].append(q)
    queues = [deque(pick(group, seed + family)) for family, group in sorted(groups.items())]
    out = []
    while len(out) < count:
        for group in queues:
            if group:
                out.append(group.popleft())
                if len(out) == count:
                    break
    return out


def select(pool: list[dict]) -> list[dict]:
    by_area = defaultdict(list)
    for q in pool:
        by_area[q["area"]].append(q)
    out = []
    for area, count in QUOTA.items():
        if area == "10":
            for lang, n in LANGUAGES.items():
                candidates = [q for q in by_area[area] if (q.get("code") or {}).get("lang") == lang]
                out.extend(balanced(candidates, n, "release500-" + lang))
        else:
            out.extend(balanced(by_area[area], count, "release500-" + area))
    return out
