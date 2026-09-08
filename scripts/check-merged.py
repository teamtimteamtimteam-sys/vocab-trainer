#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十道闸门：交付用的合并文件必须跟分批文件一字不差，且整份按词典序。

用户 2026-09-08 的要求：「每一个最终的 2500 词条文档都要按字母顺序，
没有跳过任何词条」。合并文件是真正导进 iPad 的那一份 —— 分批文件再对，
合并那一步出错学的人也照样看得见（merge-wordlist.py 自造过排序键，
把 a priori 排进 ap- 段、把 à la carte 甩到全表最后，就是这么来的）。
所以这件事不能靠「记得跑一下合并脚本」，得有一道每批都跑的检查。

查五件事：
  ① 每份合并文件内部按 wordkey.sort_key 有序
  ② 相邻两份接得上（前一份的末条 ≤ 后一份的首条）
  ③ 合并文件的词条集合与 wordlists/B-[0-9]*.txt 逐条一致 —— 不漏、不多、不重
  ④ 文件名里的编号连续、与实际条数相符（0001-2500、2501-5000、5001-…）
  ⑤ 每条正文完全相同（不只是词头对上，内容也不能在合并时被截断）
用法: python3 scripts/check-merged.py [前缀]        默认 B
"""
import sys, io, re, glob, os
sys.path.insert(0, 'scripts')
from wordkey import sort_key

def load(paths):
    out = []
    for f in paths:
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            b = b.strip()
            if b: out.append((b.split('\n')[0].strip(), b, f))
    return out

def main(prefix='B'):
    batch = sorted(glob.glob(f'wordlists/{prefix}-[0-9]*-[0-9]*.txt'))
    merged = sorted(glob.glob(f'wordlists/{prefix}-merged-*.txt'))
    if not merged:
        print(f'没有 {prefix} 的合并文件 —— 先跑 merge-wordlist.py'); return 1
    bad = []
    prev_last, prev_name, expect = None, None, 1
    total = 0
    for f in merged:
        rows = load([f])
        heads = [h for h, _, _ in rows]
        keys = [sort_key(h) for h in heads]
        # ① 份内有序
        for i in range(1, len(keys)):
            if keys[i] < keys[i-1]:
                bad.append(f'{os.path.basename(f)}：第 {i+1} 条 {heads[i]!r} 排在 {heads[i-1]!r} 之后，顺序错了')
        # ② 份间接得上
        if prev_last is not None and keys and sort_key(prev_last) > keys[0]:
            bad.append(f'{os.path.basename(prev_name)} 末条 {prev_last!r} 排在 {os.path.basename(f)} 首条 {heads[0]!r} 之后，两份之间断了')
        # ④ 文件名编号
        m = re.search(r'-(\d+)-(\d+)\.txt$', f)
        if not m:
            bad.append(f'{os.path.basename(f)}：文件名里没有编号区间')
        else:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo != expect:
                bad.append(f'{os.path.basename(f)} 从 {lo} 开始，但上一份到 {expect-1} —— 中间有跳号')
            if hi - lo + 1 != len(rows):
                bad.append(f'{os.path.basename(f)} 文件名说 {hi-lo+1} 条，实际 {len(rows)} 条')
            expect = hi + 1
        if heads: prev_last, prev_name = heads[-1], f
        total += len(rows)
        print(f'  {os.path.basename(f):<30} {len(rows):>5} 条   {heads[0] if heads else "":<16} → {heads[-1] if heads else ""}')
    # ③⑤ 与分批文件逐条对照
    src = load(batch)
    src.sort(key=lambda r: sort_key(r[0]))
    mer = load(merged)
    if len(src) != len(mer):
        bad.append(f'条数对不上：分批 {len(src)} 条，合并 {len(mer)} 条')
    smap, mmap = {}, {}
    for h, b, f in src: smap.setdefault(h, []).append(b)
    for h, b, f in mer: mmap.setdefault(h, []).append(b)
    for h in smap:
        if h not in mmap: bad.append(f'合并文件里漏了词条：{h}')
    for h in mmap:
        if h not in smap: bad.append(f'合并文件里多出词条：{h}')
        elif len(mmap[h]) > 1: bad.append(f'合并文件里重复了词条：{h}（{len(mmap[h])} 次）')
        elif h in smap and mmap[h][0] != smap[h][0]:
            bad.append(f'词条正文不一致（合并时被改动或截断）：{h}')
    print(f'\n合并 {total} 条，分批 {len(src)} 条')
    if bad:
        print('\n❌ 合并文件有问题：')
        for b in bad[:40]: print('  ' + b)
        if len(bad) > 40: print(f'  …… 另有 {len(bad)-40} 条')
        return 1
    print('✅ 每份内部有序、份间接得上、编号连续、与分批文件逐条一致')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'B'))
