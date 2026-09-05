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
import sys, io, csv, glob, os, re, string
sys.path.insert(0, 'scripts')
from wordkey import sort_key, prefix

def excluded():
    """收词范围的排除名单，见 reference/exclude.txt。
    用户裁定：地区变体英语与国别变体借词不收；学科术语、化学医药、
    音乐文体、拟声口语、文化专名里的生僻词不收。
    判断线是「雅思 6 分以上的人在一般阅读里会不会遇到」。"""
    f = 'reference/exclude.txt'
    if not os.path.exists(f): return set()
    out = set()
    for l in io.open(f, encoding='utf-8'):
        l = l.split('#')[0].strip()
        if l: out.add(sort_key(l))
    return out

def keep_names():
    """首字母大写的词头里，哪些算「已经进了词汇」。见 reference/proper-nouns-keep.txt。
    用户裁定：收 Achilles tendon、Adam's apple 这类已成词汇的，
    不收纯人名地名商标 —— 判断标准是「背了对英语能力有没有帮助」。"""
    f = 'reference/proper-nouns-keep.txt'
    if not os.path.exists(f): return None
    return {sort_key(l.strip()) for l in io.open(f, encoding='utf-8')
            if l.strip() and not l.startswith('#')}

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
    # reference/ 下不都是词头清单，本脚本自己的名单文件和任务笔记也在里面。
    # 黑名单挡过一次（「abba  # 阿拉姆语「父亲」」那种假词条），但每加一个
    # 笔记文件就要记得补一次，后来 GOAL.txt 又漏了进来：里面一行中文
    # 「a 字母 100%，……」被当成 a 段词头，a 段当场从 100% 掉到 99%。
    # 所以再加一道跟文件名无关的防线：英文词头里不可能有汉字。
    # a-only.txt 也是本脚本一族自己的名单文件（audit-ab 用它记「A 教过但
    # B 不该收」的裁定），格式是「词<TAB>搭配」。多数行带汉字判语，被
    # HAS_CJK 挡住了，但纯英文的那 29 行漏了进来，当成词头报缺 ——
    # 「computer\twork on a computer」就这么进了 co- 段的待办清单。
    OWN = {'exclude.txt', 'proper-nouns-keep.txt', 'GOAL.txt', 'a-only.txt'}
    HAS_CJK = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]')
    for f in sorted(glob.glob('reference/*.txt')):
        if os.path.basename(f) in OWN: continue
        words += [l.strip() for l in io.open(f, encoding='utf-8', errors='replace')
                  if l.strip() and not l.startswith('#') and not HAS_CJK.search(l)]

    keep, skip = keep_names(), excluded()
    RAW_LOWER = {w.lower() for w in words}   # 判同形词编号伪影时要查裸形在不在
    out = {}
    for w in words:
        # 商标条目：清单里有两种写法，带真 ™ 的 400 条，
        # 以及被清洗成小写连字符「-…tm」的 100 条（academy-awardtm = Academy Award™）。
        # 商标不是词汇，一律不收 —— 少数已成通名的（Android、AstroTurf）
        # 已经单独列在 proper-nouns-keep.txt 里。
        # 清洗后的商标有两种：带连字符的 academy-awardtm，以及直接粘死的
        # airbustm / coketm / bluetoothtm。原来只挡住了前者，后者 128 条
        # 全都漏成了「缺词」。核对过这 128 条无一例外都是商标，没有真词
        # 以 tm 收尾，所以放宽到不要求连字符是安全的。
        if '\u2122' in w or re.search(r'[a-z]tm$', w):
            continue
        if re.search(r'_\d+$', w):                    # 清单里的编号伪影
            continue                                   # abstract-expressionist_1 / _2
        # 同形词编号：清单把 bass¹ bass² 洗成 bass1 bass2，全表 47 条
        # （lead2、live1、sow1、used1、pace2…）。不能一刀切去数字，
        # 因为 MP3、MI5、ITV2、A1、U2、Omega-3 是真词头。
        # 条件收窄成「全小写 + 去掉数字后的裸形也在清单里」，实测
        # 恰好把 47 条伪影与 10 条真词头分干净。
        if re.fullmatch(r'[a-z][a-z-]*[0-9]', w) and w[:-1] in RAW_LOWER:
            continue
        # 所有格的清洗伪影：清单里同一条目有 Adam’s apple 和 adam-s-apple 两版，
        # 后者把撇号洗成了连字符，于是被切成三个词、跟前者对不上，
        # 结果 Adam's apple 明明写在 apple 条里却一直报缺。全表 178 条同此。
        w = re.sub(r'-s-', "'s ", w)
        # 同一个洗法也吃掉了词尾的撇号：ain-t、macy-s、dry-cleaner-s。
        # 全表这样的只有 20 条，逐条看过都是撇号伪影，没有真词以
        # 「连字符 + s/t」收尾，所以直接还原。
        w = re.sub(r'-(s|t)$', r"'\1", w)
        # 词尾还有两条撇号伪影推不出来，只能显式列：清单里
        # baha-i = Baha'i、maitre-d = maître d'。不能放宽成
        # 「词尾连字符加单字母一律还原」—— billy-o（like billy-o，
        # 猛烈地）那个连字符是真的，一还原就把真词改坏了。
        w = {'baha-i': "baha'i", 'maitre-d': "maitre d'"}.get(w, w)
        # 括号在清单里标的是「可选部分」，不是词头的一部分：
        # AS (level)、A2 (level)、catty-corner(ed)、(the) Netherlands。
        # 全表 9 条，去掉括号符号、保留里面的字就能跟正常写法归一。
        w = w.replace('(', '').replace(')', '').strip()
        # 清单里混着一条 en-dash 写法：cost–benefit 与 cost-benefit 并存，
        # 同一个词两种破折号，不折就永远有一条报缺（全表仅此 1 条）。
        w = w.replace('\u2013', '-').replace('\u2014', '-')
        # 全由单字母加连字符组成的，是带点缩略语被洗掉句点的产物：
        # a-m = a.m.，p-m = p.m.，e-g = e.g.，i-e = i.e.，d-b-a、o-n-o 同此。
        # 拼合起来就能跟带点写法归一（sort_key 本来就去句点）。全表 15 条，
        # 没有哪个真词是这个形状，拼合是安全的。
        if re.fullmatch(r'[A-Za-z](-[A-Za-z])+', w):
            w = w.replace('-', '')
        if w.startswith('-') or w.endswith('-'):      # 词缀条目，不收
            continue
        bare = w.replace('.', '').replace('-', '').replace(' ', '')
        if len(bare) > 1 and bare.isupper():          # 全大写缩写，不收
            continue
        k = sort_key(w)
        if not k: continue
        if k in skip:
            continue                                   # 排除名单，见 reference/exclude.txt
        if w[:1].isupper() and keep is not None and k not in keep:
            continue                                   # 纯人名地名商标，不收
        # 同一条目的多种写法，保留带空格那版（更接近词典写法）
        if k not in out or (' ' in w and ' ' not in out[k]):
            out[k] = w
    return out

