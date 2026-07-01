import json


def _card(header: dict, elements: list[dict]) -> dict:
    return {
        "config": {"wide_screen_mode": True},
        "header": header,
        "elements": elements,
    }


def _md(text: str) -> dict:
    return {"tag": "markdown", "content": text}


def _btn(text: str, value: str, type: str = "primary") -> dict:
    return {"tag": "action", "actions": [{"tag": "button", "text": {"tag": "lark_md", "content": text}, "value": {"action": value}, "type": type}]}


def _sep() -> dict:
    return {"tag": "hr"}


def loading(model: str) -> str:
    return _card(
        {"title": {"tag": "plain_text", "content": "🔍 正在搜尋..."}, "template": "blue"},
        [
            _md(f"**型號：** {model}"),
            _md("正在搜尋飛書文檔中的相關 datasheet..."),
            {"tag": "hr"},
            _md("⏳ 處理中，請稍候..."),
        ]
    )


def file_selection(model: str, files: list[dict]) -> str:
    if not files:
        return _card(
            {"title": {"tag": "plain_text", "content": "📄 未找到相關文檔"}, "template": "yellow"},
            [
                _md(f"在飛書文檔中找不到與 **{model}** 相關的檔案。"),
                _md("請先將 datasheet 上傳到飛書雲空間後再試。"),
                _btn("🔄 重新搜尋", "restart"),
            ]
        )
    items = []
    for i, f in enumerate(files, 1):
        name = f.get("name", f.get("file_name", f.get("token", "未知文檔")))
        url = f.get("url", "")
        line = f"**{i}.** {name}"
        if url:
            line += f"  [🔗]({url})"
        items.append(_md(line))
    return _card(
        {"title": {"tag": "plain_text", "content": f"📄 找到以下 {model} 相關文檔"}, "template": "blue"},
        [
            _md(f"請選擇要納入參考的文檔（回覆編號，逗號分隔）："),
            *items,
            _sep(),
            _md("📝 回覆 **1,2,3** 選擇多個，**0** 全部不選，**all** 全選"),
        ]
    )


def parameter_confirm(model: str, params: dict) -> str:
    lines = [
        f"**Sensor revision：** {params.get('revision', '?')}",
        f"**Input clock：** {params.get('input_clock_mhz', '?')} MHz",
        f"**Resolution：** {params.get('resolution', {}).get('width', '?')}x{params.get('resolution', {}).get('height', '?')}",
        f"**Pixel format：** {params.get('pixel_format', '?')}",
        f"**Frame rate：** {params.get('frame_rate_fps', '?')} fps",
        f"**System clock：** {params.get('system_clock_mhz', '?')} MHz",
        f"**Interface lanes：** {params.get('interface', {}).get('lanes', '?')}",
        f"**Interface data rate：** {params.get('interface', {}).get('data_rate_mhz', '?')} MHz",
        f"**Backend processor：** {params.get('backend_processor', '?')}",
        f"**Embedded line：** {params.get('embedded_line', '?')}",
        f"**FSIN：** {params.get('fsin', '?')}",
        f"**Core Setting version：** {params.get('core_setting_version', '?')}",
        f"**Device ID：** {params.get('device_id', '?')}",
    ]
    return _card(
        {"title": {"tag": "plain_text", "content": "✅ AI 參數萃取結果"}, "template": "green"},
        [
            _md(f"已從 datasheet 萃取到以下 **{model}** 參數："),
            _sep(),
            _md("\n".join(lines)),
            _sep(),
            _md("回覆 **ok** 確認全部正確，或輸入 **編號=新值** 修改（如 `2=50` 修改 input clock）。"),
            _btn("✅ 全部正確，下一步", "confirm_params"),
            _btn("🔄 重新萃取", "re_extract", "default"),
        ]
    )


def generating() -> str:
    return _card(
        {"title": {"tag": "plain_text", "content": "⏳ 正在產生設定檔..."}, "template": "blue"},
        [
            _md("正在計算 register values 並產生 TXT 設定檔..."),
            {"tag": "hr"},
            _md("⏳ 請稍候，約需 10-30 秒..."),
        ]
    )


def result(filename: str, file_token: str, params: dict) -> str:
    file_url = f"https://open.feishu.cn/open-apis/drive/v1/files/{file_token}"
    return _card(
        {"title": {"tag": "plain_text", "content": "✅ 設定檔產生完成！"}, "template": "green"},
        [
            _md(f"**{filename}**"),
            _sep(),
            _md("📋 **參數摘要：**"),
            _md(f"• Sensor: {params.get('revision', '?')}"),
            _md(f"• Resolution: {params.get('resolution', {}).get('width', '?')}x{params.get('resolution', {}).get('height', '?')}"),
            _md(f"• Frame rate: {params.get('frame_rate_fps', '?')} fps"),
            _md(f"• Format: {params.get('pixel_format', '?')}"),
            _sep(),
            _md(f"🔗 [📄 開啟檔案]({file_url})"),
            _sep(),
            _btn("🔄 重新產生", "restart", "default"),
            _btn("👍 設定正確", "feedback_ok", "primary"),
        ]
    )


def error(msg: str) -> str:
    return _card(
        {"title": {"tag": "plain_text", "content": "❌ 發生錯誤"}, "template": "red"},
        [
            _md(f"處理過程中發生錯誤：\n{msg}"),
            _sep(),
            _btn("🔄 重新開始", "restart", "default"),
        ]
    )
