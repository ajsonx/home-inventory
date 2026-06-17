"""家庭成就与维护基金：录入、清理过期、分类三类任务。

进度根据物品数据实时计算；领取记录与清理次数持久化到 achievements.json。

成就规则（金额/称号/描述/弹窗文案/达成门槛）可在 achievements_config.json
中编辑，改完重启服务生效；该文件不存在时会自动按默认值生成模板。
"""
import datetime
import os
import threading

import config
import storage

_lock = threading.RLock()
SOON_DAYS = 30

# 成就默认定义。
# 可配置字段（会被 achievements_config.json 覆盖）：title / fund / desc / popup / thresholds
# 固定字段（仅代码内）：id / group / group_name / icon / art / tier / metric
#   metric 决定进度用哪个指标：
#     entry_count / complete_pct / entry_amount / cleanup_count / classify_count
#   thresholds 决定达成门槛：
#     min_count（计数类）/ min_complete_pct（完整率%）/ min_amount（金额）/ min_image（图片数）
_DEFAULTS = [
    {
        "id": "entry_pioneer", "group": "entry", "group_name": "录入成就",
        "title": "开荒者", "fund": 30, "icon": "🌱", "metric": "entry_count",
        "thresholds": {"min_count": 10},
        "desc": "本人录入 ≥ 10 件",
        "popup": "初踏整理之路，喜提【开荒者】勋章！维护基金 {fund} 元已到账。",
    },
    {
        "id": "entry_archivist", "group": "entry", "group_name": "录入成就",
        "title": "档案员", "fund": 100, "icon": "📚", "metric": "entry_count",
        "thresholds": {"min_count": 50, "min_image": 15},
        "desc": "本人录入 ≥ 50 件且含图片 ≥ 15 张",
        "popup": "详录物件、图文并茂，解锁【档案员】！维护基金 {fund} 元已到账。",
    },
    {
        "id": "entry_organizer", "group": "entry", "group_name": "录入成就",
        "title": "井然主事官", "fund": 200, "icon": "🏛️", "metric": "complete_pct",
        "thresholds": {"min_complete_pct": 80},
        "desc": "本人录入物品中 ≥ 80% 填了分类+位置+归属人",
        "popup": "条理分明、信息完备，荣获【井然主事官】！维护基金 {fund} 元已到账。",
    },
    {
        "id": "entry_accountant", "group": "entry", "group_name": "录入成就",
        "title": "诚实记账", "fund": 100, "icon": "💰", "metric": "entry_amount",
        "thresholds": {"min_amount": 2000},
        "desc": "本人录入物品累计购入价 ≥ 2000 元",
        "popup": "摸清家底、账目清晰，喜提【诚实记账】！维护基金 {fund} 元已到账。",
    },
    {
        "id": "cleanup_t1", "group": "cleanup", "group_name": "清垢除旧・雅室净物", "tier": 1,
        "title": "清时小匠", "fund": 100, "icon": "🧺", "art": "basket", "metric": "cleanup_count",
        "thresholds": {"min_count": 10},
        "desc": "清理过期/临期物品 ≥ 10 件",
        "popup": "摒除积旧，守好物件时效，喜提【清时小匠】勋章！维护基金 {fund} 元已到账。",
    },
    {
        "id": "cleanup_t2", "group": "cleanup", "group_name": "清垢除旧・雅室净物", "tier": 2,
        "title": "守时行者", "fund": 200, "icon": "🗄️", "art": "cabinet", "metric": "cleanup_count",
        "thresholds": {"min_count": 30},
        "desc": "清理过期/临期物品 ≥ 30 件",
        "popup": "细致甄别、有序清整，让居所常新，解锁【守时行者】！维护基金 {fund} 元已到账。",
    },
    {
        "id": "cleanup_t3", "group": "cleanup", "group_name": "清垢除旧・雅室净物", "tier": 3,
        "title": "净庭掌事", "fund": 300, "icon": "🏡", "art": "courtyard", "metric": "cleanup_count",
        "thresholds": {"min_count": 50},
        "desc": "清理过期/临期物品 ≥ 50 件",
        "popup": "深度清扫陈年旧物，全屋焕然一新，荣获【净庭掌事】！维护基金 {fund} 元已到账。",
    },
    {
        "id": "classify_t1", "group": "classify", "group_name": "分类收纳", "tier": 1,
        "title": "分类巧匠", "fund": 100, "icon": "🏷️", "art": "labels", "metric": "classify_count",
        "thresholds": {"min_count": 10},
        "desc": "规范分类录入 ≥ 10 件（含分类+位置）",
        "popup": "细致分类，巧理杂物，喜提【分类巧匠】勋章！维护基金 {fund} 元已发放。",
    },
    {
        "id": "classify_t2", "group": "classify", "group_name": "分类收纳", "tier": 2,
        "title": "集纳达人", "fund": 200, "icon": "📦", "art": "shelves", "metric": "classify_count",
        "thresholds": {"min_count": 30},
        "desc": "规范分类录入 ≥ 30 件",
        "popup": "科学分区收纳，让物件一目了然，解锁【集纳达人】！维护基金 {fund} 元已到账。",
    },
    {
        "id": "classify_t3", "group": "classify", "group_name": "分类收纳", "tier": 3,
        "title": "藏纳规划师", "fund": 300, "icon": "✨", "art": "planner", "metric": "classify_count",
        "thresholds": {"min_count": 50},
        "desc": "规范分类录入 ≥ 50 件",
        "popup": "精心规划收纳布局，打造高效居家空间，荣获【藏纳规划师】！维护基金 {fund} 元到账。",
    },
]

