"""Reset saved categories from config.DEFAULT_CATEGORIES."""
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import config  # noqa: E402

CATEGORY_MAP = {
    "食品": "食品饮料",
    "饮料": "食品饮料",
    "药品": "医药健康",
    "医药护理": "医药健康",
    "清洁用品": "清洁洗护",
    "洗护用品": "清洁洗护",
    "厨具": "厨房餐饮",
    "厨卫用品": "厨房餐饮",
    "数码电器": "家电数码",
    "衣物": "服饰家纺",
    "文具书籍": "文体运动",
    "运动物品": "文体运动",
    "文体休闲": "文体运动",
    "工具": "工具耗材",
    "家具": "家具家装",
    "日用杂货": "其它",
}


def read_json(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fallback_category(allowed):
    if "其它" in allowed:
        return "其它"
    return config.DEFAULT_CATEGORIES[-1] if config.DEFAULT_CATEGORIES else ""


def normalize_category(name, allowed):
    name = str(name or "").strip()
    if not name or name in allowed:
        return name
    mapped = CATEGORY_MAP.get(name, fallback_category(allowed))
    return mapped if mapped in allowed else fallback_category(allowed)


def reset_meta():
    path = Path(config.META_FILE)
    meta = read_json(path, {})
    meta["categories"] = [{"name": name, "children": []} for name in config.DEFAULT_CATEGORIES]
    write_json(path, meta)
    return len(meta["categories"])


def reset_items():
    path = Path(config.ITEMS_FILE)
    items = read_json(path, [])
    if not isinstance(items, list):
        raise RuntimeError(f"{path} must contain a JSON list")

    allowed = set(config.DEFAULT_CATEGORIES)
    changed_categories = 0
    cleared_subcategories = 0

    for item in items:
        if not isinstance(item, dict):
            continue
        old_category = item.get("category", "")
        new_category = normalize_category(old_category, allowed)
        if old_category != new_category:
            item["category"] = new_category
            changed_categories += 1
        if item.get("subcategory"):
            item["subcategory"] = ""
            cleared_subcategories += 1

    write_json(path, items)
    return changed_categories, cleared_subcategories


def main():
    category_count = reset_meta()
    changed_categories, cleared_subcategories = reset_items()
    print(f"meta categories reset: {category_count}")
    print(f"item categories changed: {changed_categories}")
    print(f"item subcategories cleared: {cleared_subcategories}")


if __name__ == "__main__":
    main()
