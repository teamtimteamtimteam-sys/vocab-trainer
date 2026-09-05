#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第九道闸门：量例句的承载力。

用户 2026-09-05 指出：跟牛津高阶比，这份词表的例句太简单 ——
牛津的例句大多能顺带教出词条之外的搭配与用词，这里的不能。
实测坐实：全表 23772 条例句平均 5.5 个词，八成在 6 个词以内，
每句平均只有 3.4 个实词种类（约等于「词头 + 两个词」），
超过 9 个词的只有 1.6%。

**为什么会这样 —— 是闸门的反向激励。** 前八道闸门量的全是
「每个义项配了多少等式、多少讲解行」。例句越短，同样篇幅里塞得下
的义项越多，密度指标反而越好看。check-wordlist 对 B 又明确不量字符数。
于是例句长度这一维从来没有尺子，越写越短。

判据（用户裁定的目标）：例句除了演示这个词，还要**顺带带出别的东西** ——
一个搭配、一处语域信号、一个真实场景。量化成两条：
  · 批均词数 ≥ 9
  · 批均「词头之外的实词种类」≥ 4
用法：
  python3 scripts/audit-examples.py                 全表报告，不拦
  python3 scripts/audit-examples.py agreement brim  查指定词条，不达标就退出码 1
  python3 scripts/audit-examples.py --todo [N]      列出下一批该回填的 N 条词条

全表回填（用户 2026-09-05 裁定）按「学的人回来看的频率」排序：
一级义项 ≥8 的大词、二级 A 表也收的高频词、三级其余。
待办清单不另存文件 —— 直接从词表现算，改完一条它自己就从清单里消失，
进度记录本身不会漂。
"""
import sys, io, re, glob, importlib.util as u, statistics as st
spec = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(spec); spec.loader.exec_module(cw)

MIN_WORDS, MIN_CONTENT = 9.0, 4.0
FUNC = set('''a an the of in on to and or for at by it is are was were be been being am
i you he she we they this that these those with as from not no do does did done
my your his her its our their there here have has had will would shall should can could
me him them us if but so than then when what which who whom how all any some
into out up down over under about after before at not n't 's'''.split())

def toks(s): return re.findall(r"[A-Za-z][A-Za-z']*", s)

def stats(entry):
    """返回 (例句数, 平均词数, 平均「词头之外的实词种类」)"""
    head = set(t.lower() for t in toks(entry['word']))
    ws, cs = [], []
    for s in entry['senses']:
        t = toks(s['ex'])
        ws.append(len(t))
        # 词头本身与它的变形都不算 —— 只数「顺带学到的别的词」
        extra = {x.lower() for x in t
                 if x.lower() not in FUNC and not any(x.lower().startswith(h[:4]) or
                                                      h.startswith(x.lower()[:4]) for h in head if len(h) >= 3)}
        cs.append(len(extra))
    if not ws: return 0, 0, 0
    return len(ws), sum(ws) / len(ws), sum(cs) / len(cs)

def todo(rows, n):
    """列出下一批该回填的词条，按一级、二级、三级排。"""
    A = set()
    for f in glob.glob('wordlists/A-*.txt'):
        for e in cw.parse(f): A.add(e['word'].lower())
    bad = []
    for e in rows:
        cnt, w, c = stats(e)
        if cnt and (w < MIN_WORDS or c < MIN_CONTENT):
            tier = 1 if len(e['senses']) >= 8 else (2 if e['word'].lower() in A else 3)
            bad.append((tier, -len(e['senses']), e['word'], cnt, w, c))
    bad.sort(key=lambda x: (x[0], x[1], x[2].lower()))
    left = {1: 0, 2: 0, 3: 0}
    for b in bad: left[b[0]] += 1
    print('待回填：一级 %d、二级 %d、三级 %d，合计 %d 条词条'
          % (left[1], left[2], left[3], len(bad)))
    print('下一批 %d 条：' % min(n, len(bad)))
    print(' '.join(b[2] for b in bad[:n]))
    print()
    for t, _, w, cnt, ww, cc in bad[:n]:
        print('  %d级 %-20s %2d 条例句  均 %.1f 词 / %.1f 额外实词' % (t, w, cnt, ww, cc))
    return 0

def main(argv):
    rows = []
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')): rows += cw.parse(f)
    if argv and argv[0] == '--todo':
        return todo(rows, int(argv[1]) if len(argv) > 1 else 10)
    if argv:
        want = {w.lower() for w in argv}
        sel = [e for e in rows if e['word'].lower() in want]
        miss = want - {e['word'].lower() for e in sel}
        if miss: print('找不到词条：' + ' '.join(sorted(miss)))
        bad = []
        print('%-22s %6s %8s %10s' % ('词条', '例句', '均词数', '额外实词'))
        for e in sorted(sel, key=lambda x: x['word'].lower()):
            n, w, c = stats(e)
            flag = '' if (w >= MIN_WORDS and c >= MIN_CONTENT) else '  ← 偏薄'
            if flag: bad.append(e['word'])
            print('%-22s %6d %8.1f %10.1f%s' % (e['word'], n, w, c, flag))
        print('\n下限：批均词数 ≥ %.0f、批均额外实词 ≥ %.0f' % (MIN_WORDS, MIN_CONTENT))
        if bad:
            print('❌ %d 条例句偏薄，要把它们写成能顺带教出别的搭配的句子：%s'
                  % (len(bad), ' '.join(bad)))
            return 1
        print('✅ 都达标')
        return 0
    # 无参数：全表报告
    seg = {}
    for e in rows:
        L = e['word'][:1].lower()
        if not L.isalpha(): continue
        n, w, c = stats(e)
        if n: seg.setdefault(L, []).append((n, w, c))
    print('\n全表例句承载力（下限：均词数 %.0f、额外实词 %.0f）' % (MIN_WORDS, MIN_CONTENT))
    print('%-4s %8s %10s %12s %10s' % ('段', '词条', '均词数', '额外实词', '达标率'))
    allw = []
    for L in sorted(seg):
        v = seg[L]
        w = sum(x[0] * x[1] for x in v) / sum(x[0] for x in v)
        c = sum(x[0] * x[2] for x in v) / sum(x[0] for x in v)
        ok = sum(1 for x in v if x[1] >= MIN_WORDS and x[2] >= MIN_CONTENT)
        allw += v
        print('%-4s %8d %10.1f %12.1f %9.0f%%' % (L, len(v), w, c, 100 * ok / len(v)))
    w = sum(x[0] * x[1] for x in allw) / sum(x[0] for x in allw)
    c = sum(x[0] * x[2] for x in allw) / sum(x[0] for x in allw)
    ok = sum(1 for x in allw if x[1] >= MIN_WORDS and x[2] >= MIN_CONTENT)
    print('-' * 48)
    print('%-4s %8d %10.1f %12.1f %9.0f%%' % ('合计', len(allw), w, c, 100 * ok / len(allw)))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
