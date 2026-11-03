"""Execute C / Java / Python programs and return stdout, with an on-disk cache.

C   : `python -m ziglang cc` (clang; Debug build traps on undefined behaviour)
Java: every program must declare `public class Main`; each is placed in its own
      package, compiled with one javac call and run in-process by Harness.java.
Python: each program runs in a fresh `python -I` subprocess.
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "build-tmp"
CACHE = TMP / "run-cache.json"


def _key(lang: str, src: str) -> str:
    return hashlib.sha256(f"{lang}\x1f{src}".encode()).hexdigest()


def _load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    TMP.mkdir(exist_ok=True)
    try:
        merged = _load_cache()
    except (OSError, ValueError):
        merged = {}
    merged.update(cache)
    tmp = TMP / f"run-cache.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, CACHE)


def _run_c_one(h: str, src: str) -> tuple[str, str]:
    d = TMP / "c" / f"{h[:16]}-{os.getpid()}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "p.c").write_text(src, encoding="utf-8")
    exe = d / "p.exe"
    r = subprocess.run([sys.executable, "-m", "ziglang", "cc", "-std=c11", "-O0", "-w", "p.c", "-o", "p.exe"],
                       cwd=d, capture_output=True, text=True)
    if r.returncode != 0:
        return h, "<<COMPILE ERROR>>\n" + r.stderr[-2000:]
    r = subprocess.run([str(exe)], cwd=d, capture_output=True, timeout=10)
    out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    if r.returncode != 0:
        return h, f"<<EXIT {r.returncode}>>\n" + out
    return h, out


def _run_py_one(h: str, src: str) -> tuple[str, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONHASHSEED="0")
    r = subprocess.run([sys.executable, "-I", "-c", src], capture_output=True, timeout=10, env=env)
    out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    if r.returncode != 0:
        return h, f"<<EXIT {r.returncode}>>\n" + out + r.stderr.decode("utf-8", "replace")[-1500:]
    return h, out


HARNESS = r"""
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
public class Harness {
  public static void main(String[] args) throws Exception {
    PrintStream real = System.out;
    StringBuilder all = new StringBuilder();
    for (String pkg : Files.readAllLines(Paths.get(args[0]))) {
      if (pkg.isBlank()) continue;
      ByteArrayOutputStream buf = new ByteArrayOutputStream();
      PrintStream ps = new PrintStream(buf, true, StandardCharsets.UTF_8);
      System.setOut(ps);
      String out;
      try {
        Method m = Class.forName(pkg + ".Main").getMethod("main", String[].class);
        m.invoke(null, (Object) new String[0]);
        ps.flush();
        out = buf.toString(StandardCharsets.UTF_8);
      } catch (InvocationTargetException e) {
        ps.flush();
        out = "<<EXCEPTION " + e.getCause() + ">>\n" + buf.toString(StandardCharsets.UTF_8);
      }
      System.setOut(real);
      all.append("\u0001").append(pkg).append("\u0002").append(out);
    }
    Files.write(Paths.get(args[1]), all.toString().getBytes(StandardCharsets.UTF_8));
  }
}
"""


def _run_java(batch: dict[str, str]) -> dict[str, str]:
    d = TMP / f"java-{os.getpid()}"
    if d.exists():
        shutil.rmtree(d)
    (d / "src").mkdir(parents=True)
    pkgs = []
    for h, src in batch.items():
        pkg = "p" + h[:20]
        pdir = d / "src" / pkg
        pdir.mkdir()
        (pdir / "Main.java").write_text(f"package {pkg};\n" + src, encoding="utf-8")
        pkgs.append(pkg)
    (d / "src" / "Harness.java").write_text(HARNESS, encoding="utf-8")
    files = [str(p) for p in (d / "src").rglob("*.java")]
    (d / "files.txt").write_text("\n".join(f'"{f}"'.replace("\\", "/") for f in files), encoding="utf-8")
    r = subprocess.run(["javac", "-encoding", "UTF-8", "-nowarn", "-d", str(d / "out"), "@files.txt"],
                       cwd=d, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("javac failed:\n" + r.stdout[-4000:] + r.stderr[-4000:])
    (d / "pkgs.txt").write_text("\n".join(pkgs), encoding="utf-8")
    subprocess.run(["java", "-cp", str(d / "out"), "Harness", str(d / "pkgs.txt"), str(d / "result.txt")],
                   check=True, timeout=600)
    raw = (d / "result.txt").read_text(encoding="utf-8")
    by_pkg = {}
    for part in raw.split("\u0001")[1:]:
        pkg, out = part.split("\u0002", 1)
        by_pkg[pkg] = out.replace("\r\n", "\n")
    return {h: by_pkg["p" + h[:20]] for h in batch}


def run_all(programs: list[tuple[str, str]]) -> list[str]:
    """programs: [(lang, src)] -> stdout list in the same order."""
    cache = _load_cache()
    keys = [_key(lang, src) for lang, src in programs]
    todo: dict[str, dict[str, str]] = {"c": {}, "java": {}, "python": {}}
    for (lang, src), k in zip(programs, keys):
        if k not in cache:
            todo[lang][k] = src
    if todo["java"]:
        cache.update(_run_java(todo["java"]))
    jobs = [(_run_c_one, k, s) for k, s in todo["c"].items()] + [(_run_py_one, k, s) for k, s in todo["python"].items()]
    if jobs:
        with cf.ThreadPoolExecutor(max_workers=max(4, (os.cpu_count() or 4))) as ex:
            for k, out in ex.map(lambda j: j[0](j[1], j[2]), jobs):
                cache[k] = out
    _save_cache(cache)
    return [cache[k] for k in keys]


if __name__ == "__main__":
    print(run_all([
        ("c", '#include <stdio.h>\nint main(void){int a[]={1,2,3};int *p=a;printf("%d\\n",*(p+2));return 0;}\n'),
        ("java", 'public class Main{public static void main(String[] a){System.out.println(1+2+"x"+1+2);}}\n'),
        ("python", 'print([1,2,3][::-1])\n'),
    ]))
