# -*- coding: utf-8 -*-
"""Diag v5: sintaxis JS (node --check) + prevalencia mojibake doble-codificado."""
import io, os, re, subprocess, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"D:\Proyectos de Software\Varios\Proyecto Baloto\baloto-oracle"
FILES = ["index.html", "src/js/main.js", "src/js/data.js", "src/css/main.css"]

def check_node():
    for exe in ("node",):
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
            return exe, r.stdout.strip()
        except Exception as e:
            print(f"  node check fail: {e}")
    return None, None

def js_check(path, is_module=False):
    if not os.path.exists(path):
        return "MISSING"
    tmp = path + ".mjs" if is_module else path
    src = path
    if is_module:
        shutil_copy(path, tmp)
    try:
        r = subprocess.run(["node", "--check", src if not is_module else tmp],
                           capture_output=True, text=True, timeout=60)
        return f"exit={r.returncode} {r.stderr.strip()[:400]}"
    finally:
        if is_module and os.path.exists(tmp):
            os.remove(tmp)

def shutil_copy(s, d):
    with open(s, "rb") as f: data = f.read()
    with open(d, "wb") as f: f.write(data)

MOJI = re.compile(r'[\u00c2-\u00c3][\u0080-\u00bf]|â€|â™|âš|ðŸ|Ã¡|Ã©|Ã­|Ã³|Ãº|Ã±|Ã¼')

def scan(path):
    if not os.path.exists(path): return None
    with open(path, "rb") as f: raw = f.read()
    text = raw.decode("utf-8", errors="replace")
    total = len(text)
    # chars that would FAIL latin-1 encode => genuine unicode (>0xFF) presence
    try:
        text.encode("latin-1")
        latin1_ok = True
    except UnicodeEncodeError as e:
        latin1_ok = False
        first = e.start
    lines = text.split("\n")
    moji_hits = sum(1 for ln in lines if MOJI.search(ln))
    # sample mojibake lines
    samples = [ln.strip()[:90] for ln in lines if MOJI.search(ln)][:5]
    return dict(total=total, latin1_ok=latin1_ok, moji_lines=moji_hits,
                n_lines=len(lines), samples=samples)

exe, ver = check_node()
print(f"NODE: {exe} {ver}")
for f in FILES:
    p = os.path.join(BASE, f)
    print(f"\n=== {f} ===")
    st = scan(p)
    if st:
        print(f"  bytes~{st['total']} chars, lines={st['n_lines']}, latin1_encodable={st['latin1_ok']}, mojibake_lines={st['moji_lines']}")
        for s in st["samples"]: print(f"    MOJI: {s!r}")
    is_mod = f.endswith("main.js")
    print(f"  node --check -> {js_check(p, is_module=is_mod)}")