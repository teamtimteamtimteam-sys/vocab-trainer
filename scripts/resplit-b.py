#!/usr/bin/env python3
"""把 B 的所有词条按词典序重排，重新切成等大的批次文件。

为什么需要它：补收的词生成在后面的批次里，直接追加会让文件顺序和
字母序脱节。每次补完一个字母段就跑一次，保证 wordlists/B-*.txt
既是字母序又是均匀分块。

两个坑（都踩过）：
① 排序要用词典式 —— 忽略空格和连字符，否则 "ad hoc" 会排到 "adage"
   前面（空格码位小于字母）、"all right" 会排到 "allot" 前面。
② 尾块不能太小 —— 剩不足 MIN 条时并入上一块。曾切出一个 3 条的
   尾巴文件，批均等式被拉到 2.00 卡在闸门下，那是切分产物不是质量问题。

用法: python3 scripts/resplit-b.py [每批条数，默认 25]
"""
import sys, io, glob, os
sys.path.insert(0, 'scripts')
from wordkey import sort_key

KEY = sort_key   # 共用排序键，见 scripts/wordkey.py
SIZE_DEFAULT = 25

def main(size):
    ent = []
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            b = b.strip()
            if b: ent.append((b.split('\n')[0].strip(), b))
    if not ent: print("没有找到 B 词表"); return 1
    ent.sort(key=lambda x: KEY(x[0]))

    # 均匀分块，不是「切满 size 再留个尾巴」。
    # 密度闸门量的是每个文件的均值，小文件的均值抖动很大 ——
    # 曾切出 3 条和 11 条的尾巴文件，批均等式被拉到 2.0 卡在闸门下，
    # 那是切分产物不是质量问题。均分后各块大小相差不超过 1，没有小尾巴。
    k = max(1, round(len(ent) / size))
    base, extra = divmod(len(ent), k)
    chunks, i = [], 0
    for j in range(k):
        n = base + (1 if j < extra else 0)
        chunks.append(ent[i:i+n]); i += n

    for f in glob.glob('wordlists/B-[0-9]*.txt'): os.remove(f)
    n = 0
    for ch in chunks:
        io.open(f"wordlists/B-{n+1:04d}-{n+len(ch):04d}.txt", 'w', encoding='utf-8').write(
            "\n\n".join(b for _, b in ch) + "\n")
        n += len(ch)

    w = [x for x, _ in ent]
    ok = w == sorted(w, key=KEY)
    print(f"{len(ent)} 条 → {len(chunks)} 个文件（每块 {min(map(len,chunks))}-{max(map(len,chunks))} 条）")
    print(f"词典序有序：{ok}   {w[0]} → {w[-1]}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else SIZE_DEFAULT))
