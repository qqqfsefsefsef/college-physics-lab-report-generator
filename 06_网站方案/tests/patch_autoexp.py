# -*- coding: utf-8 -*-
r"""上传屏：不用先选实验，传图自动认；认不出再让用户选。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
P = r'C:\Users\lidey\Desktop\实验报告制作沙盒\06_网站方案\prototype_v2.html'
s = io.open(P, encoding='utf-8').read()
orig = len(s)
n = 0


def rep(old, new, tag):
    global s, n
    assert s.count(old) == 1, '未命中：%s（%d 次）' % (tag, s.count(old))
    s = s.replace(old, new)
    n += 1
    print('[OK]', tag)


# 1) 上传屏顶部那张卡：从「识别到的实验」改成「自动识别 + 认不出再手动选」
rep("""      <div class="row" style="justify-content:space-between">
        <div>
          <div style="font-weight:600">识别到的实验</div>
          <div class="muted" id="exp-detect">用静态拉伸法测金属丝的杨氏弹性模量</div>
        </div>
        <button class="btn sm" onclick="toggleExp()">改</button>
      </div>
      <select id="exp-sel" style="display:none;margin-top:10px">""",
    """      <div class="row" style="justify-content:space-between">
        <div>
          <div style="font-weight:600">做的是哪个实验？<span class="tag gray">自动识别</span></div>
          <div class="muted" id="exp-detect">先传原始数据页，我看完自己判断——不用你选</div>
        </div>
        <button class="btn sm" id="exp-edit" onclick="toggleExp()">认不出？手动选</button>
      </div>
      <select id="exp-sel" style="display:none;margin-top:10px" onchange="onExpPicked(this.value)">""",
    'S4 实验卡')

rep("""        <option>霍尔效应及其应用</option>
      </select>
    </div>""",
    """        <option>霍尔效应及其应用</option>
      </select>
      <div class="hint" id="exp-hint" style="margin-top:8px">只有照片里认不出是哪个实验时，才需要在这里手动选一个。</div>
    </div>""",
    'S4 下拉提示')

# 2) 传数据页：先 /detect 认实验，再 /recognize 认数字
rep("""  if (upId === 'up-data') {
    /* 数据页要真的认一遍，认不出来就不算上传成功 */
    identify(f, function (ok) {
      $(upId).classList[ok ? 'add' : 'remove']('done');
      STATE.files.data = !!ok;
      syncGen();
    });
    return;
  }""",
    """  if (upId === 'up-data') {
    /* 数据页：先看是哪个实验，再认数字；两步都过了才算上传成功 */
    detectThenRecognize(f, function (ok) {
      $(upId).classList[ok ? 'add' : 'remove']('done');
      STATE.files.data = !!ok;
      syncGen();
    });
    return;
  }""",
    'pick 走自动识别')

# 3) 新增 detectThenRecognize / onExpPicked / setExp
rep("function identify(file, cb) {",
    """function setExp(name, id) {
  STATE.exp = name;
  if (id) STATE.expId = id;
  var box = $('exp-detect');
  if (box) box.textContent = name;
  var sel = $('exp-sel');
  if (sel) { sel.value = name; }
}

/* 第一步：看照片是哪个实验；认出来就直接往下认数字 */
function detectThenRecognize(file, cb) {
  STATE.lastFile = file;
  var eid0 = eidForExp(STATE.exp);
  setStatus('正在看这是哪个实验…');
  readB64(file, function (b64, mime) {
    if (!b64) { setStatus('读不出这张图，换一张试试。', true); return cb(false); }
    var payload = {
      image_b64: b64, mime: mime,
      api_key: (STATE.api && STATE.api.key) || '',
      base_url: (STATE.api && STATE.api.url) || '',
      model: (STATE.api && STATE.api.model) || ''
    };
    if (STATE.mockRec) payload.mode = 'mock';
    fetch(BRIDGE + '/detect', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (r) { return r.json(); }).then(function (j) {
      if (j && j.image) STATE.detImg = j.image;
      if (j && j.ok && j.exp_id) {
        setExp(j.name, j.exp_id);
        showExpEdit(false);
        setStatus('认出来了：《' + j.name + '》，接着认数字…');
        identify(file, cb);
        return;
      }
      /* 认不出：把选择框亮出来，让用户自己选 */
      showExpEdit(true);
      var box = $('exp-detect');
      if (box) box.textContent = '认不出这是哪个实验' + (j && j.detected ? '（照片上像「' + j.detected + '」）' : '');
      setStatus('认不出是哪个实验，请在下面手动选一个，选完我会接着认数字。', true);
      cb(false);
    }).catch(function () {
      showExpEdit(true);
      setStatus('识别桥没在跑（启动.ps1），或者网络断了。', true);
      cb(false);
    });
  });
}

function showExpEdit(open) {
  var sel = $('exp-sel'), btn = $('exp-edit');
  if (sel) sel.style.display = open ? 'block' : 'none';
  if (btn) btn.textContent = open ? '收起' : '认不出？手动选';
}

function onExpPicked(name) {
  setExp(name, null);
  showExpEdit(false);
  if (!STATE.lastFile) { toast('已选《' + name + '》，现在传照片'); return; }
  toast('已选《' + name + '》，正在认这张照片的数字…');
  identify(STATE.lastFile, function (ok) {
    var up = $('up-data');
    if (up) up.classList[ok ? 'add' : 'remove']('done');
    STATE.files.data = !!ok;
    syncGen();
    if (ok) go('s-review');
  });
}

function setStatus(text, bad) {
  var el = $('rec-status');
  if (!el) return;
  el.textContent = text || '';
  el.style.color = bad ? 'var(--bad)' : '';
}

function identify(file, cb) {""",
    '加自动识别流程')

io.open(P, 'w', encoding='utf-8', newline='\n').write(s)
print('[DONE] %d -> %d 字符，%d 处' % (orig, len(s), n))
