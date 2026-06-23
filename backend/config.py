"""家庭物品管理系统配置。

所有可调参数集中在此，便于部署时修改。
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)


def _load_env_file(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file(os.path.join(ROOT_DIR, ".env"))

# 数据与文件目录
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
META_FILE = os.path.join(DATA_DIR, "meta.json")
ACHIEVEMENTS_FILE = os.path.join(DATA_DIR, "achievements.json")
# 成就规则配置（金额/称号/文案/门槛），可手动编辑，改完重启生效
ACHIEVEMENTS_CONFIG_FILE = os.path.join(DATA_DIR, "achievements_config.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# 服务监听配置：0.0.0.0 让家庭内网其它设备可访问
HOST = "0.0.0.0"
PORT = 8000

# Flask session 密钥（部署时请修改，或用环境变量覆盖）
SECRET_KEY = os.environ.get("HOME_ANALY_SECRET", "change-me-please-in-production")

# 图片 AI 识别（火山方舟 / OpenAI SDK 兼容接口）
ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
ARK_BASE_URL = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
ARK_MODEL = os.environ.get("ARK_MODEL", "ep-20260623133249-2bblt")
ARK_API_MODE = os.environ.get("ARK_API_MODE", "").strip().lower()
ARK_BACK_MODELS = [
    os.environ[f"ARK_BACK_MODEL_{idx}"].strip()
    for idx in range(1, 6)
    if os.environ.get(f"ARK_BACK_MODEL_{idx}", "").strip()
]
AI_IMAGE_MAX_SIDE = 1600
AI_IMAGE_JPEG_QUALITY = 85
AI_MAX_OUTPUT_TOKENS = int(os.environ["AI_MAX_OUTPUT_TOKENS"]) if os.environ.get("AI_MAX_OUTPUT_TOKENS") else None

# 图片缩略图最长边（像素）
THUMB_MAX_SIZE = 600
# 允许上传的图片扩展名
ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "heic", "heif"}

# 备份间隔（天）：启动补偿与判断依据
BACKUP_INTERVAL_DAYS = 30

# 默认存放位置（固定，支持快捷选择）
DEFAULT_LOCATIONS = [
    "客厅柜",
    "卧室衣柜",
    "厨房橱柜",
    "冰箱",
    "储物间",
    "书房书架",
    "阳台储物",
    "卫生间柜",
]

# 默认归属人
DEFAULT_OWNERS = [
    "女主人",
    "男主人",
]

# 默认物品分类
DEFAULT_CATEGORIES = [
    "食品",
    "药品",
    "清洁用品",
    "数码电器",
    "衣物",
    "文具书籍",
    "工具",
    "证件票据",
    "其它",
]
