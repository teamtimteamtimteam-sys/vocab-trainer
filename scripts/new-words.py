#!/usr/bin/env python3
"""从候选词里筛掉已用过的，避免跨批重复。
用法: python3 scripts/new-words.py 前缀 词1 词2 ...
      python3 scripts/new-words.py A --list   # 只列出已用词数"""
import sys, io, glob
if len(sys.argv) < 2: print("用法: new-words.py <前缀> <词...>"); sys.exit(2)
prefix = sys.argv[1]
used = set()
for f in sorted(glob.glob('wordlists/%s-*.txt' % prefix)):
    for b in io.open(f, encoding='utf-8').read().split('\n\n'):
        b = b.strip()
        if b: used.add(b.split('\n')[0].strip().lower())
if len(sys.argv) == 3 and sys.argv[2] == '--list':
    print("%s 已用 %d 词" % (prefix, len(used))); sys.exit(0)
cand = [w for w in sys.argv[2:]]
new = [w for w in cand if w.lower() not in used]
dup = [w for w in cand if w.lower() in used]
print("可用 %d：%s" % (len(new), " ".join(new)))
if dup: print("已用 %d：%s" % (len(dup), " ".join(dup)))
