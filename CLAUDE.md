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

**动笔前必须先列出该字母段的牛津高阶词条清单跑差集。** 凭手感列词已经出过三次
漏收：a 段只收了 10%、ab- 段只收了 31%、ao- 和 aa- 整段跳过、al- 段漏了
albeit/although。归档区是现成的交叉验证源 —— 里面凡属于「已收全」段却不在
主表的，都是遗漏。

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

源码 `index.html` 单文件 PWA，部署在 GitHub Pages。规则参数集中在文件顶部常量
`GROUP_SIZE / INTERVALS / DAILY_CAP / DAY_START`。用户拍板过的规则和视觉裁决见
`~/.claude/projects/-Users-timchen/memory/vocab-trainer-ipad.md`，不要擅自改动。
