# 接手须知（新会话从这里开始）

三份文件的分工，别搞混：

| 文件 | 写什么 | 会不会过期 |
|---|---|---|
| `reference/HANDOFF.md`（本文件） | 每一轮怎么干：命令、节奏、筛选与写作要求的**操作版清单** | 规则变了要改 |
| `CLAUDE.md` | 规格与规则的**完整版**（格式硬规则、例句承载力、判重、收词边界的来龙去脉） | 基本不变 |
| `reference/GOAL.txt` | **当前进度**、下一步、还没内化的教训 | 每批都更新 |

冷启动三步：

```bash
python3 scripts/status.py        # 现算进度、闸门阈值、下一步做哪个段
python3 scripts/coverage.py <段> # 看这个段缺什么：待并入 / 待新写 / 待推迟
sed -n '1,60p' reference/GOAL.txt
```

---

## 一、输出节奏（用户 2026-09-09 定的）

- **一次回复三批，每批 20-25 条**。一批太慢、七批伤质量，三批是折衷。
- 多义词扎堆的批次少写几条（do、down、enter 那种大词一条能顶半批）。
- **批与批之间分别跑闸门、分别提交**，不要攒到最后一起提。
- 提交在本地随时做；**push 等用户开口**（用户 2026-09-05 的交代）。
- 每轮结束更新 `reference/GOAL.txt` 的现状块：条数、义项数、段完成度、交付文件边界、下一步。
  条数与义项数**要从脚本读**（`check-merged.py` / `audit-padding.py`），别手写。

## 二、每批固定动作（顺序不能换）

```bash
# 1 写之前：把这一段的习语清单补进 audit-idioms.py 的 CHECK，再动笔
# 2 写：heredoc 追加到新文件 wordlists/B-<起>-<止>.txt（每条词头下面一行音标，见第十节）
python3 scripts/check-wordlist.py wordlists/B-XXXX-YYYY.txt   # 先查这一批，别先 resplit
python3 scripts/renumber.py                                    # 往老词条插过义项就要跑
python3 scripts/resplit-b.py >/dev/null
python3 scripts/merge-wordlist.py B 2500 >/dev/null            # 交付文件每份 2500，满了自动顺延
bash scripts/gates.sh <段> <这批的词头...>                      # 十三道闸门（第十三道查音标行）
python3 scripts/scan-dupes.py --loose                          # 判重（退出码恒 0，要自己看）
git add -A && git commit -q -m "..."
```

**`bash scripts/gates.sh ... | tail -N && git commit` 会把没过闸的东西提交上去。**
管道的退出码是 tail 的，永远是 0 —— gates.sh 自己那个 1 被吃掉了。
2026-09-20 就这么提交过一次（三条 audit-swallowed 没处理），只好 amend 回来。
**办法**：gates 单独跑、看完输出再敲 commit；要串就写
`bash scripts/gates.sh ha; [ ${PIPESTATUS[0]} -eq 0 ] && git commit …`，
别把 gates 放在管道左边。

**顺序要点**：check-wordlist 必须在 resplit 之前 —— resplit 会把污染打散到多个文件里，
定位起来麻烦得多。

**词头要照字面写进命令行，别用变量传**：Bash 工具跑的是 zsh，`W="a b c"; gates.sh he $W`
会把整串当成一个参数，scan-dupes 只报「指定 3 条词头」—— 通道 5 等于没查。
多词词头加引号（`"het up"`、`"hors d'oeuvre"`），或者整条包进 `bash -c '…'`。

**单文件那一步报「密度低于基线」多半是假警报**：新文件里只有一两条大词时，
批均等式按那一个文件算会偏低。以 resplit 之后 gates 里那一道 check-wordlist 为准；
要是 resplit 后仍报某个分块低于 2.13，那才是真的 —— 办法是给真有第三条搭配的词补上
（suffer from hypertension），不动基线、不凑假等式（hy- 段 2026-09-26）。

## 三、收词筛选（客观类别，不按「看着像不像词」判）

**剔除**（写进 `reference/exclude.txt`，一行一个词加理由）：

- 地区变体英语词头：澳新、苏格兰、北英格兰、爱尔兰、印度、南非、东非、威尔士、
  加拿大专有说法。**只剔词头本身属该变体的**；通用词的某个义项属该变体、
  以及澳新的动植物名，都留着。
