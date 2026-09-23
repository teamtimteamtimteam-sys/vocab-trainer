#!/usr/bin/env python3
"""生成 index.html 里例句高亮用的不规则词形表 IRREG（2026-09-23）。

为什么要有它：app 在例句里把词头高亮出来，靠的是「词头 + 规则变形」去匹配。
不规则的变形（hold→held、foot→feet、can→cannot、a→an）规则推不出来，
以前一律漏掉 —— 用户在 iPad 上看到 An hour、cannot、Canned soup 都没亮。

数据两路合并：
  ① reference/inflections.txt —— coverage 用的「变形 → 词根」对照表，
     每个字母段写到哪里补到哪里（held→hold、hooves→hoof、homoeopath→homeopath）；
  ② 本脚本里的通用表 —— 不规则动词、不规则复数、不规则比较级、否定缩略式，
     覆盖全字母表，不必等写到那个字母段。

用法：python3 scripts/gen-forms.py        改写 index.html 里 IRREG:BEGIN/END 之间那一行
      python3 scripts/gen-forms.py --check 只检查是否需要重新生成（退出码 1 = 过期）
改了 inflections.txt 之后要重跑，否则 app 认不上新登记的变形。
"""
import io, json, re, sys

VERBS = """
arise arose arisen|awake awoke awoken|bear bore borne born|beat beat beaten|become became
begin began begun|bend bent|bid bade bidden|bind bound|bite bit bitten|bleed bled|blow blew blown
break broke broken|breed bred|bring brought|build built|burn burnt|buy bought|catch caught
choose chose chosen|cling clung|come came|creep crept|deal dealt|dig dug|dive dove
do did done does doing|draw drew drawn|dream dreamt|drink drank drunk|drive drove driven|dwell dwelt
eat ate eaten|fall fell fallen|feed fed|feel felt|fight fought|find found|flee fled|fling flung
fly flew flown flies|forbid forbade forbidden|forget forgot forgotten|forgive forgave forgiven
forsake forsook forsaken|freeze froze frozen|get got gotten|give gave given|go went gone goes
grind ground|grow grew grown|hang hung|have has had having|hear heard|hide hid hidden|hold held
keep kept|kneel knelt|know knew known|lay laid|lead led|lean leant|leap leapt|learn learnt
leave left|lend lent|lie lay lain lying|light lit|lose lost|make made|mean meant|meet met
mislead misled|mistake mistook mistaken|misunderstand misunderstood|mow mown|overcome overcame
overtake overtook overtaken|pay paid|plead pled|prove proven|ride rode ridden|ring rang rung
rise rose risen|run ran|say said says|see saw seen|seek sought|sell sold|send sent|sew sewn
shake shook shaken|shine shone|shoot shot|show shown|shrink shrank shrunk|sing sang sung
sink sank sunk|sit sat|slay slew slain|sleep slept|slide slid|sling slung|slink slunk|smell smelt
sow sown|speak spoke spoken|speed sped|spell spelt|spend spent|spill spilt|spin spun|spit spat
spoil spoilt|spring sprang sprung|stand stood|steal stole stolen|stick stuck|sting stung
stink stank stunk|stride strode stridden|strike struck stricken|string strung|strive strove striven
swear swore sworn|sweep swept|swell swollen|swim swam swum|swing swung|take took taken|teach taught
tear tore torn|tell told|think thought|throw threw thrown|tread trod trodden|understand understood
undertake undertook undertaken|undo undid undone|wake woke woken|wear wore worn|weave wove woven
weep wept|win won|wind wound|withdraw withdrew withdrawn|withhold withheld|withstand withstood
wring wrung|write wrote written|be am is are was were been being|beget begot begotten
behold beheld|beseech besought|foresee foresaw foreseen|forgo forwent forgone|awaken awoke
cleave cleft clove cloven|seethe sod|shear shorn|smite smote smitten|stave stove|thrive throve thriven
"""
NOUNS = """
man men|woman women|child children|foot feet|tooth teeth|goose geese|mouse mice|person people
ox oxen|louse lice|die dice|knife knives|wife wives|life lives|leaf leaves|half halves|wolf wolves
shelf shelves|loaf loaves|thief thieves|calf calves|hoof hooves|self selves|elf elves|sheaf sheaves
scarf scarves|wharf wharves|crisis crises|analysis analyses|thesis theses|basis bases
criterion criteria|phenomenon phenomena|cactus cacti|fungus fungi|nucleus nuclei|radius radii
stimulus stimuli|syllabus syllabi|alga algae|larva larvae|formula formulae|appendix appendices
index indices|matrix matrices|vertex vertices|datum data|medium media|bacterium bacteria
curriculum curricula|memorandum memoranda|hippopotamus hippopotami|hippocampus hippocampi|glans glandes|embolus emboli
"""
OTHER = """
good better best|well better best|bad worse worst|badly worse worst|far farther further farthest furthest
little less least|many more most|much more most|old elder eldest
a an|an a|can cannot can't canst|will won't|shall shan't
"""

def table():
    m = {}
    def put(root, forms):
        for f in forms:
            if f != root:
                m.setdefault(root, [])
                if f not in m[root]: m[root].append(f)
    for block in (VERBS, NOUNS, OTHER):
        for grp in block.replace('\n', '|').split('|'):
            w = grp.split()
            if w: put(w[0], w[1:])
    for line in io.open('reference/inflections.txt', encoding='utf-8'):
        line = line.split('#')[0].strip()
        if not line: continue
        form, root = line.split()[:2]
        put(root.lower(), [form.lower()])
    return {k: m[k] for k in sorted(m)}

def render():
    return 'const IRREG = ' + json.dumps(table(), ensure_ascii=False, separators=(',', ':')) + ';'

def main(argv):
    p = 'index.html'
    src = io.open(p, encoding='utf-8').read()
    pat = re.compile(r'(/\* IRREG:BEGIN.*?\*/\n)(.*?)(\n/\* IRREG:END \*/)', re.S)
    mm = pat.search(src)
    if not mm: print('index.html 里找不到 IRREG:BEGIN / IRREG:END 标记'); return 2
    new = render()
    if '--check' in argv:
        if mm.group(2) != new: print('IRREG 过期：inflections.txt 改过，要重跑 gen-forms.py'); return 1
        print('IRREG 与 inflections.txt 一致'); return 0
    io.open(p, 'w', encoding='utf-8').write(src[:mm.start(2)] + new + src[mm.end(2):])
    print('IRREG：%d 个词根，%d 个变形' % (len(table()), sum(len(v) for v in table().values())))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
