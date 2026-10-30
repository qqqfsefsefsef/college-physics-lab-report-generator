# -*- coding: utf-8 -*-
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()

bad1 = "  tn-ok.disabled = true;"
good1 = "  $('btn-ok').disabled = true;"
bad2 = "  \\ok-hint.textContent = '还有 ' + QUIZ.list.length + ' 题等你选。';"
good2 = "  $('ok-hint').textContent = '还有 ' + QUIZ.list.length + ' 题等你选。';"

n1 = s.count(bad1)
n2 = s.count(bad2)
print('found', n1, n2)
if n1:
    s = s.replace(bad1, good1)
if n2:
    s = s.replace(bad2, good2)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)

i = s.find('function buildQuiz()')
print(s[i:i + 420])
