#!/usr/bin/env bash
# 家庭物品管理 - 一键启动脚本
# 功能：首次运行自动准备环境(Python 虚拟环境+依赖、前端依赖+构建)，之后直接启动服务。
# 用法：
#   ./start.sh            # 启动（前台运行，Ctrl+C 停止）
#   ./start.sh -d         # 后台运行（日志写入 backend/server.log）
#   ./start.sh --rebuild  # 强制重新构建前端后再启动

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
PYTHON="$VENV/bin/python"
PIDFILE="$BACKEND/server.pid"
LOGFILE="$BACKEND/server.log"

DAEMON=0
REBUILD=0
for arg in "$@"; do
  case "$arg" in
    -d|--daemon) DAEMON=1 ;;
    --rebuild) REBUILD=1 ;;
  esac
done

echo "==> 准备后端环境"
if [ ! -x "$PYTHON" ]; then
  echo "    创建虚拟环境..."
  python3 -m venv "$VENV"
fi
"$PYTHON" -m pip install -q --disable-pip-version-check -r "$BACKEND/requirements.txt"

echo "==> 准备前端"
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "    安装前端依赖(npm install)..."
  (cd "$FRONTEND" && npm install)
fi
if [ "$REBUILD" = "1" ] || [ ! -f "$FRONTEND/dist/index.html" ]; then
  echo "    构建前端(npm run build)..."
  (cd "$FRONTEND" && npm run build)
fi

# 读取端口（从 config.py）
PORT="$("$PYTHON" -c "import sys; sys.path.insert(0,'$BACKEND'); import config; print(config.PORT)")"

# 若已有实例在运行则先停止
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "==> 检测到已运行实例(PID $(cat "$PIDFILE"))，先停止"
  kill "$(cat "$PIDFILE")" 2>/dev/null || true
  sleep 1
fi

# 局域网 IP（便于其它设备访问）
LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo '<本机内网IP>')"

echo "==> 启动服务"
echo "    本机访问:    http://localhost:$PORT"
echo "    内网设备访问: http://$LAN_IP:$PORT"

cd "$BACKEND"
if [ "$DAEMON" = "1" ]; then
  nohup "$PYTHON" app.py > "$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
  echo "    已后台运行(PID $(cat "$PIDFILE"))，日志: $LOGFILE"
  echo "    停止请运行: ./stop.sh"
else
  echo "    前台运行，按 Ctrl+C 停止"
  exec "$PYTHON" app.py
fi
