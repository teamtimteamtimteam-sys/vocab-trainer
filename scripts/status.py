#!/usr/bin/env python3
"""一屏读完当前状态。新会话（或 /clear 之后）第一件事就跑它。

为什么要有这个：进度如果写死在文档里，很快就会和实际脱节。
这个脚本全部从 wordlists/ 现算，不会过期。
"""
import io, glob, sys, string
sys.path.insert(0, 'scripts')
from wordkey import sort_key, prefix

def entries(pat):
    out = []
    for f in sorted(glob.glob(pat)):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            if b.strip(): out.append(b.strip().split('\n')[0].strip())
    return out

def main():
    A = entries('wordlists/A-[0-9]*.txt')
    B = entries('wordlists/B-[0-9]*.txt')
    merged = sorted(glob.glob('wordlists/A-merged-*.txt')) + sorted(glob.glob('wordlists/B-merged-*.txt'))
    pend = entries('wordlists/pending/B-pending.txt')

    print("=" * 66)
    print("A 词表（初学者，按词频由简到难，绝不排字母序）")
    print(f"  {len(A)} 条；已交付合并文件：{', '.join(f.split('/')[-1] for f in merged) or '无'}")
    print(f"  目标 5000，下一批从第 {len(A)+1} 个词起，每批约 45 条、每条 3 个义项")
    print()
    print("B 词表（牛津高阶第 10 版全量收录，按词典序逐条收全）")
    print(f"  {len(B)} 条；归档区（早期超前写的词，到相应字母段取回复用）{len(pend)} 条")
    if B:
        print(f"  最末词条：{B[-1]}")
    done, todo = [], []
    for L in sorted({prefix(x, 1) for x in B}):
        for ch in string.ascii_lowercase:
            p = L + ch
            n = len([x for x in B if prefix(x) == p])
            (done if n else todo).append((p, n))
    print("  已有词条的双字母段：" + "  ".join(f"{p}{n}" for p, n in done))
    if todo:
        print(f"  尚未开始：{' '.join(p for p, _ in todo[:14])}{' …' if len(todo) > 14 else ''}")
    print()
    print("每批必过的闸门（scripts/check-wordlist.py，pre-commit 钩子会拦）")
    print("  A：批均义项 ≥2.10、等式 ≥2.13、字符 ≥144（基线的 92%）")
    print("  B：每条至少 2 个义项且必须有「核心：」块；")
    print("     批均等式 ≥2.13、讲解行/义项 ≥1.50")
    print("  两者共有：编号连续、译文无中英混杂、无异体字符、跨批不重复")
    print()
    print("每收完一个字母段的固定动作")
    print("  0. python3 scripts/coverage.py a         对照牛津高阶词头清单查缺 ★最重要")
    print("  1. python3 scripts/audit-prefix.py a      查双字母段有没有整段漏掉")
    print("  2. python3 scripts/resplit-b.py           按词典序重排并均匀分块")
    print("  3. python3 scripts/pull-pending.py --prune  清理已收录的归档条目")
    print("  4. 核对归档区里是否还有属于「已收全」段的词 —— 那就是遗漏")
    print("=" * 66)
    return 0

if __name__ == "__main__":
    sys.exit(main())
