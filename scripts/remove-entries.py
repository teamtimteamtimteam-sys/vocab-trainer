#!/usr/bin/env python3
"""按词头从 B 词表里删除词条（收词边界的裁定改了才用）。

为什么需要它：用户改口把某一类词划出收词范围时，这些词往往已经写好
并入了正表。手工删容易删错相邻词条，也容易忘了同步 exclude.txt ——
不同步的话 coverage 会把它们重新报成缺词，下次又写一遍。

用法: python3 scripts/remove-entries.py <词头...> [--why 理由]
删完会把词头连同理由追加进 reference/exclude.txt。
"""
import io, glob, sys

def main(argv):
    why = ""
    if '--why' in argv:
        i = argv.index('--why'); why = " ".join(argv[i+1:]); argv = argv[:i]
    words = [a for a in argv if not a.startswith('-')]
    if not words:
        print("没给词头"); return 1
    left = set(words)
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        src = io.open(f, encoding='utf-8').read()
        keep, dropped = [], False
        for b in src.split('\n\n'):
            s = b.strip()
            if not s: continue
            if s.split('\n')[0].strip() in left:
                left.discard(s.split('\n')[0].strip()); dropped = True
            else:
                keep.append(s)
        if dropped:
            io.open(f, 'w', encoding='utf-8').write("\n\n".join(keep) + "\n")
    gone = [w for w in words if w not in left]
    if left: print("词表里没找到：" + " ".join(sorted(left)))
    if gone:
        with io.open('reference/exclude.txt', 'a', encoding='utf-8') as fh:
            fh.write("\n")
            for w in gone:
                fh.write("%-12s # %s\n" % (w, why or "已裁定不收"))
        print("删除 %d 条，并记进 exclude.txt：%s" % (len(gone), " ".join(gone)))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