- 只在单一窄专业内部使用、不进通用语的术语（durative、ergative、endoglossic、
  exonormative、espressivo 这一类）。
- 整词已废、现代英语不再用的古旧词（archaic 但仍见于诗文引文的**留**，如 ere、eldritch）。
- 商标、纯人名地名、词缀（-ese、-esque）。
- 清单里被截断的残片（dulce、dum 那种）。
- 印度食物名一律不收。

**保留**：小写带句点的书面缩写（ed.、e.g.、esp.、et al.、etc.）——
2026-09-09 撤回过一次错误排除：排除名单里的「缩写」指全大写机构缩写。

**拿不准就收。** 少收的代价比多收大。动笔前把整段清单一次扫完剔干净，别边写边判。

## 四、写词条的要求（硬规则见 CLAUDE.md，这里是每批都要自查的）

1. 每条 **必须有「核心：」块**、**至少 2 个义项**。冷僻词就写两个，**两个是硬底线，
   不是凑数的起点** —— 凑第三个必出元评论假义项。
2. 每个例句紧跟一行 `= 中文译文`；译文里引用英文词要加引号。
3. **例句要有承载力**：批均词数 ≥ 9、批均「词头之外的实词种类」≥ 4。
   给场景（谁、什么情况、结果如何），顺带塞一两个值得学的搭配。
4. **等式行只在真有可复用的搭配时才写**。密度不够（批均等式 < 2.13）时，
   补的必须是词典里本来就有的真搭配，不是给每条硬凑一句。
5. **核心块讲那个词，不讲那个东西**：讲语域、搭配、跟近义词的分别；
   不讲「它能长到两米」「它产于地中海」。
6. **辨析行别点名还没写的同前缀词** —— audit-swallowed 会当场报「被吞掉」。
   要么把那个词提到本批一起写，要么改成不点名的说法。
7. **多词条目并入，字面必须连着**：coverage 按连续字符串搜。
   `endow somebody with something` 过得了 audit-swallowed（它会剥掉占位词），
   过不了 coverage —— 两种写法都要留一个。
8. 同一条词条里不许有重复义项。判据看**等式**：左边剥掉冠词占位词后相同、
   右边中文也基本相同，才算重复。改法是**改等式与场景**，不是删义项、也不是编新场景。
9. 并入之前先问「这个宿主跟它真的同源吗」——`cult` 吞掉 `cultivable` 那次就是没问。
10. **形容词的 -ly 副词、比较级与最高级不单立，一律并进形容词词条**（用户 2026-09-10 定）。
    只有当那个派生形式**另有形容词没有的义项**时才留着单立，
    例外写进 `reference/derived-keep.txt`（一行一个加理由）——
    badly 的「非常」、easily 的「无疑／很可能」、fairly 的「还算」、
    famously 的 get on famously、duly 的「果然」都是这么留下来的。
    第十一道闸门 `audit-derived.py` 查这条；并入时若副词与形容词前四个字母
    对不上（ably/able、busily/busy），还要往 `inflections.txt` 补一行，
    否则 coverage 的派生判定认不出，audit-swallowed 会报「被吞掉」。

## 五、闸门报错时先判断是词条错了还是尺子错了

改脚本的先例有五次（拉丁复数、重音折叠、EQ 正则只认 ASCII…）。
但**一句话触发启发式规则**通常改词条更划算：
especially 那句「everybody said it was」被元评论检查逮到，改例句而不是松尺子 ——
那道检查逮过太多真元评论，为一句话松绑不值。

**一直报绿或一直报红的闸门等于没有闸门。** 新加检查一定要**故意塞个错进去验一遍**。

## 六、这几轮反复踩的坑（写之前扫一眼）

1. 核心块预告了同源词却没给例句 → audit-swallowed（最高频，已出现十余次）。
1b. **并入可数名词时只写了复数形，词头的单数没露过面** → 同样被 audit-swallowed
   报「被吞掉」。globule、gramme、greenback、greengage、grenadier 都栽在这一条。
   动笔时的习惯：**等式左边写单数**（a greenback = 一张美钞），复数那句
   退成底下的补充例句。
2. 例句偏薄 → audit-examples（改例句，不动阈值）。
3. 批量补等式的脚本按字符串锚点插入时，锚点要选**那条义项独有**的字符串 ——
   ethene 那次插错义项，直接造出「两个义项等式相同」。
