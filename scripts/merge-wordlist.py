#!/usr/bin/env python3
"""把分批词表按编号顺序合并成一个大文件，便于一次性传到 iPad。
顺序即文件名顺序 —— A 的词表按词频排序，顺序错了组的内容就和「由简到难」错位。
用法: python3 scripts/merge-wordlist.py A 5000
"""
import sys, glob, io, os, re

def main(prefix, size):
    files = sorted(glob.glob(f"wordlists/{prefix}-[0-9]*-[0-9]*.txt"))
    files = [f for f in files if re.search(r'-\d+-\d+\.txt$', f)]
    if not files: print("没有找到分批文件"); return 1
    entries, gaps, expect = [], [], 1
    for f in files:
        m = re.search(r'-(\d+)-(\d+)\.txt$', f)
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo != expect: gaps.append(f"{os.path.basename(f)} 从 {lo} 开始，但上一批到 {expect-1}")
        blocks = [b.strip() for b in io.open(f, encoding='utf-8').read().split('\n\n') if b.strip()]
        if len(blocks) != hi - lo + 1:
            gaps.append(f"{os.path.basename(f)} 文件名说 {hi-lo+1} 条，实际 {len(blocks)} 条")
        entries += blocks
        expect = hi + 1
        print(f"  {os.path.basename(f):<24} {len(blocks):>5} 条  (#{lo}-{hi})")
    if gaps:
        print("\n❌ 编号不连续，合并中止：")
        for g in gaps: print("  " + g)
        return 1
    # B 是按牛津高阶字母顺序编排的，但补收的词会在后面的批次里生成，
    # 光按文件名顺序拼会让后补的 a 段词排到 b 段词后面。
    # 所以 B 在合并时按词条首行重新排字母序 —— 生成顺序就不再要紧。
    # A 不能这么做：A 是按词频由简到难排的，排字母序会毁掉难度梯度。
    if prefix == 'B':
        # 词典式排序：忽略空格和连字符，让 ad hoc / able-bodied 归到正确位置
        entries.sort(key=lambda b: b.split('\n')[0].strip().lower().replace(' ','').replace('-',''))
        print("\n  B：已按字母顺序重排")
    n = len(entries)
    made = []
    for i in range(0, n, size):
        chunk = entries[i:i+size]
        out = f"wordlists/{prefix}-merged-{i+1:04d}-{i+len(chunk):04d}.txt"
        io.open(out, 'w', encoding='utf-8').write("\n\n".join(chunk) + "\n")
        made.append((out, len(chunk), os.path.getsize(out)))
    print(f"\n合并 {n} 条 →")
    for o, c, b in made:
        print(f"  {os.path.basename(o):<30} {c:>5} 条  {b/1024/1024:.2f} MB")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2: print("用法: merge-wordlist.py <前缀> [每份词数]"); sys.exit(2)
    sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5000))