def collected():
    """返回 (已收词条键集合, 首词 -> 该词条全文)。
    第二个用来判断多词条目是否已作为搭配写在对应词条里 —— 用户裁定：
    abide by、abound in 这类短语动词，只要在 abide / abound 条里
    已经作为搭配出现过，就不必再单列。"""
    got, text, entries = {}, {}, []
    for f in sorted(glob.glob('wordlists/B-[0-9]*.txt')):
        for b in io.open(f, encoding='utf-8').read().split('\n\n'):
            b = b.strip()
            if not b: continue
            w = b.split('\n')[0].strip()
            got[sort_key(w)] = w
            low = b.lower().replace('\u2019', "'")
            text.setdefault(sort_key(w)[0], []).append(low)
            entries.append((w, low))
    return got, text, entries

# 虚词表：多词条目该并进哪条词条，看的是内容词而不是第一个词。
# in advance 要并进 advance，by accident 并进 accident，at large 并进 large ——
# 并进 in / by / at 毫无意义。反过来 abound in、abide by 的内容词在前。
# 所以规则是「挑非虚词」，不是「挑第一个」。
FUNCTION_WORDS = {
    'a','an','the','of','in','on','at','by','to','for','with','from','into','onto',
    'over','under','up','down','out','off','through','across','along','around',
    'and','or','but','not','no','as','than','that','this','these','those',
    'be','is','are','was','were','been','being','it','its','one','some',
    # 'any' 同 'all'：它是量词不是虚词。any more、any time 的重心就在 any，
    # 段里已有 anybody / anyone / anytime / anywhere 各自立条，
    # 两个词的写法没有理由被推去 m 段和 t 段。
    # 'all' 不在这里 —— 它跟 at / by / in 不是一回事。all-star、all-purpose、
    # all-terrain 的重心就在 all，等 star / purpose / terrain 各自的字母段
    # 只会把它们推到错的地方去（同 agro-industry 那条裁定）。
}

