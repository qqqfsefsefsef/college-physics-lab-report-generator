# 一键启动：前端服务(8731) + 识别桥(8732)
#
# 用法（在本目录里）：
#   .\启动.ps1                 只在本机用（127.0.0.1）
#   .\启动.ps1 -Lan            对同一 WiFi 的室友开放（0.0.0.0），会打印内网地址
#   .\启动.ps1 -Tunnel         用 cloudflared 打两条隧道，生成公网 https 地址（别人在哪儿都能用）
#   .\启动.ps1 -Mock -Lan      桩模式（不联网、不花钱），给朋友试界面用
#   .\启动.ps1 -Lan -DryRun    只打印将要执行的命令，不真的启动
#
# 注意：-Tunnel 需要先装 cloudflared：  winget install --id Cloudflare.cloudflared

param(
    [switch]$Mock,
    [switch]$Lan,
    [switch]$Tunnel,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$py = 'C:\Users\lidey\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
$W = 'C:\Users\lidey\Desktop\实验报告制作沙盒'

$bindHost = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }

$bridgeArgs = @("$W\07_流水线\bridge.py", '--host', $bindHost)
if ($Mock) { $bridgeArgs += '--mock' }

$webArgs = @('-m', 'http.server', '8731', '--bind', $bindHost, '--directory', "$W\06_网站方案")

function Show-Plan {
    Write-Host '--- 将要执行 ---' -ForegroundColor DarkGray
    Write-Host ("识别桥 : `"$py`" " + ($bridgeArgs -join ' ')) -ForegroundColor DarkGray
    Write-Host ("前端   : `"$py`" " + ($webArgs -join ' ')) -ForegroundColor DarkGray
    if ($Tunnel) {
        Write-Host '隧道   : cloudflared tunnel --url http://127.0.0.1:8732   (识别桥)' -ForegroundColor DarkGray
        Write-Host '         cloudflared tunnel --url http://127.0.0.1:8731   (页面)' -ForegroundColor DarkGray
    }
}

# 内网 IPv4：只认「有默认网关」的网卡（排除 VirtualBox 的 192.168.56.x、Radmin 的 26.x、169.254 自动地址）
function Get-LanIp {
    try {
        $cfg = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address } |
            Sort-Object { if ($_.InterfaceAlias -match 'WLAN|Wi-Fi|无线|Ethernet|以太网') { 0 } else { 1 } }
        foreach ($c in $cfg) {
            foreach ($a in $c.IPv4Address) {
                $ip = $a.IPAddress
                if ($ip -eq '127.0.0.1') { continue }
                if ($ip -like '169.254.*') { continue }
                if ($ip -like '26.*') { continue }          # Radmin VPN
                if ($ip -like '192.168.56.*') { continue }  # VirtualBox 仅主机网卡
                return $ip
            }
        }
    } catch { }
    return $null
}

if ($DryRun) {
    Show-Plan
    if ($Lan) {
        $ip = Get-LanIp
        Write-Host ("内网地址会打印成： http://{0}:8731/prototype_v2.html" -f ($(if ($ip) { $ip } else { '<你的IP>' }))) -ForegroundColor DarkGray
    }
    Write-Host '[DRY] 没有真的启动任何进程。' -ForegroundColor Yellow
    return
}

if ($Tunnel -and -not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host '没有找到 cloudflared。先装：' -ForegroundColor Red
    Write-Host '  winget install --id Cloudflare.cloudflared' -ForegroundColor Yellow
    Write-Host '装完重开一个终端再运行本脚本（或者去掉 -Tunnel 改用 -Lan）。' -ForegroundColor Yellow
    return
}

Write-Host '启动识别桥 (8732)...' -ForegroundColor Cyan
Start-Process -FilePath $py -ArgumentList $bridgeArgs -WorkingDirectory "$W\07_流水线"

Write-Host '启动前端服务 (8731)...' -ForegroundColor Cyan
Start-Process -FilePath $py -ArgumentList $webArgs -WorkingDirectory "$W\06_网站方案"

