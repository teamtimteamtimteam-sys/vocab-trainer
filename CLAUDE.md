# 背单词 app + 词表项目

**新会话第一件事：`python3 scripts/status.py`** —— 它从 wordlists/ 现算进度、
闸门阈值和下一步动作，不会像写死的文档那样过期。本文件只写不会变的规格与规则。

## 两份词表，规格完全不同

| | A | B |
|---|---|---|
| 使用者 | 英语初学者 | 雅思 6 分以上 |
| 排序 | **按词频，由简到难** | **牛津高阶第 10 版词典序** |
| 收词 | 高频词，目标 5000 | **全量收录，约 6 万词条** |
| 每条义项 | 3 个 | **收全该词在牛津高阶的所有义项** |
| 每条结构 | 例句 + 讲解 | **「核心：」总括讲解** + 每个义项造句讲解 |
| 分批依据 | 每批约 45 词 | **每批例句总数**（go/do 这类词一个就几十句） |
| 合并单位 | 3000 词一份 | 待定 |

**A 绝不能排字母序** —— 它靠词频排出难度梯度，排字母序会毁掉这个梯度。
`merge-wordlist.py` 只对 B 重排。

## B 的收词边界（用户裁定，别自作主张）

只收**真正的单词**。

- ✗ **词缀条目**：`a-` `anti-` `-able` `-ation` —— 构词知识写进真实词条的「构词」行更有用
- ✗ **全大写缩写**：AA、AIDS、AOB
- ✓ 连字符复合词：able-bodied、age-old
- ✓ 多词固定条目：ad hoc、all right、air force、according to
- ✓ 外来短语：à la carte、a cappella、a priori、a fortiori
- ? 小写带句点缩写 a.m. 暂留，未经裁定（p.m./e.g./i.e./etc. 同此）

## 排序：按词，不是按字母

空格和连字符是词边界，边界处「更短的先排」：

```
a → a cappella → a fortiori → à la carte → a posteriori → a priori → aardvark
ad → ad hoc → ad lib → adage
all → all right → all-round → allay
always → a.m. → amalgam
```

忽略空格的话 `a priori` 会被拼成 apriori 排进 ap- 段 —— 那是错的。
排序键在 `scripts/wordkey.py`，三个脚本共用，别再各写一份。

## 工作流

```bash
python3 scripts/status.py                    # 看状态
python3 scripts/pull-pending.py <词...>       # 从归档区取回复用（只读）
python3 scripts/renumber.py '<glob>'          # 重排 ①②③ 编号
python3 scripts/check-wordlist.py 'wordlists/A-*.txt' 'wordlists/B-*.txt'
python3 scripts/resplit-b.py                  # 按词典序重排并均匀分块
python3 scripts/audit-prefix.py a             # 查有没有整段漏掉
python3 scripts/pull-pending.py --prune       # 清理已收录的归档条目
python3 scripts/merge-wordlist.py A 3000      # 合并成可导入的大文件
```

**动笔前必须先列出该字母段的牛津高阶词条清单跑差集。** 凭手感列词已经出过四次
漏收，而且每次都是用户发现的：

| 何时 | 漏了什么 |
|---|---|
| a 段初次 | 只收了 10%（autumn、adjacent、acquaintance 这类常用词都不在） |
| ab- 段 | 只收了 31% |
| ao- / aa- | 整段跳过 |
| al- 段 | albeit、although（归档区一直摆着，我没核对） |
| as- 段 | 宣布收全 77 条，实际应有 110 条，漏 32 条 |

**「宣布收全」不等于收全** —— 我列的清单本身就是凭记忆写的，它短，
差集自然显示「无遗漏」。**差集只能证明「我列的都收了」，不能证明「我列全了」。**
抽查证实这是系统性的：ao- 漏 aoudad，aq- 漏 aquaplane/aquavit，
at- 漏 atavistic/atheism/atoll/atonement/atrium/attaché/attainable/
attenuate/attribution/attune。

**词头清单已经到位**：`reference/OALD10_Cleaned_Learning_List.csv`，67264 条。
完整性检查从此是机器的事：

```bash
python3 scripts/coverage.py a        # 按双字母段报缺词
python3 scripts/coverage.py ab ac    # 看具体缺哪些词
```

脚本按用户裁定的边界过滤清单（词缀、全大写缩写不收），并把清单里同一条目的
空格版与连字符版（abide by / abide-by）归一化合并。

**第一次跑它就推翻了此前的结论**：我宣布「a 字母全部收全 1288 条」，
实际清单有 3021 条，只收了 41%，26 个双字母段无一收全。漏的主要是三类：
多词条目（absolute zero、absentee landlord、above board）、
短语动词（abide by、abound in）、派生形式（abrasively、absent-mindedness）
—— 全是我此前当作「写进别的词条里的注释」而没单列的。
**每段动笔前和收尾后都必须跑 coverage.py，不要再凭记忆列清单。**

## 质量闸门：改尺子之前先想清楚

闸门在 `check-wordlist.py`，pre-commit 钩子会拦住不合格的提交。

