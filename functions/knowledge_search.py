"""搜尋飛書雲端文檔中與 sensor 型號相關的檔案，並讀取內容。"""

import re
from feishu_client import list_files, get_doc_raw_content


def search_sensor_docs(model: str) -> list[dict]:
    upper = model.upper()
    results: list[dict] = []
    seen_tokens: set[str] = set()
    page_token: str | None = None
    for _ in range(5):
        data = list_files(page_size=50, page_token=page_token)
        for f in data.get("files", []):
            name = (f.get("name") or "").upper()
            token = f.get("token", "")
            if not token or token in seen_tokens:
                continue
            if upper in name or model.upper() in name:
                seen_tokens.add(token)
                results.append(f)
        if not data.get("has_more"):
            break
        page_token = data.get("next_page_token")
    return results


def search_sensor_docs_by_query(model: str) -> list[dict]:
    upper = model.upper()
    results: list[dict] = []
    seen: set[str] = set()
    try:
        from feishu_client import search_files
        for keyword in [upper, model]:
            files = search_files(keyword)
            for f in files:
                token = f.get("token", "")
                if token and token not in seen:
                    seen.add(token)
                    results.append(f)
    except Exception:
        pass
    return results


def read_doc_content(doc_token: str) -> str:
    raw = get_doc_raw_content(doc_token)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    raw = raw.strip()
    return raw


def extract_text_from_blocks(doc_token: str) -> str:
    try:
        from feishu_client import get_doc_blocks
        blocks = get_doc_blocks(doc_token)
        texts: list[str] = []
        for block in blocks:
            block_type = block.get("block_type", 0)
            if block_type == 2:
                for elem in block.get("text", {}).get("elements", []):
                    if elem.get("text_run"):
                        texts.append(elem["text_run"].get("content", ""))
                    elif elem.get("mention_doc"):
                        texts.append(f"[Doc: {elem['mention_doc'].get('token', '')}]")
        return "\n".join(texts)
    except Exception as e:
        return f"[Error reading blocks: {e}]"
