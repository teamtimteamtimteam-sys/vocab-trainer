#!/usr/bin/env python3
"""列出 B 表里「有等式、没例句」的拓展条目 —— 用户 2026-09-11 定的补写清单。

范围（用户裁定）：
  · 补：条目末尾无标签挂上去的并入短语、「词族：」、「常用搭配：」
  · 不补：近义对照 / 注意别混 / 注意区别 / 反义词 / 配对词 / 注意地域 /
          注意拼写 / 注意英美拼写 / 注意英美差别 —— 这些是对照表，
          配例句反而冲散对比
  · A 表一概不补

用法: python3 scripts/need-example.py [字母段...] [--list]
"""
import glob, io, re, sys, collections
sys.path.insert(0, 'scripts')
from wordkey import prefix, numsort

NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚"
LABEL = re.compile(r'^[^ =]*[：:]\s*$')
SKIP  = re.compile(r'(对照|别混|区别|反义|配对|地域|拼写|英美)')
FILL  = re.compile(r'(词族|常用搭配|搭配)')

def scan(segs, want=(1, 2)):
    rows = []
    for f in numsort(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            L = [l for l in b.strip().split('\n') if l.strip()]
            if not L: continue
            head = L[0].strip()
            if segs and not any(prefix(head, len(s)) == s for s in segs): continue
            armed = False; lab = None; need = []
            for j, l in enumerate(L[1:], start=1):
                if l[0] in NUMS: armed = True; lab = None; continue
                if l.startswith('='): continue
                if LABEL.match(l.strip()): lab = l.strip(); continue
                if ' = ' in l:
                    if armed: armed = False; continue      # 紧跟例句那条，已有例句
                    if lab and SKIP.search(lab): continue   # 对照块，按裁定不补
                    if lab is None or FILL.search(lab):
                        # 下一行若是纯英文（既不是等式也不是中文），说明已经补过例句
                        nxt = L[j + 1].strip() if j + 1 < len(L) else ''
                        done = (nxt and not nxt.startswith('=') and ' = ' not in nxt
                                and not re.search(r'[一-鿿]', nxt) and nxt[0] not in NUMS)
                        if done: continue
                        lhs, rhs = [x.strip() for x in l.strip().split(' = ', 1)]
                        # 这些等式不是搭配，补例句没有意义：
                        #   · 左边没有拉丁字母（「生化用语 = 亲和力」这种标注）
                        #   · 左边是整句（「The drug affects you. = 药影响你。」对照句）
                        #   · 右边在讲拼法／变形／同义，本质上仍是对照
                        if not re.search(r'[A-Za-z]', lhs): continue
                        if lhs[-1:] in '.?!': continue
                        if re.search(r'(拼法|异拼|同义|过去式|过去分词|复数|缩写|另一种写法)', rhs): continue
                        tier = 2 if (lab and '词族' in lab) else 1
                        if tier in want: need.append(l.strip())
                else: lab = None
            if need: rows.append((f, head, need))
    return rows

def main(argv):
    segs = [a for a in argv if not a.startswith('-')]
    want = (1,) if '--tier1' in argv else (2,) if '--tier2' in argv else (1, 2)
    rows = scan(segs, want)
    n = sum(len(r[2]) for r in rows)
    print("待补例句：%d 条等式，分布在 %d 个词条" % (n, len(rows)))
    by = collections.Counter(prefix(r[1], 2) for r in rows)
    print("  按双字母段：" + "  ".join("%s %d" % kv for kv in sorted(by.items())))
    if '--list' in argv:
        for f, head, need in rows:
            print("\n%s  [%s]" % (head, f.split('/')[-1]))
            for x in need: print("    " + x)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
