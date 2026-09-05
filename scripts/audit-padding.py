#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查「凑数义项」：薄词条为了凑满义项数，末尾那条写成
「这个词很旧 / 美国人怎么拼 / 它能长多大」这类元评论，
再挂一个跟词头无关的等式 —— 等于拿另一个词去顶数。
check-wordlist 只数数目，audit-depth 只看讲解行比例，两个都拦不住。
判据：三义项词条里，最后一个义项的第一条等式，左边不含词头前五个字母。
用法：python3 scripts/audit-padding.py [字母段]
"""
import sys, io, re, glob, importlib.util as u
spec = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(spec); spec.loader.exec_module(cw)
NUMS = set(cw.NUMS)

def main(argv):
    seg = argv[0].lower() if argv else None
    ent = []
    for p in [f for f in sorted(glob.glob('wordlists/B-*.txt')) if 'merged' not in f]:
        for blk in io.open(p, encoding='utf-8').read().split('\n\n'):
            L = [l for l in blk.strip().split('\n') if l.strip()]
            if L: ent.append((L[0], L))
    n3 = 0; fake = []; lazy = []
    for h, L in ent:
        if seg and not h.lower().startswith(seg): continue
        nums = [k for k, l in enumerate(L) if l[0] in NUMS]
        if len(nums) != 3: continue
        n3 += 1
        stem = re.sub(r'[^a-z]', '', h.lower())[:5]
        eqs = [l for l in L[nums[-1]:] if cw.EQ.match(l)]
        if not (eqs and stem): continue
        if stem in re.sub(r'[^a-z]', '', eqs[0].split('=')[0].lower()): continue
        # 例句里有没有词头，决定这是「假义项」还是「等式挂歪」
        inex = stem in re.sub(r'[^a-z]', '', L[nums[-1]].lower())
        (lazy if inex else fake).append((h, L[nums[-1]].strip(), eqs[0].strip()))
    label = (seg + '- 段') if seg else '全表'
    print('\n%s：三义项词条 %d 条' % (label, n3))
    print('  【假义项】末义项整条跟词头无关，纯粹为凑数：%d 条 (%.0f%%)'
          % (len(fake), 100.0 * len(fake) / max(n3, 1)))
    for h, ex, eq in fake[:40]:
        print('      %-18s %s   ← %s' % (h, ex[:40], eq[:30]))
    print('  【等式挂歪】例句是真义项，但等式教的是另一个词：%d 条 (%.0f%%)'
          % (len(lazy), 100.0 * len(lazy) / max(n3, 1)))
    for h, ex, eq in lazy[:12]:
        print('      %-18s %s   ← %s' % (h, ex[:40], eq[:30]))
    return 1 if fake else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