def phrase_hosts(w, got):
    """这个多词条目可以并进哪些已收词条 —— 只认内容词。
    内容词一个都没收时返回空：说明该等词根收了再并，不能塞进虚词条。
    at large 的内容词是 large（还在 l 段没轮到），不该并进 at。"""
    k = sort_key(w)
    if len(k) < 2: return []
    return [p for p in k if p not in FUNCTION_WORDS and (p,) in got]

def phrase_pending(w, got, ref):
    """内容词还没收，等轮到那个字母再并 —— 既不用新写也还并不进去。
    但内容词必须在词头清单里确实存在，否则永远等不到：
    ab initio 的 initio 不是英语词条，它是独立的拉丁短语，该新写。"""
    k = sort_key(w)
    if len(k) < 2: return False
    content = [p for p in k if p not in FUNCTION_WORDS]
    if not content: return False
    if any((p,) in got for p in content): return False
    return any((p,) in ref for p in content)

def phrase_covered(w, got, text):
    """多词条目：只要它出现在任一候选宿主词条的正文里，就算覆盖。
    用户裁定：abide by 写在 abide 条里就算收了，不必单列。"""
    k = sort_key(w)
    if len(k) < 2: return False
    needle = ' '.join(k)
    for p in phrase_hosts(w, got):
        if any(needle in t.replace('-', ' ') for t in text.get(p, [])):
            return True
    return False

def host_entry(w, got, entries):
    """这个缺词该并进哪条已有词条？并不进去就返回 None（需要单独立条）。
    多词条目看首词，派生词看词干。"""
    k = sort_key(w)
    if len(k) > 1:
        hosts = phrase_hosts(w, got)
        if hosts: return got[(hosts[0],)]
    lw = w.lower().replace('\u2019', "'")
    best = None
    for head, _ in entries:
        h = head.lower().replace('\u2019', "'")
        if len(h) >= 4 and lw.startswith(h) and lw != h:
            if best is None or len(h) > len(best): best = head
    return best

def derived_covered(w, entries):
    """派生词：出现在其词根词条的正文里，就算覆盖。
    用户裁定：abrasively 写进 abrasive 条（并配例句）即可，不必单列；
    但若词根本身也没收，那是真遗漏，词根要反向补进来。
    判定条件是两条同时成立 ——
      ① 该词出现在某条词条的正文里
      ② 那条词条的词头是它的词干（前 4 个字母起同源）
    只看①会太松：词可能碰巧出现在无关词条的例句里。"""
    lw = w.lower().replace('’', "'")
    # 必须整词匹配，不能裸子串 —— 否则 alpha 会因为「alphabet」里含这五个
    # 字母而被判为已收，amen 因为 amendment、arse 因为 arsenal、
    # aster 因为 asterisk。a 段实测有 26 个词是这么被虚报成已收的，
    # 全是真词、一个都没写。这正是 CLAUDE.md 说的「宣布收全不等于收全」。
    pat = re.compile(r'(?<![a-z])' + re.escape(lw) + r'(?![a-z])')
    for head, body in entries:
        h = head.lower().replace('’', "'")
        # 词干下限取 3 不取 4：apt / act / age / air / arm / art 这类
        # 三字母词根在词表里有 34 个，卡在 4 会让 aptness 这种正当派生词
        # 并进词根后仍被判成缺词，逼着人去给派生词单开条目 —— 那违反
        # 「派生词一律并入词根」的裁定。实测放宽后全表只多认出 ayes 一条，
        # 且是对的：整词匹配那一关已经挡住了碰巧同前缀的误判。
        if len(h) < 3 or not lw.startswith(h[:4]) or lw == h:
            continue
        if pat.search(body):
            return True
    return False

