import os


APP_ID = os.environ.get("APP_ID", "")
APP_SECRET = os.environ.get("APP_SECRET", "")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")

SESSION_BASE_ID = os.environ.get("SESSION_BASE_ID", "")
SESSION_TABLE_ID = os.environ.get("SESSION_TABLE_ID", "")

FEISHU_BASE = "https://open.feishu.cn/open-apis"

BOT_NAME = "Sensor 設定小幫手"
BOT_OPEN_ID = os.environ.get("BOT_OPEN_ID", "")

SENSOR_MODELS = ["OX03C10", "OX03C", "OX012A", "OX01A", "X3C", "OX08"]
