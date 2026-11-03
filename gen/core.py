"""Question contract shared by every generator.

Every generator returns a list of dicts built by `make_question`. The contract is
checked here at construction time so a bad item fails at its source, and checked
again over the whole bank by `validate.py`.
"""
from __future__ import annotations

import hashlib
import re

AREAS = {
    "01": "요구사항 확인",
    "02": "데이터 입출력 구현",
    "03": "통합 구현",
    "04": "서버프로그램 구현",
    "05": "인터페이스 구현",
    "06": "화면 설계",
    "07": "애플리케이션 테스트 관리",
    "08": "SQL 응용",
    "09": "소프트웨어 개발 보안 구축",
    "10": "프로그래밍 언어 활용",
    "11": "응용 SW 기초 기술 활용",
    "12": "제품소프트웨어 패키징",
}
LABELS = {1: "코딩·SQL", 2: "실무 이론", 3: "시험 암기"}
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MIN_CHOICES = 10
MAX_CHOICES = 12


class QuestionError(ValueError):
    pass


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _choice_id(qid: str, text: str, taken: set[str]) -> str:
    alphabet = "abcdefghijkmnpqrstuvwxyz23456789"
    salt = 0
    while True:
        h = int(_hash(qid, text, str(salt)), 16)
        cid = "".join(alphabet[(h >> (5 * i)) & 31] for i in range(3))
        if cid not in taken:
            taken.add(cid)
            return cid
        salt += 1


def _check_blocks(qid: str, blocks) -> list:
    if isinstance(blocks, str):
        blocks = [blocks]
    out = []
    for b in blocks:
        if isinstance(b, str):
            if not norm(b):
                raise QuestionError(f"{qid}: empty solve block")
            out.append(b.strip())
        elif isinstance(b, dict) and ("pre" in b or "table" in b):
            out.append(b)
        else:
            raise QuestionError(f"{qid}: bad solve block {b!r}")
    if not out:
        raise QuestionError(f"{qid}: solve is empty")
    return out


def _check_table(qid: str, t: dict) -> dict:
    cols = t.get("columns")
    rows = t.get("rows")
    if not cols or rows is None:
        raise QuestionError(f"{qid}: table needs columns and rows")
    for r in rows:
        if len(r) != len(cols):
            raise QuestionError(f"{qid}: table row width {len(r)} != {len(cols)}")
    return {"caption": t.get("caption", ""), "columns": [str(c) for c in cols],
            "rows": [["NULL" if v is None else str(v) for v in r] for r in rows]}


def make_question(*, id: str, area: str, label: int, difficulty: int, topic: str,
                  tags: list[str], stem: str, answer, distractors, ask: str, solve, tip: str,
                  code: dict | None = None, tables: list[dict] | None = None,
                  family: str | None = None, source_ideas=(), verify: dict | None = None) -> dict:
    """Build one question.

    answer: (text, note). distractors: iterable of (text, note), at least 9; first
    MAX_CHOICES-1 kept in given order of relevance. note explains why that choice is
    right/wrong and must be specific to it.
    verify: optional {"lang": "c"|"java"|"python", "src": str, "expect": str} — the
    build executes src and fails if stdout differs from expect.
    """
    if not ID_RE.match(id):
        raise QuestionError(f"bad id {id!r}")
    if area not in AREAS:
        raise QuestionError(f"{id}: bad area {area}")
    if label not in LABELS:
        raise QuestionError(f"{id}: bad label {label}")
    if difficulty not in (1, 2, 3):
        raise QuestionError(f"{id}: bad difficulty {difficulty}")
    for name, val in (("topic", topic), ("stem", stem), ("ask", ask), ("tip", tip)):
        if not norm(val):
            raise QuestionError(f"{id}: empty {name}")

    a_text, a_note = answer
    seen = {norm(a_text).lower()}
    kept = []
    for text, note in distractors:
        key = norm(text).lower()
        if key in seen:
            continue  # generators may propose overlapping wrong values; keep first
        if not norm(note):
            raise QuestionError(f"{id}: distractor {text!r} has no note")
        seen.add(key)
        kept.append((str(text), note))
        if len(kept) == MAX_CHOICES - 1:
            break
    if len(kept) < MIN_CHOICES - 1:
        raise QuestionError(f"{id}: only {len(kept)} distinct distractors (need {MIN_CHOICES - 1})")
    if not norm(a_text) or not norm(a_note):
        raise QuestionError(f"{id}: empty answer text/note")

    taken: set[str] = set()
    choices = [{"id": _choice_id(id, str(a_text), taken), "text": str(a_text), "note": a_note.strip()}]
    answer_id = choices[0]["id"]
    for text, note in kept:
        choices.append({"id": _choice_id(id, text, taken), "text": text, "note": note.strip()})
    # Store in a hash-determined order so the answer is not always first in the data.
    choices.sort(key=lambda c: _hash(id, "order", c["id"]))

    if code is not None:
        if not code.get("text", "").strip() or code.get("lang") not in ("c", "java", "python", "sql", "text", "cpp"):
            raise QuestionError(f"{id}: bad code block")
        code = {"lang": code["lang"], "text": code["text"].rstrip("\n")}
    if tables:
        tables = [_check_table(id, t) for t in tables]

    q = {
        "id": id,
        "area": area,
        "label": label,
        "difficulty": difficulty,
        "topic": norm(topic),
        "tags": [norm(t) for t in tags if norm(t)],
        "stem": stem.strip(),
        "code": code,
        "tables": tables or None,
        "choices": choices,
        "answer": answer_id,
        "explain": {"ask": ask.strip(), "solve": _check_blocks(id, solve), "tip": tip.strip()},
        "_family": family or id.rsplit("-", 1)[0],
        "_sources": list(source_ideas),
    }
    if verify is not None:
        if verify.get("lang") not in ("c", "java", "python") or "src" not in verify or "expect" not in verify:
            raise QuestionError(f"{id}: bad verify spec")
        q["_verify"] = verify
    return q


def pick(seq, seed: str, n: int | None = None):
    """Deterministic shuffle/pick keyed by seed (stable across runs and Python versions)."""
    ordered = sorted(seq, key=lambda x: _hash(seed, repr(x)))
    return ordered if n is None else ordered[:n]


def rng(seed: str):
    import random
    return random.Random(int(_hash(seed)[:16], 16))