# 用户可编辑的字段（来自 achievements_config.json）
_EDITABLE_KEYS = ("title", "fund", "desc", "popup", "thresholds")


def _ensure_config_file():
    """配置文件不存在时，按默认值生成可编辑模板。"""
    if os.path.exists(config.ACHIEVEMENTS_CONFIG_FILE):
        return
    template = {
        "_说明": "可编辑每个成就的 fund(维护基金)/title(称号)/desc(描述)/popup(弹窗文案)/"
                 "thresholds(达成门槛)。popup 中 {fund} 会自动替换为金额。改完重启服务生效。",
        "achievements": {
            a["id"]: {k: a[k] for k in _EDITABLE_KEYS if k in a} for a in _DEFAULTS
        },
    }
    storage._atomic_write_json(config.ACHIEVEMENTS_CONFIG_FILE, template)


def _load_overrides() -> dict:
    _ensure_config_file()
    data = storage._read_json(config.ACHIEVEMENTS_CONFIG_FILE, {})
    return data.get("achievements", {}) if isinstance(data, dict) else {}


def get_achievements() -> list:
    """返回合并了用户配置的成就列表（每次读取，便于改文件后即时生效）。"""
    overrides = _load_overrides()
    merged = []
    for base in _DEFAULTS:
        ach = dict(base)
        ov = overrides.get(base["id"], {})
        for k in _EDITABLE_KEYS:
            if k not in ov:
                continue
            if k == "thresholds" and isinstance(ov[k], dict):
                ach["thresholds"] = {**base.get("thresholds", {}), **ov[k]}
            else:
                ach[k] = ov[k]
        merged.append(ach)
    return merged


def _read_state():
    return storage._read_json(config.ACHIEVEMENTS_FILE, {"claimed": {}, "cleanup_counts": {}})


def _save_state(state):
    storage._atomic_write_json(config.ACHIEVEMENTS_FILE, state)


def _item_expiry_date(item) -> datetime.date | None:
    if item.get("expiry_months") and item.get("created_at"):
        d = datetime.datetime.fromtimestamp(item["created_at"])
        month = d.month - 1 + int(item["expiry_months"])
        year = d.year + month // 12
        month = month % 12 + 1
        day = min(d.day, 28)
        return datetime.date(year, month, day)
    if item.get("expiry_date"):
        try:
            return datetime.datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _is_cleanable_item(item) -> bool:
    """有过期设置且已过期或 30 天内到期，删除时计为清理。"""
    exp = _item_expiry_date(item)
    if not exp:
        return False
    today = datetime.date.today()
    days = (exp - today).days
    return days <= SOON_DAYS


def maybe_record_cleanup(member: str, item: dict) -> bool:
    if not member or not _is_cleanable_item(item):
        return False
    with _lock:
        state = _read_state()
        counts = state.setdefault("cleanup_counts", {})
        counts[member] = counts.get(member, 0) + 1
        _save_state(state)
    return True


def _member_items(items: list, member: str) -> list:
    return [it for it in items if it.get("created_by") == member]


def _is_classified(item) -> bool:
    return bool(item.get("category") and item.get("location"))


def _is_complete(item) -> bool:
    return bool(item.get("category") and item.get("location") and item.get("owner"))


