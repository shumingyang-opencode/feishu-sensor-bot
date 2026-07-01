import asyncio
import json
import re
import traceback
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from feishu_client import send_message, send_text
from knowledge_search import search_sensor_docs, read_doc_content, search_sensor_docs_by_query
from llm_handler import extract_parameters, calculate_registers
from txt_generator import assemble_txt, upload_txt, validate as validate_txt
from session_manager import get_session


_recent_events: list[dict] = []
_MAX_LOG = 20


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Bot server started")
    yield
    print("Bot server stopped")


app = FastAPI(title="Sensor Setting Bot", version="1.0.0", lifespan=lifespan)


@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/logs")
async def view_logs():
    return _recent_events[-_MAX_LOG:]


def _log(source: str, body: dict, msg: str = ""):
    global _recent_events
    event_type = body.get("header", {}).get("event_type", body.get("type", "unknown"))
    _recent_events.append({
        "time": datetime.now().isoformat(),
        "source": source,
        "event_type": event_type,
        "msg": msg[:100],
    })
    if len(_recent_events) > _MAX_LOG * 3:
        _recent_events = _recent_events[-_MAX_LOG:]


def _get_open_id(event: dict) -> str:
    return event.get("event", {}).get("message", {}).get("sender", {}).get("sender_id", {}).get("open_id", "")


def _get_text(event: dict) -> str:
    content = event.get("event", {}).get("message", {}).get("content", "{}")
    try:
        return json.loads(content).get("text", "")
    except (json.JSONDecodeError, TypeError):
        return str(content)


def _extract_model(text: str) -> str | None:
    upper = text.upper()
    for pat in [r'(OX\w{4,10})', r'(X\d{2,4}\w?)']:
        m = re.search(pat, upper)
        if m:
            return m.group(1).upper()
    return None


async def _process_message(open_id: str, text: str):
    model = _extract_model(text)
    try:
        if not model:
            send_text(open_id, "請告訴我 sensor 型號，例如：OX03C10")
            return
        send_text(open_id, f"收到型號 {model}，正在搜尋文檔...")
        files = search_sensor_docs(model) or search_sensor_docs_by_query(model) or []
        if files:
            session = get_session()
            session.set(open_id, {"model": model, "files": files, "step": "select_files"})
            items = "\n".join(f"{i+1}. {f.get('name','?')}" for i, f in enumerate(files[:10]))
            send_text(open_id, f"找到 {len(files)} 份文檔，請選擇（如 1 或 all）：\n{items}")
        else:
            send_text(open_id, f"找不到 {model} 的相關文檔。請先上傳 datasheet 到飛書雲空間。")
    except Exception as e:
        send_text(open_id, f"處理時發生錯誤：{str(e)[:100]}")


@app.post("/webhook/im")
async def webhook_im(request: Request):
    body = await request.json()
    _log("im", body)
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    open_id = _get_open_id(body)
    text = _get_text(body)
    if open_id and text:
        asyncio.create_task(_process_message(open_id, text))
    return {"code": 0}


@app.post("/webhook/card")
async def webhook_card(request: Request):
    body = await request.json()
    _log("card", body)
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    return {"code": 0}
