#!/usr/bin/env python3
"""拿 reference/ 里的牛津高阶词头清单核对 B 的收词完整性。

这个脚本存在的理由：在此之前每个字母段的目标清单都是我凭记忆列的，
清单本身就短，跑差集只能证明「我列的都收了」，不能证明「我列全了」。
结果反复出现「宣布收全、实际漏三成」，四次都是用户发现的。
有了词头文件，完整性就从「靠记性」变成机器检查。

按用户裁定的收词边界过滤清单：
  ✗ 词缀条目（以 - 开头或结尾）：a- aero- Anglo- ante-
  ✗ 全大写缩写：AA AAA ABC AARP
  ✓ 其余保留：连字符复合词、多词条目、外来短语
清单里同一条目常有空格版和连字符版两份（abide by / abide-by），
按 wordkey 归一化后自动合并。

用法:
  python3 scripts/coverage.py a          某个字母的分段报告
  python3 scripts/coverage.py a ab ac    只看这几个双字母段的缺词
  python3 scripts/coverage.py --names a  另列首字母大写的条目（人名地名等）
"""
import sys, io, csv, glob, os, string
sys.path.insert(0, 'scripts')
from wordkey import sort_key, prefix

def load_reference():
    """读 reference/ 下的 csv 与 txt，返回过滤去重后的 {归一化键: 原词}。"""
    words = []
    for f in sorted(glob.glob('reference/*.csv')):
        with io.open(f, encoding='utf-8-sig', errors='replace') as fh:
            rows = list(csv.reader(fh))
        if not rows: continue
        head = [c.strip().lower() for c in rows[0]]
        col = next((i for i, c in enumerate(head)
                    if c in ('headword', 'word', 'entry', 'term')), 0)
        start = 1 if any(c in ('headword', 'word', 'entry', 'term') for c in head) else 0
        words += [r[col].strip() for r in rows[start:] if len(r) > col and r[col].strip()]
    for f in sorted(glob.glob('reference/*.txt')):
        words += [l.strip() for l in io.open(f, encoding='utf-8', errors='replace')
                  if l.strip() and not l.startswith('#')]

    out = {}
    for w in words:
        if w.startswith('-') or w.endswith('-'):      # 词缀条目，不收
            continue
        bare = w.replace('.', '').replace('-', '').replace(' ', '')
        if len(bare) > 1 and bare.isupper():          # 全大写缩写，不收
            continue
        k = sort_key(w)
        if not k: continue
        # 同一条目的多种写法，保留带空格那版（更接近词典写法）
        if k not in out or (' ' in w and ' ' not in out[k]):
            out[k] = w
    return out

def collected():
    got = {}
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            if b.strip():
                w = b.strip().split('\n')[0].strip()
                got[sort_key(w)] = w
    return got

def main(argv):
    show_names = '--names' in argv
    argv = [a for a in argv if a != '--names']
    ref, got = load_reference(), collected()
    if not ref:
        print("reference/ 里没找到词头文件"); return 2

    targets = argv or sorted({p[0] for p in ref if p})
    grand_ref = grand_got = 0
    for t in targets:
        sel = {k: v for k, v in ref.items() if prefix(v, len(t)) == t or (len(t) == 1 and k[0][:1] == t)}
        if not sel: continue
        missing = {k: v for k, v in sel.items() if k not in got}
        names = [v for v in missing.values() if v[:1].isupper()]
        grand_ref += len(sel); grand_got += len(sel) - len(missing)
        pct = (len(sel) - len(missing)) * 100 // len(sel)
        print(f"\n{t}- 段：清单 {len(sel)} 条，已收 {len(sel)-len(missing)} 条（{pct}%），缺 {len(missing)} 条")
        if len(t) == 1:   # 单字母时按双字母段细分
            for ch in string.ascii_lowercase:
                p = t + ch
                s2 = {k: v for k, v in sel.items() if prefix(v) == p}
                if not s2: continue
                m2 = [v for k, v in s2.items() if k not in got]
                flag = "  ← 缺" if m2 else ""
                print(f"    {p}  清单 {len(s2):4}  已收 {len(s2)-len(m2):4}  缺 {len(m2):4}{flag}")
        else:
            body = [v for v in missing.values() if not v[:1].isupper()]
            if body: print("  缺（普通词）：" + " ".join(sorted(body, key=sort_key)))
            if names: print(f"  缺（首字母大写，多为人名地名商标，待裁定）{len(names)} 条：" + " ".join(sorted(names)[:20]))
        if len(t) == 1 and names:
            print(f"  其中首字母大写 {len(names)} 条（人名地名商标等，待裁定是否收）")
        if show_names and names:
            print("  大写条目：" + " ".join(sorted(names)))
    if len(targets) > 1 or len(targets[0]) == 1:
        print(f"\n合计：清单 {grand_ref} 条，已收 {grand_got} 条（{grand_got*100//max(grand_ref,1)}%）")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
