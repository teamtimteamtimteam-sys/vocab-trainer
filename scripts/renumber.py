#!/usr/bin/env python3
"""把每个词条里的例句编号重排成 ①②③…，消灭漏号/重号。
用法: python3 scripts/renumber.py 'wordlists/A-*.txt'"""
import sys, io, glob
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
for a in sys.argv[1:]: paths += glob.glob(a)
for p in sorted(paths):
    c = fix(p)
    total += c
    if c: print("  %s 重排 %d 处" % (p, c))
print("共重排 %d 处" % total)
