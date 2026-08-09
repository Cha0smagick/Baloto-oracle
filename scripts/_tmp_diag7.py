# -*- coding: utf-8 -*-
"""Localizar residuos: \ufffd y 0x8f en index.html post-fix."""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"D:\Proyectos de Software\Varios\Proyecto Baloto\baloto-oracle"
HTML = os.path.join(BASE, "index.html")

with open(HTML, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8", errors="replace")
lines = text.split("\n")

print("=== lineas con U+FFFD (replacement) ===")
n = 0
for i, ln in enumerate(lines, 1):
    if "\ufffd" in ln:
        n += 1
        if n <= 8:
            print(f"  L{i}: {ln.strip()[:130]!r}")
print("total:", n)

print("\n=== lineas con char 0x8f ===")
n = 0
for i, ln in enumerate(lines, 1):
    if any(ord(c) == 0x8f for c in ln):
        n += 1
        if n <= 8:
            print(f"  L{i}: {ln.strip()[:130]!r}")
print("total:", n)