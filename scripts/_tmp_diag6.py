# -*- coding: utf-8 -*-
"""Diag v6: (1) runtime de data.js en node con shim window - ¿BAL_DATA se setea?
(2) chars >0xFF en index.html para planear de-mojibake seguro."""
import io, os, re, subprocess, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"D:\Proyectos de Software\Varios\Proyecto Baloto\baloto-oracle"
DATA = os.path.join(BASE, "src", "js", "data.js")
HTML = os.path.join(BASE, "index.html")

print("=== (1) RUNTIME data.js en node (shim window) ===")
r = subprocess.run(
    ["node", "-e",
     "global.window=global;require(%r);"
     "const b=window.BAL_DATA;"
     "console.log('keys:',Object.keys(b||{}).join(','));"
     "console.log('baloto len:',b&&b.baloto?b.baloto.length:'N/A');"
     "console.log('revancha len:',b&&b.revancha?b.revancha.length:'N/A');"
     "console.log('metadata?',!!(b&&b.metadata));"
     "console.log('analysis_results?',!!(b&&b.analysis_results));" % DATA],
    capture_output=True, text=True, timeout=120,
    encoding='utf-8', errors='replace')
print("exit:", r.returncode)
print("STDOUT:", r.stdout.strip()[:500])
print("STDERR:", r.stderr.strip()[:800])

print("\n=== (2) chars >0xFF en index.html ===")
with open(HTML, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8", errors="replace")
lines = text.split("\n")
found = 0
for i, ln in enumerate(lines, 1):
    high = [(ch, hex(ord(ch))) for ch in ln if ord(ch) > 0xFF]
    if high:
        found += 1
        if found <= 12:
            ctx = ln.strip()[:110]
            print(f"  L{i}: {high[:4]} | {ctx!r}")
print(f"  total lineas con chars >0xFF: {found}")
# conteo del rango mojibake habitual
moji = sum(1 for ln in lines if re.search(r'[\u00c2-\u00c3][\u0080-\u00bf]|Ã|Â©|ðŸ|âš|â€', ln))
print(f"  lineas con patrones mojibake: {moji}")