#!/usr/bin/env python3
"""词表批次校验。跨批生成的真正风险是漂移和重复，这里用数字盯着，不靠感觉。
用法: python3 scripts/check-wordlist.py 'wordlists/A-*.txt'"""
import sys, re, io, glob, os

NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
EQ = re.compile(r"^([A-Za-z][A-Za-z0-9’'\-\s.]{0,44}?)\s*=\s*(.+)$")
WORD_OK = re.compile(r"^[A-Za-z][A-Za-z0-9’'\-. ]*$")

def parse(path):
    lines = io.open(path, encoding='utf-8').read().replace('\r\n', '\n').split('\n')
    blocks, cur = [], None
    for i, raw in enumerate(lines):
        t = raw.strip()
        if not t:
            if cur: blocks.append(cur); cur = None
            continue
        if not cur: cur = {'start': i + 1, 'lines': []}
        cur['lines'].append((i + 1, t))
    if cur: blocks.append(cur)
    out = []
    for b in blocks:
        e = {'word': b['lines'][0][1], 'line': b['start'], 'senses': [], 'eqs': 0, 'issues': [],
             'chars': sum(len(t) for _, t in b['lines'])}
        if not WORD_OK.match(e['word']) or len(e['word'].split()) > 4:
            e['issues'].append("首行不像单词：%r" % e['word'])
        sense = None
        for n, t in b['lines'][1:]:
            if t[0] in NUMS:
                sense = {'ex': t[1:].strip(), 'tr': ''}
                e['senses'].append(sense); continue
            if t.startswith('='):
                if sense and not sense['tr']: sense['tr'] = t[1:].strip()
                continue
            m = EQ.match(t)
            if m and re.search(r'[A-Za-z]', m.group(1)): e['eqs'] += 1
        if not e['senses']: e['issues'].append("没有 ①②③ 例句")
        # 编号必须从 ① 开始且连续 —— 漏一个 ② 在 app 里会直接显示成 ①③
        nums = [NUMS.index(t[0]) for _, t in b['lines'][1:] if t[0] in NUMS]
        if nums and nums != list(range(len(nums))):
            e['issues'].append("例句编号不连续：" + "".join(NUMS[i] for i in nums))
        for i, s in enumerate(e['senses']):
            if not s['tr']: e['issues'].append("例句 %s 缺少 = 中文翻译" % NUMS[i])
            if not re.search(r'[A-Za-z]', s['ex']): e['issues'].append("例句 %s 里没有英文" % NUMS[i])
            # 译文行混进英文单词几乎都是手误（专名和缩写除外）
            stray = re.findall(r'[A-Za-z]{3,}', s['tr'])
            stray = [w for w in stray if not w[0].isupper()]
            if stray: e['issues'].append("例句 %s 的中文译文里混入英文：%s" % (NUMS[i], "、".join(stray)))
        out.append(e)
    return out

# 基线取自第一批人工验收过的 A-0001-0050
BASE_SE, BASE_EQ, BASE_CH = 2.28, 2.32, 156

def main(paths):
    seen, dupes, fail, allw = {}, [], False, []
    print("%-26s%5s%8s%8s%8s%6s%6s" % ("文件", "词条", "均义项", "均等式", "均字符", "问题", "重复"))
    print("-" * 70)
    for p in sorted(paths):
        es = parse(p)
        if not es:
            print("%-26s  空文件" % os.path.basename(p)); fail = True; continue
        bad = [e for e in es if e['issues']]
        d = []
        for e in es:
            k = e['word'].lower()
            if k in seen: d.append((e['word'], seen[k])); dupes.append((e['word'], seen[k], p))
            else: seen[k] = os.path.basename(p)
        n = len(es)
        avg_se = sum(len(e['senses']) for e in es) / n
        avg_eq = sum(e['eqs'] for e in es) / n
        avg_ch = sum(e['chars'] for e in es) / n
        # 密度闸门：低于基线 8% 直接判失败，不靠肉眼盯
        flag = ""
        if avg_se < BASE_SE * 0.92 or avg_eq < BASE_EQ * 0.92 or avg_ch < BASE_CH * 0.92:
            flag = "  ← 密度低于基线，需补写"
            fail = True
        print("%-26s%5d%8.2f%8.2f%8.0f%6d%6d%s" % (
            os.path.basename(p), n, avg_se, avg_eq, avg_ch, len(bad), len(d), flag))
        for e in bad[:5]:
            for m in e['issues']:
                print("    第 %d 行  %s: %s" % (e['line'], e['word'], m)); fail = True
        allw += es
    print("-" * 70)
    if allw:
        n = len(allw)
        se = [len(e['senses']) for e in allw]; ch = [e['chars'] for e in allw]
        print("合计 %d 词条   义项 %.2f (min %d / max %d)   字符 %.0f (min %d / max %d)" % (
            n, sum(se)/n, min(se), max(se), sum(ch)/n, min(ch), max(ch)))
    if dupes:
        fail = True
        print("\n跨批重复 %d 个：" % len(dupes))
        for w, first, p in dupes[:20]:
            print("  %s  已出现在 %s，又出现在 %s" % (w, first, os.path.basename(p)))
    print("\n" + ("❌ 有问题，需要重写" if fail else "✅ 全部通过"))
    return 1 if fail else 0

if __name__ == "__main__":
    ps = []
    for a in sys.argv[1:]: ps += glob.glob(a)
    if not ps: print("用法: check-wordlist.py '<glob>'"); sys.exit(2)
    sys.exit(main(ps))
