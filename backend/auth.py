"""家庭成员账号：每人独立密码，密码与身份绑定。

密码以哈希存储；首次使用需 setup，之后可注册新成员或修改自己的密码。
"""
import re

from werkzeug.security import check_password_hash, generate_password_hash

import config
import storage

_MIN_PASSWORD_LEN = 4
_MAX_MEMBER_LEN = 32


def _read_users():
    data = storage._read_json(config.USERS_FILE, None)
    if data is None:
        return {"users": []}
    if "users" not in data:
        data["users"] = []
    return data


def _save_users(data):
    storage._atomic_write_json(config.USERS_FILE, data)


def _normalize_member(name: str) -> str:
    return (name or "").strip()[:_MAX_MEMBER_LEN]


def needs_setup() -> bool:
    return len(_read_users()["users"]) == 0


def list_members() -> list:
    return [u["member"] for u in _read_users()["users"]]


def get_status() -> dict:
    users = list_members()
    registered = set(users)
    suggestions = [n for n in config.DEFAULT_OWNERS if n not in registered]
    return {
        "needs_setup": len(users) == 0,
        "users": users,
        "suggestions": suggestions,
    }


def _validate_password(password: str):
    if not password or len(password) < _MIN_PASSWORD_LEN:
        return f"密码至少 {_MIN_PASSWORD_LEN} 位"


def _validate_member(member: str):
    m = _normalize_member(member)
    if not m:
        return "请填写身份名称", ""
    if not re.match(r"^[\u4e00-\u9fa5a-zA-Z0-9_\-\s]{1,32}$", m):
        return "身份名称仅支持中文、字母、数字及常用符号", ""
    return None, m


def register(member: str, password: str):
    """注册新成员账号（setup 或追加注册）。"""
    err, m = _validate_member(member)
    if err:
        return None, err
    pwd_err = _validate_password(password)
    if pwd_err:
        return None, pwd_err
    data = _read_users()
    if any(u["member"] == m for u in data["users"]):
        return None, f"「{m}」已注册，请直接登录或换一个身份名称"
    now = storage._now()
    data["users"].append({
        "member": m,
        "password_hash": generate_password_hash(password),
        "created_at": now,
    })
    _save_users(data)
    return m, None


def verify(member: str, password: str):
    m = _normalize_member(member)
    if not m:
        return False, "请选择身份"
    data = _read_users()
    user = next((u for u in data["users"] if u["member"] == m), None)
    if not user:
        return False, "该身份尚未注册"
    if not check_password_hash(user["password_hash"], password):
        return False, "密码错误"
    return True, m


def change_password(member: str, old_password: str, new_password: str):
    ok, msg = verify(member, old_password)
    if not ok:
        return msg
    pwd_err = _validate_password(new_password)
    if pwd_err:
        return pwd_err
    if old_password == new_password:
        return "新密码不能与旧密码相同"
    data = _read_users()
    for u in data["users"]:
        if u["member"] == member:
            u["password_hash"] = generate_password_hash(new_password)
            _save_users(data)
            return None
    return "用户不存在"