**已经废弃过五把尺子**，规律很清楚：**凡是「除以词条数」的批均指标，都会被
「这批碰巧是哪些词」左右，量不出投入**。字符/词条、字符/义项、批均义项都因此
作废。现在留下的是逐条规则（每条至少 2 个义项、必须有「核心：」块）加两个不随
多义性漂移的密度指标。

**闸门拦下时，先判断是我写薄了还是尺子错了，别条件反射去调基线。** 曾为消一个
误报放宽中英混杂检查，结果放过了真错误（「他kicked了球」）。正确做法是改内容：
引用英文词加引号、近义对照写成 `abate = 平息（正式）` 的等式形式。

## 已经踩过的坑

- **`git add -A` 盲提交**曾把用户在 Finder 里的删除一并提交，线上 404。提交前
  先 `git status --short` 看一眼。
- **`chunks[-2] += chunks.pop()`** 的求值顺序陷阱覆盖掉一整块，丢了 25 条词条，
  靠 checker 的跨批查重才发现。
- **pull-pending 曾「取出即删除」**，取出的内容被临时文件覆盖后 17 条词就没了。
  现已改为只读 + `--prune`（依据从「打算收」变成「确实收了」）。
- **拼接归档条目要显式补空行**，否则前后两块会粘成一条（aegis 曾被 aesthetic 吞掉）。
- **小尾巴文件会拉低批均**，`resplit-b.py` 已改为均匀分块，别再切「满 25 留尾巴」。

## app 本体

源码 `index.html` 单文件 PWA，数据存 IndexedDB(`vocab_v1`)，设置存 localStorage。
已部署到 GitHub Pages：https://teamtimteamtimteam-sys.github.io/vocab-trainer/
开发服务器见 `~/.claude/launch.json` 的 `vocab-trainer`（python3 http.server 8413）。
参数集中在 `index.html` 顶部常量 `GROUP_SIZE / INTERVALS / DAILY_CAP / DAY_START`。

### 用户拍板的规则，不要擅自改动

严格 50 词一组，不满 50 进暂存区等下次导入补满；艾宾浩斯**以组为单位**调度，
间隔 1/2/4/7/15/30 天共 6 轮，走完归档为「已掌握」；每日复习配额 5 组（逾期优先，
超出部分不计入解锁条件）；**门禁硬锁无后门** —— 当日配额未清完就不能背新词；
一次只背一组、一天只背一组（**但重置「今天消耗掉额度的那一组」会退还当日额度**，
靠 `lastNewGroupId` 判定；重置旧组不退，否则可以刷）；一天以凌晨 4:00 为分界；
复习只显示英文单词+英文例句，「记不清」的词展开全部内容并进入本组下一轮，
循环到全部「还记得」。

这些规则是一次 4 轮 grilling 逐条问出来并由用户裁决的，其中门禁和「一天一组」
是用户主动追加的自律需求，不是默认设计。

### 视觉

基底近白 `#FBFBFA`，绿与墨黑只渗在四角，中心用 `--core` 洗回近白保证正文不带色。
玻璃两级：内容面板 `--glass` .86、chrome `--glass-chrome` .72。品牌绿 `#1B8A3D`
用于色块/填充/进度环；浅色底上的**小号绿字**另用 `--green-text` `#177C34`
（品牌绿配白字只有 4.42，差 AA 一点点）；深色下两者都是 `#40B968`。
**绿色只用于重点与掌握状态，不作装饰**。字体三个角色：英文衬线 / 中文苹方 /
**数据等宽**（组号、12/50、R3、日期）—— 等宽绝不套在中文标签上，否则字距会把
「这里：」拉开。签名元素是螺旋进度环 `ring()`。用户明确否决过背景里的大螺旋球
线稿，不要再加回来。

收藏夹：星标在词卡标题栏，存 meta 的 `starredIds` 数组（数组顺序即收藏先后，
不动 IndexedDB schema）。复习点「记不清」给词的 `forgotCount` +1，供「忘得最多」
排序。**星标用墨黑不用绿** —— 绿在本项目表示「重点与已掌握」，收藏夹装的是没掌握
的词，用绿会让语义打架。

### app 相关的坑

① 主题差异**一律走 CSS 变量**，绝不写 `html[data-theme=dark] .某组件` —— 它的
优先级 (0,2,1) 会压过 `.btn.ghost`(0,2,0) 这类变体，曾导致深色下四个按钮黑字黑底。
② 别用 `JSON.stringify(字符串)` 往 `onclick="..."` 里拼参数，双引号会截断属性；
用 data 属性 + 事件委托。
③ JS 里的内联 `style="color:..."` 会压过 CSS 规则，改设计系统时要一起清。
④ 用户量级目标 10 万+ 词、分批导入，避免任何全表 `getAll()`（备份导出已改成
游标分块）。
⑤ iPad 上必须从主屏幕图标进入才能豁免 Safari 的 7 天存储清理。
**iOS Safari 打不开本地 file:// 网页**，必须走 HTTPS 托管 —— 这也是 Service
Worker 的硬性前提（局域网 http:// 不是安全上下文，注册会失败）。
⑥ **origin 绑定存储**：换域名等于清空进度，只能靠导出/导入备份 JSON 迁移。
⑦ 改代码后 `git push` 即自动重新部署；SW 用 stale-while-revalidate，
用户下次打开生效。