def main(argv):
    show_names = '--names' in argv
    argv = [a for a in argv if a != '--names']
    ref = load_reference()
    got, text, entries = collected()
    if not ref:
        print("reference/ 里没找到词头文件"); return 2

    targets = argv or sorted({p[0] for p in ref if p})
    grand_ref = grand_got = 0
    for t in targets:
        sel = {k: v for k, v in ref.items() if prefix(v, len(t)) == t or (len(t) == 1 and k[0][:1] == t)}
        if not sel: continue
        missing = {k: v for k, v in sel.items()
                   if k not in got and not phrase_covered(v, got, text)
                   and not derived_covered(v, entries)}
        names = [v for v in missing.values() if v[:1].isupper()]
        grand_ref += len(sel); grand_got += len(sel) - len(missing)
        pct = (len(sel) - len(missing)) * 100 // len(sel)
        print(f"\n{t}- 段：清单 {len(sel)} 条，已收 {len(sel)-len(missing)} 条（{pct}%），缺 {len(missing)} 条")
        if len(t) == 1:   # 单字母时按双字母段细分
            for ch in string.ascii_lowercase:
                p = t + ch
                s2 = {k: v for k, v in sel.items() if prefix(v) == p}
                if not s2: continue
                # 必须用同一个 missing 判定 —— 曾经这里只查 k not in got，
                # 漏掉了并入覆盖，于是总数说 100% 而明细说 73%，自相矛盾。
                m2 = [s2[k] for k in s2 if k in missing]
                flag = "  ← 缺" if m2 else ""
                print(f"    {p}  清单 {len(s2):4}  已收 {len(s2)-len(m2):4}  缺 {len(m2):4}{flag}")
        else:
            # 缺口分三类，处理方式完全不同（用户裁定）：
            #   并入 —— 多词条目和派生词，词根已收，写进那条词条里加例句即可
            #   新写 —— 词根本身也没收，得单独立条
            fold, fresh, later = {}, [], []
            for v in missing.values():
                if phrase_pending(v, got, ref):
                    later.append(v); continue
                base = host_entry(v, got, entries)
                (fold.setdefault(base, []).append(v) if base else fresh.append(v))
            if fold:
                n = sum(len(x) for x in fold.values())
                print(f"  待并入已有词条 {n} 条（写进词根条里并补例句，不单列）：")
                for h in sorted(fold, key=sort_key):
                    print(f"    {h}  ←  {' '.join(sorted(fold[h], key=sort_key))}")
            if fresh:
                print(f"  待新写 {len(fresh)} 条：" + " ".join(sorted(fresh, key=sort_key)))
            if later:
                print(f"  待推迟 {len(later)} 条（内容词还在后面的字母段，等收到再并）："
                      + " ".join(sorted(later, key=sort_key)))
        if len(t) == 1 and names:
            print(f"  其中首字母大写 {len(names)} 条（均在 keep 名单内，需要收）")
        if show_names and names:
            print("  大写条目：" + " ".join(sorted(names)))
    if len(targets) > 1 or len(targets[0]) == 1:
        print(f"\n合计：清单 {grand_ref} 条，已收 {grand_got} 条（{grand_got*100//max(grand_ref,1)}%）")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