4. 思考注记漏进 heredoc → check-wordlist 的草稿行检查（ergo 那次）。
5. A 表教过的用法 B 里没有 → audit-ab（email address、be equipped with、
   exclusive of、exert oneself 都是这么补上的）。只是初学者脚手架的（feel hungry）
   按 CLAUDE.md「A 不是 B 的标尺」记进 reference/a-only.txt，不补。
6. **1b 仍是最高频的坑**（2026-09-20 到 09-27 又栽了十来次：heroic couplet、hijacker、
   hiker、homing pigeon、ice skate、identical twin、idler…）。每并入一个可数名词都问一句
   「单数在等式左边露过面没有」。
7. **讲解行里写「更正式的写法是 X」「美式说 X」也算点名** —— hinge upon、hired hand、
   horseback riding 都这么被报「被吞掉」。要么给 X 一个义项，要么改用中文说。
8. **大词的例句里别顺手用同前缀的另一个词条**：hot 的例句里写了 hotel，coverage 就按
   前缀把 hotel 判成「已收」，从待新写里消失，而且没有闸门会报（它在例句里）。
   写完大词，回头确认同前缀的单词都还在待新写清单上（house 那次查过，没吞）。
9. **核心块写「东西」而不是「词」**仍会反复出现（海鲜酱配料、大猪草灼伤皮肤、
   马毛旧用途、臭氧层、花色随酸碱变…）。闸门拦不住，全靠写完自查。
10. **说名称的句子是元评论**：「管它叫…」「历史学家避免用这个词」「过去称为…」——
   冒犯语、旧称、别名最容易写成这样。audit-padding 只拦得住一部分，自查。
11. **变体与截短要分清**：拼法变体、不规则变形登 inflections.txt（hm→hmm、
   humor→humour、ikon→icon）；**截短词单立**（homie 不能挂在 homeboy 下）。
   登完 inflections.txt 必须重跑 `python3 scripts/gen-forms.py`（第十二道闸门会拦）。
12. **词根是名词的 -ly 词**（hourly、daily）不归 audit-derived 那条规矩管，
   登进 derived-keep.txt 写明「词根是名词」。
13. **拼法变体不要单开义项写「某某把它拼成…」** —— 那是元评论，audit-padding 当场拦（lychee、mileage 连栽两次）。
   做法：变体登 inflections.txt，然后在宿主词条已有义项下面**加一条等式**（`milage = 里程（mileage 的另一种拼法）`），
   想配例句就写一条真用法（She bought a kilo of fresh lichees…）。
14. **登了 inflections 的同形词仍要单立**：left→leave、lost→lose、lay→lie、found→find 这类，登记后 coverage 不再把它列进
   待新写，但「左」「迷路的」「放」这些独立的词条照样要写 —— 写到那个位置自己记着。
15. **并进主条却前四个字母对不上的派生词，coverage 不认**（lazily / laziness→lazy、mating→mate、mining→mine、
   layperson / laywoman→layman）。两条路：登 inflections（仍并在主条里），或者单立。audit-padding 报
   「例句里没有词」多半也是这个原因（men、left、lay、lying 都是登记后解决的）。
16. **讲解行密度是整块算的，会随重切漂移**：三四十义的大词必然把所在切块拉到基线下；隔几批以后，
   早先通过的切块也可能因为总条数变了、边界挪动而重新掉线。每批跑完都看一眼
   `python3 scripts/check-wordlist.py 'wordlists/B-*.txt' | grep '←'`，掉线就给那一块补讲解行。
   **预防**：大词动笔时至少一半义项直接配讲解行；两义小词每个义项都配一行。
17. **高频小词、科技名词、单义名词的例句最容易写短**（like、may、menu、microwave、minute…）。
   每句动笔就带上时间、地点、原因或结果，目标十个词以上；别等 audit-examples 报了再补。
18. **只有一个意思的名词**（minidress、minibus、megastore）两条例句别都配「a X = X」—— 等式相同会被判重复义项。
   第二条给一个真搭配（a wool minidress、a minibus meets the train）。同理，名词义和同形动词义
   （a minor in / minor in）剥掉占位词后等式相同，合成一个义项、挂两条等式。
