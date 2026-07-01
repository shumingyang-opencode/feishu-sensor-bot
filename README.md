# Sensor 設定小幫手 — 飛書 Bot

在飛書上直接搜尋文檔、AI 萃取參數、產出 sensor 初始化 TXT 設定檔。

## 部署方式

### 選項 A：Railway.app（推薦）

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template?referralCode=)

1. 把 `feishu-bot/` 目錄推送到 GitHub
2. 在 Railway 建立 New Project → Deploy from GitHub repo
3. Setting 中加環境變數（見下方）
4. 你會拿到一個 URL 如 `https://your-app.railway.app`
5. 到飛書後台 → 事件訂閱 → 設定 webhook URL

### 選項 B：Docker

```bash
cd feishu-bot/functions
docker build -t sensor-bot .
docker run -p 8080:8080 sensor-bot
```

### 選項 C：本機 Python

```bash
pip install fastapi uvicorn httpx
cd feishu-bot/functions
uvicorn main:app --host 0.0.0.0 --port 8080
```

## 環境變數

| 變數 | 必要 | 說明 |
|------|------|------|
| `APP_ID` | ✅ | 飛書應用 ID |
| `APP_SECRET` | ✅ | 飛書應用 Secret |
| `LLM_PROVIDER` | ✅ | `openai` / `claude` / `azure` |
| `LLM_MODEL` | ✅ | `gpt-4o-mini` / `claude-sonnet-4-20250514` |
| `LLM_API_KEY` | ✅ | LLM API 金鑰 |
| `LLM_BASE_URL` | ❌ | 自訂 API 端點（選擇性） |

## 飛書後台設定

1. **事件訂閱** → `im.message.receive_v1` → 填你的 Railway URL + `/webhook/im`
2. **卡片回調** → `card.action.trigger` → 填你的 Railway URL + `/webhook/card`

## 使用方式

```
使用者：幫我建 OX03C10
Bot：搜尋文檔 → 列出 → 選擇 → AI 萃取 → 確認 → 產出 TXT
```
