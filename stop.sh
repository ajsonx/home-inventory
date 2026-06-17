#!/usr/bin/env bash
# 家庭物品管理 - 停止脚本（停止由 ./start.sh -d 启动的后台服务）

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$ROOT/backend/server.pid"

if [ -f "$PIDFILE" ]; then
  PID="$(cat "$PIDFILE")"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    sleep 1
    kill -9 "$PID" 2>/dev/null || true
    echo "已停止服务(PID $PID)"
  else
    echo "进程不存在，清理 pid 文件"
  fi
  rm -f "$PIDFILE"
else
  echo "未找到 pid 文件，尝试按端口停止"
  PORT="$("$ROOT/backend/.venv/bin/python" -c "import sys; sys.path.insert(0,'$ROOT/backend'); import config; print(config.PORT)" 2>/dev/null || echo 8000)"
  PID="$(lsof -ti tcp:$PORT 2>/dev/null || true)"
  if [ -n "$PID" ]; then
    kill -9 $PID && echo "已按端口 $PORT 停止(PID $PID)"
  else
    echo "未发现运行中的服务"
  fi
fi
