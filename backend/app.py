"""家庭物品管理系统 —— Flask REST API + 前端静态托管。

启动: python app.py
"""
import datetime
import io
import json as _json
import os
import shutil
import time
import uuid
from functools import wraps

from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory,
    session,
)
from flask_cors import CORS
from PIL import Image, ImageOps

import achievements
import auth
import backup
import config
import storage

# 前端构建产物目录（npm run build 生成）
FRONTEND_DIST = os.path.join(os.path.dirname(config.BASE_DIR), "frontend", "dist")

app = Flask(__name__, static_folder=None)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 单次请求最大 20MB

# 开发环境允许前端 dev server 跨域并携带 cookie
CORS(app, supports_credentials=True)


# ---------------- 鉴权 ----------------

def _date_to_ts(s):
    """把 'YYYY-MM-DD' 转为当天本地时间的秒级时间戳；空/非法返回 None。"""
    s = (s or "").strip()
    if not s:
        return None
    try:
        dt = datetime.datetime.strptime(s, "%Y-%m-%d")
        return int(time.mktime(dt.timetuple()))
    except ValueError:
        return None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("authed"):
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


@app.get("/api/auth/status")
def auth_status():
    return jsonify(auth.get_status())


@app.post("/api/auth/setup")
def auth_setup():
    """首次使用：选择身份并设置密码。"""
    if not auth.needs_setup():
        return jsonify({"error": "已完成初始化，请直接登录或注册新成员"}), 400
    data = request.get_json(silent=True) or {}
    member, err = auth.register(data.get("member"), data.get("password"))
    if err:
        return jsonify({"error": err}), 400
    session["authed"] = True
    session["member"] = member
    session.permanent = True
    return jsonify({"ok": True, "member": member})


@app.post("/api/auth/register")
def auth_register():
    """追加注册新的家庭成员账号。"""
    if auth.needs_setup():
        return jsonify({"error": "请先完成首次设置"}), 400
    data = request.get_json(silent=True) or {}
    member, err = auth.register(data.get("member"), data.get("password"))
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True, "member": member})


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    if auth.needs_setup():
        return jsonify({"error": "请先完成首次设置"}), 400
    ok, result = auth.verify(data.get("member"), data.get("password"))
    if not ok:
        return jsonify({"error": result}), 401
    session["authed"] = True
    session["member"] = result
    session.permanent = True
    return jsonify({"ok": True, "member": result})


@app.post("/api/auth/change_password")
@login_required
def auth_change_password():
    data = request.get_json(silent=True) or {}
    member = session.get("member", "")
    err = auth.change_password(
        member,
        data.get("old_password"),
        data.get("new_password"),
    )
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
def me():
    return jsonify({
        "authed": bool(session.get("authed")),
        "member": session.get("member", ""),
    })


# ---------------- meta ----------------

@app.get("/api/meta")
@login_required
def get_meta():
    return jsonify(storage.get_meta())


@app.post("/api/meta")
@login_required
def post_meta():
    data = request.get_json(silent=True) or {}
    meta = storage.update_meta(
        locations=data.get("locations"),
        categories=data.get("categories"),
        owners=data.get("owners"),
    )
    return jsonify(meta)


# ---------------- 图片处理 ----------------

