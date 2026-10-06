#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音标行：每条词条的词头下面单占一行，以「/」开头（用户 2026-10-06 定：只标英式）。

    mug
    /mʌɡ/
    核心：……

多音词写成几段，每段后面可以用全角括号注明：
    /ˈrekɔːd/（名）/rɪˈkɔːd/（动）

用法：
    python3 scripts/ipa.py status                # 两张表各有多少条有音标
    python3 scripts/ipa.py fill                  # 用 data/pron 里的 Britfone 自动填（只填单词、读法无歧义的）
    python3 scripts/ipa.py missing [前缀] [-n N]  # 列出还没有音标的词头
    python3 scripts/ipa.py draft [A|B] [前缀] [-n N] # 给缺音标的词头出草稿（机器合成的底子，必须逐条校对）
    python3 scripts/ipa.py set 文件.tsv           # 手写的批量写入：每行「词头<TAB>音标行」
    python3 scripts/ipa.py check [词头...]        # 闸门：全表音标行格式合法；点名的词头必须有音标

来源：data/pron/britfone.main.3.0.1.csv（Britfone，MIT 许可）。它的记法跟学习词典不一样，
这里转成学习词典通行的写法：ɹ→r、ɛ→e、ɐ→ʌ、g→ɡ；重音符号从元音前挪到音节开头；
单音节词不标重音；主重音之后的次重音不标；拼写以 r / re 结尾而读音以元音收尾的加 (r)。
非重读的 ə 一律保留（写 /ˈbɒtəl/ 不写 /ˈbɒtl/）—— 自动删容易删错，保留是合法的宽式记法。
"""
import sys, io, re, glob, os, collections

BRITFONE = 'data/pron/britfone.main.3.0.1.csv'
NUMS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴⓵⓶⓷⓸⓹⓺⓻⓼⓽⓾"

# 音标行里允许出现的符号：英式学习词典的那一套，外加外来词用的 x（loch）与鼻化符
IPA_CHARS = "abdefhijklmnprstuvwzxæðŋɑɒɔəɜɪʃʊʌʒθɡːˈˌ() ̃"
SEG = r'/[' + re.escape(IPA_CHARS) + r']+/(?:（[一-鿿、，]{1,12}）)?'
LINE_RE = re.compile(r'^(?:' + SEG + r')+$')

def is_ipa(line):
    return line.startswith('/')

def valid(line):
    return bool(LINE_RE.match(line))

# ------------------------------------------------------------ 读写词表
def files():
    return sorted(glob.glob('wordlists/A-[0-9]*.txt') + glob.glob('wordlists/B-[0-9]*.txt'))

def blocks(path):
    return [b for b in io.open(path, encoding='utf-8').read().replace('\r\n', '\n').split('\n\n') if b.strip()]

def get_ipa(block):
    L = block.strip('\n').split('\n')
    for l in L[1:]:
        if l and l[0] in NUMS: break
        if is_ipa(l): return l
    return None

def put_ipa(block, line):
    L = block.strip('\n').split('\n')
    L = [L[0]] + [l for i, l in enumerate(L[1:]) if not (is_ipa(l) and not any(x and x[0] in NUMS for x in L[1:i+1]))]
    return '\n'.join([L[0], line] + L[1:])

def rewrite(mapping, overwrite=False):
    """mapping: {词头: 音标行}。返回写入条数。"""
    n = 0
    for f in files():
        raw = io.open(f, encoding='utf-8').read()
        bs = [b.strip('\n') for b in raw.replace('\r\n', '\n').split('\n\n') if b.strip()]
        changed = False
        for i, b in enumerate(bs):
            head = b.split('\n')[0].strip()
            if head in mapping and (overwrite or get_ipa(b) is None):
                nb = put_ipa(b, mapping[head])
                if nb != b: bs[i] = nb; changed = True; n += 1
        if changed:
            io.open(f, 'w', encoding='utf-8').write('\n\n'.join(bs) + '\n')
    return n

# ------------------------------------------------------------ Britfone → 学习词典记法
MAP = {'ɹ': 'r', 'ɛ': 'e', 'ɛə': 'eə', 'ɐ': 'ʌ', 'g': 'ɡ'}
VOWELS = {'aɪ', 'aʊ', 'eɪ', 'i', 'iː', 'uː', 'æ', 'ɑː', 'ɒ', 'ɔɪ', 'ɔː', 'ə', 'əʊ', 'e', 'eə', 'ɜː', 'ɪ', 'ɪə', 'ʊ', 'ʊə', 'ʌ', 'u', 'iə', 'uə'}
R_VOWELS = {'ə', 'ɑː', 'ɔː', 'ɜː', 'ɪə', 'eə', 'ʊə', 'iə', 'uə'}
ONSETS = set("""p b t d k ɡ f v θ ð s z ʃ ʒ h m n l r j w tʃ dʒ
pl pr pj bl br bj tr tw tj dr dw dj kl kr kw kj ɡl ɡr ɡw fl fr fj vj θr θw θj
sl sw sj sp st sk sm sn sf ʃr hj mj nj lj zj
spl spr spj str stj skr skw skj""".split())

def load_britfone():
    d = collections.defaultdict(list)
    for l in io.open(BRITFONE, encoding='utf-8'):
        l = l.rstrip('\n')
        if ', ' not in l: continue
        w, p = l.split(', ', 1)
        d[re.sub(r'\(\d+\)$', '', w).lower()].append(p.split())
    return d

def convert(phones, spelling):
    """Britfone 的音素列表 → '/…/' 里面的字符串（不带斜杠）。"""
    ph, st = [], []                       # 音素、各自的重音（'' / 'ˈ' / 'ˌ'）
    for p in phones:
        s = p[0] if p[0] in 'ˈˌ' else ''
        p = p.lstrip('ˈˌ')
        ph.append(MAP.get(p, p)); st.append(s)
    vow = [i for i, p in enumerate(ph) if p in VOWELS]
    # 非重读的 ɪə / ʊə 与元音前的 ʊ，学习词典写成 iə / uə / u（area /ˈeəriə/、actually /ˈæktʃuəli/）
    if len(vow) > 1:
        for i, p in enumerate(ph):
            if st[i]: continue
            if p == 'ɪə': ph[i] = 'iə'
            elif p == 'ʊə': ph[i] = 'uə'
            elif p == 'ʊ' and i + 1 < len(ph) and ph[i+1] in VOWELS: ph[i] = 'u'
    # 主重音之后的次重音不标；单音节词不标重音
    if 'ˈ' in st:
        k = st.index('ˈ')
        st = [s if (i <= k or s != 'ˌ') else '' for i, s in enumerate(st)]
    if len(vow) <= 1:
        st = [''] * len(st)
    # 重音符号挪到音节开头：往前收尽量长的合法辅音丛
    marks = {}
    low = spelling.lower()
    for i, s in enumerate(st):
        if not s: continue
        j = i - 1
        while j >= 0 and ph[j] not in VOWELS: j -= 1
        cons = ph[j+1:i]
        if j < 0:
            pos = 0
        else:
            pos = i
            for k in range(len(cons) + 1):
                if k == len(cons) or ''.join(cons[k:]) in ONSETS:
                    pos = j + 1 + k; break
            # dis- / mis- 前缀自带次重音、或后面是 l 时，音节界在 s 后面（dɪsˈlaɪk、ˌmɪsˈpleɪs）
            if low[:3] in ('dis', 'mis') and j == 1 and cons[:1] == ['s'] and pos == j + 1 and len(cons) > 1:
                if st[j] == 'ˌ' or cons[1] == 'l':
                    pos = j + 2
        marks[pos] = s
    out = ''.join(marks.get(i, '') + p for i, p in enumerate(ph))
    # 连读的 r
    if ph and ph[-1] in R_VOWELS:
        if low.endswith('r') or (low.endswith('re') and (len(ph) < 2 or ph[-2] != 'r')):
            out += '(r)'
    return out

def stress_shape(phones):
    v = [p for p in phones if p.lstrip('ˈˌ') in VOWELS or MAP.get(p.lstrip('ˈˌ')) in VOWELS]
    return tuple(i for i, p in enumerate(v) if p.startswith('ˈ'))

def lookup(word, bf):
    """返回 (音标行或 None, 原因)。只处理单个词、各读法重音位置一致的。"""
    k = word.lower()
    if not re.match(r"^[a-z]+$", k): return None, '非单词'
    if k not in bf: return None, '词典里没有'
    vs = bf[k]
    if len(set(stress_shape(v) for v in vs)) > 1: return None, '重音有两读'
    return '/' + convert(vs[0], word) + '/', ''

# ------------------------------------------------------------ 草稿：ipa-dict 的 en_UK
# 这份文件是语音合成软件按规则生成的，不是人编的词典：拿它跟 Britfone 对，
# 12996 个共有的词里 12% 读法不同，其中相当一部分是它错（conquer 读成 nk、muse 读成 s、
# apparatchik 重音错位、gymkhana 冒出 kh）。**所以它只用来出草稿，草稿必须逐条看过、
# 改过，再记进 manual.tsv —— 绝不直接写进词表。**
DRAFT = 'data/pron/ipa-dict.en_UK.txt'
_PH = sorted(['aɪə', 'aʊə', 'aɪ', 'aʊ', 'eɪ', 'iː', 'uː', 'ɑː', 'ɔɪ', 'ɔː', 'əʊ', 'ɛə', 'eə', 'ɜː', 'ɪə', 'ʊə', 'tʃ', 'dʒ',
              'b', 'd', 'f', 'ɡ', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 's', 't', 'v', 'w', 'z', 'æ', 'ð', 'ŋ', 'ɐ', 'ɒ',
              'ə', 'ɛ', 'e', 'ɪ', 'ɹ', 'r', 'ʃ', 'ʊ', 'ʒ', 'θ', 'ʌ', 'i', 'u', 'a', 'x', 'o'], key=len, reverse=True)

def _tok(s):
    out, i, st = [], 0, ''
    while i < len(s):
        if s[i] in 'ˈˌ': st = s[i]; i += 1; continue
        for p in _PH:
            if s.startswith(p, i):
                if p in ('aɪə', 'aʊə'): out.append(st + p[:2]); out.append('ə')
                else: out.append(st + p)
                st = ''; i += len(p); break
        else:
            return None
    return out

def load_draft():
    d = {}
    for l in io.open(DRAFT, encoding='utf-8'):
        if '\t' not in l: continue
        w, p = l.rstrip('\n').split('\t', 1)
        d[w.lower()] = p.split(',')[0].strip().strip('/')
    return d

def draft_one(word, d):
    k = word.lower()
    if k not in d: return None
    t = _tok(d[k])
    if t is None: return None
    t = [x.replace('ɐ', 'ə') for x in t]
    for i in range(len(t) - 1):                       # n 在 k 前读 ŋ
        if t[i] == 'n' and t[i+1].lstrip('ˈˌ') == 'k': t[i] = 'ŋ'
        if t[i] == 'uː' and t[i+1].lstrip('ˈˌ') in VOWELS | {'ɛ', 'ɛə'}: t[i] = 'ʊ'   # 非重读的 uː 在元音前
    if len(t) > 2 and t[0] == 'ɛ' and t[1] in ('k', 'ɡ', 'g'): t[0] = 'ɪ'            # 非重读的 ex-
    for i in range(len(t) - 1):
        nxt = t[i+1].lstrip('ˈˌ')
        if t[i] == 'ɪ' and (nxt in VOWELS or nxt in ('ɛ', 'ɛə')): t[i] = 'i'              # 元音前的非重读 ɪ：abbreviation
    j = 0; u = []
    while j < len(t):                                                                   # 重读的 i 加 ə 是一个 ɪə：adherent
        if t[j] in ('ˈi', 'ˌi') and j + 1 < len(t) and t[j+1] == 'ə': u.append(t[j][0] + 'ɪə'); j += 2
        else: u.append(t[j]); j += 1
    t = u
    try:
        line = '/' + convert(t, word) + '/'
    except Exception:
        return None
    return line if valid(line) else None

def cmd_draft(args):
    n = 300; pref = ''; table = None
    it = iter(args)
    for a in it:
        if a == '-n': n = int(next(it))
        elif a in ('A', 'B'): table = a
        else: pref = a.lower()
    d = load_draft()
    ms = [h for t, h, ip in all_heads() if not ip and h.lower().startswith(pref) and (table is None or t == table)]
    for h in ms[:n]:
        parts = re.split(r'([ \-])', h)
        if len(parts) == 1:
            print('%s\t%s' % (h, draft_one(h, d) or '?'))
        else:   # 多词：各部分的草稿拼在一起，重音要人来定
            ds = [draft_one(x, d) if x not in ' -' else x for x in parts]
            print('%s\t%s' % (h, ' '.join((x or '?').strip('/') if x not in (' ', '-') else '' for x in ds).replace('  ', ' ') if all(ds) else '?'))
    print('# 草稿 %d 条（共缺 %d 条）。逐条看过、改过，再追加到 data/pron/manual.tsv' % (min(n, len(ms)), len(ms)), file=sys.stderr)

def draft_rows(args):
    n = 300; pref = ''; table = None
    it = iter(args)
    for a in it:
        if a == '-n': n = int(next(it))
        elif a in ('A', 'B'): table = a
        else: pref = a.lower()
    d = load_draft()
    ms = [h for t, h, ip in all_heads() if not ip and h.lower().startswith(pref) and (table is None or t == table)]
    rows = []
    for h in ms[:n]:
        rows.append((h, draft_one(h, d) if re.match(r'^[A-Za-z]+$', h) else None))
    return rows, len(ms)

def cmd_accept(args):
    """accept <改正文件> [A|B] [前缀] [-n N]：同一组草稿里，校对时没动的照收，动过的用改正文件里的。
    改正文件每行「词头<TAB>音标行」；草稿打「?」的词头必须在改正文件里，否则那一条留着不写。"""
    fix = {}
    for l in io.open(args[0], encoding='utf-8'):
        l = l.rstrip('\n')
        if l.strip() and not l.startswith('#'):
            w, ip = l.split('\t', 1); fix[w.strip()] = ip.strip()
    rows, total = draft_rows(args[1:])
    bad = [(w, ip) for w, ip in fix.items() if not valid(ip)]
    if bad:
        print("❌ 改正文件里 %d 行格式不合法：" % len(bad))
        for w, ip in bad[:30]: print("   %s\t%s" % (w, ip))
        return 1
    out, left = [], []
    for h, dr in rows:
        ip = fix.get(h, dr)
        if ip: out.append((h, ip))
        else: left.append(h)
    stray = [w for w in fix if w not in dict(rows)]
    with io.open('data/pron/manual.tsv', 'a', encoding='utf-8') as f:
        f.write("# 校对批次：%s —— 草稿照收 %d 条，改正或手写 %d 条\n" % (' '.join(args[1:]), len(out) - sum(1 for h, _ in out if h in fix), sum(1 for h, _ in out if h in fix)))
        for h, ip in out: f.write("%s\t%s\n" % (h, ip))
        for w in stray: f.write("%s\t%s\n" % (w, fix[w]))
    mapping = dict(out); mapping.update({w: fix[w] for w in stray})
    n = rewrite(mapping, overwrite=True)
    print("写入 %d 条；这一组里还没着落的 %d 条：%s" % (n, len(left), ' '.join(left[:40])))
    return 0

# ------------------------------------------------------------ 命令
def all_heads():
    out = []
    for f in files():
        t = os.path.basename(f)[0]
        for b in blocks(f):
            out.append((t, b.strip('\n').split('\n')[0].strip(), get_ipa(b)))
    return out

def cmd_status():
    H = all_heads()
    for t in 'AB':
        hs = [h for h in H if h[0] == t]
        have = sum(1 for h in hs if h[2])
        print("%s 词表：%d 条，有音标 %d 条，缺 %d 条（%.1f%%）" % (t, len(hs), have, len(hs) - have, 100.0 * have / max(1, len(hs))))

def cmd_fill():
    bf = load_britfone()
    mapping, why = {}, collections.Counter()
    for t, h, ip in all_heads():
        if ip: continue
        line, reason = lookup(h, bf)
        if line and valid(line): mapping[h] = line
        else: why[reason or '转换结果不合法'] += 1
    n = rewrite(mapping)
    print("自动填入 %d 条；没填的：%s" % (n, '、'.join('%s %d' % kv for kv in why.most_common())))

def cmd_missing(args):
    n = 400; pref = ''
    it = iter(args)
    for a in it:
        if a == '-n': n = int(next(it))
        else: pref = a.lower()
    ms = [h for t, h, ip in all_heads() if not ip and h.lower().startswith(pref)]
    print('\n'.join(ms[:n])); print('# 共 %d 条缺音标（前缀 %r），这里列了 %d 条' % (len(ms), pref, min(n, len(ms))), file=sys.stderr)

def cmd_set(path):
    mapping, bad = {}, []
    for l in io.open(path, encoding='utf-8'):
        l = l.rstrip('\n')
        if not l.strip() or l.startswith('#'): continue
        w, ip = l.split('\t', 1)
        ip = ip.strip()
        if not valid(ip): bad.append((w, ip)); continue
        mapping[w.strip()] = ip
    if bad:
        print("❌ %d 行音标格式不合法，一条都没写：" % len(bad))
        for w, ip in bad[:30]: print("   %s\t%s" % (w, ip))
        return 1
    n = rewrite(mapping, overwrite=True)
    known = set(h for _, h, _ in all_heads())
    unknown = [w for w in mapping if w not in known]
    print("写入 %d 条（文件里 %d 条）" % (n, len(mapping)))
    if unknown: print("⚠ 词表里没有这些词头：" + ' '.join(unknown[:30]))
    return 0

def cmd_check(words):
    H = all_heads()
    bad = [(h, ip) for _, h, ip in H if ip and not valid(ip)]
    have = {h: ip for _, h, ip in H}
    lack = [h for _, h, ip in H if not ip]
    if bad:
        print("【音标行格式不合法】%d 条" % len(bad))
        for h, ip in bad[:20]: print("    %-20s %s" % (h, ip))
    if lack:
        print("【缺音标】%d 条：%s" % (len(lack), ' '.join(lack[:40])))
    else:
        print("全表 %d 条都有音标" % len(H))
    return 1 if (bad or lack) else 0

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == 'status': cmd_status()
    elif a[0] == 'fill': cmd_fill()
    elif a[0] == 'missing': cmd_missing(a[1:])
    elif a[0] == 'draft': cmd_draft(a[1:])
    elif a[0] == 'accept': sys.exit(cmd_accept(a[1:]))
    elif a[0] == 'set': sys.exit(cmd_set(a[1]))
    elif a[0] == 'check': sys.exit(cmd_check(a[1:]))
    else: print(__doc__); sys.exit(2)
