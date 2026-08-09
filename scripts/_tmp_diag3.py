# -*- coding: utf-8 -*-
"""Diagnostico v3: data.js clave-por-clave."""
import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
root = r'D:\Proyectos de Software\Varios\Proyecto Baloto'
dj = open(root + r'\baloto-oracle\src\js\data.js', encoding='utf-8', errors='replace').read()

bal = re.search(r'BAL_DATA\.baloto\s*=\s*\[(.*?)\n\s*\];', dj, re.S)
rev = re.search(r'BAL_DATA\.revancha\s*=\s*\[(.*?)\n\s*\];', dj, re.S)
meta = re.search(r'BAL_DATA\.metadata\s*=\s*(\{.*?\n\s*\})', dj, re.S)
ar = re.search(r'BAL_DATA\.analysis_results\s*=\s*(\{.*?\n\s*\})', dj, re.S)

print('[baloto head 500]')
print(bal.group(1)[:500] if bal else 'NOT FOUND')
print('\n[baloto tail 500]')
print(bal.group(1)[-500:] if bal else '-')
n_bal = bal.group(1).count('{') if bal else -1
print('\n[baloto count {]', n_bal)
print('\n[last draw_id sample]')
ids = re.findall(r'"draw_id":(\d+)', bal.group(1) if bal else '')
print('first id:', ids[0] if ids else '-', '| last id:', ids[-1] if ids else '-')

print('\n[revancha head 400]')
print(rev.group(1)[:400] if rev else 'NOT FOUND')
print('\n[revancha tail 300]')
print(rev.group(1)[-300:] if rev else '-')
n_rev = rev.group(1).count('{') if rev else -1
print('\n[revancha count {]', n_rev)

print('\n[metadata full (up to 1500)]')
print(meta.group(1)[:1500] if meta else 'NOT FOUND')
print('\n[analysis_results head 500]')
print(ar.group(1)[:500] if ar else 'NOT FOUND')