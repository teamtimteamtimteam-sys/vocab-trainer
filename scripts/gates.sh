#!/bin/bash
# 每批回填/新写之后要跑的九道闸门 —— 一道一道跑，各记各的退出码。
#
# 为什么要有这个脚本：2026-09-06 之前是手敲九条命令，串成
# `audit-examples && audit-padding; echo $?` 的时候前者失败就短路，
# $? 报的是前者的码，把没过闸的东西提交了上去（accurate 那次）。
# 这里每道单独跑、单独记码，最后汇总，结构上就串不起来。
#
# 用法：bash scripts/gates.sh <字母段> <这批的词头...>
#   bash scripts/gates.sh c charter chorus clay ...
# 退出码：有任何一道不为 0 就是 1。
set -u
seg="$1"; shift
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
echo "九道闸门（段：$seg）"
run check-wordlist  python3 scripts/check-wordlist.py 'wordlists/A-*.txt' 'wordlists/B-*.txt'
run "coverage $seg"   python3 scripts/coverage.py "$seg"
run "audit-depth $seg" python3 scripts/audit-depth.py "$seg"
run audit-swallowed python3 scripts/audit-swallowed.py
run audit-padding   python3 scripts/audit-padding.py
run audit-ab        python3 scripts/audit-ab.py
run audit-idioms    python3 scripts/audit-idioms.py
run "audit-prefix $seg" python3 scripts/audit-prefix.py "$seg"
run audit-examples  python3 scripts/audit-examples.py "$@"
if [ $fail -eq 0 ]; then echo "全部通过"; else echo "有闸门没过 —— 别提交"; fi
exit $fail
