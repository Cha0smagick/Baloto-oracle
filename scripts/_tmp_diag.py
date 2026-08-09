# -*- coding: utf-8 -*-
"""Diagnostico puntual: schema data.js + ref main.js + stats247."""
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
root = r'D:\Proyectos de Software\Varios\Proyecto Baloto'

mj = open(root + r'\baloto-oracle\src\js\main.js', encoding='utf-8', errors='replace').read()
lines = mj.split('\n')
print('[main.js lines 160-185]')
print('\n'.join(lines[159:185]))
print()

dj = open(root + r'\baloto-oracle\src\js\data.js', encoding='utf-8', errors='replace').read()
print('[data.js size]', len(dj))

metaM = re.search(r'BAL_DATA\.metadata\s*=\s*(\{.*?\n\s*\});', dj, re.S)
print('\n[metadata JSON]')
print(metaM.group(1)[:900] if metaM else 'NOT FOUND')

revM = re.search(r'BAL_DATA\.revancha\s*=\s*(\[.*?\n\s*\]);', dj, re.S)
print('\n[revancha array head]')
print(revM.group(1)[:500] if revM else 'NOT FOUND')

balM = re.search(r'BAL_DATA\.baloto\s*=\s*(\[.*?\},\{', dj, re.S)
print('\n[baloto first 2 entries]')
print(balM.group(1)[:600] if balM else 'NOT FOUND')

bc = re.search(r'BAL_DATA\.baloto\s*=\s*\[(.*?)\];', dj, re.S)
rc = re.search(r'BAL_DATA\.revancha\s*=\s*\[(.*?)\];', dj, re.S)
print('\n[counts] baloto: %d entries, revancha: %d entries' % (
    (bc.group(1).count('{') if bc else -1),
    (rc.group(1).count('{') if rc else -1)))

st = open(root + r'\.firecrawl\baloto-stats247.md', encoding='utf-8', errors='replace').read()
sl = st.split('\n')
tbl = [i+1 for i, l in enumerate(sl) if l.strip().startswith('|') and not re.match(r'^\|\s*-', l.strip())]
print('\n[stats247] table lines total: %d; first 5 at: %s' % (len(tbl), ','.join(map(str, tbl[:5]))))

arch = []
for u in re.findall(r'https?://[^\s)"\'\]<>]+', st):
    if re.search(r'colombia-baloto|page|history|archive|results|year', u, re.I) and not re.search(r'\.png|\.svg', u):
        arch.append(u)
seen = set(); uniq = []
for u in arch:
    if u not in seen:
        seen.add(u); uniq.append(u)
print('\n[stats247 archive-ish urls]')
for u in uniq[:10]:
    print('   ' + u[:130])