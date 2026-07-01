import json
import re
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import BackgroundTasks, FastAPI, Request
from feishu_client import send_text
from knowledge_search import search_sensor_docs, search_sensor_docs_by_query
from session_manager import get_session


_recent_events: list[dict] = []
_MAX_LOG = 50


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
    return sorted(_recent_events, key=lambda x: x["time"], reverse=True)[:_MAX_LOG]


def _log(event_type: str, msg: str = ""):
    _recent_events.append({
        "time": datetime.now().isoformat(),
        "type": event_type,
        "msg": msg[:100],
    })
    if len(_recent_events) > _MAX_LOG * 3:
        _recent_events.clear()


def _get_open_id(body: dict) -> str:
    try:
        return body["event"]["message"]["sender"]["sender_id"]["open_id"]
    except (KeyError, TypeError):
        return ""


def _get_text(body: dict) -> str:
    try:
        return json.loads(body["event"]["message"]["content"]).get("text", "")
    except (KeyError, json.JSONDecodeError, TypeError):
        return ""


def _extract_model(text: str) -> str | None:
    for pat in [r'(OX\w{4,10})', r'(X\d{2,4}\w?)']:
        m = re.search(pat, text.upper())
        if m:
            return m.group(1).upper()
    return None


def process(open_id: str, text: str):
    _log("start", f"text='{text[:50]}'")
    try:
        model = _extract_model(text)
        if not model:
            send_text(open_id, "請告訴我 sensor 型號（如 OX03C10）")
            _log("done", "no_model")
            return
        send_text(open_id, f"收到型號 {model}，正在搜尋文檔...")
        _log("search", model)
        files = search_sensor_docs(model) or search_sensor_docs_by_query(model) or []
        if files:
            session = get_session()
            session.set(open_id, {"model": model, "files": files, "step": "select"})
            items = "\n".join(f"{i+1}. {f.get('name','?')}" for i, f in enumerate(files[:10]))
            send_text(open_id, f"找到 {len(files)} 份文檔：\n{items}\n請回覆編號（如 1）或 all")
        else:
            send_text(open_id, f"找不到 {model} 的相關文檔。請先上傳 datasheet。")
        _log("done", "ok")
    except Exception as e:
        _log("error", str(e)[:100])
        try:
            send_text(open_id, f"錯誤：{str(e)[:100]}")
        except Exception:
            pass


@app.post("/webhook/im")
async def webhook_im(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    _log("webhook", "received")
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    open_id = _get_open_id(body)
    text = _get_text(body)
    if open_id and text:
        _log("schedule", f"open_id={open_id[:10]}.. text={text[:30]}")
        background_tasks.add_task(process, open_id, text)
    else:
        _log("skip", f"open_id={open_id[:10]} text={text[:20]}")
    return {"code": 0}


@app.post("/webhook/card")
async def webhook_card(request: Request):
    body = await request.json()
    _log("card", "received")
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    return {"code": 0}
