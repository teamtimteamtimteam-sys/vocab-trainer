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
        # 混进异体字符（韩文、日文假名、西里尔等）几乎都是输入法手误，
        # 肉眼极难发现 —— log = 원木 这种就是这么混进来的。
        allowed = re.compile(
            r'[\u4e00-\u9fff\u3400-\u4dbf'                 # 汉字
            r'A-Za-z0-9'                                     # 拉丁字母数字
            r'\u00c0-\u024f'                                # 带变音的拉丁字母
            r'\u0250-\u02af\u02b0-\u02ff'                  # 国际音标（讲解里到处在用）
            r'\u3000-\u303f\uff00-\uffef'                  # 中日文标点、全角
            r'\u2010-\u203b\u2460-\u24ff\u2190-\u21ff'    # 破折号、序号、箭头
            r'\u2713\u2714\u2717\u2718\u2022\u00b7\u00b0' # 勾叉、项目符号、度
            r'\u0370-\u03ff'                                 # 希腊字母（音标 θ ð 等）
            r'\u2248\u2260\u2264\u2265\u00d7\u00f7'          # 约等于、不等号、乘除
            r'\s' + re.escape("=+-*/%<>()[]{}.,;:!?'\"&#@~$^_|\\`") + r']')
        odd = sorted(set(c for l in (t for _, t in b['lines']) for c in l if not allowed.match(c)))
        if odd:
            e['issues'].append("混入异体字符：" + " ".join("%s(U+%04X)" % (c, ord(c)) for c in odd[:6]))
        if not e['senses']: e['issues'].append("没有 ①②③ 例句")
        # 编号必须从 ① 开始且连续 —— 漏一个 ② 在 app 里会直接显示成 ①③
        nums = [NUMS.index(t[0]) for _, t in b['lines'][1:] if t[0] in NUMS]
        if nums and nums != list(range(len(nums))):
            e['issues'].append("例句编号不连续：" + "".join(NUMS[i] for i in nums))
        for i, s in enumerate(e['senses']):
            if not s['tr']: e['issues'].append("例句 %s 缺少 = 中文翻译" % NUMS[i])
            if not re.search(r'[A-Za-z]', s['ex']): e['issues'].append("例句 %s 里没有英文" % NUMS[i])
            # 译文行混进英文单词多半是手误（盯着英文句子打中文时最容易犯）。
            # 正当情况只有一种：译文在讨论某个英文词本身 —— 那种必须加引号，
            # 引号内的词跳过，其余一律算手误。
            tr = re.sub(r'[\"“”「」][^\"“”「」]*[\"“”「」]', ' ', s['tr'])
            stray = [w for w in re.findall(r'[A-Za-z]{3,}', tr) if not w[0].isupper()]
            if stray: e['issues'].append("例句 %s 的中文译文里混入英文：%s" % (NUMS[i], "、".join(stray)))
            # 反方向同样要查：英文例句里混进汉字（打字时中英输入法没切）。
            # 我写 "Supply and demand決定价格" 时就犯过，靠肉眼才发现。
            cjk = re.findall(r'[\u4e00-\u9fff]+', s['ex'])
            if cjk: e['issues'].append("例句 %s 的英文里混入中文：%s" % (NUMS[i], "、".join(cjk)))
        out.append(e)
    return out

# 基线取自第一批人工验收过的 A-0001-0050
BASE_SE, BASE_EQ, BASE_CH = 2.28, 2.32, 156

def main(paths):
    # 查重按文件名前缀分组：A 和 B 是两个人各自的词表，
    # 同一个词在两边各出现一次是正常的，不该判为重复。
    seen, dupes, fail, allw = {}, [], False, []
    print("%-26s%5s%8s%8s%8s%6s%6s" % ("文件", "词条", "均义项", "均等式", "均字符", "问题", "重复"))
    print("-" * 70)
    for p in sorted(paths):
        es = parse(p)
        if not es:
            print("%-26s  空文件" % os.path.basename(p)); fail = True; continue
        bad = [e for e in es if e['issues']]
        d = []
        prefix = os.path.basename(p).split('-')[0]
        for e in es:
            k = (prefix, e['word'].lower())
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
