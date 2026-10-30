# -*- coding: utf-8 -*-
r"""让打印版 HTML 的页脚跟着 docx 走（原来硬编码「长度测量」）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\04_生成过程_脚本图表\docx_to_print_html.py'
s = io.open(P, encoding='utf-8').read()

# 1) 加取页脚的小函数（放在文件里第一个 def 之前）
if 'def footer_text(' not in s:
    i = s.index('def ')
    helper = '''def footer_text(doc, default='长度测量'):
    try:
        t = ' '.join(p.text for sec in doc.sections for p in sec.footer.paragraphs
                     if p.text.strip())
        return t.strip() or default
    except Exception:
        return default


'''
    s = s[:i] + helper + s[i:]
    print('[OK] 加 footer_text()')

# 2) 模板里不写死
old = '<div class="runfoot">长度测量</div>'
new = '<div class="runfoot">%s</div>'
if s.count(old) == 1:
    s = s.replace(old, new)
    print('[OK] 模板改成占位')

# 3) 参数补齐
old = "% (os.path.basename(path).replace('.docx', ''), CSS, HEADER_TEXT, '\\n'.join(body))"
new = ("% (os.path.basename(path).replace('.docx', ''), CSS, HEADER_TEXT,\n"
       "       footer_text(doc), '\\n'.join(body))")
assert s.count(old) == 1, '参数元组未命中'
s = s.replace(old, new)
print('[OK] 参数元组加 footer_text(doc)')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE]', len(s), '字符')
