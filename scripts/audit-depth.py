#!/usr/bin/env python3
"""查 B 词表里被"压薄"的多义常用词。

为什么需要它：check-wordlist.py 量的是批均密度，一批里多义词写薄了、
术语词写厚了，均值照样过闸。这个脚本逐条量，并且用 A 词表的词频序
当常用度标尺 —— A 越靠前的词越高频，高频词只有 3 个义项就是可疑的。

用法: python3 scripts/audit-depth.py [字母段...] [--all]
"""
import io, glob, sys, collections
sys.path.insert(0, 'scripts')
from wordkey import prefix

NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿" \
       "❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴⓵⓶⓷⓸⓹⓺⓻⓼⓽⓾"

def a_rank():
    """A 词表按词频排，序号就是常用度。返回 词 -> 名次。"""
    r, n = {}, 0
    for f in sorted(glob.glob('wordlists/A-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            b = b.strip()
            if b:
                n += 1
                r.setdefault(b.split('\n')[0].strip().lower(), n)
    return r

def entries():
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            b = b.strip()
            if b: yield f, b

def measure(block):
    L = block.split('\n')
    se = [l for l in L[1:] if l and l[0] in NUMS]
    ci = next((i for i, l in enumerate(L) if l.startswith('核心')), None)
    si = next((i for i, l in enumerate(L) if l and l[0] in NUMS), len(L))
    notes = [l for l in L[1:] if l and l[0] not in NUMS and not l.startswith('=')]
    return {'word': L[0].strip(), 'senses': len(se),
            'core': (si - ci) if ci is not None else 0,
            'notes': len(notes), 'chars': len(block)}

def main(argv):
    segs = [a for a in argv if not a.startswith('-')]
    rank = a_rank()
    rows = []
    for f, b in entries():
        m = measure(b)
        w = m['word'].lower()
        if segs and not any(prefix(m['word'], len(s)) == s or
                            (len(s) == 1 and w[:1] == s) for s in segs):
            continue
        m['rank'] = rank.get(w)
        m['file'] = f
        rows.append(m)
    if not rows:
        print("没有匹配的词条"); return 1

    print(f"共 {len(rows)} 条；其中 {sum(1 for r in rows if r['rank'])} 条在 A 高频词表里\n")

    # 压薄嫌疑：高频词却只有 3 个义项。名次越靠前越可疑。
    thin = sorted([r for r in rows if r['rank'] and r['senses'] <= 3],
                  key=lambda r: r['rank'])
    print(f"【压薄嫌疑】高频词只有 ≤3 个义项：{len(thin)} 条（按词频由高到低）")
    for r in thin[:60]:
        print(f"    A#{r['rank']:<5} {r['word']:<22} {r['senses']} 义项  "
              f"核心 {r['core']} 行  {r['chars']} 字")
    if len(thin) > 60: print(f"    …… 另有 {len(thin)-60} 条")

    # 【核心块过短】这一项已撤（用户 2026-09-04 交代：核心块长度没有强制
    # 要求，按词的实际情况定）。留着它等于换个地方继续拿行数当尺子 ——
    # 规则改了、尺子没拆，报告里照样每次点名，写的人照样会去凑行数。
    # 核心块「必须存在」仍由 check-wordlist.py 把关，那是有无，不是长短。

    lean = [r for r in rows if r['notes'] < 1.5 * r['senses']]
    if lean:
        print(f"\n【讲解偏少】讲解行不足义项数的 1.5 倍：{len(lean)} 条")
        print("    " + "  ".join(f"{r['word']}({r['notes']}/{r['senses']})" for r in lean))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
