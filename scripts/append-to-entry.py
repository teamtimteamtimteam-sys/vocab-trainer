#!/usr/bin/env python3
"""把并入内容追加到已有词条末尾（每个字母段收尾时都要做的动作）。

为什么需要它：派生词和多词条目不单列，要写进词根条里并补例句。
用 patch-entries.py 得把整条重抄一遍，既费事又容易抄漏原有内容
（重写 all 时就丢过一个并入的拼法）。这个脚本只追加，不动原文。

补丁文件格式跟词表一样：首行是要追加到的词头，其余是追加的内容。
例句编号随便写，追加完跑 renumber.py 自动补号。

用法: python3 scripts/append-to-entry.py <补丁文件>
"""
import io, glob, sys

def main(patch):
    add = {}
    for b in io.open(patch, encoding='utf-8').read().split('\n\n'):
        b = b.strip()
        if not b: continue
        L = b.split('\n')
        w = L[0].strip()
        if w in add: print(f"补丁里 {w} 出现两次"); return 1
        add[w] = '\n'.join(L[1:]).strip()
    hit = {w: 0 for w in add}
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        src = io.open(f, encoding='utf-8').read()
        out, changed = [], False
        for b in src.split('\n\n'):
            s = b.strip()
            if not s: continue
            w = s.split('\n')[0].strip()
            if w in add:
                hit[w] += 1; out.append(s + '\n' + add[w]); changed = True
            else:
                out.append(s)
        if changed:
            io.open(f, 'w', encoding='utf-8').write("\n\n".join(out) + "\n")
    miss = [w for w, n in hit.items() if n == 0]
    dup  = [w for w, n in hit.items() if n > 1]
    if miss: print("词表里没有这些词头：" + " ".join(miss))
    if dup:  print("词表里重复出现：" + " ".join(dup))
    print(f"追加到 {sum(1 for n in hit.values() if n == 1)} 条")
    return 1 if miss or dup else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
