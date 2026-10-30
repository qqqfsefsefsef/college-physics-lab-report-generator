# -*- coding: utf-8 -*-
"""UI 第三轮（修正锚点）：把剩下那些常驻小字再压一压，并给预览表加滚动容器。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = s


def rep(old, new, tag):
    global s
    assert old in s, 'anchor not found: ' + tag
    assert s.count(old) == 1, 'anchor not unique: ' + tag
    s = s.replace(old, new, 1)


rep('  .hint.auto:empty{display:none}',
    """  .hint.auto:empty{display:none}
  #rec-preview{max-height:132px;overflow:auto;border-radius:8px}
  #rec-preview .mini{font-size:11px}""", 'css-preview')

rep('      <div class="hint">密钥仅保存在 JavaScript 变量中；不写 localStorage、不写 cookie、不随报告落盘。</div>',
    '      <div class="hint">密钥只存在这个页面里，不写盘、不写 cookie。</div>', 's2-hint1')
rep('      <div class="hint">不填密钥也能先走完整个流程看效果；改动任何一项会重新校验。</div>',
    '', 's2-hint2')

rep('      <div class="hint">开放后：一次一码，用后即失效；同一码可重做 2 次。</div>',
    '      <div class="hint">一次一码，用后即失效。</div>', 's3-hint')

rep('    <div class="hint">单位 10⁻² m。表里显示几位，计算就用几位。</div>',
    '    <div class="hint">表里显示几位，计算就用几位。</div>', 's5-hint1')
rep('<div class="hint" id="ok-hint">先看下面：有几道题等你选。</div>',
    '<div class="hint" id="ok-hint"></div>', 's5-okhint')

rep('      <div class="hint">沿用数据只需重写文字，花费约为完整流程的 1/10；取消勾选会重新识别照片。</div>',
    '      <div class="hint">沿用数据只重写文字，花费约为完整流程的 1/10。</div>', 's8-hint1')
rep('      <div class="hint">你选的原因会记进系统做优化（只记选项与耗时，不记你的图片与姓名）。</div>',
    '      <div class="hint">只记选项和耗时，不记你的图片与姓名。</div>', 's8-hint2')

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] UI 3rd pass: %d -> %d chars' % (len(orig), len(s)))
