#!/usr/bin/env python3
"""把每个词条里的例句编号重排成 ①②③…，消灭漏号/重号。
用法: python3 scripts/renumber.py 'wordlists/A-*.txt'"""
import sys, io, glob
sys.path.insert(0, 'scripts')
from wordkey import numsort
NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴⓵⓶⓷⓸⓹⓺⓻⓼⓽⓾"   # 1-50 圈码 + 51-80 反白圈码，见 CLAUDE.md
MAXN = len(NUMS)
def fix(path):
    blocks = [b for b in io.open(path, encoding='utf-8').read().split('\n\n')]
    changed = 0
    out = []
    for b in blocks:
        if not b.strip(): continue
        lines = b.rstrip('\n').split('\n')
        i = 0; new = []
        for l in lines:
            s = l.strip()
            if s and s[0] in NUMS:
                if i >= MAXN:
                    raise SystemExit("%s：%s 的义项超过 %d 个，编号用完了。"
                                     "把只是同词根的具体名词拆成独立词条。"
                                     % (path, lines[0].strip(), MAXN))
                want = NUMS[i]
                if s[0] != want: changed += 1
                new.append(want + s[1:]); i += 1
            else:
                new.append(l)
        out.append('\n'.join(new))
    io.open(path, 'w', encoding='utf-8').write('\n\n'.join(out) + '\n')
    return changed
total = 0
paths = []
# 不给参数时默认整份词表 —— 2026-09-08 踩过：GOAL.txt 记的四步里写的就是
# 光秃秃一句 `python3 scripts/renumber.py`，于是 paths 是空的，脚本一路
# 打印「共重排 0 处」，看着像通过，实际一个文件都没读。真有重号时
# （daughter 那次插了一条义项，变成 ①②③③④⑤）它照样报 0，
# 全靠 check-wordlist 的「编号不连续」把它拦下来。
# 一直报 0 的脚本等于没有脚本，所以把默认路径补上。
args = sys.argv[1:] or ['wordlists/A-*.txt', 'wordlists/B-*.txt']
for a in args: paths += glob.glob(a)
for p in numsort(paths):
    c = fix(p)
    total += c
    if c: print("  %s 重排 %d 处" % (p, c))
print("共重排 %d 处" % total)
