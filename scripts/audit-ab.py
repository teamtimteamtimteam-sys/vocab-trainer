#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查 B 词表有没有漏掉 A 词表已经教过的用法。

存在的理由：B 是牛津高阶全量表，义项要收全；但「收全了没有」
手上没有任何机器可校验的依据 —— reference 里只有词头清单，
没有义项数据。用户 2026-09-05 追问「每个词条的全部义项都涵盖到了吗」，
抽查发现 corner 漏了 turn the corner / cut corners，
cool 漏了 lose one's cool —— 而 audit-depth 对它们全部放行，
因为它只数义项个数，不看覆盖面。

能查的那一半：A 词表按词频排，高频词两张表都有。
**B 是全量表，理应是 A 的超集** —— A 里出现过的等式左边，
B 的同名词条里必须找得到。找不到就是漏了一个用法。
这查不出「OALD 有而两张表都没有」的义项，只查得出「自己跟自己打架」。

用法：python3 scripts/audit-ab.py [字母段]
"""
import sys, io, re, glob, unicodedata, importlib.util as u
spec = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(spec); spec.loader.exec_module(cw)
NUMS = set(cw.NUMS)

def fold(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def entries(pat):
    out = {}
    for p in sorted(glob.glob(pat)):
        if 'merged' in p: continue
        for blk in io.open(p, encoding='utf-8').read().split('\n\n'):
            L = [l for l in blk.strip().split('\n') if l.strip()]
            if L: out.setdefault(L[0], []).extend(L)
    return out

def lhs_set(lines):
    """取出一条词条里所有等式的英文左边"""
    out = []
    for l in lines:
        if cw.EQ.match(l) and '=' in l:
            t = fold(l.split('=', 1)[0])
            t = re.sub(r'^(a|an|the|to) ', '', t)
            if len(t) >= 2: out.append(t)
    return out

FUNC = ('it', 's', 'be', 'a', 'an', 'the', 'to', 'somebody', 'something',
        'one', 'ones', 'your', 'his', 'her', 'their', 'is', 'do', 'did')

def variants(t):
    """同一个搭配在两张表里写法未必一样：A 写 it's a piece of cake，
    B 合理地写 be a piece of cake。所以除了原字面，还要试剥掉
    首尾虚词和占位词之后的核心串。"""
    yield t
    w = t.split()
    while w and w[0] in FUNC:
        w = w[1:]
        if len(w) >= 2: yield ' '.join(w)
    w2 = [x for x in t.split() if x not in FUNC]
    if len(w2) >= 2: yield ' '.join(w2)

def present(t, body, allB):
    for v in variants(t):
        if v in body or v in allB: return True
    return False

def main(argv):
    seg = argv[0].lower() if argv else None
    A, B = entries('wordlists/A-*.txt'), entries('wordlists/B-*.txt')
    shared = sorted(set(A) & set(B))
    if seg: shared = [h for h in shared if h.lower().startswith(seg)]
    gaps = []; checked = 0
    # B 是全量词典，派生词各有自己的词条：A 的 absent 条下教了 absence，
    # 而 B 里 absence 是独立词头 —— 那不是漏，是分工。
    bheads = {fold(x) for x in B}
    # 一个搭配可能教在别的词条里 —— A 的 after 条教了 look after，
    # B 把它放在 look 条下，那不是漏。所以要全表搜，不能只搜同名词条。
    allB = fold(' '.join(l for v in B.values() for l in v))
    for h in shared:
        body = fold(' '.join(B[h]))
        stem = fold(h)[:4]
        for t in lhs_set(A[h]):
            # 只查真正属于这个词的搭配：等式左边得含词头。
            # A 里常拿同义词作注解（abandon 条下的 leave），那不是 B 的漏洞。
            if stem and stem not in t.replace(' ', ''): continue
            if t in bheads: continue          # 它自己就是 B 的词头
            checked += 1
            if not present(t, body, allB):
                gaps.append((h, t))
    label = (seg + '- 段') if seg else '全表'
    print('\n%s：A 与 B 共有的词条 %d 条，核对 A 的等式 %d 条'
          % (label, len(shared), checked))
    print('  B 里找不到的用法：%d 条' % len(gaps))
    cur = None
    for h, t in gaps[:120]:
        if h != cur: print('    %s' % h); cur = h
        print('        缺：%s' % t)
    if len(gaps) > 120: print('    ……还有 %d 条' % (len(gaps) - 120))
    return 1 if gaps else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
