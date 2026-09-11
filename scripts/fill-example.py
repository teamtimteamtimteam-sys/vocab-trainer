#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给拓展块里的等式补例句：在等式行下面插一行英文例句、一行中文翻译。

用法：
    1. 先看清单，挑一段来写：
         python3 scripts/need-example.py de di --tier1 --list
    2. 把要补的写成一个 python 文件（默认 /tmp/fill_data.py），内容是一个字典：
         F = {
           ("词头", "等式左边原样"): ("English example sentence.", "中文译文"),
           ...
         }
       键必须跟词表里的字面**完全一致**（含 a / the / 连字符），否则对不上。
    3. python3 scripts/fill-example.py [数据文件路径]

插入后的结构（parseVocab 认得）：
    flight deck = 驾驶舱
    The flight deck door stays locked from the moment the engines start.
    = 从发动机启动那一刻起，驾驶舱门就锁着。
英文行被解析成 en 笔记、中文行解析成 gloss，渲染时英文行里那条搭配会自动高亮。

已经补过的不会重复插（下一行若已是同一句就跳过）。
"""
import glob, io, sys, importlib.util
sys.path.insert(0, 'scripts')
from wordkey import numsort

def load(path):
    spec = importlib.util.spec_from_file_location('fill_data', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.F

def main(argv):
    path = argv[0] if argv else '/tmp/fill_data.py'
    F = load(path)
    hit = 0; miss = set(F)
    for f in numsort(glob.glob('wordlists/B-[0-9]*.txt')):
        s = io.open(f, encoding='utf-8').read()
        blocks = s.split('\n\n'); ch = False
        for i, b in enumerate(blocks):
            L = b.rstrip('\n').split('\n')
            if not L or not L[0].strip(): continue
            head = L[0].strip(); out = []
            for j, line in enumerate(L):
                out.append(line)
                if ' = ' in line and not line.startswith('='):
                    k = (head, line.split(' = ')[0].strip())
                    if k in F:
                        en, zh = F[k]
                        nxt = L[j+1] if j+1 < len(L) else ''
                        if nxt.strip() != en:
                            out.append(en); out.append('= ' + zh); hit += 1
                        miss.discard(k)
            if out != L: blocks[i] = '\n'.join(out); ch = True
        if ch: io.open(f, 'w', encoding='utf-8').write('\n\n'.join(blocks))
    print('插入 %d 条（清单 %d 条）' % (hit, len(F)))
    if miss:
        print('没对上（键跟词表字面不一致）：')
        for k in sorted(miss)[:20]: print('    %s | %s' % k)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
