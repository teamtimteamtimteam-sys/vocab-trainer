#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查大词的习语收全了没有。

audit-ab 只查得出「A 教过而 B 没有」的，A 只收 3002 个高频词，
两表共有的才 517 条 —— A 没收的词依然没有尺子。corner 漏掉的
turn the corner / cut corners / just around the corner /
out of the corner of one's eye 就属于这一类，是手工翻出来的。

这个脚本把「知识」和「核对」分开：清单由人写（下面的 CHECK），
机器负责查 B 里有没有。写完一个字母段的大词，就往 CHECK 里
补一批，跑一遍，缺什么补什么。
首跑（2026-09-05）查 23 个 c 段大词的 101 条习语，缺 34 条，已全部补上。

用法：python3 scripts/audit-idioms.py
"""
import sys, re, unicodedata, importlib.util as u
spec = u.spec_from_file_location('ap', 'scripts/audit-padding.py')
ap = u.module_from_spec(spec); spec.loader.exec_module(ap)

def fold(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

CHECK = {
 'call': ['call it a day', 'call the shots', 'call off', 'call for', 'on call',
          'a close call', "call somebody's bluff", 'call in'],
 'carry': ['carry on', 'carry out', 'get carried away', 'carry weight', 'carry the can'],
 'case': ['in case', 'in any case', 'in that case', 'a case in point', 'make a case for'],
 'cast': ['cast doubt on', 'cast a shadow', 'cast off', "cast one's mind back"],
 'catch': ['catch on', 'catch up', 'catch out', 'catch fire', "catch somebody's eye"],
 'chance': ['by chance', 'take a chance', 'stand a chance', 'the chances are',
            'a fighting chance'],
 'change': ['change hands', "change one's mind", 'small change', 'a change of heart',
            'for a change'],
 'check': ['check in', 'check out', 'check up on', 'keep in check', 'a rain check'],
 'chip': ['chip in', "a chip on one's shoulder", 'when the chips are down'],
 'clear': ['clear up', 'clear out', 'clear the air', 'in the clear', 'steer clear of',
           'clear-cut'],
 'close': ['close down', 'close in', 'a close shave', 'close ranks', 'behind closed doors'],
 'cold': ['cold feet', 'in cold blood', 'the cold shoulder', 'out in the cold', 'cold turkey'],
 'come': ['come across', 'come up with', 'come to terms with', 'come what may',
          'come clean', 'come of age', 'come around'],
 'company': ['keep somebody company', 'part company', 'in good company'],
 'contact': ['make contact', 'lose contact'],
 'control': ['out of control', 'under control', 'take control', 'lose control'],
 'cool': ["lose one's cool", 'a cool million', 'be cool with', 'cool it'],
 'corn': ['corn on the cob'],
 'corner': ['turn the corner', 'cut corners', 'just around the corner',
            "out of the corner of one's eye", 'a corner shop'],
 'count': ["count one's blessings", 'count for nothing', 'at the last count'],
 # 往下写到哪个字母段，就在这里补哪一段的大词
}

def main():
    B = {}
    for h, L in ap.entries(): B.setdefault(h, []).extend(L)
    allB = fold(' '.join(l for v in B.values() for l in v))
    miss = []; tot = 0; skipped = []
    for h, items in sorted(CHECK.items()):
        if h not in B: skipped.append(h); continue
        body = fold(' '.join(B[h]))
        for it in items:
            tot += 1
            f = fold(it)
            if f not in body and f not in allB: miss.append((h, it))
    print('\n查 %d 个大词的 %d 条习语，B 里缺 %d 条' % (len(CHECK) - len(skipped), tot, len(miss)))
    if skipped: print('  （还没写到的词条，跳过：%s）' % ' '.join(skipped))
    cur = None
    for h, it in miss:
        if h != cur: print('    %s' % h); cur = h
        print('        缺：%s' % it)
    if not miss: print('  ✅ 清单里的习语都收了')
    return 1 if miss else 0

if __name__ == '__main__':
    sys.exit(main())
