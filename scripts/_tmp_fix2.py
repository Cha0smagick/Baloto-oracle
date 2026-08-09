# -*- coding: utf-8 -*-
"""Fix v2: reverse cp1252->UTF-8 byte-preserving (maneja bytes undefined 0x81/0x8D/0x8F/0x90/0x9D)
para recuperar emojis/variation selectors (⚠️, U+FE0F) y 4-byte emojis. Re-lee backup original."""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"D:\Proyectos de Software\Varios\Proyecto Baloto\baloto-oracle"
HTML = os.path.join(BASE, "index.html")
BACKUP = os.path.join(BASE, "index.html.bak_mojibake")

with open(BACKUP, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8", errors="replace")

# mapeo inverso cp1252: char -> byte
CP1252 = {
    '\u20ac':0x80,'\u201a':0x82,'\u0192':0x83,'\u201e':0x84,'\u2026':0x85,'\u2020':0x86,
    '\u2021':0x87,'\u02c6':0x88,'\u2030':0x89,'\u0160':0x8a,'\u2039':0x8b,'\u0152':0x8c,
    '\u017d':0x8e,'\u2018':0x91,'\u2019':0x92,'\u201c':0x93,'\u201d':0x94,'\u2022':0x95,
    '\u2013':0x96,'\u2014':0x97,'\u02dc':0x98,'\u2122':0x99,'\u0161':0x9a,'\u203a':0x9b,
    '\u0153':0x9c,'\u017e':0x9e,'\u0178':0x9f,
}
def byte_of(ch):
    o = ord(ch)
    if ch in CP1252:
        return CP1252[ch]
    if 0xA0 <= o <= 0xFF:
        return o
    if 0x80 <= o <= 0x9F:
        return o  # C1 controles: conserva byte undefined original (0x81,0x8D,0x8F,0x90,0x9D)
    return None

out = bytearray()
genuine = []
for ch in text:
    b = byte_of(ch)
    if b is not None:
        out.append(b)
    else:
        genuine.append(ch)
        out.extend(ch.encode("utf-8"))  # empotrar unicode genuino en el stream

fixed = out.decode("utf-8", errors="replace")
print("unicode genuino conservado:", sorted({hex(ord(c)) for c in genuine})[:20])

with open(HTML, "wb") as f:
    f.write(fixed.encode("utf-8"))

# ===== Verificacion =====
with open(HTML, "rb") as f:
    new_text = f.read().decode("utf-8", errors="replace")

import re
moji_pat = re.compile(r'[\u00c2-\u00c3][\u0080-\u00bf]|Ã.|ðŸ|â€|âš|â€œ|â€\u009c')
lines = new_text.split("\n")
bad = [(i+1, ln.strip()[:90]) for i, ln in enumerate(lines) if moji_pat.search(ln)]
print(f"\n== VERIFICACION POST-FIX v2 ==\nlineas con mojibake: {len(bad)}")
for n, c in bad[:10]:
    print(f"  L{n}: {c!r}")

for probe in ["Análisis", "aplicación", "Últimos 50", "⚠️", "🔎", "🔮", "—", "…", "¡", "á", "ñ", "Actualización"]:
    print(f"  contiene {probe!r}: {probe in new_text}")

print("\nchars >0xFF restantes:", [(c, hex(ord(c))) for c in sorted({c for c in new_text if ord(c) > 0xFF})][:15])
print("replacement U+FFFD:", new_text.count("\ufffd"))
print("\nL372:", [l for l in lines if "Aviso importante" in l][:1])
print("L513:", [l for l in lines if "error-panel-icon" in l][:1])
print("L26 (favicon):", [l for l in lines if "favicon" in l.lower() or "icon" in l.lower()][:2])