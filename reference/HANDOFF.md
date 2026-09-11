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
# 2 写：heredoc 追加到新文件 wordlists/B-<起>-<止>.txt
python3 scripts/check-wordlist.py wordlists/B-XXXX-YYYY.txt   # 先查这一批，别先 resplit
python3 scripts/renumber.py                                    # 往老词条插过义项就要跑
python3 scripts/resplit-b.py >/dev/null
python3 scripts/merge-wordlist.py B 2500 >/dev/null            # 交付文件每份 2500，满了自动顺延
bash scripts/gates.sh <段> <这批的词头...>                      # 十一道闸门
python3 scripts/scan-dupes.py --loose                          # 判重（退出码恒 0，要自己看）
git add -A && git commit -q -m "..."
```

**顺序要点**：check-wordlist 必须在 resplit 之前 —— resplit 会把污染打散到多个文件里，
定位起来麻烦得多。

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
2. 例句偏薄 → audit-examples（改例句，不动阈值）。
3. 批量补等式的脚本按字符串锚点插入时，锚点要选**那条义项独有**的字符串 ——
   ethene 那次插错义项，直接造出「两个义项等式相同」。
4. 思考注记漏进 heredoc → check-wordlist 的草稿行检查（ergo 那次）。
5. A 表教过的用法 B 里没有 → audit-ab（email address、be equipped with、
   exclusive of、exert oneself 都是这么补上的）。

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

## 八、当前进度（2026-09-11）

- B 词表 **10060 条**，词典序 a → geochemistry；交付文件第五份已开头
  （`B-merged-10001-*.txt`）。A 表 3002 条。
- **词典本身**：f 段 99%（剩的是待推迟），g 段在写，**下一批从 geode 起**
  （geography / geology / geometry / German / germ / gerrymander 一带）。
  G 段大写词头 51 条已登记进 proper-nouns-keep。
- **补例句**：tier1 剩约 836，tier2（词族）约 849。**d 段与整个 e 段都清空了**，
  **下一段 fa / fe / fi**（fi 53、fl 48、ex 那种上百条的大段按词头分两三批做，
  每批 35–65 条，各自过闸各自提交）。
- **push 策略**：用户 2026-09-11 说「补完一起推」——
  补例句这件事做完之前，只在本地提交，不要 push。

## 九、iPad app（index.html 单文件）也归这个仓库管

用户会报 app 的 bug，改完要自己在浏览器里验证，并且**同时升两个版本号**：
`index.html` 里的 `APP_VERSION` 与 `sw.js` 里的 `CACHE`，否则装了 PWA 的设备
拿的还是旧缓存（stale-while-revalidate：打开一次拿旧的、后台更新，第二次才生效）。

已修过的两个，改法可作先例：

- **例句高亮**（2.0.2）：老规则只取词头第一个词、再放宽词尾 0–6 个字母，
  `a cappella` 变成匹配 `a[a-z]{0,6}`，把 and/an/about 全涂绿。
  现在整条词头作为整体匹配，词尾变形只在单词且 ≥4 字母时允许，且**只高亮第一处**。
- **背诵会话计数失准**（2.0.1）：`getWords` 会把解析不出的 id 静默丢掉，
  于是「下一个」在真正的末尾之前变灰、整组永远判不了完成；
  `learnedCount` 又只在 toggleMark 里重算，漂了就一直错。
  现在 `startLearn` 开背前对账（修 wordIds、重算 learnedCount），
  并在导航条加了「找未标记」。
