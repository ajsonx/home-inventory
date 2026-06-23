"""AI image recognition for item entry forms."""
import base64
import io
import json

from PIL import Image, ImageOps

import config

ALLOWED_EXPIRY_MONTHS = {0, 3, 6, 12, 24}

PROMPT = """你是家庭物品管理系统的图片识别助手。
请识别图片中的家庭物品，并只返回一个合法 JSON 对象，不要输出解释。
如果图片中有多个独立物品，请在 items 中返回多项；如果只是一个物品，请返回一项。
分类、子分类、存放位置、具体位置、归属人优先从我提供的可选值中选择；无法确定就填空字符串。
价格通常无法从图片判断，无法确定就填空字符串。
有效期只允许返回 0、3、6、12、24，分别表示无、3个月、6个月、1年、2年。
返回格式固定如下：
{
  "shared": {
    "category": "",
    "subcategory": "",
    "location": "",
    "sublocation": "",
    "owner": "",
    "expiry_months": 0
  },
  "items": [
    {
      "name": "",
      "quantity": 1,
      "category": "",
      "subcategory": "",
      "location": "",
      "sublocation": "",
      "owner": "",
      "purchase_price": "",
      "expiry_months": 0
    }
  ]
}
"""


def recognize_items(image_bytes: bytes, mime_type: str, meta: dict) -> dict:
    if not config.ARK_API_KEY:
        raise RuntimeError("未配置 ARK_API_KEY")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("后端未安装 openai>=1.0，请先安装依赖") from exc

    client = OpenAI(base_url=config.ARK_BASE_URL, api_key=config.ARK_API_KEY)
    prepared = _prepare_image(image_bytes)
    models = _candidate_models()
    for idx, model in enumerate(models):
        try:
            return _recognize_with_model(client, model, prepared, meta)
        except Exception as exc:
            if idx < len(models) - 1 and _is_quota_error(exc):
                continue
            raise


def _candidate_models() -> list:
    models = [config.ARK_MODEL, *config.ARK_BACK_MODELS]
    result = []
    for model in models:
        if model and model not in result:
            result.append(model)
    return result


def _recognize_with_model(client, model: str, image_bytes: bytes, meta: dict) -> dict:
    if _api_mode(model) == "chat":
        response = _create_chat_completion(client, model, image_bytes, meta)
        return _normalize_result(_parse_json_text(_chat_output_text(response)))
    response = _create_response(client, model, image_bytes, meta)
    return _normalize_result(_parse_json_response(response))


def _api_mode(model: str) -> str:
    if config.ARK_API_MODE in {"chat", "responses"}:
        return config.ARK_API_MODE
    return "chat" if model.startswith("ep-") else "responses"


def _create_response(client, model: str, image_bytes: bytes, meta: dict):
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": _to_data_url(image_bytes, "image/jpeg"),
                    },
                    {
                        "type": "input_text",
                        "text": _build_prompt(meta),
                    },
                ],
            },
        ],
        "text": {"format": {"type": "json_object"}},
    }
    if config.AI_MAX_OUTPUT_TOKENS:
        payload["max_output_tokens"] = config.AI_MAX_OUTPUT_TOKENS
    return client.responses.create(**payload)


def _create_chat_completion(client, model: str, image_bytes: bytes, meta: dict):
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": _to_data_url(image_bytes, "image/jpeg")},
                    },
                    {"type": "text", "text": _build_prompt(meta)},
                ],
            }
        ],
        "response_format": {"type": "json_object"},
    }
    if config.AI_MAX_OUTPUT_TOKENS:
        payload["max_completion_tokens"] = config.AI_MAX_OUTPUT_TOKENS
    return client.chat.completions.create(**payload)


def _is_quota_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    code = getattr(exc, "code", "") or ""
    body = getattr(exc, "body", None)
    text = f"{code} {body} {exc}".lower()
    quota_words = (
        "quota",
        "insufficient",
        "exceed",
        "exceeded",
        "balance",
        "credit",
        "额度",
        "配额",
        "余额",
        "欠费",
    )
    return status == 429 or any(word in text for word in quota_words)


def _to_data_url(image_bytes: bytes, mime_type: str) -> str:
    mime = mime_type or "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _prepare_image(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((config.AI_IMAGE_MAX_SIDE, config.AI_IMAGE_MAX_SIDE))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=config.AI_IMAGE_JPEG_QUALITY, optimize=True)
    return out.getvalue()


def _build_prompt(meta: dict) -> str:
    options = {
        "categories": meta.get("categories", []),
        "locations": meta.get("locations", []),
        "owners": meta.get("owners", []),
    }
    return PROMPT + "\n当前可选值：" + json.dumps(options, ensure_ascii=False)


def _parse_json_response(response) -> dict:
    text = getattr(response, "output_text", "") or _collect_output_text(response)
    return _parse_json_text(text)


def _parse_json_text(text: str) -> dict:
    if not text:
        raise RuntimeError("AI 未返回可解析内容")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI 返回的内容不是合法 JSON") from exc
    if not isinstance(data, dict):
        raise RuntimeError("AI 返回 JSON 格式不正确")
    return data


def _chat_output_text(response) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    return getattr(message, "content", "") or ""


def _collect_output_text(response) -> str:
    chunks = []
    output = getattr(response, "output", None) or []
    for item in output:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    return "".join(chunks)


def _normalize_result(data: dict) -> dict:
    items = data.get("items")
    if not isinstance(items, list):
        items = []
    normalized_items = [_normalize_item(it) for it in items if isinstance(it, dict)]
    normalized_items = [it for it in normalized_items if it["name"]]
    return {
        "shared": _normalize_shared(data.get("shared") if isinstance(data.get("shared"), dict) else {}),
        "items": normalized_items[:20],
    }


def _normalize_shared(data: dict) -> dict:
    return {
        "category": _text(data.get("category")),
        "subcategory": _text(data.get("subcategory")),
        "location": _text(data.get("location")),
        "sublocation": _text(data.get("sublocation")),
        "owner": _text(data.get("owner")),
        "expiry_months": _expiry_months(data.get("expiry_months")),
    }


def _normalize_item(data: dict) -> dict:
    return {
        "name": _text(data.get("name")),
        "quantity": _quantity(data.get("quantity")),
        "category": _text(data.get("category")),
        "subcategory": _text(data.get("subcategory")),
        "location": _text(data.get("location")),
        "sublocation": _text(data.get("sublocation")),
        "owner": _text(data.get("owner")),
        "purchase_price": _price(data.get("purchase_price")),
        "expiry_months": _expiry_months(data.get("expiry_months")),
    }


def _text(value) -> str:
    return str(value or "").strip()


def _quantity(value) -> int:
    try:
        qty = int(value)
    except (TypeError, ValueError):
        qty = 1
    return max(1, qty)


def _price(value):
    if value in (None, ""):
        return ""
    try:
        price = float(value)
    except (TypeError, ValueError):
        return ""
    return "" if price < 0 else price


def _expiry_months(value) -> int:
    try:
        months = int(value)
    except (TypeError, ValueError):
        months = 0
    return months if months in ALLOWED_EXPIRY_MONTHS else 0
