"""LLM 參數萃取與 register 計算。支援 OpenAI / Claude 等相容 API。"""

import json
import os
from typing import Any

import httpx

from config import LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL


def _get_headers() -> dict[str, str]:
    if LLM_PROVIDER == "openai":
        headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    elif LLM_PROVIDER == "azure":
        headers = {"api-key": LLM_API_KEY, "Content-Type": "application/json"}
    elif LLM_PROVIDER == "claude":
        headers = {"x-api-key": LLM_API_KEY, "Content-Type": "application/json", "anthropic-version": "2023-06-01"}
    else:
        headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    return headers


def _get_url() -> str:
    if LLM_BASE_URL:
        base = LLM_BASE_URL.rstrip("/")
        if LLM_PROVIDER == "claude":
            return f"{base}/v1/messages"
        return f"{base}/v1/chat/completions"
    if LLM_PROVIDER == "claude":
        return "https://api.anthropic.com/v1/messages"
    return "https://api.openai.com/v1/chat/completions"


def _get_payload(messages: list[dict], response_format: dict | None = None) -> dict:
    if LLM_PROVIDER == "claude":
        payload: dict[str, Any] = {
            "model": LLM_MODEL or "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [m for m in messages if m["role"] != "system"],
        }
        system_msgs = [m["content"] for m in messages if m["role"] == "system"]
        if system_msgs:
            payload["system"] = system_msgs[0]
    else:
        payload = {
            "model": LLM_MODEL or "gpt-4o-mini",
            "messages": messages,
            "max_tokens": 4096,
        }
        if response_format:
            payload["response_format"] = response_format
    return payload


def _call_llm(messages: list[dict], response_format: dict | None = None) -> str:
    if not LLM_API_KEY:
        return json.dumps({"error": "LLM_API_KEY not configured"})
    headers = _get_headers()
    url = _get_url()
    payload = _get_payload(messages, response_format)
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, headers=headers, json=payload)
        data = resp.json()
    if LLM_PROVIDER == "claude":
        content = data.get("content", [{}])
        return content[0].get("text", "") if isinstance(content, list) else str(content)
    choice = data.get("choices", [{}])[0]
    return choice.get("message", {}).get("content", "")


def extract_parameters(model: str, doc_content: str) -> dict:
    system_msg = "你是一個專業的 sensor 規格參數萃取助手。請從 datasheet 內容中萃取出 sensor 初始化參數，並以 JSON 格式回覆。"
    user_msg = f"""請從以下 {model} datasheet 中萃取出 sensor 初始化參數。

回傳 JSON 格式，包含以下欄位（若找不到該資訊則填 null）：
{{
  "revision": "感測器版本號",
  "input_clock_mhz": 輸入時脈頻率(數字),
  "resolution": {{"width": 水平解析度, "height": 垂直解析度}},
  "crop": "裁切設定，若無則 null",
  "pixel_format": "像素格式",
  "frame_rate_fps": 幀率(數字),
  "system_clock_mhz": 系統時脈頻率(數字),
  "interface": {{"lanes": MIPI通道數, "data_rate_mhz": MIPI資料速率}},
  "backend_processor": "後端處理器",
  "embedded_line": "embedded line 設定",
  "fsin": "FSIN 設定",
  "core_setting_version": "core setting 版本",
  "device_id": "I2C device ID",
  "others": "其他備註"
}}

Datasheet 內容：
{doc_content[:80000]}
"""
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    result = _call_llm(messages, response_format={"type": "json_object"})
    try:
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"_raw": result, "error": "Failed to parse LLM response as JSON"}


def calculate_registers(model: str, params: dict, doc_content: str) -> str:
    system_msg = "你是一個專業的 sensor 初始化設定工程師。請根據規格參數計算出 register write 列表。"
    user_msg = f"""請根據以下 {model} 規格參數和 datasheet，產生 sensor 初始化 TXT 設定檔。

規格參數：
{json.dumps(params, indent=2, ensure_ascii=False)}

格式要求：
1. 檔頭以 `;TAG:0x10` 開頭，包含規格註解
2. 區段以 `;=== 區段名稱 ===` 分隔（Software Reset, System Control, PLL1, PLL2, Timing, Analog, MIPI, ISP, HDR, Output Format, EML, Safety）
3. 每行 register write 格式：`{{dev_id}} {{reg}} {{val}}  ;register功能說明`
4. 行內註解以兩個空格 + 分號分隔
5. Sleep 指令：`SL {{ms}}`
6. 使用空格而非 tab
7. 嚴格參考 datasheet 中的 register 預設值與配置

Datasheet 參考內容：
{doc_content[:80000]}
"""
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    return _call_llm(messages)
