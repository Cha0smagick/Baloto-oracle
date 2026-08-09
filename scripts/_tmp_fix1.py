# -*- coding: utf-8 -*-
"""Fix v1: de-mojibake index.html (doble codificacion cp1252 -> UTF-8) + backup."""
import io, os, re, shutil, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"D:\Proyectos de Software\Varios\Proyecto Baloto\baloto-oracle"
HTML = os.path.join(BASE, "index.html")
BACKUP = os.path.join(BASE, "index.html.bak_mojibake")

with open(HTML, "rb") as f:
    raw = f.read()
text = raw.decode("utf-8", errors="replace")  # incluye BOM \ufeff si existe

def fix(text):
    """Invierte cp1252->utf8: acumula bytes cp1252 de chars mapables; chars genuinos se conservan."""
    out = []
    buf = bytearray()
    def flush():
        nonlocal buf
        if buf:
            out.append(buf.decode("utf-8", errors="replace"))
            buf = bytearray()
    unmapped = []
    for ch in text:
        try:
            b = ch.encode("cp1252")  # siempre 1 byte para cp1252
            buf += b
        except UnicodeEncodeError:
            flush()
            out.append(ch)
            unmapped.append(hex(ord(ch)))
    flush()
    return "".join(out), unmapped

fixed, unmapped = fix(text)
print("chars no-cp1252 conservados como unicode genuino:", sorted(set(unmapped))[:20])

# backup solo si aún no existe
if not os.path.exists(BACKUP):
    with open(BACKUP, "wb") as f:
        f.write(raw)
    print("backup creado: index.html.bak_mojibake")
else:
    print("backup ya existia, omitido")

with open(HTML, "wb") as f:
    f.write(fixed.encode("utf-8"))  # conserva BOM si venia en text

# ===== Verificacion =====
with open(HTML, "rb") as f:
    new_raw = f.read()
new_text = new_raw.decode("utf-8", errors="replace")
lines = new_text.split("\n")

moji_pat = re.compile(r'[\u00c2-\u00c3][\u0080-\u00bf]|Ã.|Â©|ðŸ|â€|âš|â€œ|â€\u009c')
bad_lines = [(i + 1, ln.strip()[:90]) for i, ln in enumerate(lines) if moji_pat.search(ln)]
print(f"\n== VERIFICACION POST-FIX ==")
print(f"lineas con patrones mojibake: {len(bad_lines)}")
for n, ctx in bad_lines[:10]:
    print(f"  L{n}: {ctx!r}")

# muestras clave
for probe in ["Análisis", "aplicación", "última Actualización", "Últimos 50", "⚠️", "🔎", "—", "¡", "á", "ñ"]:
    print(f"  contiene {probe!r}: {probe in new_text}")

print("\nchars >0xFF restantes (deben ser emojis/genuinos):")
high = sorted({ch for ch in new_text if ord(ch) > 0xFF})
print("  ", [(ch, hex(ord(ch))) for ch in high][:15], "total:", len(high))
print("\nBOM al inicio:", repr(new_text[:1]) == "'\ufeff'")
print("primeros 80 chars:", new_text[:80])