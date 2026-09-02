#!/usr/bin/env python3
"""B 词表的词典排序键。三个脚本共用，避免各存一份走偏。

用「按词排序」（word-by-word），不是「忽略空格」（letter-by-letter）：
空格和连字符是词的边界，边界处按「更短的先排」。
    a → a cappella → à la carte → a priori → aardvark
    ad → ad hoc → ad lib → adage
    all → all right → all-round → allay
如果忽略空格，a priori 会被拼成 apriori 排进 ap- 段 —— 那是错的，
它属于 a 段。用户明确裁定过这一点。

标点（句点）直接去掉：a.m. 归到 am 的位置。
弯撇号归一化成直撇号：Adam’s 与 Adam's 必须算同一个键 ——
否则 coverage 拿清单里的弯撇号去比对词条里的直撇号，永远比不上。
重音字母归一化：à la carte 的 à 按 a 排。
"""
import unicodedata

def _fold(s):
    """去重音：à→a, é→e, ï→i。"""
    return "".join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def sort_key(headword):
    """按词切分后的元组，空格与连字符都算词边界。"""
    s = _fold(headword.lower()).replace('\u2019', "'")
    s = s.replace('-', ' ').replace('.', '')
    return tuple(w for w in s.split(' ') if w)

def prefix(headword, n=2):
    """按首词的前 n 个字母归段；首词不足 n 个字母则返回首词本身。
    a priori 的首词是 a，归到 a 段而不是 ap 段。"""
    first = sort_key(headword)[0]
    return first[:n] if len(first) >= n else first
