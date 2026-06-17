"""数据存储层：基于 JSON 文本文件，提供原子读写与物品 CRUD、搜索、统计。

并发模型：家用单机低并发，使用进程内可重入锁 + 临时文件原子替换，
保证写入过程中不会产生半截损坏文件。
"""
import json
import os
import tempfile
import threading
import time
import uuid

import config

_lock = threading.RLock()


def _now() -> int:
    """当前秒级时间戳（遵循 IGG 时间存储规范）。"""
    return int(time.time())


def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _atomic_write_json(path: str, data) -> None:
    """原子写入：先写临时文件再 rename，避免写一半损坏。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dir_name = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


# ---------------- meta（位置 / 分类 / 备份时间） ----------------

def _default_meta():
    return {
        "locations": [{"name": n, "children": []} for n in config.DEFAULT_LOCATIONS],
        "categories": [{"name": n, "children": []} for n in config.DEFAULT_CATEGORIES],
        "owners": list(config.DEFAULT_OWNERS),
        "last_backup_at": 0,
    }


def _normalize_list(items):
    """规整为去重的非空字符串列表（用于归属人等单级数据）。"""
    result = []
    seen = set()
    for it in items or []:
        s = it.strip() if isinstance(it, str) else ""
        if s and s not in seen:
            seen.add(s)
            result.append(s)
    return result


def _normalize_tree(items):
    """把分类/位置规整为两级树结构 [{name, children:[str,...]}]。

    兼容旧版扁平字符串数组（自动升级为一级节点）。
    """
    result = []
    seen = set()
    for it in items or []:
        if isinstance(it, str):
            name = it.strip()
            children = []
        elif isinstance(it, dict):
            name = (it.get("name") or "").strip()
            children = []
            child_seen = set()
            for c in it.get("children") or []:
                cs = c.strip() if isinstance(c, str) else ""
                if cs and cs not in child_seen:
                    child_seen.add(cs)
                    children.append(cs)
        else:
            continue
        if name and name not in seen:
            seen.add(name)
            result.append({"name": name, "children": children})
    return result


def get_meta() -> dict:
    with _lock:
        meta = _read_json(config.META_FILE, None)
        if meta is None:
            meta = _default_meta()
            _atomic_write_json(config.META_FILE, meta)
            return meta
        changed = False
        for k, v in _default_meta().items():
            if k not in meta:
                meta[k] = v
                changed = True
        # 规整树结构（含旧扁平数据迁移）
        norm_loc = _normalize_tree(meta.get("locations"))
        norm_cat = _normalize_tree(meta.get("categories"))
        norm_owner = _normalize_list(meta.get("owners"))
        if norm_loc != meta.get("locations"):
            meta["locations"] = norm_loc
            changed = True
        if norm_cat != meta.get("categories"):
            meta["categories"] = norm_cat
            changed = True
        if norm_owner != meta.get("owners"):
            meta["owners"] = norm_owner
            changed = True
        if changed:
            _atomic_write_json(config.META_FILE, meta)
        return meta


def update_meta(locations=None, categories=None, owners=None) -> dict:
    with _lock:
        meta = get_meta()
        if locations is not None:
            meta["locations"] = _normalize_tree(locations)
        if categories is not None:
            meta["categories"] = _normalize_tree(categories)
        if owners is not None:
            meta["owners"] = _normalize_list(owners)
        _atomic_write_json(config.META_FILE, meta)
        return meta


def set_last_backup_at(ts: int) -> None:
    with _lock:
        meta = get_meta()
        meta["last_backup_at"] = ts
        _atomic_write_json(config.META_FILE, meta)


# ---------------- items CRUD ----------------

def _load_items() -> list:
    return _read_json(config.ITEMS_FILE, [])


def _save_items(items: list) -> None:
    _atomic_write_json(config.ITEMS_FILE, items)


def list_items(q: str = "", location: str = "", category: str = "") -> list:
    """列表 + 全局搜索 + 筛选。按存入时间倒序。"""
    with _lock:
        items = _load_items()
    q = (q or "").strip().lower()
    if q:
        def _match(it):
            hay = " ".join([
                str(it.get("name", "")),
                str(it.get("category", "")),
                str(it.get("subcategory", "")),
                str(it.get("location", "")),
                str(it.get("sublocation", "")),
                str(it.get("owner", "")),
            ]).lower()
            return q in hay
        items = [it for it in items if _match(it)]
    if location:
        items = [it for it in items if it.get("location") == location]
    if category:
        items = [it for it in items if it.get("category") == category]
    items.sort(key=lambda it: it.get("created_at", 0), reverse=True)
    return items


def get_item(item_id: str):
    with _lock:
        for it in _load_items():
            if it.get("id") == item_id:
                return it
    return None


def create_item(data: dict) -> dict:
    with _lock:
        items = _load_items()
        now = _now()
        created = _coerce_ts(data.get("created_at")) or now
        item = {
            "id": uuid.uuid4().hex,
            "name": (data.get("name") or "").strip(),
            "quantity": _coerce_qty(data.get("quantity")),
            "image": data.get("image") or "",
            "expiry_date": (data.get("expiry_date") or "").strip(),
            "expiry_months": _coerce_count(data.get("expiry_months")),
            "category": (data.get("category") or "").strip(),
            "subcategory": (data.get("subcategory") or "").strip(),
            "location": (data.get("location") or "").strip(),
            "sublocation": (data.get("sublocation") or "").strip(),
            "owner": (data.get("owner") or "").strip(),
            "created_by": (data.get("created_by") or "").strip(),
            "purchase_price": _coerce_price(data.get("purchase_price")),
            "use_count": _coerce_count(data.get("use_count")),
            "created_at": created,
            "updated_at": now,
        }
        items.append(item)
        _save_items(items)
        return item


def update_item(item_id: str, data: dict):
    with _lock:
        items = _load_items()
        for it in items:
            if it.get("id") == item_id:
                if "name" in data:
                    it["name"] = (data.get("name") or "").strip()
                if "quantity" in data:
                    it["quantity"] = _coerce_qty(data.get("quantity"))
                if "image" in data and data.get("image") is not None:
                    it["image"] = data.get("image")
                if "expiry_date" in data:
                    it["expiry_date"] = (data.get("expiry_date") or "").strip()
                if "expiry_months" in data:
                    it["expiry_months"] = _coerce_count(data.get("expiry_months"))
                if data.get("created_at"):
                    it["created_at"] = _coerce_ts(data.get("created_at")) or it.get("created_at")
                if "category" in data:
                    it["category"] = (data.get("category") or "").strip()
                if "subcategory" in data:
                    it["subcategory"] = (data.get("subcategory") or "").strip()
                if "location" in data:
                    it["location"] = (data.get("location") or "").strip()
                if "sublocation" in data:
                    it["sublocation"] = (data.get("sublocation") or "").strip()
                if "owner" in data:
                    it["owner"] = (data.get("owner") or "").strip()
                if "purchase_price" in data:
                    it["purchase_price"] = _coerce_price(data.get("purchase_price"))
                if "use_count" in data:
                    it["use_count"] = _coerce_count(data.get("use_count"))
                it["updated_at"] = _now()
                _save_items(items)
                return it
    return None


def adjust_use_count(item_id: str, delta: int):
    """在原有使用次数上增减（不低于 0），用于列表页快捷调整。"""
    with _lock:
        items = _load_items()
        for it in items:
            if it.get("id") == item_id:
                current = _coerce_count(it.get("use_count"))
                it["use_count"] = max(0, current + int(delta))
                it["updated_at"] = _now()
                _save_items(items)
                return it
    return None


def delete_item(item_id: str):
    """删除物品，返回被删除的记录（含图片名，供调用方清理文件）。"""
    with _lock:
        items = _load_items()
        removed = None
        kept = []
        for it in items:
            if it.get("id") == item_id:
                removed = it
            else:
                kept.append(it)
        if removed is not None:
            _save_items(kept)
        return removed


def _coerce_qty(value) -> int:
    try:
        n = int(value)
        return n if n >= 1 else 1
    except (TypeError, ValueError):
        return 1


def _coerce_price(value):
    """购入价格：可选填，空则为 None，否则保留两位的非负浮点。"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        f = round(float(value), 2)
        return f if f >= 0 else None
    except (TypeError, ValueError):
        return None


