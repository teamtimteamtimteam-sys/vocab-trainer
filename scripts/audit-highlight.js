#!/usr/bin/env node
// 例句高亮体检（2026-09-23）：用 index.html 里的真实高亮代码，把 B 表每个义项例句
// 都跑一遍 —— 先认本义项的等式、再退回词头，跟 app 渲染时一模一样 —— 数一数
// 「整句一处都没亮」的有多少。只报告，退出码恒 0。
// 用法：node scripts/audit-highlight.js [--list]
// 基线：修之前 12.6%（5210 句）；2.0.3 之后约 1.0%，剩下的多是例句用了
// 近义说法或截短词（autofill 之于 autocomplete、hetero 之于 heterosexual）。
const fs = require('fs'), path = require('path');
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const h = fs.readFileSync('index.html', 'utf8');
const a = h.indexOf('/* -------------------------------------------------------- 高亮目标词 */');
const b = h.indexOf('/* ---------------------------------------------------------- 词条渲染 */');
const [hl, key] = new Function('esc', h.slice(a, b) + '\nreturn [hl, hlSenseKey];')(esc);
// 编号字符取 check-wordlist 的 NUMS 原样（别用区间 ①-㊿：它把「」也圈进去了）
const NUMS = new Set([...'①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴⓵⓶⓷⓸⓹⓺⓻⓼⓽⓾']);
let tot = 0; const miss = [];
for (const f of fs.readdirSync('wordlists').filter(f => /^B-\d+-\d+\.txt$/.test(f)))
  for (const p of fs.readFileSync(path.join('wordlists', f), 'utf8').split('\n\n')) {
    const L = p.trim().split('\n'); const head = (L[0] || '').trim(); if (!head) continue;
    for (let i = 0; i < L.length; i++) if (NUMS.has([...L[i]][0])) {
      const ex = [...L[i]].slice(1).join('').trim(); const notes = [];
      for (let j = i + 2; j < L.length && !NUMS.has([...L[j]][0]); j++) {
        const m = L[j].match(/^(.+?) = /); if (m && /[A-Za-z]/.test(m[1])) notes.push({ t: 'eq', lhs: m[1].trim() });
      }
      const k = key(notes, head); const r = k ? hl(ex, k, head) : hl(ex, head); tot++;
      if (!r.includes('class="hl"')) miss.push(head + ' | ' + ex);
    }
  }
console.log('例句 ' + tot + ' 句，整句一处没高亮上 ' + miss.length + ' 句（' + (100 * miss.length / tot).toFixed(1) + '%）');
if (process.argv.includes('--list')) console.log(miss.join('\n'));
