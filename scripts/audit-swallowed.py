#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查「被吞掉的词」：清单里的词被 coverage 判成已覆盖，但在宿主词条里
只出现在核心块、构词行或注意行里，没有配例句与等式 —— 那不是合法并入，
是被顺手提了一句就误判成已收。

已经栽过三次：carriage 被 car 吞、camphor 被 camp 吞、comfort 被 comfit
的「注意别混」吞。前两次靠 audit-depth 与人工核对偶然发现，这个脚本把它
变成机器检查。

判据：该词没有自己的词头，且在任何宿主词条里都不满足
      「出现在 ①②③ 例句行或等式行里」。
用法：python3 scripts/audit-swallowed.py [字母段]
"""
import sys, io, re, glob, importlib.util as u

spec = u.spec_from_file_location('cv', 'scripts/coverage.py')
cv = u.module_from_spec(spec); spec.loader.exec_module(cv)
spec2 = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(spec2); spec2.loader.exec_module(cw)
NUMS = set(cw.NUMS)

def main(argv):
    seg = argv[0].lower() if argv else None
    ref = cv.load_reference()
    got, text, entries = cv.collected()
    import unicodedata
    def defold(t):
        # 折掉重音：coverage 的判定是折过的，这里不折就会把 cortège 之于
        # cortege、cinéma 之于 cinema 误报成「被吞掉」（2026-09-05）
        t = unicodedata.normalize('NFD', t)
        return ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    heads = {defold(h.lower().replace('’', "'")) for h, _ in entries}
    # 每条词条拆成「例句与等式行」与「其余行」两桶
    ex_text, note_text = {}, {}
    for h, body in entries:
        ex, note = [], []
        for line in body.split('\n'):
            t = line.strip()
            if not t: continue
            if t[0] in NUMS or cw.EQ.match(t) or t.startswith('='):
                ex.append(t)
            else:
                note.append(t)
        ex_text[h] = '\n'.join(ex); note_text[h] = '\n'.join(note)

    swallowed = []
    for k, w in sorted(ref.items()):
        lw = defold(w.lower().replace('’', "'"))
        if seg and not lw.startswith(seg): continue
        if lw in heads: continue                      # 自己有词条
        if not cv.derived_covered(w, entries): continue  # 不是靠派生判定覆盖的
        pat = re.compile(r'(?<![a-z])' + re.escape(lw) + r'(?![a-z])')
        ok = False; hosts = []
        # 带宾语的短语动词：等式行写成 call somebody away，去掉占位词后
        # 等于 call away，那是合法并入，不算被吞。
        placeholders = re.compile(
            r'\b(somebody|something|sb|sth|one\'s|your|his|her|their|it)\b')
        for h, body in entries:
            hl = h.lower().replace('’', "'")
            if len(hl) < 3 or not lw.startswith(hl[:4]) or lw == hl: continue
            if pat.search(ex_text.get(h, '')): ok = True; break
            stripped = ' '.join(placeholders.sub(' ', ex_text.get(h, '')).split())
            if pat.search(stripped): ok = True; break
            if pat.search(note_text.get(h, '')): hosts.append(h)
        if not ok and hosts:
            swallowed.append((w, hosts[0]))

    seg_label = (seg + '- 段') if seg else '全表'
    print('\n%s：被吞掉的词 %d 条' % (seg_label, len(swallowed)))
    if swallowed:
        print('（只在宿主的核心块或注意行里被提到，没有例句与等式 —— 应当补并入或单列）')
        for w, h in swallowed:
            print('    %-24s 被 %s 吞掉' % (w, h))
    else:
        print('  ✅ 没有被吞掉的词')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
