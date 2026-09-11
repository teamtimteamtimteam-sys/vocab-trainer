#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查「凑数义项」：为了凑够义项数，写出跟词条本身无关的例句和讲解 ——
「这个词很旧 / 美国人怎么拼 / 它能长多大 / 那个东西怎么用」，
再挂一个跟词头毫无关系的等式，等于拿另一个词去顶数。
用户 2026-09-05 明令：冷僻词真实义项只有一两个就写一两个，不许硬凑。

前四道闸门（check-wordlist / coverage / audit-depth / audit-swallowed）
只数数目、不读内容，一条都拦不住这个。

判据：一个义项（编号例句 + 译文 + 等式 + 讲解行）整段里，
找不到任何跟词头同源的字眼，就是跟词条无关。
为了不误伤，同源判定放宽到三条：
  · 词头任一实词的前四个字母，在义项里以子串出现（megabyte 认得 byte）
  · 多词词头只要命中最长的那个实词即可（air show、box office）
  · 编辑距离 ≤2 的形态变化也算（arise→arose、become→became）
两类分别报：
  【假义项】例句本身就跟词头无关 —— 必须改写或删掉
  【等式挂歪】例句是真义项，只是等式顺手教了别的词 —— 可容忍，不该多

另外两道：
  【例句里没有词】例句本身必须出现词头（2026-09-05 加，计退出码）
  【元评论例句】例句在谈论这个词本身、不是在用它（2026-09-06 加，**只报告**）
用法：python3 scripts/audit-padding.py [字母段]      不给段就查全表
      python3 scripts/audit-padding.py --selftest    只跑【元评论例句】的用例
