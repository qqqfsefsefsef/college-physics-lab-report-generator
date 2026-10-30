# -*- coding: utf-8 -*-
"""结果页显示「本次用量 + 估算花费」；修 doneClean() 里把「下一步」又置灰的死锁。"""
import io
import shutil
import sys

HP = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(HP, encoding='utf-8').read()
n0 = len(s)


def rep(name, old, new):
    global s
    c = s.count(old)
    if c != 1:
        print('[FAIL] %s 命中 %d 次' % (name, c))
        sys.exit(1)
    s = s.replace(old, new)
    print('[OK] %s' % name)


# 1) 加 costText
rep('costText',
    "function identify(file, cb) {\n",
    "function costText(u) {\n"
    "  if (!u) return '';\n"
    "  var i = u.prompt_tokens || 0, o = u.completion_tokens || 0;\n"
    "  var cny = i / 1e6 * 2 + o / 1e6 * 8;      /* 官网价口径：输入 ¥2/百万、输出 ¥8/百万 */\n"
    "  return cny < 0.01 ? ('¥' + cny.toFixed(4)) : ('¥' + cny.toFixed(3));\n"
    "}\n"
    "\n"
    "function identify(file, cb) {\n")

# 2) 结果页写用量
rep('结果页用量',
    "    dl.onclick = function () { window.location.href = BRIDGE + STATE.out.url; };\n",
    "    dl.onclick = function () { window.location.href = BRIDGE + STATE.out.url; };\n"
    "    var u = (STATE.out.meta && STATE.out.meta.usage) || STATE.out.usage || null;\n"
    "    if (ubox) {\n"
    "      if (u && (u.total_tokens || u.prompt_tokens)) {\n"
    "        ubox.style.display = 'block';\n"
    "        ubox.textContent = '本次用量：' + (u.total_tokens || (u.prompt_tokens + u.completion_tokens)) +\n"
    "          ' tokens（输入 ' + (u.prompt_tokens || 0) + ' + 输出 ' + (u.completion_tokens || 0) +\n"
    "          '）· 按官网价估算约 ' + costText(u) + '。重做时选「沿用已核对数据」会更省。';\n"
    "      } else {\n"
    "        ubox.style.display = 'none';\n"
    "      }\n"
    "    }\n")

# 3) doneClean 不再把下一步置灰（那会造成又一次死锁）
rep('doneClean 死锁',
    "  $('api-status').textContent = '未测试';\n  $('api-next').disabled = true;\n",
    "  $('api-status').textContent = '未测试';\n")

shutil.copyfile(HP, HP + '.bak8')
io.open(HP, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] prototype_v2.html %d -> %d chars' % (n0, len(s)))
