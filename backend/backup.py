"""备份模块：每月将 data 与 uploads 打包为 zip 存到 backups 目录。

- APScheduler 每月 1 号 03:00 执行一次。
- 启动补偿：若距上次备份超过 BACKUP_INTERVAL_DAYS 天则立即补备。
"""
import os
import time
import zipfile

from apscheduler.schedulers.background import BackgroundScheduler

import config
import storage


def _add_dir_to_zip(zf: zipfile.ZipFile, dir_path: str, arc_root: str) -> None:
    if not os.path.isdir(dir_path):
        return
    for root, _dirs, files in os.walk(dir_path):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, dir_path)
            zf.write(full, arcname=os.path.join(arc_root, rel))


def run_backup() -> str:
    """执行一次备份，返回生成的 zip 路径。"""
    os.makedirs(config.BACKUP_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(config.BACKUP_DIR, f"backup_{stamp}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        _add_dir_to_zip(zf, config.DATA_DIR, "data")
        _add_dir_to_zip(zf, config.UPLOAD_DIR, "uploads")
    storage.set_last_backup_at(int(time.time()))
    return zip_path


def _maybe_backup_on_start() -> None:
    meta = storage.get_meta()
    last = meta.get("last_backup_at", 0)
    interval = config.BACKUP_INTERVAL_DAYS * 86400
    if int(time.time()) - last >= interval:
        try:
            path = run_backup()
            print(f"[backup] 启动补偿备份完成: {path}")
        except Exception as e:  # noqa: BLE001
            print(f"[backup] 启动补偿备份失败: {e}")


def start_scheduler() -> BackgroundScheduler:
    """启动后台调度：每月 1 号 03:00 备份；并做启动补偿检查。"""
    _maybe_backup_on_start()
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(run_backup, "cron", day=1, hour=3, minute=0, id="monthly_backup")
    scheduler.start()
    return scheduler
