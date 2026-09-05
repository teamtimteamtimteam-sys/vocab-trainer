#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按义项号改写例句与译文，别的行一概不动。

全表回填例句时用（用户 2026-09-05 裁定：例句要能顺带教出别的搭配）。
只换「编号那一行」和紧跟的「= 译文」行 —— 等式行、讲解行、核心块都不碰，
因为 coverage、audit-idioms、audit-ab 认的字面全在那些行里，动了会掉覆盖。

写完自查两条，不过就抛错、不写文件：
  · 新例句里必须仍有词头或其变形（audit-padding 的铁律）
  · 译文里不许出现未加引号的英文（check-wordlist 的规则）

用法：脚本里 import 之后
  reword('agreement', {1: ("After eighteen months …", "谈了十八个月……"), 3: (...)})
"""
import io, re, glob, importlib.util as u

_s = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(_s); _s.loader.exec_module(cw)
_s2 = u.spec_from_file_location('ap', 'scripts/audit-padding.py')
ap = u.module_from_spec(_s2); _s2.loader.exec_module(ap)
NUMS = list(cw.NUMS)

def reword(head, pairs):
    for path in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        lines = io.open(path, encoding='utf-8').read().split('\n')
        try:
            i = next(k for k, l in enumerate(lines)
                     if l == head and (k == 0 or lines[k - 1].strip() == ''))
        except StopIteration:
            continue
        j, end = i + 1, i + 1
        while j < len(lines) and lines[j].strip() != '':
            end = j + 1; j += 1
        idx = {}
        for k in range(i + 1, end):
            if lines[k] and lines[k][0] in NUMS:
                idx[NUMS.index(lines[k][0]) + 1] = k
        miss = set(pairs) - set(idx)
        if miss: raise SystemExit('%s 没有义项 %s' % (head, sorted(miss)))
        for n, (ex, tr) in pairs.items():
            if not ap.related(head, ap.fold(ex)):
                raise SystemExit('%s 义项 %d 的新例句里没有词头：%s' % (head, n, ex))
            t = re.sub(r'[\"“”「」][^\"“”「」]*[\"“”「」]', ' ', tr)
            stray = [w for w in re.findall(r'[A-Za-z]{3,}', t) if not w[0].isupper()]
            if stray:
                raise SystemExit('%s 义项 %d 的译文里混入英文：%s' % (head, n, '、'.join(stray)))
            k = idx[n]
            lines[k] = lines[k][0] + ' ' + ex
            if k + 1 < end and lines[k + 1].startswith('='):
                lines[k + 1] = '= ' + tr
            else:
                raise SystemExit('%s 义项 %d 后面没有译文行' % (head, n))
        io.open(path, 'w', encoding='utf-8').write('\n'.join(lines))
        return path
    raise SystemExit('找不到词头：' + head)
