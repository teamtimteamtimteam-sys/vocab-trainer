#!/usr/bin/env python3
"""从归档区取回词条，供顺序推进到该字母段时复用。

背景：早期 B 词表是「按词频挑词再排字母序」，收词不全。改成按牛津高阶
逐条收全后，那些超前写好的词（ae 及之后）被移到 wordlists/pending/，
等顺序推进到时再取回 —— 免得重写，也免得同一份词表里两种收词密度并存。

用法: python3 scripts/pull-pending.py aerial aerobic aesthetic
     不带参数则列出归档区还剩哪些词。
"""
import sys, io, os
P = 'wordlists/pending/B-pending.txt'

def blocks():
    if not os.path.exists(P): return []
    return [b.strip() for b in io.open(P, encoding='utf-8').read().split('\n\n') if b.strip()]

def main(words):
    bs = blocks()
    idx = {b.split('\n')[0].strip().lower(): b for b in bs}
    if not words:
        ws = sorted(idx)
        print(f"归档区 {len(ws)} 条：")
        print(" ".join(ws))
        return 0
    got, miss = [], []
    for w in words:
        k = w.lower()
        (got.append(idx[k]) if k in idx else miss.append(w))
    if miss: print("不在归档区：" + " ".join(miss), file=sys.stderr)
    if got:
        print("\n\n".join(got))
        # 取走的从归档区删掉，避免重复收录
        taken = {b.split('\n')[0].strip().lower() for b in got}
        rest = [b for b in bs if b.split('\n')[0].strip().lower() not in taken]
        io.open(P, 'w', encoding='utf-8').write("\n\n".join(rest) + ("\n" if rest else ""))
        print(f"\n（已取出 {len(got)} 条，归档区剩 {len(rest)} 条）", file=sys.stderr)
    return 0 if got else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
