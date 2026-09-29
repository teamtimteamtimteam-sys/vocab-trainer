#!/usr/bin/env python3
"""把分批词表按编号顺序合并成一个大文件，便于一次性传到 iPad。
顺序即文件名顺序 —— A 的词表按词频排序，顺序错了组的内容就和「由简到难」错位。
用法: python3 scripts/merge-wordlist.py A 5000
"""
import sys, glob, io, os, re
sys.path.insert(0, 'scripts')
from wordkey import sort_key, numsort

LEDGER = 'reference/B-delivered.txt'

def read_ledger():
    """交付台账：{份号: [词头...]}。已交付的份内容构成不再变。"""
    led = {}
    if not os.path.exists(LEDGER): return led
    for line in io.open(LEDGER, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.startswith('#'): continue
        k, h = line.split('\t', 1)
        led.setdefault(int(k), []).append(h)
    return led

def merge_b_by_ledger(entries, size):
    """B 按交付台账合并（2026-09-29 用户要求改的）。

    原来是整表排序后按位置每 2500 条一切。后来回头补写前面字母段的词
    （Gaelic、Gaia…七条补在 g 段），第四份的边界就往前挪了七条，
    用户导入第五份时 app 报「7 个重复」，而补写的七条 app 里根本没有。
    位置切法下，已交付的文件会随着回头补词不断变 —— 导进 iPad 的东西对不上。

    现在：台账里登记过的份，词头构成固定（正文照当前最新版输出）；
    没交付过的词条按词典序排，从下一份起每 2500 条一份。满 2500 的新份
    自动登记进台账（视为可交付）；不满的尾巴不登记，下次合并还会变。
    每份内部仍按 wordkey.sort_key 排序；回头补写的词进下一份，不改旧份。"""
    body = {}
    for b in entries:
        h = b.split('\n')[0].strip()
        if h in body:
            print(f"❌ 分批文件里词头重复：{h}"); return None
        body[h] = b
    led = read_ledger()
    delivered = set()
    made = []
    k = 0
    for k in sorted(led):
        heads = [h for h in led[k] if h in body]
        gone = [h for h in led[k] if h not in body]
        if gone:
            print(f"  第 {k} 份：{len(gone)} 条已不在词表里（改名或并入别条）：{'、'.join(gone[:10])}")
        heads.sort(key=sort_key)
        delivered.update(led[k])
        lo = (k - 1) * size + 1
        out = f"wordlists/B-merged-{lo:04d}-{lo+len(heads)-1:04d}.txt"
        io.open(out, 'w', encoding='utf-8').write("\n\n".join(body[h] for h in heads) + "\n")
        made.append((out, len(heads), os.path.getsize(out)))
    rest = sorted((h for h in body if h not in delivered), key=sort_key)
    new_frozen = []
    for i in range(0, len(rest), size):
        k += 1
        chunk = rest[i:i+size]
        lo = (k - 1) * size + 1
        out = f"wordlists/B-merged-{lo:04d}-{lo+len(chunk)-1:04d}.txt"
        io.open(out, 'w', encoding='utf-8').write("\n\n".join(body[h] for h in chunk) + "\n")
        made.append((out, len(chunk), os.path.getsize(out)))
        if len(chunk) == size:
            new_frozen.append((k, chunk))
    if new_frozen:
        with io.open(LEDGER, 'a', encoding='utf-8') as fh:
            for kk, chunk in new_frozen:
                for h in chunk: fh.write(f"{kk}\t{h}\n")
                print(f"  第 {kk} 份满 {size} 条，已登记进交付台账")
    print(f"\n  B：按交付台账合并（已交付 {len(led)} 份不变，未交付 {len(rest)} 条按词典序接在后面）")
    return made

def main(prefix, size):
    files = numsort(glob.glob(f"wordlists/{prefix}-[0-9]*-[0-9]*.txt"))
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
        made = merge_b_by_ledger(entries, size)
        if made is None: return 1
        n = len(entries)
    else:
        n = len(entries)
        made = []
        for i in range(0, n, size):
            chunk = entries[i:i+size]
            out = f"wordlists/{prefix}-merged-{i+1:04d}-{i+len(chunk):04d}.txt"
            io.open(out, 'w', encoding='utf-8').write("\n\n".join(chunk) + "\n")
            made.append((out, len(chunk), os.path.getsize(out)))
    # 上一次合并留下的旧尾巴要清掉 —— 尾部文件的名字每次都变
    # （B-merged-5001-5933 → …-5955），不删就会越积越多。
    # 2026-09-08 之前正是这么攒下六份 5001-58xx 的残骸；那天新加的
    # check-merged.py 一上来就把它们当成「同一条词条出现两次」报了出来，
    # 因为它是照 wordlists/<前缀>-merged-*.txt 全量读的。
    kept = {o for o, _, _ in made}
    for old in numsort(glob.glob(f"wordlists/{prefix}-merged-*.txt")):
        if old not in kept:
            os.remove(old)
            print(f"  删掉上一轮的旧文件 {os.path.basename(old)}")
    print(f"\n合并 {n} 条 →")
    for o, c, b in made:
        print(f"  {os.path.basename(o):<30} {c:>5} 条  {b/1024/1024:.2f} MB")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2: print("用法: merge-wordlist.py <前缀> [每份词数]"); sys.exit(2)
    sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5000))