def _ext_ok(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_IMAGE_EXTS


def _save_image(file_storage) -> str:
    """保存上传图片并生成缩略图，返回存储文件名（统一为 jpg）。"""
    if not file_storage or not file_storage.filename:
        return ""
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    name = f"{uuid.uuid4().hex}.jpg"
    raw = file_storage.read()
    img = Image.open(io.BytesIO(raw))
    # 依据 EXIF 方向校正，转 RGB 后缩放保存
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((config.THUMB_MAX_SIZE, config.THUMB_MAX_SIZE))
    img.save(os.path.join(config.UPLOAD_DIR, name), "JPEG", quality=85)
    return name


def _delete_image(name: str) -> None:
    if not name:
        return
    path = os.path.join(config.UPLOAD_DIR, name)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _copy_image(src_name: str) -> str:
    """复制一份图片为新文件名，使每个物品拥有独立图片（删除互不影响）。"""
    if not src_name:
        return ""
    src = os.path.join(config.UPLOAD_DIR, src_name)
    if not os.path.isfile(src):
        return ""
    new_name = f"{uuid.uuid4().hex}.jpg"
    shutil.copyfile(src, os.path.join(config.UPLOAD_DIR, new_name))
    return new_name


@app.get("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    return send_from_directory(config.UPLOAD_DIR, filename)


# ---------------- items CRUD ----------------

@app.get("/api/items")
@login_required
def api_list_items():
    items = storage.list_items(
        q=request.args.get("q", ""),
        location=request.args.get("location", ""),
        category=request.args.get("category", ""),
    )
    return jsonify(items)


@app.get("/api/items/<item_id>")
@login_required
def api_get_item(item_id):
    item = storage.get_item(item_id)
    if not item:
        return jsonify({"error": "not found"}), 404
    return jsonify(item)


@app.post("/api/items")
@login_required
def api_create_item():
    form = request.form
    image_name = ""
    if "image" in request.files:
        f = request.files["image"]
        if f and f.filename:
            if not _ext_ok(f.filename):
                return jsonify({"error": "不支持的图片格式"}), 400
            image_name = _save_image(f)
    if not (form.get("name") or "").strip():
        return jsonify({"error": "名称必填"}), 400
    item = storage.create_item({
        "name": form.get("name"),
        "quantity": form.get("quantity"),
        "image": image_name,
        "expiry_date": form.get("expiry_date"),
        "category": form.get("category"),
        "subcategory": form.get("subcategory"),
        "location": form.get("location"),
        "sublocation": form.get("sublocation"),
        "owner": form.get("owner"),
        "purchase_price": form.get("purchase_price"),
        "expiry_months": form.get("expiry_months"),
        "created_at": _date_to_ts(form.get("created_date")),
        "created_by": session.get("member", ""),
    })
    return jsonify(item), 201


@app.post("/api/items/batch")
@login_required
def api_batch_items():
    """批量新增：shared 为共享字段，items 为多行（name 必填）。

    支持 multipart：form 字段 payload(JSON 字符串) + 可选 image(整批共享图片)。
    也兼容纯 JSON（无图片）。共享图片会为每条物品复制独立副本。
    """
    if request.content_type and "multipart" in request.content_type:
        payload = _json.loads(request.form.get("payload") or "{}")
        image_file = request.files.get("image")
    else:
        payload = request.get_json(silent=True) or {}
        image_file = None

    shared = payload.get("shared") or {}
    rows = payload.get("items") or []
    created_ts = _date_to_ts(shared.get("created_date"))

    base_image = ""
    if image_file and image_file.filename:
        if not _ext_ok(image_file.filename):
            return jsonify({"error": "不支持的图片格式"}), 400
        base_image = _save_image(image_file)

    count = 0
    for r in rows:
        name = (r.get("name") or "").strip()
        if not name:
            continue
        storage.create_item({
            "name": name,
            "quantity": r.get("quantity"),
            "purchase_price": r.get("purchase_price"),
            "image": _copy_image(base_image) if base_image else "",
            "category": shared.get("category"),
            "subcategory": shared.get("subcategory"),
            "location": shared.get("location"),
            "sublocation": shared.get("sublocation"),
            "owner": shared.get("owner"),
            "expiry_months": shared.get("expiry_months"),
            "created_at": created_ts,
            "created_by": session.get("member", ""),
        })
        count += 1

    # 基准图已为每条复制独立副本，删除基准图避免悬挂文件
    if base_image:
        _delete_image(base_image)

    return jsonify({"created": count}), 201


@app.put("/api/items/<item_id>")
@login_required
def api_update_item(item_id):
    existing = storage.get_item(item_id)
    if not existing:
        return jsonify({"error": "not found"}), 404
    form = request.form
    update = {
        "name": form.get("name"),
        "quantity": form.get("quantity"),
        "expiry_date": form.get("expiry_date"),
        "category": form.get("category"),
        "subcategory": form.get("subcategory"),
        "location": form.get("location"),
        "sublocation": form.get("sublocation"),
        "owner": form.get("owner"),
        "purchase_price": form.get("purchase_price"),
        "expiry_months": form.get("expiry_months"),
        "created_at": _date_to_ts(form.get("created_date")),
    }
    if "image" in request.files:
        f = request.files["image"]
        if f and f.filename:
            if not _ext_ok(f.filename):
                return jsonify({"error": "不支持的图片格式"}), 400
            new_name = _save_image(f)
            update["image"] = new_name
            _delete_image(existing.get("image"))
    item = storage.update_item(item_id, update)
    return jsonify(item)


@app.post("/api/items/<item_id>/use_count")
@login_required
def api_adjust_use_count(item_id):
    """列表页快捷调整使用次数：body {delta: ±N}。"""
    data = request.get_json(silent=True) or {}
    try:
        delta = int(data.get("delta", 0))
    except (TypeError, ValueError):
        delta = 0
    item = storage.adjust_use_count(item_id, delta)
    if not item:
        return jsonify({"error": "not found"}), 404
    return jsonify(item)


@app.delete("/api/items/<item_id>")
@login_required
def api_delete_item(item_id):
    removed = storage.delete_item(item_id)
    if not removed:
        return jsonify({"error": "not found"}), 404
    _delete_image(removed.get("image"))
    cleaned = achievements.maybe_record_cleanup(session.get("member", ""), removed)
    return jsonify({"ok": True, "cleanup_recorded": cleaned})


# ---------------- 成就 ----------------

@app.get("/api/achievements")
@login_required
def api_achievements():
    member = session.get("member", "")
    return jsonify(achievements.get_dashboard(member))


@app.post("/api/achievements/claim")
@login_required
def api_claim_achievement():
    member = session.get("member", "")
    if not member:
        return jsonify({"error": "请先在登录或导航栏选择家庭成员身份"}), 400
    data = request.get_json(silent=True) or {}
    ach_id = (data.get("id") or "").strip()
    result, err = achievements.claim(member, ach_id)
    if err:
        return jsonify({"error": err}), 400
    return jsonify(result)


# ---------------- 统计 ----------------

@app.get("/api/stats")
@login_required
def api_stats():
    return jsonify(storage.stats())


# ---------------- 前端静态托管（生产） ----------------

@app.get("/")
@app.get("/<path:path>")
def serve_frontend(path=""):
    """托管 Vue 构建产物；非静态文件回退到 index.html 支持前端路由。"""
    if not os.path.isdir(FRONTEND_DIST):
        return (
            "前端尚未构建。请在 frontend 目录执行 npm install && npm run build，"
            "或开发时使用 npm run dev。",
            200,
        )
    target = os.path.join(FRONTEND_DIST, path)
    if path and os.path.isfile(target):
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    backup.start_scheduler()
    print(f"家庭物品管理系统启动: http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)
