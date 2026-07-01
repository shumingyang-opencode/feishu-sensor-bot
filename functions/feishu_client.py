import time
import json
from typing import Any
from urllib.parse import urlencode

import httpx

from config import APP_ID, APP_SECRET, FEISHU_BASE


_token: str | None = None
_token_expire: float = 0


def _get_token(client: httpx.Client | None = None) -> str:
    global _token, _token_expire
    if _token and time.time() < _token_expire - 60:
        return _token
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    r = _request("POST", "/auth/v3/tenant_access_token/internal", json=data, client=client, use_token=False)
    _token = r["tenant_access_token"]
    _token_expire = time.time() + r["expire"]
    return _token


def _request(method: str, path: str, json: Any = None, params: dict | None = None,
             client: httpx.Client | None = None, use_token: bool = True) -> dict:
    url = f"{FEISHU_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if use_token:
        headers["Authorization"] = f"Bearer {_get_token(client)}"
    closer = client or httpx.Client(timeout=30.0)
    try:
        resp = closer.request(method, url, headers=headers, json=json, params=params)
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"API error [{path}]: code={result['code']} msg={result.get('msg')}")
        return result
    finally:
        if client is None:
            closer.close()


def bot_info() -> dict:
    return _request("GET", "/bot/v3/info")["bot"]


def list_files(page_size: int = 20, page_token: str | None = None) -> dict:
    params = {"page_size": page_size}
    if page_token:
        params["page_token"] = page_token
    return _request("GET", "/drive/v1/files", params=params)["data"]


def search_files(query: str, page_size: int = 20) -> list[dict]:
    params = {"page_size": page_size, "search_key": query}
    result = _request("GET", "/drive/v1/files/search", params=params)
    return result.get("data", {}).get("files", [])


def get_doc_raw_content(doc_token: str) -> str:
    result = _request("GET", f"/docx/v1/documents/{doc_token}/raw_content")
    return result.get("data", {}).get("content", "")


def get_doc_blocks(doc_token: str) -> list[dict]:
    result = _request("GET", f"/docx/v1/documents/{doc_token}/blocks")
    return result.get("data", {}).get("items", [])


def send_message(open_id: str, content: str | dict, msg_type: str = "interactive") -> dict:
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False)
    body = {
        "receive_id": open_id,
        "msg_type": msg_type,
        "content": content,
    }
    return _request("POST", "/im/v1/messages", json=body, params={"receive_id_type": "open_id"})


def send_text(open_id: str, text: str) -> dict:
    payload = json.dumps({"text": text}, ensure_ascii=False)
    return send_message(open_id, payload, msg_type="text")


def upload_file_to_cloud(file_name: str, content: bytes, parent_token: str | None = None) -> str:
    token = _get_token()
    url = f"{FEISHU_BASE}/drive/v1/files/upload_all"
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=60.0) as client:
        data: dict[str, str] = {"file_name": file_name, "file_size": str(len(content))}
        if parent_token:
            data["parent_token"] = parent_token
        files = {"file": (file_name, content)}
        resp = client.post(url, headers=headers, data=data, files=files)
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"Upload failed: {result}")
        return result["data"]["file_token"]
