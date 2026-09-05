#!/usr/bin/env python3
"""按双字母前缀统计 B 的收词，报出「夹在中间却一条都没有」的空段。

为什么需要它：按字母顺序推进时，很容易整段跳过 —— 我从 an- 直接跳到
ap-，漏掉了 ao-（aorta、aortic、AOB）；更早还漏了 aa-（aardvark）。
这两次都是用户问出来的，不是我自己发现的。空段的特征很清楚：
前后都有词、它自己是零。这个脚本就查这个。

注意：不是所有零段都是漏 —— 英语里确实没有 aq- 之外某些组合的词。
所以只报「内部空段」（前后都有词的零段），并把它当作待核对项，
逐一去牛津高阶确认是真没有还是我跳过了。

用法: python3 scripts/audit-prefix.py [首字母，默认全部]
"""
import sys, io, glob, string
sys.path.insert(0, 'scripts')
from wordkey import sort_key, prefix
from collections import Counter

# 各字母下确实存在牛津高阶词条的双字母前缀。逐个字母核对后填进来 ——
# 有了它，前沿处的漏段才查得出来（a- 段 26 个前缀全都有词）。
EXPECT = {
    'a': ['a'+c for c in string.ascii_lowercase],
    # b 的 13 个空段已逐条核对过（2026-09-04），确实无词可收，不是漏收：
    #   bd bg bj bk bv bx —— 词头清单里本来就是 0 条
    #   bb bf bm bq bs bt —— 清单里只有全大写缩写（BBC、BFF、BMI、Bq、BSc、BTW），
    #                        按收词边界「全大写缩写不收」剔除后即空
    #   bw               —— 清单里只有 bwana 一条，东非英语，按国别变体通则剔除
    'b': ['ba','bc','be','bh','bi','bl','bn','bo','bp','br','bu','by'],
    # c 的 10 个空段已逐条核对过（2026-09-04），对着 reference 的词头清单查的：
    #   cb cd cg cj ck cn cq cs cv cx —— 清单里 0 条，不是漏收
    # 清单里确实有词的 16 个前缀列在下面（coverage.py c 的分段报告与此一致）
    'c': ['ca','cc','ce','cf','ch','ci','cl','cm','co','cp','cr','ct','cu','cw','cy','cz'],
}

KEY = sort_key   # 共用排序键，见 scripts/wordkey.py

def main(letter=None):
    w = []
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            if b.strip(): w.append(b.strip().split('\n')[0])
    c = Counter(prefix(x) for x in w)
    letters = [letter] if letter else sorted({prefix(x, 1) for x in w})
    gaps = []
    for L in letters:
        row = [(L + ch, c.get(L + ch, 0)) for ch in string.ascii_lowercase]
        nz = [i for i, (_, n) in enumerate(row) if n]
        if not nz: continue
        lo, hi = nz[0], nz[-1]
        # 首词只有一个字母的条目（a、a cappella、a priori）归不进双字母段，
        # 单列出来，否则表里的合计会和总数对不上，看着像丢了词。
        solo = [x for x in w if prefix(x) == L]
        head = f"\n{L}- 段（共 {sum(n for _, n in row) + len(solo)} 条）"
        print(head)
        if solo:
            print(f"  「{L}」及以「{L} 」开头的多词条目 {len(solo)} 条：{' '.join(solo)}")
        for i in range(0, 26, 6):
            print("  " + "  ".join(f"{p} {n:4}" if n else f"{p}    ·" for p, n in row[i:i+6]))
        # 只查「内部空段」是不够的 —— 顺序推进时漏段总发生在前沿，
        # 而前沿之外的空段看起来和「还没做到那里」一样。抽掉 ao- 做回归时
        # 这个检测器就没报警。所以改成对照 EXPECT：某个字母下确实存在
        # 牛津高阶词条的双字母前缀，一个都不能是零。
        exp = EXPECT.get(L)
        if exp:
            empty = [p for p, n in row if p in exp and not n]
            if empty:
                gaps += empty
                print(f"  ⚠ 应有词条却为空：{' '.join(empty)}")
        else:
            inner = [p for i, (p, n) in enumerate(row) if not n and lo < i < hi]
            if inner:
                gaps += inner
                print(f"  ⚠ 内部空段（未登记 EXPECT，按前后有词推断）：{' '.join(inner)}")
    if gaps:
        print(f"\n共 {len(gaps)} 个内部空段待核对：{' '.join(gaps)}")
        return 1
    print("\n✅ 无内部空段")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