19. **一段写完后再跑一次 coverage**：宿主词条写出来以后，才会冒出挂在它名下的「待并入已有词条」
   （machine tool、marriage certificate、marsh gas 都是这么补的）。用 `scripts/add-sense.py` 的 `add()` 补进宿主条，
   疾病名、X + 名词挂在别的字母宿主下的（Lassa fever→fever、lima bean→bean、meta-analysis→analysis）也用它。
20. **补丁脚本的 glob 要覆盖重切后的文件名**（`B-13[67]*.txt` 而不是只写 `B-137*`），并且**每次看打印的替换数**：
   匹配不到时替换数是 0，脚本不报错，闸门照旧红。
21. **中文译文和讲解行里不许出现数学符号、希腊字母等异体字符**（minus 那次写了 U+2212 的减号，check-wordlist 报
   「混入异体字符」）—— 一律用文字。
22. **audit-padding 的「元评论」偶有误判**：「says matins」被当成「某人 says 某词」的句式。换个动词（leads matins），别动尺子。
23. **gates.sh 传了还没有词条的段名会报「没有匹配的词条」**（kp、ly 刚开段时）—— 属正常，那一段有了词条再带上。
24. **义项超过 ㊿ 用 ❶❷❸…**（NUMS 共 80 个，low 53 义是头一个）；自己数义项的正则要带上 `❶-❿`。
25. **scratchpad 路径每个会话不同**，闸门输出写到当前会话的 scratchpad（系统提示里给），别照抄旧路径。

## 七、另一条并行的活：给拓展块补例句（用户 2026-09-11 定）

词条末尾那些「等式但没有例句」的拓展行（`flight deck = 驾驶舱`、
`A-list = 一线名流`），用户要求补上例句 —— `coverage` 里那句
「写进词根条里**并补例句**」本来就是这么定的，之前的并入 pass 只写了等式。

**范围（用户裁定，别自行放大或缩小）**

- 只补 **B 表**；A 表一概不动。
- **辨析类不补**：近义对照 / 注意别混 / 注意区别 / 反义词 / 配对词 /
  注意地域 / 注意拼写 / 英美差别。这些块是对照表，配例句反而冲散对比。
- 剩下的都补：条目末尾无标签挂上去的并入短语、「常用搭配：」、「词族：」。
- 三类看着像等式、其实不是搭配的，`need-example.py` 已自动剔掉：
  左边没有拉丁字母的标注、整句对照、右边在讲拼法／变形／同义的。

**每轮怎么做**

```bash
python3 scripts/need-example.py de di --tier1 --list   # 挑一段，看要补哪些
# 写 /tmp/fill_data.py：F = {("词头","等式左边原样"): ("English sentence.","中文译文"), ...}
python3 scripts/fill-example.py                        # 插入
python3 scripts/check-wordlist.py 'wordlists/B-[0-9]*.txt'
python3 scripts/merge-wordlist.py B 2500 >/dev/null
bash scripts/gates.sh <段>                              # 每两三批跑一次整段
python3 scripts/scan-dupes.py --loose
git commit -m "拓展块补例句（N）：<段> 若干条"
```

**例句的标准跟义项例句一样**：11–14 词、有场景（谁、什么情况、结果如何）、
不谈这个词本身（元评论）、译文里不混英文、**搭配本身必须原样出现在句中**
（渲染时靠字面匹配高亮）。同一条搭配在别处已有词条的（词族那类），
场景要另起，别跟那个词条自己的例句撞 —— scan-dupes 会报。

**进度从脚本读，别手写**：`python3 scripts/status.py` 末尾会打出两档的剩余条数。

## 八、当前进度（2026-10-05，k → mi 这一长段会话收尾时写）

- **条数、义项数、段完成度一律从脚本读**（`status.py` / `check-merged.py` /
  `coverage.py`），这一节只记「现在在哪、下一步干什么、有什么没收尾的」。
  **最新的现状块在 reference/GOAL.txt 顶部**，比这一节更细，下一批的词头清单也在那里。
- B 词表 14486 条，词典序 a → mirth；A 表 3002 条。**a–l 十二个字母收完**，m 字母写完 ma- / me-，
  mi- 写到 mirth，**下一批从 mis-selling 起**（mis- 一族约 135 条）。
- **交付按台账走**（`reference/B-delivered.txt`，见第二节与 CLAUDE.md）：前五份用户已导入 app；
  第六份现为 `B-merged-12501-14486.txt`（1986 条），**满 2500 条时主动告诉用户并用 SendUserFile 发过去**。