Start-Sleep -Seconds 2
try {
    $h = (Invoke-WebRequest -Uri 'http://127.0.0.1:8732/health' -UseBasicParsing -TimeoutSec 5).Content | ConvertFrom-Json
    $k = if ($h.has_key) { '有' } else { '无（用页面里填的）' }
    Write-Host ("识别桥：{0} 模式，{1} 个实验，服务端密钥：{2}" -f $h.mode, $h.experiments.Count, $k) -ForegroundColor Green
} catch {
    Write-Host '识别桥没起来，看看弹出的那个窗口报了什么错。' -ForegroundColor Red
}

$localUrl = 'http://127.0.0.1:8731/prototype_v2.html'

if ($Lan) {
    $ip = Get-LanIp
    if ($ip) {
        Write-Host ''
        Write-Host '发给室友的地址：' -ForegroundColor Green
        Write-Host ("  http://{0}:8731/prototype_v2.html" -f $ip) -ForegroundColor Yellow
        Write-Host ("  「连接设置」里填： http://{0}:8732" -f $ip) -ForegroundColor Yellow
        Write-Host '  （第一次会弹防火墙，勾「专用网络」允许）' -ForegroundColor DarkGray
    } else {
        Write-Host '没识别到内网 IP，用 ipconfig 自己看一眼 IPv4。' -ForegroundColor Red
    }
}

if ($Tunnel) {
    Write-Host ''
    Write-Host '打隧道中（30 秒内出地址）...' -ForegroundColor Cyan
    $logB = Join-Path $env:TEMP 'cf-bridge.log'
    $logW = Join-Path $env:TEMP 'cf-web.log'
    foreach ($f in @($logB, $logW)) { if (Test-Path $f) { Remove-Item $f -Force } }

    Start-Process -FilePath 'cloudflared' -ArgumentList @('tunnel', '--url', 'http://127.0.0.1:8732', '--no-autoupdate') `
        -RedirectStandardError $logB -WindowStyle Hidden
    Start-Process -FilePath 'cloudflared' -ArgumentList @('tunnel', '--url', 'http://127.0.0.1:8731', '--no-autoupdate') `
        -RedirectStandardError $logW -WindowStyle Hidden

    function Wait-Url($file) {
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Milliseconds 800
            if (Test-Path $file) {
                $t = Get-Content $file -Raw -ErrorAction SilentlyContinue
                $m = [regex]::Match($t, 'https://[a-z0-9-]+\.trycloudflare\.com')
                if ($m.Success) { return $m.Value }
            }
        }
        return $null
    }

    $uBridge = Wait-Url $logB
    $uWeb = Wait-Url $logW

    if ($uWeb) {
        Write-Host ''
        Write-Host '发给别人的页面地址：' -ForegroundColor Green
        Write-Host ("  {0}/prototype_v2.html" -f $uWeb) -ForegroundColor Yellow
        if ($uBridge) {
            Write-Host '对方第一次打开要点右上角「连接设置」，填：' -ForegroundColor Green
            Write-Host ("  {0}" -f $uBridge) -ForegroundColor Yellow
        } else {
            Write-Host '识别桥的隧道没起来，看 %TEMP%\cf-bridge.log' -ForegroundColor Red
        }
        Write-Host '  （临时地址，关掉窗口就失效；对方只在自己的浏览器里填一次，会记住）' -ForegroundColor DarkGray
        Write-Host '  （这个地址是公网可访问的：不想被人乱用就设 BRIDGE_TOKEN 口令）' -ForegroundColor DarkGray
    } else {
        Write-Host '隧道没出地址，看 %TEMP%\cf-web.log 里的报错。' -ForegroundColor Red
    }
}

Write-Host ''
Write-Host ("本机打开：{0}" -f $localUrl) -ForegroundColor Cyan
if (-not $Lan -and -not $Tunnel) { Start-Process $localUrl }
Write-Host ''
Write-Host '关闭时：把两个黑色的 Python 窗口关掉即可（或结束 python.exe / cloudflared.exe）。' -ForegroundColor DarkGray
