from __future__ import annotations

import os
from typing import Any

import httpx

SYSTEM = """你是小红书图文编辑。只写能过审的种草笔记。
规则：
- 标题最多 20 个字，不要emoji
- 不要微信号、电话、加V、站外链接
- 不要绝对化承诺、医疗夸大、虚假折扣
- 语气像真人在分享经验，不要广告腔
只输出要求的内容，不要解释。"""


def llm_enabled() -> bool:
    if os.getenv("OPENAI_API_KEY"):
        return True
    return os.getenv("OLLAMA_HOST", "").strip() != "" or _ollama_up()


def _ollama_up() -> bool:
    try:
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=0.4)
        return r.status_code == 200
    except Exception:
        return False


def complete(prompt: str) -> str | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        try:
            r = httpx.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "temperature": 0.7,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=45,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

    if not _ollama_up():
        return None
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    try:
        r = httpx.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60,
        )
        r.raise_for_status()
        data: dict[str, Any] = r.json()
        return str(data.get("message", {}).get("content") or "").strip() or None
    except Exception:
        return None