- **开新字母、新段的固定准备**（l、m 两个字母都是分段做的，一段一做，别一口气判完整个字母）：
  ① 大写词头：从 `reference/OALD10_Cleaned_Learning_List.csv` 第二列列出该字母的大写词头，
     按「已进词汇才收」逐条判，收的登进 `proper-nouns-keep.txt` 并在段首写判语注释
     （纯人名地名、全大写缩写、商标、称谓缩写不收）—— **整个字母一次判完**；
  ② exclude：扫该段「待新写」「待推迟」「待并入」三张清单，把地区变体（印度、东非、南非、西非、澳新、苏格兰、爱尔兰）、
     窄专业、专名与书名残片、小写单位缩写、冒犯性标签、清单里的重复写法登进 exclude.txt；
  ③ inflections：不规则过去式与复数、美式拼法、拼法变体（登完跑 gen-forms.py）；
  ④ audit-idioms：给该段的大词补习语清单（插在 `'image':` 那个键前面，先 grep 同名键）；
  ⑤ 提交一笔「X 段开段准备」，再动笔。
- Mr / Mrs / Ms 用户 2026-10-07 裁定收，已写。
- **蔑称**：用户 2026-10-07 裁定 nigger 照 Negro 条写法收，同日又裁定 Paki、Polack 不收 —— 前一条裁定只针对那一个词，
  别的种族、族群蔑称照「冒犯性标签不收」办，不外推，也不必逐个问。
  2026-10-09 又裁定 poof（对男同性恋的蔑称）不收：针对性取向的蔑称同样不收。
- **mo- / mu- / my- 三段的准备还没做。**
- **排序规则**：按词（word-by-word）排，和原始 CSV 的逐字母排在带空格、连字符的词头上有约百处相邻逆序；
  用户 2026-10 问过、知道、没要求改，保持现状。
- **推送**：origin 在 51e34015；本地领先两百多笔提交全没推，**push 照旧等用户开口**。

## 九、iPad app（index.html 单文件）也归这个仓库管

- **导入报「重复」＝交付文件边界挪了**（2026-09-29 用户导入第五份报 7 个重复、实导 2493）：
  原来按位置每 2500 条切，回头补写前面的词会把后面所有份的边界往前推。已改为按交付台账
  `reference/B-delivered.txt` 切（详见 CLAUDE.md「交付文件按台账切」）：已交付的份词头构成不变，
  新词只进下一份。**再遇到这种报告**：拿 git 里各版本合并文件的词头集跟现在比，找出重复数对得上的
  那一版，就知道 app 里实际有什么；台账要与之一致。

用户会报 app 的 bug，改完要自己在浏览器里验证，并且**同时升两个版本号**：
`index.html` 里的 `APP_VERSION` 与 `sw.js` 里的 `CACHE`，否则装了 PWA 的设备
拿的还是旧缓存（stale-while-revalidate：打开一次拿旧的、后台更新，第二次才生效）。

已修过的三个，改法可作先例：

- **例句高亮认不出变形**（2.0.3，2026-09-23 用户在 iPad 上报：An hour、cannot、
  Canned soup 不亮，can't 只亮一半）。改成先列词形再匹配：原形、规则变形
  （双写辅音、去 e、y→i、f→ves）、`IRREG` 表里的不规则形，外加 n't / 's 这类
  缩略词尾连着亮；三层依次退：词头原样 → 所有词形 → 词干前缀（派生词）。
  义项例句优先亮这个义项自己的等式（hope against hope 整条亮）。
  `IRREG` 由 `scripts/gen-forms.py` 从 `inflections.txt` 加一张通用不规则表生成，
  **改了 inflections.txt 要重跑它**（第十二道闸门 `gen-forms --check` 会拦）。
  体检：`node scripts/audit-highlight.js`，修前整句不亮 12.6%，修后 0.9%。

- **例句高亮**（2.0.2）：老规则只取词头第一个词、再放宽词尾 0–6 个字母，
  `a cappella` 变成匹配 `a[a-z]{0,6}`，把 and/an/about 全涂绿。
  现在整条词头作为整体匹配，词尾变形只在单词且 ≥4 字母时允许，且**只高亮第一处**。