"""
import sys, io, re, glob, unicodedata, importlib.util as u
sys.path.insert(0, 'scripts')
from wordkey import numsort
spec = u.spec_from_file_location('cw', 'scripts/check-wordlist.py')
cw = u.module_from_spec(spec); spec.loader.exec_module(cw)
NUMS = set(cw.NUMS)
TAIL = ('构词', '注意', '辨析')

def fold(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace('\u2019', '').replace("'", '')   # 撇号并进词里：we're→were、cow's→cows
    return re.sub(r'[^a-z ]', ' ', s.lower())

def dist(a, b):
    if abs(len(a) - len(b)) > 2: return 9
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

# -ough-／-augh- 一类强变化动词，元音全换、编辑距离拉得太开，
# 上面那几条形态规则一个都够不着，只能列表。列的是词干，
# 派生形式（bought out、caught on）靠前缀匹配自然认得。
STRONG = {'catch': ['caught'], 'buy': ['bought'], 'teach': ['taught'],
          'bring': ['brought'], 'seek': ['sought'], 'think': ['thought'],
          'fight': ['fought'], 'come': ['came'], 'become': ['became'],
          'beseech': ['besought'], 'bid': ['bade', 'bidden'], 'are': ['were', 'is', 'am'],
          'bear': ['bore', 'born', 'borne'], 'break': ['broke', 'broken'],
          'beget': ['begot', 'begotten'], 'behold': ['beheld'], 'arise': ['arose', 'arisen'],
          'awake': ['awoke', 'awoken'], 'become': ['became'], 'begin': ['began', 'begun'],
          'bite': ['bit', 'bitten'], 'blow': ['blew', 'blown'], 'breed': ['bred'],
          'bring': ['brought'], 'build': ['built'], 'choose': ['chose', 'chosen'],
          'cling': ['clung'], 'creep': ['crept'], 'eat': ['ate', 'eaten'],
          'die': ['dying', 'died'], 'dig': ['dug'], 'do': ['did', 'done', 'does'],
          'draw': ['drew', 'drawn'], 'drive': ['drove', 'driven'],
          'drink': ['drank', 'drunk'], 'deal': ['dealt'], 'dry': ['dried', 'drier'],
          'speak': ['spoke'], 'steal': ['stole'], 'freeze': ['froze'],
          'choose': ['chose'], 'seek': ['sought'], 'strike': ['struck']}

def cuts_of(t):
    """词头实词 t 的各种派生词干 —— 词尾 e / y 脱落、强变化、拉丁复数"""
    cuts = [t, t.rstrip('e'), t.rstrip('y'), t[:-1]]   # bake→baking、apiary→apiarist
    if t.endswith('y'): cuts.append(t[:-1] + 'i')      # cry→cried、copy→copies
    if t.endswith('f'): cuts.append(t[:-1] + 'v')      # calf→calves、leaf→leaves
    if t in STRONG: cuts += STRONG[t]                  # catch→caught 这类强变化
    if t.endswith(('ex', 'ix')): cuts.append(t[:-2] + 'ic')   # codex→codices
    return cuts

def same_word(t, w, firm=False):
    """句中单词 w 是不是词头实词 t 的一个词形 —— 逐词判定。

    firm=True 只认**确凿**的词形（原形、派生、复合词里的词干），不认编辑距离
    猜出来的形近词。两档并存是有用的：判「有没有沾边」要放宽（宁可漏报），
    判「这一句里还有没有真用法」要收紧 —— 否则 The word once meant a candle
    maker. 会因为 candle 跟 chandler 只差两个字母而被当成真用法放行。
    """
    for cut in cuts_of(t):
        if len(cut) >= 3 and w.startswith(cut): return True
        # 变形出现在复合词尾部：airborne 里的 borne、handmade 里的 made。
        # 长度收到 4 以上，免得三字母词干到处误命中。
        if len(cut) >= 4 and cut in w: return True
    if firm or len(t) < 4: return False
    if dist(t, w) <= 2: return True                    # 认得不规则变位
    # betake→betook、forsake→forsook：前三字母相同的强变化动词
    if len(t) >= 6 and w[:3] == t[:3] and dist(t, w) <= 3: return True
    # bear→bore、speak→spoke：首尾字母相同、只换中间元音
    if (len(w) == len(t) and w[0] == t[0] and w[-1] == t[-1]
            and sum(a != b for a, b in zip(w, t)) <= 2): return True
    return False

def heads_of(head):
    return [t for t in fold(head).split() if len(t) >= 3]

def related(head, text):
    """义项里有没有跟词头同源的字眼"""
    hts = heads_of(head)
    if not hts: return True
    flat = text.replace(' ', '')
    toks = text.split()
    for t in sorted(hts, key=len, reverse=True):
        if t[:4] in flat: return True          # 子串即可，认得复合词
        if any(same_word(t, w) for w in toks): return True
    return False

# ── 【元评论例句】整句在谈论这个词本身，而不是在使用它 ──────────────
# 【例句里没有词】只问「词头在不在句子里」，问不出「它在句子里是被使用还是
# 被谈论」。apprehension ③ 曾经写成
#     The word covers both the fear and the arrest, and only the context
#     tells you which apprehension is meant.
# 词形就在句中，九道闸门全绿，可这一句从头到尾在谈论这个词。（2026-09-06
# 第十八批，GOAL.txt 里记的「改撞车的时候最容易滑进元评论」。）
#
# 判据是语言学里的「使用 / 提及」（use / mention）之分，**不是**「有没有提到
# 语言」—— 这一点是不误伤的关键。仓库里 anagram、antonym、apocope、
# allophone、antepenultimate、alphabetical 这些词条的例句天生在讲语言现象
# （"Listen" is an anagram of "silent"、The stress falls on the
# antepenultimate syllable），可它们把词头用在真实位置上，一条都不该报。
#
# 做法：
#   ① 找出词头在句中的所有词形；
#   ② 逐个判断它是「被提及」还是「被使用」——
#      被提及＝夹在引号里（排除直接引语）、跟在 the word / the term /
#      the spelling 之类元语言名词后面作同位语、或是 spell it … 的宾语；
#   ③ **只要还剩一个确凿词形是在正常使用，就放行**；
#   ④ 全是提及、或整句根本没有确凿词形，且句中确有元语言框架，才报。
# 第 ③ 步用的是 same_word(firm=True)：编辑距离猜出来的形近词（candle 之于
# chandler、long 之于 auld lang syne）不算真用法，否则一句纯元评论只要碰巧
# 含一个形近词就被放行。
META_STRONG = ('word', 'term', 'phrase', 'expression', 'spelling',
               'abbreviation', 'plural', 'singular')
# 这几个日常义太常见（the name of the shop、the verb takes an object），
# 只在「紧跟着一个词头词形」时才当元语言名词用，不单独当句首框架。
META_WEAK = ('name', 'adjective', 'adverb', 'noun', 'verb', 'suffix', 'prefix')
META = META_STRONG + META_WEAK
DET = ('the', 'a', 'an', 'this', 'that')
# 直接引语里的词头是真用法："Aye, captain." / He cried "Begone!"
SPEECH = ('said', 'says', 'cried', 'shouted', 'whispered', 'asked', 'replied',
          'added', 'announced', 'muttered', 'yelled', 'answered', 'remarked')
# 「提及」动词：跟在它后面的 the word X 是在谈这个词，不是在用
MENTIONV = ('use', 'uses', 'used', 'using', 'mention', 'mentions', 'mentioned',
            'prefer', 'prefers', 'preferred', 'reclaim', 'reclaims', 'reclaimed',
            'write', 'writes', 'wrote', 'spell', 'spells', 'spelled', 'spelt',
            'hate', 'hates', 'hated', 'avoid', 'avoids', 'avoided', 'coin',
            'coined', 'replaced', 'dislike', 'dislikes', 'disliked', 'banned')
# 只收动词形。'spelling' 是名词（won the spelling bee），
# 'pronounce' 有 pronounce anathema / sentence 这类真用法，都不能进。
SPELLV = ('spell', 'spells', 'spelled', 'spelt', 'misspell', 'misspells')
# write / say 本身太常见（wrote a biography、said amen、writes code 都是真
# 用法），只有主语是「某一群人 / 某一类文本」时才是在说这个词怎么写。
SAYV = ('write', 'writes', 'wrote', 'say', 'says', 'said')
SOURCE = ('americans', 'american', 'british', 'canadians', 'canadian',
          'australians', 'australian', 'scots', 'irish', 'older', 'old',
          'modern', 'victorian', 'most', 'some', 'many', 'nobody', 'everybody',
          'writers', 'editors', 'texts', 'books', 'novels', 'maps', 'labels',
          'guides', 'dictionaries', 'papers', 'journals', 'menus', 'recipes',
          'accounts', 'editions', 'comics', 'sources', 'publishers',
          'speakers', 'style')
BRIDGE = ('it', 'as', 'them', 'often', 'usually', 'always', 'still', 'now',
          'also', 'only', 'not', 'the', 'sound', 'word', 'name')
# 系动词/助动词：用来分辨「the term comprehends…」（comprehend 是谓语动词，
# 真用法）与「the spelling crudités is also used」（crudités 是被提到的词）
AUX = ('is', 'are', 'was', 'were', 'has', 'have', 'had', 'does', 'do', 'did',
       'will', 'would', 'can', 'could', 'may', 'might', 'seems', 'sounds',
       'remains', 'appears', 'looks')
# 铁定在谈词语本身的谓语（跟在被提及的词后面）
METAPRED = (r'is (spelt|spelled|pronounced|hyphenated|capitalised|capitalized)\b',
            r'is (a|an|the) [a-z ]{0,14}spelling\b',
            r'is short for\b', r'rhymes with\b', r'is stressed\b',
            r'is an abbreviation\b', r'is a loanword\b')

def metatalk(head, ex):
    """例句是不是在谈论这个词本身。是就返回理由列表，不是返回 None。"""
    raw = ex.strip(); low = fold(raw); toks = low.split()
    hts = heads_of(head)
    if not hts: return None
    # 引号里的短片段（1-3 个词）算「被引用的词」；直接引语不算
    quoted = set()
    for m in re.finditer(r'["“”‘’](\w[\w \-\'’]*?)["“”‘’]', raw):
        span = fold(m.group(1)).split()
        if not 1 <= len(span) <= 3: continue
        b = raw[:m.start()].split(); a = raw[m.end():].split()
        if (b and fold(b[-1]).strip() in SPEECH) or (a and fold(a[0]).strip(' ,.') in SPEECH):
            continue
        quoted.update(span)
    occ = [i for i, w in enumerate(toks) if any(same_word(t, w) for t in hts)]
    firm = set(i for i in occ if any(same_word(t, toks[i], True) for t in hts))

    def meta_np(j):
        """toks[j] 是元语言名词，且这个名词短语正处在「谈论一个词」的位置"""
        if j < 0 or j >= len(toks) or toks[j] not in META: return False
        k = j - 1
        while k >= 0 and k >= j - 3 and toks[k] not in DET: k -= 1   # 跳过形容词
        if k < 0 or toks[k] not in DET: return False
        return k == 0 or toks[k - 1] in MENTIONV        # 句首，或跟在提及动词后

    def spell_frame():
        for k, w in enumerate(toks):
            if w in SPELLV and toks[k + 1:k + 2] and toks[k + 1] in ('it', 'them'):
                return '「%s it ＜某拼法＞」' % w
            if w in SAYV and k + 1 < len(toks) and set(toks[:k]) & set(SOURCE):
                return '「＜某群体＞ %s ＜某词＞」' % w
        return None

    def mention(i):
        w = toks[i]
        if w in quoted: return '引号里的＜词头＞'
        # 同位语：the word alleluia / the spelling bulgur。
        # 词尾 -s 多半是跟元语言主语一致的动词（The term comprehends both
        # senses），-ly 是副词（I use the word advisedly）—— 除非后面紧跟
        # 系动词，那说明它自己就是被提到的那个词（The spelling crudités is…）。
        if not w.endswith(('s', 'ly')) or set(toks[i + 1:i + 4]) & set(AUX):
            j = i - 1
            if j >= 0 and toks[j] in DET: j -= 1
            if j >= i - 2 and meta_np(j): return 'the %s ＜词头＞' % toks[j]
        # 拼写/说法动词的宾语：Old accounts spell it assagai / Americans write center
        if not w.endswith('ly'):
            for k in range(max(0, i - 3), i):
                if not all(x in BRIDGE for x in toks[k + 1:i]): continue
                if toks[k] in SPELLV: return '%s … ＜词头＞' % toks[k]
                if toks[k] in SAYV and set(toks[:k]) & set(SOURCE):
                    return '＜某群体＞ %s ＜词头＞' % toks[k]
        # spell it sissy, not cissy —— 对照项也是被提及的
        if i and toks[i - 1] in ('not', 'than') and spell_frame():
            return 'not ＜词头＞'
        rest = ' '.join(toks[i + 1:i + 5])
        for p in METAPRED:
            m = re.match(p, rest)
            if m: return '＜词头＞ ' + m.group(0)
        # which apprehension is meant —— 词头被指着说「是哪个意思」
        if i and toks[i - 1] in ('which', 'that', 'what') and re.match(r'is meant\b', rest):
            return 'which ＜词头＞ is meant'
        return None

    reasons = [mention(i) for i in occ]
    if any(r is None and i in firm for i, r in zip(occ, reasons)):
        return None                     # 还有一个确凿词形在正常使用 → 放行
    frames = [r for r in reasons if r]
    for j, w in enumerate(toks[:4]):
        if w in META_STRONG and meta_np(j):
            frames.append('句首「the %s」' % w); break
    f = spell_frame()
    if f: frames.append(f)
    return list(dict.fromkeys(frames)) or None

def entries():
    for p in [f for f in numsort(glob.glob('wordlists/B-*.txt')) if 'merged' not in f]:
        for blk in io.open(p, encoding='utf-8').read().split('\n\n'):
            L = [l for l in blk.strip().split('\n') if l.strip()]
            if L: yield L[0], L

def senses(L):
    nums = [k for k, l in enumerate(L) if l[0] in NUMS]
    for a, b in zip(nums, nums[1:] + [len(L)]):
        body = []
        for l in L[a + 1:b]:
            if any(l.startswith(t) for t in TAIL): break
            body.append(l)
        yield L[a], body

# 【元评论例句】这道尺子的整个难处在于「不误伤」：仓库里 anagram、antonym、
# apocope、allophone、antepenultimate 这些词条的例句本来就在讲语言现象。
# 这些例子钉在这里，改尺子时先跑 `python3 scripts/audit-padding.py --selftest`。
SELFTEST = [
    # 该报的
    ('apprehension', 'The word covers both the fear and the arrest, and only '
                     'the context tells you which apprehension is meant.', True),
    ('banister', 'This word also has another spelling.', True),
    ('cunt', 'The word cunt is the strongest in English.', True),
    ('bailiwick', 'The word once meant a bailiff’s district.', True),
    ('centre', 'Americans write center and put the last two letters the other way round.', True),
    ('assagai', 'Old accounts spell it assagai.', True),
    # 不该报：例句在讲语言现象，但词头用在真实位置上
    ('anagram', '"Listen" is an anagram of "silent", which is the example every '
                'puzzle book opens with.', False),
    ('antonym', '"Hot" is the antonym of "cold", though neither word means much '
                'without something to measure.', False),
    ('apocope', 'Apocope shortened the word over time until the ending disappeared '
                'altogether.', False),
    ('allomorph', 'The plural ending has three allomorphs in English.', False),
    ('antepenultimate', 'The stress falls on the antepenultimate syllable, which is '
                        'why the word sounds wrong when shortened.', False),
    ('alphabetical', 'Files are in alphabetical order, which is no help if you '
                     'forget the name.', False),
    # 不该报：元语言字眼在句子里，可词头本身是被使用的
    ('advise', 'I use the word advisedly, having read every page of the report.', False),
    ('comprehend', 'The term comprehends both senses.', False),
    ('collocate', 'The two words collocate strongly.', False),
    ('connotation', 'The word has negative connotations.', False),
    ('borrowing', 'The word is a borrowing from Japanese and kept its original plural.', False),
    ('correct', 'Spell it correctly or the whole record will be filed under the wrong letter.', False),
    ('bee', 'She won the spelling bee on a word that nobody in the hall could define.', False),
    # 不该报：the word / the term / the form 的日常义
    ('term', 'The term ends in June and the exams start the week after.', False),
    ('form', 'Please complete the form in black ink and sign it at the bottom.', False),
    ('biography', 'She wrote a biography of Churchill.', False),
    ('amen', 'The congregation said amen and the organ started before anyone had lifted a head.', False),
    ('anathema', 'The council pronounced anathema on him and the sentence stood for centuries.', False),
]

def selftest():
    bad = 0
    for h, ex, want in SELFTEST:
        got = bool(metatalk(h, ex))
        if got != want:
            bad += 1
            print('  ✗ %-16s 应%s报，实际%s报：%s'
                  % (h, '' if want else '不', '' if got else '不', ex[:62]))
    print('【元评论例句】自测 %d 条，不合 %d 条' % (len(SELFTEST), bad))
    return 1 if bad else 0

def main(argv):
    if argv and argv[0] == '--selftest': return selftest()
    seg = argv[0].lower() if argv else None
    tot = 0; fake = []; lazy = []; meta = []; talk = []
    for h, L in entries():
        if seg and not h.lower().startswith(seg): continue
        for ex, body in senses(L):
            tot += 1
            eqs = [l for l in body if cw.EQ.match(l)]
            whole = fold(ex + ' ' + ' '.join(body))
            # 【例句里没有词】铁律：每个义项的例句里必须真的出现这个词。
            # 上面那条【假义项】看的是「例句 + 译文 + 等式 + 讲解行」整段，
            # 只要等式行里带着词头就算沾边 —— 于是「The word is a strong
            # insult.」配上「a cocksucker = …」照样过关。2026-09-05 全表查出
            # 22 条这种元评论义项（c 段 15、b 段 6），全是冷僻词、缩写、
            # 禁忌词那三类：写的人凑不出自然例句，就改写成「这个词很重 /
            # 美国人怎么拼 / 那个缩写没有复数」。它们不教词，只谈词。
            if not related(h, fold(ex)):
                meta.append((h, ex.strip(), eqs[0].strip() if eqs else ''))
            why = metatalk(h, ex[1:])
            if why: talk.append((h, ex.strip(), '；'.join(why)))
            if related(h, whole): 
                # 例句沾边，再看第一条等式是不是在教别的词
                if eqs and not related(h, fold(eqs[0].split('=')[0])):
                    lazy.append((h, ex.strip(), eqs[0].strip()))
                continue
            fake.append((h, ex.strip(), eqs[0].strip() if eqs else ''))
    # 重复义项：同一词条里两条例句实质是同一句。
    # believe「I believe her / I believe in her」这种最小对立对是有意为之，
    # 必须放行 —— 判据收紧成「词集完全相同」，或者「差一个词且译出的
    # 中文也一模一样」（bell jar / bell glass 那种同义词各占一条）。
    # 2026-09-06 补第二条判据：上面只比例句字面，比不出「例句写得不一样、
    # 教的其实是同一件事」——bluff 一条词条里 bluff your way in / into /
    # out of / through 占了四个义项，cable television 与 cable TV 各占一条。
    # 用户当天明令：重复义项只保留一个，不要遗漏义项，也不要硬凑义项。
    # 尺子改成看等式：左边剥掉冠词与占位词后相同，且右边中文释义也基本相同，
    # 才算重复 —— 单看左边会误伤 dig in / draw in 这类真的一词多义的短语动词。
    EQPH = ('a', 'an', 'the', 'to', 'be', 'somebody', 'something', 'sb', 'sth',
            'one', 'ones', 'your', 'his', 'her', 'their', 'its', 'my', 'our',
            'oneself', 'yourself', 'himself', 'herself', 'itself', 'themselves',
            'so', 'it')
    def eq_lhs(l):
        # 这里不能用 fold：它把数字也抹掉，caesium-137 会跟 caesium 撞成一条。
        t = re.sub(r'[^a-z0-9 ]', ' ', l.split('=', 1)[0].lower())
        return ' '.join(x for x in t.split() if x not in EQPH)
    def eq_rhs(l):
        # 括号里的限定语不能剥：这张表的区别常常就写在括号里
        # （「贝都因人（全体）」对「一个贝都因人」）。剥掉就把真义项也判成重复。
        return re.sub(r'[，。、,.;；！!？?　 ]', '', l.split('=', 1)[1])
    def first_eq(b):
        for l in b:
            if cw.EQ.match(l) and '=' in l and not l.startswith('= '): return l
        return None

    import itertools
    dupes = []
    for h, L in entries():
        if seg and not h.lower().startswith(seg): continue
        ss = [(e.strip(), b) for e, b in senses(L)]
        for (e1, b1), (e2, b2) in itertools.combinations(ss, 2):
            q1, q2 = first_eq(b1), first_eq(b2)
            if q1 and q2 and eq_lhs(q1) == eq_lhs(q2) and eq_lhs(q1):
                # 中文释义要卡得很紧才行：Bahamian「巴哈马的 / 巴哈马人」、
                # another「再一个 / 另一个」都共着大半个字面，却是两个真义项。
                # 阈值放到 0.8，包含关系还要求长度相当，才不会误伤。
                r1, r2 = eq_rhs(q1), eq_rhs(q2)
                if not (r1 and r2): continue
                # 只用字集相似度，不用包含关系：中文里「樱桃」是「樱桃木」的
                # 子串，可它们是两个义项。包含关系判重会把这类全部误伤。
                if len(set(r1) & set(r2)) / max(len(set(r1) | set(r2)), 1) >= 0.8:
                    dupes.append((h, e1, e2)); continue
            w1, w2 = set(fold(e1[1:]).split()), set(fold(e2[1:]).split())
            if len(w1) < 3 or len(w2) < 3: continue
            j = len(w1 & w2) / len(w1 | w2)
            if j == 1.0:
                dupes.append((h, e1, e2)); continue
            if j >= 0.75:
                z = [ [l for l in b if l.startswith('= ')] for b in (b1, b2) ]
                if z[0] and z[1] and z[0][0] == z[1][0]:
                    dupes.append((h, e1, e2))

    label = (seg + '- 段') if seg else '全表'
    print('\n%s：义项 %d 条' % (label, tot))
    print('  【假义项】整条跟词头无关，纯粹凑数：%d 条 (%.1f%%)'
          % (len(fake), 100.0 * len(fake) / max(tot, 1)))
    for h, ex, eq in fake[:80]:
        print('      %-20s %-44s %s' % (h, ex[:44], eq[:30]))
    if len(fake) > 80: print('      ……还有 %d 条' % (len(fake) - 80))
    print('  【例句里没有词】义项的例句里找不到词头或其变形：%d 条 (%.1f%%)'
          % (len(meta), 100.0 * len(meta) / max(tot, 1)))
    for h, ex, eq in meta[:60]:
        print('      %-20s %-44s %s' % (h, ex[:44], eq[:30]))
    if len(meta) > 60: print('      ……还有 %d 条' % (len(meta) - 60))
    print('  【元评论例句】整句在谈论这个词本身、不是在用它：%d 条 (%.1f%%)  ← 计入退出码'
          % (len(talk), 100.0 * len(talk) / max(tot, 1)))
    for h, ex, why in talk[:80]:
        print('      %-18s %-52s %s' % (h, ex[:52], why))
    if len(talk) > 80: print('      ……还有 %d 条' % (len(talk) - 80))
    print('  【等式挂歪】例句是真义项，等式教了别的词：%d 条 (%.1f%%)'
          % (len(lazy), 100.0 * len(lazy) / max(tot, 1)))
    print('  【重复义项】同一词条里两条例句实质是同一句：%d 对' % len(dupes))
    for h, e1, e2 in dupes[:30]:
        print('      %-18s %s' % (h, e1[:44]))
        print('      %-18s %s' % ('', e2[:44]))
    # 【元评论例句】2026-09-06 头一次全表跑报出 50 条，全是真的（拼写变体、
    # 词源、语域说明写成了例句），当时不计退出码，免得闸门一直红着 ——
    # GOAL.txt 记着「一直报红的闸门等于没有闸门」。
    # 2026-09-08 回填做完，最后三条（bristols、catfight、cocksucker）也
    # 改成了真用法，全表清到 0，按当初记下的办法把 talk 并进退出码，
    # 这道尺子从此真的拦人：再写出「the word X」「X means Y」那类句子会红。
    return 1 if (fake or dupes or meta or talk) else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
