# -*- coding: utf-8 -*-
r"""页面：别重复「识别失败：」，并把 finish_reason 之类的诊断信息显示出来。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = len(s)

old = ("      if (j.error) { setRec('识别失败：' + j.error, 'bad'); return cb(false); }")
new = ("      if (j.error) {\n"
       "        var msg = String(j.error).replace(/^识别失败：/, '');\n"
       "        var dg = j.diag || {};\n"
       "        if (dg.finish_reason) msg += '（finish_reason=' + dg.finish_reason +\n"
       "          '，正文 ' + (dg.len_content || 0) + ' 字，思考 ' + (dg.len_reasoning || 0) + ' 字）';\n"
       "        if (j.first_error) msg += '｜第一次：' + String(j.first_error).slice(0, 120);\n"
       "        setRec('识别失败：' + msg, 'bad');\n"
       "        return cb(false);\n"
       "      }")
assert s.count(old) == 1, '报错分支未命中'
s = s.replace(old, new)
print('[OK] 报错分支改好')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] %d -> %d 字符' % (orig, len(s)))
