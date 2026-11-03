"""Reconstruct and execute every SQL question from the actual public bundle."""
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def value(text):
    if text == "NULL":
        return None
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    return text


def show(value):
    if value is None:
        return "NULL"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def statements(text):
    pending = ""
    out = []
    for char in text:
        pending += char
        if char == ";" and sqlite3.complete_statement(pending):
            out.append(pending)
            pending = ""
    assert not pending.strip(), "Query must have a terminating semicolon"
    return out


def main():
    index = json.loads((ROOT / "site/data/index.json").read_text(encoding="utf-8"))
    questions = []
    for path in sorted((ROOT / "site/data/chunks").glob("*.json")):
        questions.extend(json.loads(path.read_text(encoding="utf-8")))
    assert len(questions) == index["total"] == 500
    assert len({q["id"] for q in questions}) == 500
    assert {q["id"] for q in questions} == {item[0] for item in index["items"]}
    checked = 0
    for q in questions:
        if not q.get("code") or q["code"]["lang"] != "sql":
            continue
        with sqlite3.connect(":memory:") as db:
            for table in q["tables"]:
                name = table["caption"]
                identifiers = [name] + table["columns"]
                assert all(re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]*", c) for c in identifiers), q["id"]
                columns = ", ".join('"' + c + '"' for c in table["columns"])
                db.execute(f'CREATE TABLE "{name}" ({columns})')
                slots = ",".join("?" for _ in table["columns"])
                db.executemany(f'INSERT INTO "{name}" VALUES ({slots})',
                               [[value(x) for x in row] for row in table["rows"]])
            results = [db.execute(sql).fetchall() for sql in statements(q["code"]["text"])]
        if len(results) == 2:
            assert "-- (가)" in q["code"]["text"] and "-- (나)" in q["code"]["text"], q["id"]
            assert all(len(rows) == 1 and len(rows[0]) == 1 for rows in results), q["id"]
            actual = f"(가) {show(results[0][0][0])}, (나) {show(results[1][0][0])}"
        else:
            assert len(results) == 1, q["id"]
            rows = results[0]
            actual = " / ".join(", ".join(show(x) for x in row) for row in rows) if rows else "결과 없음"
        expected = next(c["text"] for c in q["choices"] if c["id"] == q["answer"])
        assert actual == expected, (q["id"], actual, expected)
        checked += 1
    assert checked == 47, checked
    print(f"Public bundle: 500 distinct questions; {checked} SQL results independently matched")


if __name__ == "__main__":
    main()
