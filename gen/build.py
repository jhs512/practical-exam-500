"""Generate every question, execute code answers, validate, write site/data.

usage: python gen/build.py [--only <family-module-or-bank-substring>] [--no-write]
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "runners"))

from core import AREAS, LABELS  # noqa: E402
import theory  # noqa: E402
import validate  # noqa: E402
import release  # noqa: E402
from run import run_all  # noqa: E402

DATA = ROOT / "site" / "data"
CHUNK = 100


def collect(only: str | None) -> list[dict]:
    qs: list[dict] = []
    for p in sorted((HERE / "families").glob("*.py")):
        if p.stem not in release.MODULES or (only and not p.stem.startswith(only)):
            continue
        mod = importlib.import_module(f"families.{p.stem}")
        if not hasattr(mod, "generate"):
            continue  # shared helper module
        got = mod.generate()
        print(f"  {p.stem:28s} {len(got):5d}")
        qs.extend(got)
    for p in sorted(theory.CONCEPT_DIR.glob("*.json")):
        if p.stem not in release.BANKS:
            continue
        if only and not p.stem.startswith(only):
            continue
        got = theory.bank_questions(p)
        print(f"  {p.stem:28s} {len(got):5d}  (bank)")
        qs.extend(got)
    return qs


def verify(qs: list[dict]) -> list[str]:
    targets = [q for q in qs if "_verify" in q]
    outs = run_all([(q["_verify"]["lang"], q["_verify"]["src"]) for q in targets])
    errors = []
    for q, out in zip(targets, outs):
        exp = q["_verify"]["expect"]
        if out.rstrip("\n") != exp.rstrip("\n"):
            errors.append(f"{q['id']}: executed output differs\n--- expected\n{exp}\n--- actual\n{out}")
    print(f"  executed {len(targets)} programs, {len(errors)} mismatches")
    return errors


def write(qs: list[dict]) -> None:
    qs = sorted(qs, key=lambda q: (q["area"], q["id"]))
    if DATA.resolve() != (ROOT.resolve() / "site" / "data"):
        raise ValueError("Data output must stay inside this project's site/data")
    if DATA.exists():
        shutil.rmtree(DATA)
    (DATA / "chunks").mkdir(parents=True)
    items = []
    private_map = {}
    for i in range(0, len(qs), CHUNK):
        n = i // CHUNK
        chunk = []
        for q in qs[i:i + CHUNK]:
            private_map[q["id"]] = {"family": q["_family"], "sources": q["_sources"], "tags": q["tags"]}
            pub = {k: v for k, v in q.items() if not k.startswith("_")}
            chunk.append(pub)
            items.append([q["id"], q["area"], q["label"], q["topic"], n])
        (DATA / "chunks" / f"c{n:03d}.json").write_text(
            json.dumps(chunk, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    index = {"version": 1, "total": len(qs), "chunkSize": CHUNK,
             "areas": [{"id": k, "name": v} for k, v in AREAS.items()],
             "labels": {str(k): v for k, v in LABELS.items()}, "items": items}
    (DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (ROOT / "private").mkdir(exist_ok=True)
    (ROOT / "private" / "source-map.json").write_text(json.dumps(private_map, ensure_ascii=False, indent=0),
                                                       encoding="utf-8")
    print(f"  wrote {len(qs)} questions in {(len(qs) + CHUNK - 1) // CHUNK} chunks")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--no-exec", action="store_true")
    ap.add_argument("--write-partial", action="store_true", help="dev only: write site data for a subset")
    args = ap.parse_args()
    print("collect")
    qs = collect(args.only)
    if not args.only:
        qs = release.select(qs)
    errors = [] if args.no_exec else verify(qs)
    report = validate.validate(qs, full=not args.only)
    errors += report["errors"]
    (ROOT / "reports").mkdir(exist_ok=True)
    name = "validation.json" if not args.only else f"validation-{args.only}.json"
    (ROOT / "reports" / name).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for e in errors[:40]:
        print("ERROR", e)
    print(f"total {len(qs)}, errors {len(errors)}, warnings {len(report['warnings'])}")
    if errors:
        return 1
    if not args.no_write and (not args.only or args.write_partial):
        write(qs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
