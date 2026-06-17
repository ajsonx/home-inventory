"""家庭物品管理系统配置。

所有可调参数集中在此，便于部署时修改。
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
