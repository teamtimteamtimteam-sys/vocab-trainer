#!/usr/bin/env python3
"""按双字母前缀统计 B 的收词，报出「夹在中间却一条都没有」的空段。

为什么需要它：按字母顺序推进时，很容易整段跳过 —— 我从 an- 直接跳到
ap-，漏掉了 ao-（aorta、aortic、AOB）；更早还漏了 aa-（aardvark）。
这两次都是用户问出来的，不是我自己发现的。空段的特征很清楚：
前后都有词、它自己是零。这个脚本就查这个。

注意：不是所有零段都是漏 —— 英语里确实没有 aq- 之外某些组合的词。
所以只报「内部空段」（前后都有词的零段），并把它当作待核对项，
逐一去牛津高阶确认是真没有还是我跳过了。

**退出码只对登记进 EXPECT 的字母负责**（目前是 a、b、c —— 已经收完、
逐条核对过的那几段）。没登记的字母还在写，空段照报但不计入退出码。

用法: python3 scripts/audit-prefix.py [首字母，默认全部]
"""
import sys, io, glob, string
sys.path.insert(0, 'scripts')
from wordkey import sort_key, prefix, numsort
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
    # d 与 e 收完后登记（2026-09-10）。清单里逐个核过：这两个字母下
    # 没有词的双字母段，牛津高阶本来就没有词头，不是漏收。
    # **为什么非登记不可**：ey- 段（eye 一族 22 条）整段没写，
    # audit-prefix 一直把它当「还没写到」列在参考栏里、不计退出码，
    # 于是 e 段一路报到「收完」都没人拦。登记之后，这类整段空缺直接红。
    'd': ['da','de','di','do','dr','du','dw','dy'],
    'e': ['e'+c for c in string.ascii_lowercase if c != 'z'],
    'b': ['ba','bc','be','bh','bi','bl','bn','bo','bp','br','bu','by'],
    # c 的空段已逐条核对过（2026-09-04 一轮，2026-09-06 补一条），
    # 对着 reference 的词头清单查的：
    #   cb cd cg cj ck cn cq cv cx —— 清单里 0 条，不是漏收
    #   cp                        —— 清单里 8 条，但全是缩写：cp.（已进 exclude）
    #                                与 CPA CPE CPI Cpl CPP CPR CPU，按收词边界
    #                                「全大写缩写不收」剔除后即空，同 b 段的
    #                                bb bf bm bq bs bt。**这一条原来错列在下面，
    #                                害得 audit-prefix c 从 c 段收完起就一直报红。**
    #                                核对办法记在这儿免得再错：词头在 CSV 的
    #                                第二列，不是第一列（第一列是序号），
    #                                查的时候别 grep 错列。
    # 清单里确实有可收词的 15 个前缀列在下面
    'c': ['ca','cc','ce','cf','ch','ci','cl','cm','co','cr','ct','cu','cw','cy','cz'],
}

KEY = sort_key   # 共用排序键，见 scripts/wordkey.py

def main(letter=None):
    w = []
    for f in numsort(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            if b.strip(): w.append(b.strip().split('\n')[0])
    c = Counter(prefix(x) for x in w)
    letters = [letter] if letter else sorted({prefix(x, 1) for x in w})
    gaps = []      # 已收完的段出的洞 —— 计入退出码
    info = []      # 还在写的段出的洞 —— 只报不拦
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
            # 没登记进 EXPECT 的字母 = 这一段还没收完（d 段就是）。
            # 对着一个正在写的段报「内部空段」毫无意义 —— 它当然到处是洞。
            # 所以照报不误，但**不计入退出码**：退出码只在「已经收完的段
            # 出了洞」时才该红。2026-09-06 加的，起因是回填第三十九批
            # 只碰了一个 d- 词，audit-prefix d 就报了 13 个空段。
            # 一个每次都红的闸门，跟没有闸门是一回事 —— 这个月已经栽过一次
            # （EXPECT['c'] 把 cp 错列成「应有词条」，害它从 c 段收完起一直报红）。
            inner = [p for i, (p, n) in enumerate(row) if not n and lo < i < hi]
            if inner:
                info += inner
                print(f"  · 空段（{L}- 段还没登记进 EXPECT，多半是还没写到）："
                      f"{' '.join(inner)}  —— 仅供参考，不计入退出码")
    if gaps:
        print(f"\n共 {len(gaps)} 个内部空段待核对：{' '.join(gaps)}")
        return 1
    print("\n✅ 已收完的字母段没有空段"
          + ("（还在写的段上面单列了，不计入）" if info else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
