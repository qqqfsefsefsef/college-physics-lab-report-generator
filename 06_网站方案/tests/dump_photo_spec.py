import json
import sys

p = r'C:\Users\lidey\Desktop\实验报告制作沙盒\07_流水线\experiments\photo.json'
d = json.load(open(p, encoding='utf-8'))
out = []
out.append('keys: ' + str(list(d.keys())))
out.append('tables: ' + json.dumps(d.get('tables'), ensure_ascii=False, indent=1)[:1500])
out.append('formulas: ' + json.dumps(d.get('formulas'), ensure_ascii=False)[:600])
open(r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\tests\photo_spec.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written')
