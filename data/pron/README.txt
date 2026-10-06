Britfone 3.0.1（britfone.main.3.0.1.csv）
来源：https://github.com/JoseLlarena/Britfone  许可：MIT（Copyright (c) 2017 Jose Llarena）
2026-10-06 下载，用作英式音标的底本；scripts/ipa.py 把它的记法转成学习词典通行的写法。
抽查 170 条，硬错误约 1%（caffeine、refugee、employee 已在 manual.tsv 更正）；名动异读的词它常只给一个读法。
manual.tsv 是手写与更正的音标，写入时覆盖自动填的。

ipa-dict 的 en_UK（ipa-dict.en_UK.txt）
来源：https://github.com/open-dict-data/ipa-dict  data/en_UK.txt  许可：MIT
2026-10-06 下载。**这份是语音合成软件按规则生成的，不是人编的词典**：跟 Britfone 共有的 12996 个词里，
86.5% 完全一致，1.7% 只差重音，11.9% 读法不同，不同的里面相当一部分是它错
（conquer 读成 nk、muse / refusal / residue 读成 s、sample / drastic 读成 ɑː、apparatchik 重音错位、gymkhana 冒出 kh）。
所以只拿它出草稿（scripts/ipa.py draft），草稿逐条校过才记进 manual.tsv，绝不直接填进词表。
