#!/usr/bin/env python3
"""给缺等式行的义项批量补一行「英文 = 中文」。

为什么需要它：回填是按"词头 + 义项号码"定位插入点的操作，不是整条重写
（patch-entries.py）也不是整条追加（append-to-entry.py）。义项号码从
audit 脚本的输出里现成拿得到，比手写锚点文本可靠——锚点文本万一在别处
重复出现，append 逻辑会插错地方。

插入位置：该义项自己的讲解之后、**对照/别混/区别/反义块之前**——
不能无脑插在义项末尾。「近义对照：」这类标签一旦出现，coverage 判定会
认为标签之后的内容都属于"讲别的词"，插在标签块后面等于插进了这段"挡光"
区域，仍然判定为缺失。第一版就是无脑插到末尾，导致 although/at/almost
三条插了等于没插，肉眼查 coverage 才发现。现在改成：找到该义项内第一处
命中「对照|别混|区别|反义」的标签行，插在它前面；没有这种标签就仍插在
义项末尾。

**同一个词多处插入必须按位置从后往前改**——先按原始行号把所有插入点
都算好，再按位置从大到小依次插入，否则前面插入完，后面的位置就全错位。

补丁文件格式：
    word<TAB>sense_no<TAB>equation_line
一行一条，sense_no 是义项在词条里的序号（从 1 开始，对应 ①②③…）。

用法: python3 scripts/backfill-eq.py <补丁文件>
"""
import io, glob, re, sys

NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿" \
       "❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴⓵⓶⓷⓸⓹⓺⓻⓼⓽⓾"
LAB = re.compile(r'[：:]$')
CONTRAST = re.compile(r'(对照|别混|区别|反义)')

def main(patch):
    tasks = {}  # word -> {sense_no: [line, ...]}
    for raw in io.open(patch, encoding='utf-8'):
        raw = raw.rstrip('\n')
        if not raw.strip() or raw.startswith('#'): continue
        parts = raw.split('\t')
        if len(parts) != 3:
            print("格式错误（要 3 列，用 tab 分隔）：", raw); return 1
        w, no, eq = parts
        tasks.setdefault(w, {}).setdefault(int(no), []).append(eq)

    hit = {w: set() for w in tasks}
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        src = io.open(f, encoding='utf-8').read()
        blocks = src.split('\n\n')
        changed = False
        for bi, b in enumerate(blocks):
            s = b.strip()
            if not s: continue
            L = s.split('\n')
            w = L[0].strip()
            if w not in tasks: continue
            idx = [j for j, l in enumerate(L) if l and l[0] in NUMS]
            inserts = []
            for no, eqs in tasks[w].items():
                if no < 1 or no > len(idx): continue
                start = idx[no - 1] + 1
                end = idx[no] if no < len(idx) else len(L)
                pos = end
                for k in range(start, end):
                    if LAB.search(L[k]) and len(L[k]) <= 24 and CONTRAST.search(L[k]):
                        pos = k; break
                inserts.append((pos, no, eqs))
            for pos, no, eqs in sorted(inserts, key=lambda x: -x[0]):
                for eq in reversed(eqs):
                    L.insert(pos, eq)
                hit[w].add(no)
            blocks[bi] = '\n'.join(L)
            changed = True
        if changed:
            io.open(f, 'w', encoding='utf-8').write('\n\n'.join(blocks))

    miss = []
    for w, nos in tasks.items():
        for no in nos:
            if no not in hit[w]: miss.append(f"{w}#{no}")
    if miss:
        print("没找到这些词的这些义项号（词头不存在，或义项号超出范围）：")
        print(" ", " ".join(miss))
    n = sum(len(v) for v in hit.values())
    print(f"插入 {n} 行等式")
    return 1 if miss else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
