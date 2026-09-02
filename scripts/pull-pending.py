#!/usr/bin/env python3
"""从归档区取回词条，供顺序推进到该字母段时复用。

背景：早期 B 词表是「按词频挑词再排字母序」，收词不全。改成按牛津高阶
逐条收全后，那些超前写好的词（ae 及之后）被移到 wordlists/pending/，
等顺序推进到时再取回 —— 免得重写，也免得同一份词表里两种收词密度并存。

用法: python3 scripts/pull-pending.py aerial aerobic aesthetic
     不带参数则列出归档区还剩哪些词。
     --prune 清掉已经进入 wordlists/B 的条目。
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
        print(f"\n（取出 {len(got)} 条；归档区不动 —— 等它们真的进了 wordlists/B\n"
              f"  再跑 --prune 清理。曾经「取出即删除」，结果取出的内容被临时文件\n"
              f"  覆盖后 17 条词就没了，只能翻 git 找回。）", file=sys.stderr)
    return 0 if got else 1

def prune():
    """把已经真正进入 wordlists/B 的条目从归档区删掉。"""
    import glob
    mine = set()
    for f in glob.glob('wordlists/B-[0-9]*.txt'):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            if b.strip(): mine.add(b.strip().split('\n')[0].strip().lower())
    bs = blocks()
    rest = [b for b in bs if b.split('\n')[0].strip().lower() not in mine]
    gone = len(bs) - len(rest)
    io.open(P, 'w', encoding='utf-8').write("\n\n".join(rest) + ("\n" if rest else ""))
    print(f"清理 {gone} 条（已在主表中），归档区剩 {len(rest)} 条")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--prune':
        sys.exit(prune())
    sys.exit(main(sys.argv[1:]))