def _coerce_count(value) -> int:
    """非负整数（使用次数 / 有效期月数等），默认 0。"""
    try:
        n = int(value)
        return n if n >= 0 else 0
    except (TypeError, ValueError):
        return 0


def _coerce_ts(value):
    """秒级时间戳；空或非法返回 None。"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    try:
        n = int(value)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


# ---------------- 统计聚合 ----------------

def stats() -> dict:
    """聚合统计：全局分类占比、各位置物品数与位置内分类占比。"""
    with _lock:
        items = _load_items()

    category_counts = {}
    category_amount = {}
    location_counts = {}
    # 位置 -> 分类 -> 数量
    location_category = {}
    total_amount = 0.0

    for it in items:
        cat = it.get("category") or "未分类"
        loc = it.get("location") or "未指定"
        qty = _coerce_qty(it.get("quantity"))
        price = it.get("purchase_price")
        amount = round((price or 0) * qty, 2)

        category_counts[cat] = category_counts.get(cat, 0) + 1
        category_amount[cat] = round(category_amount.get(cat, 0) + amount, 2)
        location_counts[loc] = location_counts.get(loc, 0) + 1
        location_category.setdefault(loc, {})
        location_category[loc][cat] = location_category[loc].get(cat, 0) + 1
        total_amount = round(total_amount + amount, 2)

    return {
        "total": len(items),
        "total_amount": total_amount,
        "category_counts": category_counts,
        "category_amount": category_amount,
        "location_counts": location_counts,
        "location_category": location_category,
    }
