# -*- coding: utf-8 -*-
"""UI 第二轮：首页居中两卡、上传屏三列横排、小字按需显示、文案精简、公告每次都出现。"""
import io

P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = s


def rep(old, new, tag):
    global s
    assert old in s, 'anchor not found: ' + tag
    assert s.count(old) == 1, 'anchor not unique: ' + tag
    s = s.replace(old, new, 1)


# ---------------- 1. CSS ----------------
rep('</style>', """  /* 首页：两个入口居中、并排 */
  .homewrap{min-height:calc(100vh - 190px);display:flex;flex-direction:column;
    justify-content:center;align-items:center;text-align:center;gap:14px}
  .homewrap h1,.homewrap .lead{margin:0 auto;text-align:center}
  .paths{display:flex;gap:16px;width:min(820px,100%);margin-top:8px}
  .paths .pathcard{flex:1;text-align:left;display:flex;flex-direction:column;gap:8px}
  .paths .pathcard .t{font-size:13px;line-height:1.65}
  /* 素材三栏横排 */
  .grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
  .grid3 .card{min-width:0}
  .ct{font-weight:600;margin-bottom:10px;font-size:14px}
  /* 小字按需显示：没有内容就整行不占位 */
  .hint.auto:empty{display:none}
  @media(max-width:900px){.paths{flex-direction:column}.grid3{grid-template-columns:1fr}}
</style>""", 'css')

# ---------------- 2. 首页 ----------------
a = s.find('  <section id="s-home" class="screen on">')
b = s.find('  </section>', a) + len('  </section>')
assert a > 0 and b > a
new_home = """  <section id="s-home" class="screen on">
    <div class="homewrap">
      <h1>把你的实验数据，变成一份能交的报告</h1>
      <p class="lead">上传原始数据页 → 核对数字 → 按学校模板出 PDF / Word。数字全部由你的数据算出。</p>
      <div class="paths">
        <div class="card pathcard" onclick="go('s-api')">
          <h3>自带 API <span class="tag">推荐</span></h3>
          <div class="t">用你在开放平台申请的密钥和额度，密钥只在本次会话的内存里。</div>
          <div class="go">开始配置 →</div>
        </div>
        <div class="card pathcard off" id="card-official" onclick="officialTap()">
          <h3>官方通道 <span class="tag gray" id="official-tag">未开放</span></h3>
          <div class="t">提交兑换码即可用，一次一码。测试阶段暂未开放。</div>
          <div class="go" style="color:var(--gray)">暂不可用</div>
        </div>
      </div>
    </div>
  </section>"""
s = s[:a] + new_home + s[b:]

# ---------------- 3. 上传屏：三栏横排 + 精简文案 ----------------
rep('    <p class="lead">识别出实验类型、收齐三类文件，然后选输出格式。</p>',
    '    <p class="lead">自动认出实验、收三样素材、选格式。</p>', 'lead4')

a = s.find('    <div class="grid2">', s.find('id="s-upload"'))
b = s.find('    <div class="card">\n      <div style="font-weight:600">输出格式</div>')
assert a > 0 and b > a
new_cards = """    <div class="grid3">
      <div class="card">
        <div class="ct">原始数据页 <span style="color:var(--bad)">*</span></div>
        <label class="up" id="up-data" for="f-data">
          <div>点这里选照片</div>
          <div class="fn" id="fn-data"></div>
          <input id="f-data" type="file" accept="image/*" hidden onchange="pick(this,'up-data','fn-data')">
        </label>
        <div class="hint auto" id="rec-status" style="margin-top:8px"></div>
        <div id="rec-preview" style="margin-top:8px"></div>
      </div>
      <div class="card">
        <div class="ct">以前做过的作业 <span style="color:var(--bad)">*</span></div>
        <label class="up" id="up-hw" for="f-hw">
          <div>点这里选 docx</div>
          <div class="fn" id="fn-hw"></div>
          <input id="f-hw" type="file" accept=".docx,.pdf,.doc" hidden onchange="pick(this,'up-hw','fn-hw')">
        </label>
        <div class="hint auto" id="hw-tip" style="margin-top:8px"></div>
      </div>
      <div class="card">
        <div class="ct">学习通截图 <span class="tag gray">可跳过</span></div>
        <label class="up" id="up-shot" for="f-shot">
          <div>点这里选截图</div>
          <div class="fn" id="fn-shot"></div>
          <input id="f-shot" type="file" accept="image/*" hidden onchange="pick(this,'up-shot','fn-shot')">
        </label>
        <div class="hint auto" id="shot-tip" style="margin-top:8px"></div>
      </div>
    </div>

"""
s = s[:a] + new_cards + s[b:]

# 实验选择卡的小字：默认不显示
rep('      <div class="hint" id="exp-hint" style="margin-top:8px">只有照片里认不出是哪个实验时，才需要在这里手动选一个。</div>',
    '      <div class="hint auto" id="exp-hint" style="margin-top:8px"></div>', 'exp-hint')

# 输出格式卡：文案精简 + 就绪时不显示小字
rep('      <div class="fine" style="margin-top:2px">勾几个都不涨价；推荐 PDF，作业一般就交 PDF。</div>',
    '      <div class="fine" style="margin-top:2px">可多选，不加价；作业一般交 PDF。</div>', 'fmt-fine')
rep('      <div class="hint" id="gen-hint">还差：原始数据页、以前的作业</div>',
    '      <div class="hint auto" id="gen-hint"></div>', 'gen-hint')

# ---------------- 4. 步骤 3 的说明收短 ----------------
rep('    <p class="lead">下面这些数字是从你刚上传的照片里认出来的。<b>拿它和你纸上的表格对一遍</b>：哪个格子错了就直接点它改过来。数字对了，点最下面那个按钮，就开始生成报告——<b>报告里的数字只认这张表</b>，它不会再去看照片。</p>',
    '    <p class="lead">数字是从照片里认出来的。<b>拿它和你纸上的表格对一遍</b>，错格的直接点它改。<b>报告里只认这张表</b>，不会再去看照片。</p>', 'lead5')

# ---------------- 5. 公告每次打开都出现 ----------------
rep("""function boot() {
  var seen = null;
  try { seen = localStorage.getItem('notice.ok'); } catch (e) {}
  if (seen) $('notice').classList.add('hide');
""", """function boot() {
  /* 公告每次打开都出现：不再按 localStorage 跳过 */
""", 'boot-notice')

# ---------------- 6. 就绪时不再常驻小字 ----------------
rep("""  if (STATE.demo) {
    $('btn-gen').disabled = false;
    $('gen-hint').textContent = '示例模式：可以直接生成';
    return;
  }""",
    """  if (STATE.demo) {
    $('btn-gen').disabled = false;
    $('gen-hint').textContent = '';
    return;
  }""", 'syncGen-demo')
rep("  $('gen-hint').textContent = ok ? '齐了，可以生成' : ('还差：' + need.join('、'));",
    "  $('gen-hint').textContent = ok ? '' : ('还差：' + need.join('、'));", 'syncGen-hint')

assert s != orig
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[OK] UI 2nd pass: %d -> %d chars' % (len(orig), len(s)))
