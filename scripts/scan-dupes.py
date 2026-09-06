#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判重的第 2、3、4 条通道 —— 报告，不是闸门。

背景：2026-09-06 定下四条扫描通道，第 1 条（等式左边相同 + 中文字集相似）
已经并进 audit-padding.py 当闸门跑；2、3、4 当时是临时脚本，用完就丢了，
GOAL.txt 里只留了一句「三级开工时值得重跑一遍」。这次三级开工，
把它们写成常驻脚本 —— **没有尺子的维度会悄悄退化，丢掉的尺子等于没有尺子**。

  通道 2：两条义项都没有等式行 → 只比中文译文
  通道 3：不限有无等式，中文译文字集相似 ≥ 0.7
          （抓 swear / pledge allegiance 这类换了个说法的同一件事）
  通道 4：例句剥掉虚词与代词后，实词骨架 Jaccard ≥ 0.8
          （抓只换了代词或介词的重复）

通道 2 是通道 3 的子集，分开报是因为「两条都没等式」时人判起来最省事：
没有等式意味着没有可搬的字面，删掉那条就完事。

**这是给人看的候选名单，不是判决。** 判重的裁定在 GOAL.txt 里：
重复义项只保留一个、不要遗漏义项、也不要硬凑义项；合并时**把被删那条
身上不重复的等式行搬到留下的那条**（coverage 认的是等式里的字面串），
但等式教的如果是别处已有的独立词条就不该搬。撞见的最常见情况**不是重复，
是等式没写出区别** —— 那种要改等式，不要删义项。

用法：
  python3 scripts/scan-dupes.py            全表
  python3 scripts/scan-dupes.py b          只扫 b- 段
  python3 scripts/scan-dupes.py banana bay 只扫这几条（词头多于一个字母时按词头认）
  加 --loose 把阈值放到 0.5 / 0.6

**回填时该用 --loose。** 2026-09-06 全表按 0.7 跑过一遍只剩 4 对，
真正成批的都落在 0.5–0.7 那一带：aground 的 ran / went、abstraction 的两条、
backmost 的 row / rank、air conditioning 与 air conditioner。
0.7 是「几乎肯定重复」的线，0.5 是「值得看一眼」的线 —— 回填一条词条时
本来就要把七个义项从头读一遍，顺手判掉最省事。

退出码恒为 0：它报的是候选，不是错误。
"""
import sys, re, io, itertools, importlib.util as u

_s = u.spec_from_file_location('ap', 'scripts/audit-padding.py')
ap = u.module_from_spec(_s); _s.loader.exec_module(ap)

# 剥掉虚词与代词之后剩下的才算「实词骨架」。这张表比 coverage 的
# FUNCTION_WORDS 长：那张表是用来找多词条目的宿主的，代词和情态动词
# 留着无妨；这里要的是「只换了代词或介词还算不算同一句」，
# 所以人称代词、物主代词、助动词、系动词全部剥掉。
STOP = set('''a an the of in on at by to for with from into onto over under up down
out off through across along around against between among during after before
and or but not no nor so as than that this these those there here
be is are was were been being am get got
i you he she it we they me him her us them my your his its our their mine yours
myself yourself himself herself itself ourselves themselves
do does did done have has had will would shall should can could may might must
one ones some any all very just too much many more most
who whom whose which what when where why how
'''.split())

def skeleton(ex):
    """例句 → 实词骨架词集。ap.fold 会抹掉重音、数字与标点。"""
    return set(w for w in ap.fold(ex[1:]).split() if w not in STOP and len(w) > 1)

def zh(body):
    """义项的中文译文行（紧跟例句那一行，以 = 开头）。"""
    for l in body:
        if l.startswith('= '): return l[2:].strip()
    return ''

def zhset(t):
    """中文按字比，剥掉标点。英文字母连成串算一个单位，别拆成字母。"""
    t = re.sub(r'[，。、；：！？“”「」（）,.;:!?"\'()\s　]', '', t)
    return set(re.findall(r'[A-Za-z]+|.', t))

def sim(a, b):
    A, B = zhset(a), zhset(b)
    if not A or not B: return 0.0
    return len(A & B) / len(A | B)

def has_eq(body):
    import importlib.util as _u
    return any(ap.cw.EQ.match(l) and '=' in l and not l.startswith('= ')
               for l in body)

def main(argv):
    loose = '--loose' in argv
    argv = [a for a in argv if a != '--loose']
    T_ZH, T_SK = (0.5, 0.6) if loose else (0.7, 0.8)
    seg = None; heads = None
    if len(argv) == 1 and len(argv[0]) == 1:
        seg = argv[0].lower()
    elif argv:
        heads = set(a.lower() for a in argv)

    ch2 = []; ch3 = []; ch4 = []
    for h, L in ap.entries():
        if seg and not h.lower().startswith(seg): continue
        if heads and h.lower() not in heads: continue
        ss = [(e.strip(), b) for e, b in ap.senses(L)]
        for (e1, b1), (e2, b2) in itertools.combinations(ss, 2):
            t1, t2 = zh(b1), zh(b2)
            s = sim(t1, t2)
            if s >= T_ZH:
                (ch2 if not (has_eq(b1) or has_eq(b2)) else ch3).append(
                    (h, s, e1, t1, e2, t2))
            k1, k2 = skeleton(e1), skeleton(e2)
            if len(k1) >= 3 and len(k2) >= 3:
                j = len(k1 & k2) / len(k1 | k2)
                if j >= T_SK: ch4.append((h, j, e1, t1, e2, t2))

    def show(title, rows, note):
        print('\n【%s】%d 对   %s' % (title, len(rows), note))
        for h, s, e1, t1, e2, t2 in sorted(rows, key=lambda r: -r[1]):
            print('  %-18s %.2f' % (h, s))
            print('      %-52s %s' % (e1[:52], t1[:24]))
            print('      %-52s %s' % (e2[:52], t2[:24]))

    where = ('%s- 段' % seg) if seg else ('指定 %d 条词头' % len(heads)) if heads else '全表'
    print('判重扫描：%s' % where)
    show('通道2 两条都没有等式，译文相似 ≥%.1f' % T_ZH, ch2, '没有等式可搬，判定重复就直接删')
    show('通道3 译文相似 ≥%.1f（至少一条有等式）' % T_ZH, ch3, '删之前先把不重复的等式搬过去')
    show('通道4 实词骨架 Jaccard ≥%.1f' % T_SK, ch4, '多半是只换了代词或介词')
    print('\n合计候选 %d 对。**这是候选，不是判决** —— '
          '最常见的情况是等式没写出区别，那就改等式，别删义项。'
          % (len(ch2) + len(ch3) + len(ch4)))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
