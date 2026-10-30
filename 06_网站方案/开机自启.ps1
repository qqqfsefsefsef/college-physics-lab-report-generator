param(
    [switch]$Remove,
    [switch]$Mock,
    [switch]$DryRun
)

# 注册/删除「登录时自动启动」的计划任务：
#   1) ReportSite        跑 start.ps1 -Lan（静态页 8731 + 识别桥 8732）
#   2) ReportSiteTunnel  跑 cloudflared tunnel run（仅当存在 ~\.cloudflared\config.yml）
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File .\开机自启.ps1
#   powershell -ExecutionPolicy Bypass -File .\开机自启.ps1 -Mock
#   powershell -ExecutionPolicy Bypass -File .\开机自启.ps1 -Remove

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$site = Join-Path $here 'start.ps1'
$taskSite = 'ReportSite'
$taskTun = 'ReportSiteTunnel'
$cf = Join-Path $env:USERPROFILE '.cloudflared\config.yml'

function Say($t) { Write-Host $t }
function Q($p) { '"' + $p + '"' }

if ($Remove) {
    foreach ($n in @($taskSite, $taskTun)) {
        $exists = $null
        try { $exists = schtasks /query /tn $n 2>$null } catch { $exists = $null }
        if ($exists) {
            if ($DryRun) { Say ('[dry] schtasks /delete /tn ' + $n + ' /f') }
            else {
                schtasks /delete /tn $n /f | Out-Null
                Say ('[删] ' + $n)
            }
        } else {
            Say ('[跳过] ' + $n + ' 本来就没有')
        }
    }
    Say ''
    Say '已取消开机自启。之后要手动启动：双击 start.cmd'
    exit 0
}

if (-not (Test-Path -LiteralPath $site)) {
    Say ('[ERR] 找不到 ' + $site)
    exit 1
}

# 1) 网站本体
$psArgs = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ' + (Q $site) + ' -Lan'
if ($Mock) { $psArgs = $psArgs + ' -Mock' }
$cmdSite = 'powershell.exe ' + $psArgs

# 2) 隧道（有配置文件才注册）
$hasTun = Test-Path -LiteralPath $cf
$cmdTun = 'cloudflared tunnel --config ' + (Q $cf) + ' run'

if ($DryRun) {
    Say '[dry] 将创建计划任务：'
    Say ('  名称: ' + $taskSite)
    Say ('  命令: ' + $cmdSite)
    if ($hasTun) {
        Say ('  名称: ' + $taskTun)
        Say ('  命令: ' + $cmdTun)
    } else {
        Say ('  (跳过 ' + $taskTun + '：没找到 ' + $cf + ')')
    }
    Say ''
    Say '[dry] 没做任何修改。去掉 -DryRun 才会真的注册。'
    exit 0
}

Say ('[1/2] 注册 ' + $taskSite + ' …')
schtasks /create /tn $taskSite /tr $cmdSite /sc onlogon /f | Out-Null
Say '      OK'

if ($hasTun) {
    Say ('[2/2] 注册 ' + $taskTun + ' …')
    schtasks /create /tn $taskTun /tr $cmdTun /sc onlogon /f | Out-Null
    Say '      OK'
} else {
    Say '[2/2] 跳过隧道：没找到 ~\.cloudflared\config.yml（先按「固定网址_免费方案.md」建隧道）'
}

Say ''
Say '完成。下次登录 Windows 会自动在后台起服务。'
Say '想现在就用，直接双击 start.cmd；不想自动启动了用 -Remove。'
