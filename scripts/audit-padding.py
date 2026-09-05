#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查「凑数义项」：为了凑够义项数，写出跟词条本身无关的例句和讲解 ——
「这个词很旧 / 美国人怎么拼 / 它能长多大 / 那个东西怎么用」，
再挂一个跟词头毫无关系的等式，等于拿另一个词去顶数。
用户 2026-09-05 明令：冷僻词真实义项只有一两个就写一两个，不许硬凑。

前四道闸门（check-wordlist / coverage / audit-depth / audit-swallowed）
只数数目、不读内容，一条都拦不住这个。

判据：一个义项（编号例句 + 译文 + 等式 + 讲解行）整段里，
找不到任何跟词头同源的字眼，就是跟词条无关。
为了不误伤，同源判定放宽到三条：
  · 词头任一实词的前四个字母，在义项里以子串出现（megabyte 认得 byte）
  · 多词词头只要命中最长的那个实词即可（air show、box office）
  · 编辑距离 ≤2 的形态变化也算（arise→arose、become→became）
两类分别报：
  【假义项】例句本身就跟词头无关 —— 必须改写或删掉
  【等式挂歪】例句是真义项，只是等式顺手教了别的词 —— 可容忍，不该多
用法：python3 scripts/audit-padding.py [字母段]      不给段就查全表
"""
import sys, io, re, glob, unicodedata, importlib.util as u
spec = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(spec); spec.loader.exec_module(cw)
NUMS = set(cw.NUMS)
TAIL = ('构词', '注意', '辨析')

def fold(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z ]', ' ', s.lower())

def dist(a, b):
    if abs(len(a) - len(b)) > 2: return 9
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def related(head, text):
    """义项里有没有跟词头同源的字眼"""
    hts = [t for t in fold(head).split() if len(t) >= 3]
    if not hts: return True
    flat = text.replace(' ', '')
    toks = text.split()
    for t in sorted(hts, key=len, reverse=True):
        if t[:4] in flat: return True          # 子串即可，认得复合词
        # 词尾 e / y 脱落的派生：bake→baking、ally→allies、apiary→apiarist
        cuts = [t.rstrip('e'), t.rstrip('y'), t[:-1]]
        if t.endswith(('ex', 'ix')): cuts.append(t[:-2] + 'ic')   # codex→codices
        for cut in cuts:
            if len(cut) >= 3 and any(w.startswith(cut) for w in toks): return True
    for t in hts:
        if len(t) < 4: continue
        for w in toks:
            if dist(t, w) <= 2: return True    # 认得不规则变位
            # betake→betook、forsake→forsook：前三字母相同的强变化动词
            if len(t) >= 6 and w[:3] == t[:3] and dist(t, w) <= 3: return True
            # bear→bore、speak→spoke：首尾字母相同、只换中间元音
            if (len(w) == len(t) and w[0] == t[0] and w[-1] == t[-1]
                    and sum(a != b for a, b in zip(w, t)) <= 2): return True
    return False

def entries():
    for p in [f for f in sorted(glob.glob('wordlists/B-*.txt')) if 'merged' not in f]:
        for blk in io.open(p, encoding='utf-8').read().split('\n\n'):
            L = [l for l in blk.strip().split('\n') if l.strip()]
            if L: yield L[0], L

def senses(L):
    nums = [k for k, l in enumerate(L) if l[0] in NUMS]
    for a, b in zip(nums, nums[1:] + [len(L)]):
        body = []
        for l in L[a + 1:b]:
            if any(l.startswith(t) for t in TAIL): break
            body.append(l)
        yield L[a], body

def main(argv):
    seg = argv[0].lower() if argv else None
    tot = 0; fake = []; lazy = []
    for h, L in entries():
        if seg and not h.lower().startswith(seg): continue
        for ex, body in senses(L):
            tot += 1
            eqs = [l for l in body if cw.EQ.match(l)]
            whole = fold(ex + ' ' + ' '.join(body))
            if related(h, whole): 
                # 例句沾边，再看第一条等式是不是在教别的词
                if eqs and not related(h, fold(eqs[0].split('=')[0])):
                    lazy.append((h, ex.strip(), eqs[0].strip()))
                continue
            fake.append((h, ex.strip(), eqs[0].strip() if eqs else ''))
    # 重复义项：同一词条里两条例句实质是同一句。
    # believe「I believe her / I believe in her」这种最小对立对是有意为之，
    # 必须放行 —— 判据收紧成「词集完全相同」，或者「差一个词且译出的
    # 中文也一模一样」（bell jar / bell glass 那种同义词各占一条）。
    import itertools
    dupes = []
    for h, L in entries():
        if seg and not h.lower().startswith(seg): continue
        ss = [(e.strip(), b) for e, b in senses(L)]
        for (e1, b1), (e2, b2) in itertools.combinations(ss, 2):
            w1, w2 = set(fold(e1[1:]).split()), set(fold(e2[1:]).split())
            if len(w1) < 3 or len(w2) < 3: continue
            j = len(w1 & w2) / len(w1 | w2)
            if j == 1.0:
                dupes.append((h, e1, e2)); continue
            if j >= 0.75:
                z = [ [l for l in b if l.startswith('= ')] for b in (b1, b2) ]
                if z[0] and z[1] and z[0][0] == z[1][0]:
                    dupes.append((h, e1, e2))

    label = (seg + '- 段') if seg else '全表'
    print('\n%s：义项 %d 条' % (label, tot))
    print('  【假义项】整条跟词头无关，纯粹凑数：%d 条 (%.1f%%)'
          % (len(fake), 100.0 * len(fake) / max(tot, 1)))
    for h, ex, eq in fake[:80]:
        print('      %-20s %-44s %s' % (h, ex[:44], eq[:30]))
    if len(fake) > 80: print('      ……还有 %d 条' % (len(fake) - 80))
    print('  【等式挂歪】例句是真义项，等式教了别的词：%d 条 (%.1f%%)'
          % (len(lazy), 100.0 * len(lazy) / max(tot, 1)))
    print('  【重复义项】同一词条里两条例句实质是同一句：%d 对' % len(dupes))
    for h, e1, e2 in dupes[:30]:
        print('      %-18s %s' % (h, e1[:44]))
        print('      %-18s %s' % ('', e2[:44]))
    return 1 if (fake or dupes) else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