def compute_stats(member: str) -> dict:
    items = _member_items(storage._load_items(), member)
    entry_count = len(items)
    entry_with_image = sum(1 for it in items if it.get("image"))
    complete = sum(1 for it in items if _is_complete(it))
    complete_rate = (complete / entry_count) if entry_count else 0
    entry_amount = round(
        sum((it.get("purchase_price") or 0) * storage._coerce_qty(it.get("quantity")) for it in items),
        2,
    )
    classify_count = sum(1 for it in items if _is_classified(it))
    state = _read_state()
    cleanup_count = state.get("cleanup_counts", {}).get(member, 0)
    return {
        "entry_count": entry_count,
        "entry_with_image": entry_with_image,
        "complete_rate": complete_rate,
        "entry_amount": entry_amount,
        "classify_count": classify_count,
        "cleanup_count": cleanup_count,
    }


def _metric_value(metric: str, stats: dict):
    if metric == "complete_pct":
        return int(stats["complete_rate"] * 100)
    return stats.get(metric, 0)


def _progress_for(ach: dict, stats: dict) -> dict:
    """返回当前值、目标值（用于进度条）。"""
    th = ach.get("thresholds", {})
    metric = ach.get("metric", "entry_count")
    cur = _metric_value(metric, stats)
    if metric == "complete_pct":
        return {"current": cur, "target": th.get("min_complete_pct", 100), "unit": "%"}
    if metric == "entry_amount":
        return {"current": cur, "target": th.get("min_amount", 0), "unit": "元"}
    target = th.get("min_count", 1)
    prog = {"current": min(cur, target), "target": target}
    if "min_image" in th:
        prog["extra"] = f"图片 {stats['entry_with_image']}/{th['min_image']}"
    return prog


def _is_eligible(ach: dict, stats: dict) -> bool:
    th = ach.get("thresholds", {})
    metric = ach.get("metric", "entry_count")
    cur = _metric_value(metric, stats)
    if metric == "complete_pct":
        return stats["entry_count"] >= 1 and cur >= th.get("min_complete_pct", 100)
    if metric == "entry_amount":
        return cur >= th.get("min_amount", 0)
    if cur < th.get("min_count", 1):
        return False
    if "min_image" in th and stats.get("entry_with_image", 0) < th["min_image"]:
        return False
    return True


def get_dashboard(member: str) -> dict:
    if not member:
        return {"member": "", "stats": {}, "groups": [], "total_fund_claimed": 0}
    stats = compute_stats(member)
    state = _read_state()
    claimed = state.get("claimed", {}).get(member, {})
    total_fund = sum(c.get("fund", 0) for c in claimed.values())

    groups_map = {}
    for ach in get_achievements():
        g = ach["group"]
        if g not in groups_map:
            groups_map[g] = {"id": g, "name": ach["group_name"], "items": []}
        prog = _progress_for(ach, stats)
        is_claimed = ach["id"] in claimed
        eligible = _is_eligible(ach, stats)
        pct = 100 if is_claimed else min(100, int(prog["current"] / prog["target"] * 100)) if prog["target"] else 0
        groups_map[g]["items"].append({
            **{k: ach[k] for k in ("id", "title", "fund", "icon", "desc", "popup", "tier", "art") if k in ach},
            "progress": prog,
            "percent": pct,
            "eligible": eligible and not is_claimed,
            "claimed": is_claimed,
            "claimed_at": claimed.get(ach["id"], {}).get("claimed_at"),
        })

    order = ["entry", "cleanup", "classify"]
    groups = [groups_map[k] for k in order if k in groups_map]
    return {
        "member": member,
        "stats": stats,
        "groups": groups,
        "total_fund_claimed": total_fund,
    }


def claim(member: str, ach_id: str):
    ach = next((a for a in get_achievements() if a["id"] == ach_id), None)
    if not ach or not member:
        return None, "无效成就或成员"
    stats = compute_stats(member)
    if not _is_eligible(ach, stats):
        return None, "尚未达成领取条件"
    with _lock:
        state = _read_state()
        member_claimed = state.setdefault("claimed", {}).setdefault(member, {})
        if ach_id in member_claimed:
            return None, "已领取过该成就"
        now = storage._now()
        member_claimed[ach_id] = {"claimed_at": now, "fund": ach["fund"]}
        _save_state(state)
    popup = ach["popup"].format(fund=ach["fund"], title=ach["title"])
    return {
        "id": ach_id,
        "title": ach["title"],
        "fund": ach["fund"],
        "popup": popup,
        "icon": ach.get("icon"),
        "art": ach.get("art"),
        "claimed_at": now,
    }, None
