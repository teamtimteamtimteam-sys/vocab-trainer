#!/bin/bash
# 每批回填/新写之后要跑的十一道闸门 —— 一道一道跑，各记各的退出码。
# 第十道 check-merged 是 2026-09-08 加的：交付用的合并文件必须跟分批文件
# 一字不差、整份按词典序（用户当天的要求：每份 2500 条都要有序、不漏条）。
#
# 为什么要有这个脚本：2026-09-06 之前是手敲九条命令，串成
# `audit-examples && audit-padding; echo $?` 的时候前者失败就短路，
# $? 报的是前者的码，把没过闸的东西提交了上去（accurate 那次）。
# 这里每道单独跑、单独记码，最后汇总，结构上就串不起来。
#
# 用法：bash scripts/gates.sh <字母段> <这批的词头...>
#   bash scripts/gates.sh c charter chorus clay ...
#   bash scripts/gates.sh a,c criminal crook ... abrasive across
#
# 字母段可以用逗号写多个 —— 分段的三道（coverage / audit-depth /
# audit-prefix）会对每一段各跑一次。待回填清单是按「义项数多的在前」排的，
# 不是按字母，所以一批里常常同时有 c- 和 a- 的词；只报一段的话，
# 另一段的覆盖率就没人看着。
#
# 退出码：有任何一道不为 0 就是 1。
set -u
segs="$1"; shift
fail=0
run() {                       # run <名字> <命令...>
  local name="$1"; shift
  "$@" > /tmp/gate.$$ 2>&1
  local code=$?
  if [ $code -eq 0 ]; then
    printf '  ✅ %-28s exit=%d\n' "$name" $code
  else
    printf '  ❌ %-28s exit=%d\n' "$name" $code
    tail -20 /tmp/gate.$$ | sed 's/^/       /'
    fail=1
  fi
  rm -f /tmp/gate.$$
}
echo "十一道闸门（段：$segs）"
run check-wordlist  python3 scripts/check-wordlist.py 'wordlists/A-*.txt' 'wordlists/B-*.txt'
for seg in ${segs//,/ }; do
  run "coverage $seg"     python3 scripts/coverage.py "$seg"
done
for seg in ${segs//,/ }; do
  run "audit-depth $seg"  python3 scripts/audit-depth.py "$seg"
done
run audit-swallowed python3 scripts/audit-swallowed.py
run audit-padding   python3 scripts/audit-padding.py
run audit-ab        python3 scripts/audit-ab.py
run audit-idioms    python3 scripts/audit-idioms.py
for seg in ${segs//,/ }; do
  run "audit-prefix $seg" python3 scripts/audit-prefix.py "$seg"
done
run audit-examples  python3 scripts/audit-examples.py "$@"
run check-merged    python3 scripts/check-merged.py B
run audit-derived   python3 scripts/audit-derived.py
if [ $fail -eq 0 ]; then echo "全部通过"; else echo "有闸门没过 —— 别提交"; fi
exit $fail
