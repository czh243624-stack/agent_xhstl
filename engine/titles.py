from __future__ import annotations

import re

from engine import llm

MAX_TITLE = 20

_TEMPLATES = [
    "第一次{t}别急着下手",
    "{t}我劝你先看完",
    "把{t}讲清楚只要三步",
    "{t}这件事我走了弯路",
    "做{t}最容易忽略的点",
    "真心建议你这样开始{t}",
    "{t}别再按老办法做了",
    "我把{t}拆成能照做的步骤",
]


def clip(text: str, n: int = MAX_TITLE) -> str:
    s = re.sub(r"\s+", "", text)
    s = re.sub(r"[#@]|微信|加V|v信", "", s, flags=re.I)
    return s[:n]


def short_topic(topic: str) -> str:
    t = re.sub(r"\s+", "", topic)
    return t[:8] if len(t) > 8 else t or "这件事"


def from_templates(topic: str, points: list[str]) -> list[str]:
    t = short_topic(topic)
    out: list[str] = []
    for tpl in _TEMPLATES:
        title = clip(tpl.format(t=t))
        if title and title not in out:
            out.append(title)
        if len(out) >= 5:
            break
    if points:
        hook = clip(f"{short_topic(points[0])}，我是这么做的")
        if hook not in out:
            out.insert(1, hook)
    return out[:5]


def generate_titles(topic: str, points: list[str], audience: str) -> tuple[list[str], str]:
    prompt = f"""根据下面信息写 5 个小红书标题，每行一个，不要编号。
主题：{topic}
卖点：{"；".join(points) or "无"}
受众：{audience or "普通用户"}
每个标题不超过 20 字，口语，像搜索时会点进去的那种。"""
    raw = llm.complete(prompt)
    if raw:
        cleaned: list[str] = []
        for line in raw.splitlines():
            line = re.sub(r"^[\d\.\-\*、]+", "", line).strip()
            line = clip(line)
            if line and len(line) >= 4 and line not in cleaned:
                cleaned.append(line)
        if len(cleaned) >= 3:
            return cleaned[:5], "model"
    return from_templates(topic, points), "rules"
