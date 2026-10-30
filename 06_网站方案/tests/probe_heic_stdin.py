import base64
import io
import subprocess

raw = open(r'C:\Users\lidey\Desktop\实验报告制作沙盒\01_素材_数据与截图\IMG_20261026_213601.HEIC', 'rb').read()

PS = (
    '$in=[Console]::OpenStandardInput();'
    '$ms=New-Object System.IO.MemoryStream;'
    '$in.CopyTo($ms);$ms.Position=0;'
    'Add-Type -AssemblyName PresentationCore;'
    '$d=[System.Windows.Media.Imaging.BitmapDecoder]::Create('
    '$ms,'
    '[System.Windows.Media.Imaging.BitmapCreateOptions]::None,'
    '[System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad);'
    '$e=New-Object System.Windows.Media.Imaging.PngBitmapEncoder;'
    '$e.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($d.Frames[0]));'
    '$o=New-Object System.IO.MemoryStream;$e.Save($o);'
    '[Console]::Out.Write([Convert]::ToBase64String($o.ToArray()))'
)

try:
    r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', PS],
                       input=raw, capture_output=True, timeout=120)
    print('rc', r.returncode, 'stdout', len(r.stdout), 'stderr', r.stderr[:300])
    if r.returncode == 0 and r.stdout:
        png = base64.b64decode(r.stdout.strip())
        print('png bytes', len(png), png[:8].hex())
        from PIL import Image
        im = Image.open(io.BytesIO(png))
        print('decoded', im.size, im.mode)
except Exception as e:
    print('FAIL', type(e).__name__, e)
