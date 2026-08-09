# -*- coding: utf-8 -*-
"""Diagnostico v2: schema data.js (objeto unico) + stats247 urls/secciones."""
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
root = r'D:\Proyectos de Software\Varios\Proyecto Baloto'

dj = open(root + r'\baloto-oracle\src\js\data.js', encoding='utf-8', errors='replace').read()
print('[data.js size]', len(dj))
print('[head 600]')
print(dj[:600])
print()

bal = re.search(r'baloto:\s*\[(.*?)\n\s*\],', dj, re.S)
rev = re.search(r'revancha:\s*\[(.*?)\n\s*\],', dj, re.S)
meta = re.search(r'metadata:\s*(\{.*?\n\s*\})', dj, re.S)
print('[baloto head 400]')
print(bal.group(1)[:400] if bal else 'NOT FOUND')
print('\n[baloto tail 400]')
print(bal.group(1)[-400:] if bal else '-')
print('\n[revancha head 300]')
print(rev.group(1)[:300] if rev else 'NOT FOUND')
print('\n[metadata shape]')
print(meta.group(1)[:800] if meta else 'NOT FOUND')
print('\n[counts] baloto {%s}, revancha {%s}' % (
    (bal.group(1).count('{') if bal else '?'),
    (rev.group(1).count('{') if rev else '?')))

st = open(root + r'\.firecrawl\baloto-stats247.md', encoding='utf-8', errors='replace').read()
print('\n[stats247 size]', len(st))
heads = [l for l in st.split('\n') if re.match(r'^#{1,4}\s', l)]
print('[stats247 section headers]')
for h in heads[:30]:
    print('   ' + h.strip()[:100])
urls = set(re.findall(r'https?://[^\s)"\'\]<>]+', st))
print('[stats247 all unique urls: %d]' % len(urls))
for u in sorted(urls)[:30]:
    print('   ' + u[:140])
nm = re.search(r'Next Draw[^\n]*', st, re.I)
print('[Next Draw line]', nm.group(0).strip()[:120] if nm else 'none')