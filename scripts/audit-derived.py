#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十一道闸门：查「本该并进形容词、却单立着」的派生词条。

用户 2026-09-10 定的规则：
  · 形容词的 -ly 副词并进该形容词的词条，**除非副词另有形容词没有的义项**；
  · 形容词的比较级与最高级同样并进去，**除非另有别义**。
例外一律写进 reference/derived-keep.txt，一行一个加理由 —— 跟
proper-nouns-keep.txt、exclude.txt 一个办法：例外要留痕，不能靠记性。

判据：词条头是 -ly 副词（或 -er/-est 比较级），按构词规则推出的形容词
也在表里，且这条词条本身看得出是副词条（核心里有「副词」「地」，
或有「构词：X 加 -ly」那一行）。

用法：python3 scripts/audit-derived.py [字母段]
退出码：有未并、又没登记进 derived-keep 的候选就是 1。
"""
import sys, io, glob, os
sys.path.insert(0, 'scripts')
from wordkey import numsort

IRREG_ADV = {'truly':'true', 'duly':'due', 'wholly':'whole', 'publicly':'public',
             'idly':'idle', 'ably':'able', 'nobly':'noble', 'subtly':'subtle'}
IRREG_CMP = {'better':'good', 'best':'good', 'worse':'bad', 'worst':'bad',
             'elder':'old', 'eldest':'old', 'farther':'far', 'farthest':'far',
             'further':'far', 'furthest':'far', 'less':'little', 'least':'little',
             'more':'much', 'most':'much'}

def adv_bases(w):
    """-ly 副词 → 可能的形容词词干"""
    w = w.lower()
    if w in IRREG_ADV: return [IRREG_ADV[w]]
    if not w.endswith('ly') or len(w) < 5: return []
    stem = w[:-2]
    out = [stem, stem + 'e']
    if stem.endswith('i'): out.append(stem[:-1] + 'y')       # angrily → angry
    if stem.endswith('al') is False: pass
    out.append(stem + 'le')                                   # simply → simple
    if w.endswith('lly'): out.append(w[:-1])                  # fully → full
    if w.endswith('ically'): out.append(w[:-6] + 'ic')        # basically → basic
    return out

def cmp_bases(w):
    w = w.lower()
    if w in IRREG_CMP: return [IRREG_CMP[w]]
    for suf in ('est', 'er'):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            stem = w[:-len(suf)]
            out = [stem, stem + 'e']
            if stem.endswith('i'): out.append(stem[:-1] + 'y')   # happiest → happy
            if len(stem) > 2 and stem[-1] == stem[-2]: out.append(stem[:-1])  # bigger → big
            return out
    return []

def load_keep():
    p = 'reference/derived-keep.txt'
    if not os.path.exists(p): return {}
    keep = {}
    for line in io.open(p, encoding='utf-8'):
        line = line.split('#')[0].strip()
        if line: keep[line.lower()] = True
    return keep

def entries():
    for f in numsort(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            b = b.strip()
            if b: yield f, b.split('\n')[0].strip(), b

def main(argv):
    seg = argv[0].lower() if argv else None
    rows = list(entries())
    heads = {h.lower(): b for _, h, b in rows}
    keep = load_keep()
    adv_hits, cmp_hits = [], []
    for f, h, body in rows:
        low = h.lower()
        if seg and not low.startswith(seg): continue
        if low in keep: continue
        # 只认真的副词条：核心里说了副词或「地」，或者有 -ly 构词行
        core = '\n'.join(l for l in body.split('\n')[1:] if not l[:1].isdigit())
        looks_adv = ('副词' in body or '加 -ly' in body or '地：' in body or '地、' in body)
        cands = [b for b in adv_bases(low) if b in heads and b != low]
        if cands and looks_adv:
            b = max(cands, key=len)          # amply → ample，不是 amp
            adv_hits.append((h, heads[b].split('\n')[0].strip(), f))
        cands = [b for b in cmp_bases(low) if b in heads and b != low]
        if cands and ('比较级' in body or '最高级' in body):
            b = max(cands, key=len)
            cmp_hits.append((h, heads[b].split('\n')[0].strip(), f))
    print('【副词该并进形容词】%d 条' % len(adv_hits))
    for h, b, f in adv_hits[:400]:
        print('    %-22s → %s' % (h, b))
    print('\n【比较级／最高级该并进形容词】%d 条' % len(cmp_hits))
    for h, b, f in cmp_hits[:200]:
        print('    %-22s → %s' % (h, b))
    n = len(adv_hits) + len(cmp_hits)
    print('\n合计 %d 条待并。例外写进 reference/derived-keep.txt（一行一个加理由）。' % n)
    return 1 if n else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
