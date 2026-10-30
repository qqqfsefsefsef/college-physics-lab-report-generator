#!/usr/bin/env bash
# 不装 Docker 的裸机版（Ubuntu 22.04 / 24.04，1 核 1G 就能跑）
# 用法：sudo bash install.sh
# 装完：静态页面在 /opt/report/web，引擎在 /opt/report/pipeline，服务名 report-bridge
set -euo pipefail

APP_DIR=/opt/report
PY=python3

echo "[1/6] 依赖"
apt-get update
apt-get install -y python3 python3-pip python3-venv curl debian-keyring debian-archive-keyring \
                   apt-transport-https gnupg

echo "[2/6] Caddy（自动 HTTPS + 反代 /api）"
if ! command -v caddy >/dev/null 2>&1; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update
  apt-get install -y caddy
fi

echo "[3/6] 程序文件"
mkdir -p "$APP_DIR"
cp -r ./app "$APP_DIR/"
mkdir -p "$APP_DIR/pipeline/projects" "$APP_DIR/logs"

echo "[4/6] Python 依赖（pillow + pillow-heif：让服务器也能读 iPhone 的 HEIC）"
"$PY" -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q pillow pillow-heif

echo "[5/6] systemd 服务"
cat > /etc/systemd/system/report-bridge.service <<'UNIT'
[Unit]
Description=Report bridge (prototype_v2 + 07_流水线/bridge.py)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/report/pipeline
EnvironmentFile=/opt/report/.env
Environment=BRIDGE_HOST=127.0.0.1
Environment=BRIDGE_PORT=8732
Environment=PIPE_GEN=/opt/report/app/assets
Environment=PIPE_BASE=/opt/report/app/assets/template.docx
ExecStart=/opt/report/venv/bin/python /opt/report/pipeline/bridge.py --host 127.0.0.1 --port 8732
Restart=always
RestartSec=2
StandardOutput=append:/opt/report/logs/bridge.log
StandardError=append:/opt/report/logs/bridge.log

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now report-bridge

echo "[6/6] Caddy 站点"
[ -f "$APP_DIR/.env" ] || cp ./.env.example "$APP_DIR/.env"
set -a; . "$APP_DIR/.env"; set +a
mkdir -p /var/log/caddy
sed -e "s#{\$BRIDGE_UPSTREAM}#127.0.0.1:8732#" \
    -e "s#{\$SITE_ADDR}#${SITE_ADDR}#" \
    -e "s#/srv/web#$APP_DIR/app/web#" ./Caddyfile > /etc/caddy/Caddyfile
systemctl restart caddy

echo
echo "完成。检查："
echo "  systemctl status report-bridge --no-pager"
echo "  tail -n 20 /opt/report/logs/bridge.log"
echo "  curl -s http://127.0.0.1:8732/health"
echo "  浏览器打开 http://<服务器IP>/  （有域名则是 https://<域名>/）"
echo
echo "注意：云厂商安全组要放行 80 和 443；有域名才可能签发 HTTPS 证书。"
