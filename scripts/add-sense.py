#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""往已有词条尾部补一个义项（例句 + 译文 + 等式 + 可选讲解行）。
序号自动接着往下排，插在 构词/注意 这类收尾行之前。
用法：脚本里 import，或命令行 add-sense.py 词头 例句 译文 等式 [讲解行]
"""
import sys, io, glob, importlib.util as u
spec = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(spec); spec.loader.exec_module(cw)
NUMS = list(cw.NUMS)
TAIL = ('构词', '注意', '辨析', '语域', '搭配')

def add(head, ex, zh, eq, note=None):
    for path in sorted(glob.glob('wordlists/B-*.txt')):
        lines = io.open(path, encoding='utf-8').read().split('\n')
        try:
            i = next(k for k, l in enumerate(lines)
                     if l == head and (k == 0 or lines[k-1].strip() == ''))
        except StopIteration:
            continue
        j = i + 1
        last = -1
        end = j
        while j < len(lines) and lines[j].strip() != '':
            t = lines[j]
            if t and t[0] in NUMS:
                last = NUMS.index(t[0])
            end = j + 1
            j += 1
        # 收尾的构词/注意行只认「最后一个编号之后」的那一段，
        # 词条中间出现的注意块不能当插入点，否则新义项排到旧编号前面去。
        lastnum = i
        for k in range(i + 1, end):
            if lines[k] and lines[k][0] in NUMS:
                lastnum = k
        cut = end
        for k in range(lastnum + 1, end):
            if any(lines[k].startswith(t) for t in TAIL):
                cut = k; break
        # 别把已经在词条里的句子再加一遍 —— booger 与 bargain 就是这么
        # 出现两个一模一样的义项的（2026-09-05）。
        import re as _re
        def _k(t): return set(_re.sub(r'[^a-z ]', ' ', t.lower()).split())
        for _l in lines[i + 1:end]:
            if _l and _l[0] in NUMS and _k(_l[1:]) == _k(ex):
                raise SystemExit('%s 里已经有这句例句了，别重复加：%s' % (head, ex))
        block = [NUMS[last + 1] + ' ' + ex, '= ' + zh, eq]
        if note: block.append(note)
        lines[cut:cut] = block
        io.open(path, 'w', encoding='utf-8').write('\n'.join(lines))
        return path
    raise SystemExit('找不到词头：' + head)

if __name__ == '__main__':
    a = sys.argv[1:]
    print(add(*a))
