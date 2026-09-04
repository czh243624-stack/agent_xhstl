from __future__ import annotations

from engine import llm
from engine.titles import short_topic


def _from_rules(topic: str, points: list[str], audience: str) -> str:
    who = audience.strip() or "想把这件事做清楚的人"
    t = topic.strip() or "这件事"
    bullets = points[:3] or ["先把目标说清楚", "按能执行的步骤拆", "做完回头检查一遍"]
    lines = [
        f"很多人做{short_topic(t)}时一上来就猛干，后面才发现方向偏了。",
        "",
        f"如果是{who}，我建议先抓住这几步：",
    ]
    for i, point in enumerate(bullets, start=1):
        lines.append(f"{i}. {point.strip('。.')}。")
    lines.extend(
        [
            "",
            "注意：别追求一次做完美，先跑通最小闭环。",
            "",
            "你现在卡在哪一步，评论区告诉我，我按你的情况拆一版。",
        ]
    )
    return "\n".join(lines)


def generate_body(topic: str, points: list[str], audience: str, title: str) -> tuple[str, str]:
    prompt = f"""写一篇小红书图文正文，配合这个标题：{title}
主题：{topic}
卖点：{"；".join(points) or "无"}
受众：{audience or "普通用户"}
要求：
- 300 到 500 字
- 开头点痛点，中间给 3 步做法，结尾引导评论
- 不要微信号、电话、链接
- 分段，口语"""
    raw = llm.complete(prompt)
    if raw and len(raw) > 80:
        return raw.strip(), "model"
    return _from_rules(topic, points, audience), "rules"


def generate_tags(topic: str, points: list[str]) -> list[str]:
    tags = [short_topic(topic)]
    for point in points[:3]:
        tag = short_topic(point)
        if tag not in tags:
            tags.append(tag)
    extras = ["经验分享", "避坑指南", "新手必看"]
    for extra in extras:
        if extra not in tags:
            tags.append(extra)
        if len(tags) >= 6:
            break
    return tags[:6]
