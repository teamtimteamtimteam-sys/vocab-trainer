#!/usr/bin/env python3
"""按词头整条替换 B 词表里的词条。

为什么需要它：补讲解、补义项要改的是散落在 95 个批次文件里的单条词条，
用 sed 改容易伤到同前缀的别的词。这个脚本按词头精确匹配，
找不到或找到多条都报错退出，不做部分替换。

用法: python3 scripts/patch-entries.py <补丁文件>
补丁文件的格式跟词表一样：一条一段，段间空行，首行是词头。
"""
import io, glob, sys

def main(patch):
    blocks = [b.strip() for b in io.open(patch, encoding='utf-8').read().split('\n\n') if b.strip()]
    new = {}
    for b in blocks:
        w = b.split('\n')[0].strip()
        if w in new: print(f"补丁里 {w} 出现两次"); return 1
        new[w] = b
    hit = {w: 0 for w in new}
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        src = io.open(f, encoding='utf-8').read()
        out, changed = [], False
        for b in src.split('\n\n'):
            s = b.strip()
            if not s: continue
            w = s.split('\n')[0].strip()
            if w in new:
                hit[w] += 1; out.append(new[w]); changed = True
            else:
                out.append(s)
        if changed:
            io.open(f, 'w', encoding='utf-8').write("\n\n".join(out) + "\n")
    miss = [w for w, n in hit.items() if n == 0]
    dup  = [w for w, n in hit.items() if n > 1]
    if miss: print("词表里没有这些词头：" + " ".join(miss))
    if dup:  print("词表里重复出现：" + " ".join(dup))
    print(f"替换 {sum(1 for n in hit.values() if n == 1)} 条")
    return 1 if miss or dup else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
