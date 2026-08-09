# -*- coding: utf-8 -*-
"""Diagnostico v4: segmentos por clave via busqueda de marcadores."""
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
p = r'D:\Proyectos de Software\Varios\Proyecto Baloto\baloto-oracle\src\js\data.js'
dj = open(p, encoding='utf-8', errors='replace').read()

for k in ['baloto', 'revancha', 'metadata', 'analysis_results']:
    m = re.search(r'BAL_DATA\.%s\s*=\s*' % k, dj)
    print(k, '->', ('FOUND at %d' % m.start()) if m else 'NOT FOUND')
print('total len', len(dj))

def seg(k, nxt):
    a = re.search(r'BAL_DATA\.%s\s*=\s*\[' % k, dj)
    b = re.search(r'BAL_DATA\.%s\s*=\s*' % nxt, dj)
    if not a:
        return None
    end = b.start() if b else len(dj)
    return dj[a.end():end]

bo = seg('baloto', 'revancha')
rv = seg('revancha', 'metadata')
if bo:
    ids = re.findall(r'"draw_id":(\d+)', bo)
    dates = re.findall(r'"date":"([0-9-]+)"', bo)
    print('baloto draws:', len(ids), '| first', dates[0] if dates else '-', '| last', dates[-1] if dates else '-')
    print('baloto head 130:', bo[:130])
    print('baloto tail 180:', bo[-180:])
if rv:
    ids = re.findall(r'"draw_id":(\d+)', rv)
    dates = re.findall(r'"date":"([0-9-]+)"', rv)
    print('revancha draws:', len(ids), '| first', dates[0] if dates else '-', '| last', dates[-1] if dates else '-')
    print('revancha head 150:', rv[:150])