- **背诵会话计数失准**（2.0.1）：`getWords` 会把解析不出的 id 静默丢掉，
  于是「下一个」在真正的末尾之前变灰、整组永远判不了完成；
  `learnedCount` 又只在 toggleMark 里重算，漂了就一直错。
  现在 `startLearn` 开背前对账（修 wordIds、重算 learnedCount），
  并在导航条加了「找未标记」。

## 十、音标（用户 2026-10-06 要求：给所有词条补音标）

**用户定的四件事**：只标英式；下载开源读音词典打底；**app 的导入逻辑不改**（已导入 iPad 的词条不更新，
只管以后新导入的）；A、B 两张表都补。

**格式**：词头下面单占一行，以「/」开头，写法见 CLAUDE.md「音标行」。闸门的字符集放行国际音标，
`scripts/ipa.py` 里的 `LINE_RE` 管这一行的合法性（check-wordlist 与第十三道闸门都用它）。

```bash
python3 scripts/ipa.py status              # 两张表各缺多少
python3 scripts/ipa.py missing mu -n 300   # 列出某个前缀下缺音标的词头
# 把手写的追加到 data/pron/manual.tsv（词头<TAB>音标行），然后：
python3 scripts/ipa.py set data/pron/manual.tsv
python3 scripts/merge-wordlist.py B 2500 >/dev/null     # 改了分批文件必须重新合并，否则 check-merged 红
python3 scripts/merge-wordlist.py A 3000 >/dev/null; rm -f wordlists/A-merged-3001-3002.txt   # A 的尾巴不交付，别留
bash scripts/gates.sh <段>
```

**现状从 `ipa.py status` 读**。2026-10-06 自动填了 7728 条（A 表 93%、B 表 33%），余下一万条左右：
Britfone 里没有的（九千多）、多词与带连字符的词头（五百多）、重音有两读的（199 条，多半是名动异读，
要手写成两段）。**Britfone 本身有错**（抽查 170 条错 1 条：caffeine；另见过 refugee、employee），
而且名动异读的词它常只给一个读法（separate、use、close、lead、live…）—— 这一类要另列清单逐个改。

**余下的怎么补（用户 2026-10-06 同意再下载一份词典；下载后量出来不合格，改成「草稿加逐条校对」）**：
第二份 `data/pron/ipa-dict.en_UK.txt` 是语音合成软件生成的，跟 Britfone 对有一成多读法不同，不能直接填。
做法是 `python3 scripts/ipa.py draft B -n 330` 出草稿，**逐条看、逐条改**：把要改的与打「?」的写成一个改正文件
（词头<TAB>音标行），再 `python3 scripts/ipa.py accept <改正文件> B -n 330` —— 没动的草稿照收、动过的用改正文件里的，
一并记进 manual.tsv 并写入词表（**accept 的参数要跟 draft 的一模一样**，它按同一组词头取草稿）。
头三批 990 条里，要改或手写的占四成多，所以「照收」的那六成也得是真看过的。
草稿里最常见的错，校的时候专门盯：元音间的 s / z（muse、residue）、a 读 æ 还是 ɑː、非重读前缀 en- / ex- / ob- / sub- 的元音
（应是 ɪn、ɪk、əb、səb）、双写辅音读成两个（innate）、dis- / mis- 后面的音节界、重音位置（外来词、三音节以上的词）、
多词词头的主次重音（草稿只是各部分拼起来，要自己定）。草稿打「?」的是名动异读或词典里没有的，直接手写。
A 表 2026-10-06 已全部补完（216 条手校）；B 表从字母 a 起按前缀一批批来。

**音标行不是正文，读词条正文的脚本都得跳过它**（2026-10-06 栽过）：lentil 的音标 `/ˈlentəl/` 里有 lent 这串字母，
coverage 就当成「lentil 条里提到了 lent」，audit-swallowed 报「lent 被 lentil 吞掉」。已在 coverage.py 的 collected() 里
把以「/」开头的行剔掉（audit-swallowed 用的是它的结果）。check-wordlist、audit-depth 也各自跳过。
**以后新写读正文的脚本，第一步先剔音标行。** 那一次还犯了老错：闸门红着就把提交串在同一条命令后面提了上去 ——
提交必须写成 `bash scripts/gates.sh … && git commit …`，不能用分号接。

**新写词条时**：每条词头下面直接写音标行；写完 `gates.sh` 第十三道会查这一批点名的词头有没有。
存量 2026-10-06 已全部补齐，`ipa.py check` 从此要求全表每一条都有音标，缺一条闸门就红。

