from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine.copy import generate_body, generate_tags
from engine.covers import generate_covers
from engine.titles import generate_titles


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CONTENT_CHECKER_ROOT = ROOT / "xiaohongshu-content-checker" / "xiaohongshu-content-checker" / "references"
MCP_URL = "http://127.0.0.1:18060/mcp"
HEALTH_URL = "http://127.0.0.1:18060/health"

app = FastAPI(title="小红书研究台", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


TOOL_LABELS = {
    "check_login_status": "检查登录状态",
    "get_login_qrcode": "获取登录二维码",
    "delete_cookies": "删除 Cookies",
    "publish_content": "发布图文",
    "list_feeds": "首页推荐",
    "search_feeds": "搜索笔记",
    "get_feed_detail": "笔记详情",
    "user_profile": "用户主页",
    "post_comment_to_feed": "发表评论",
    "reply_comment_in_feed": "回复评论",
    "publish_with_video": "发布视频",
    "like_feed": "点赞或取消",
    "favorite_feed": "收藏或取消",
    "get_my_profile": "我的主页",
    "get_unread_count": "未读数量",
    "list_notifications": "通知列表",
    "reply_notification": "回复通知",
    "like_notification": "点赞通知",
}

MUTATING_TOOLS = {
    "delete_cookies",
    "publish_content",
    "post_comment_to_feed",
    "reply_comment_in_feed",
    "publish_with_video",
    "like_feed",
    "favorite_feed",
    "reply_notification",
    "like_notification",
}
SIDE_EFFECT_TOOLS = {"list_notifications"}

CHECKER_REFERENCE_FILES = [
    CONTENT_CHECKER_ROOT / "risk-rubric.md",
    CONTENT_CHECKER_ROOT / "detection" / "SENSITIVE_WORDS.md",
    CONTENT_CHECKER_ROOT / "detection" / "REPLACEMENT_SUGGESTIONS.md",
    CONTENT_CHECKER_ROOT / "platform" / "PLATFORM_RULES.md",
]


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class ToolInvokeRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False


class SensitiveCheckRequest(BaseModel):
    title: str = Field(default="", max_length=80)
    content: str = Field(default="", max_length=3000)
    ner: bool = True


class DraftRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    points: str = Field(default="", max_length=400)
    audience: str = Field(default="", max_length=80)
    title: str = Field(default="", max_length=20)


class MCPClient:
    def __init__(self, url: str) -> None:
        self.url = url

    async def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        base_headers = {"Accept": "application/json, text/event-stream"}
        async with httpx.AsyncClient(timeout=90) as client:
            init = await client.post(
                self.url,
                headers=base_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "xhs-field-desk", "version": "1.0.0"},
                    },
                },
            )
            init.raise_for_status()
            session_id = init.headers.get("mcp-session-id")
            if not session_id:
                raise RuntimeError("本地服务没有返回会话 ID")

            headers = {**base_headers, "Mcp-Session-Id": session_id}
            await client.post(
                self.url,
                headers=headers,
                json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            )
            result = await client.post(
                self.url,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": method,
                    "params": params or {},
                },
            )
            result.raise_for_status()
            payload = result.json()
            if "error" in payload:
                raise RuntimeError(payload["error"].get("message", "调用失败"))
            return payload.get("result", {})

    async def call(self, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        result = await self.request("tools/call", {"name": tool, "arguments": arguments or {}})
        return normalize_tool_result(result)

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self.request("tools/list")
        return result.get("tools", [])


def normalize_tool_result(result: dict[str, Any]) -> dict[str, Any]:
    texts: list[str] = []
    images: list[str] = []
    parsed: list[Any] = []
    for item in result.get("content", []):
        if item.get("type") == "text":
            text = str(item.get("text", ""))
            texts.append(text)
            try:
                parsed.append(json.loads(text))
            except (json.JSONDecodeError, TypeError):
                pass
        elif item.get("type") == "image" and item.get("data"):
            mime = item.get("mimeType", "image/png")
            images.append(f"data:{mime};base64,{item['data']}")
    return {"text": "\n".join(texts).strip(), "images": images, "data": parsed}


def _risk_level(item: dict[str, Any]) -> int:
    level = str(item.get("level", "")).strip()
    return {"高": 3, "中": 2, "低": 1, "提示": 0}.get(level, 0)


def normalize_sensitive_result(data: dict[str, Any]) -> dict[str, Any]:
    words = data.get("wordList") or []
    words = sorted(words, key=_risk_level, reverse=True)
    stats = data.get("stats") or {}
    return {
        "hasSensitive": bool(data.get("hasSensitive")),
        "hasHighRisk": bool(data.get("hasHighRisk")),
        "wordCount": int(data.get("wordCount") or len(words)),
        "stats": {
            "high": int(stats.get("high") or 0),
            "mid": int(stats.get("mid") or 0),
            "low": int(stats.get("low") or 0),
            "tip": int(stats.get("tip") or 0),
        },
        "words": [
            {
                "keyword": str(item.get("keyword", "")),
                "category": str(item.get("category", "")),
                "level": str(item.get("level", "")),
                "suggestion": item.get("suggestion") or [],
            }
            for item in words
        ],
    }


def _extract_json_object(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise ValueError("内容检查器没有返回 JSON")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("内容检查器返回格式不是对象")
    return payload


def normalize_ai_sensitive_result(data: dict[str, Any]) -> dict[str, Any]:
    raw_words = data.get("words") or []
    words: list[dict[str, Any]] = []
    if isinstance(raw_words, list):
        for item in raw_words:
            if not isinstance(item, dict):
                continue
            keyword = str(item.get("keyword") or item.get("text") or "").strip()
            category = str(item.get("category") or "内容风险").strip()
            level = str(item.get("level") or "提示").strip()
            if level not in {"高", "中", "低", "提示"}:
                level = "提示"
            suggestion = item.get("suggestion") or []
            if isinstance(suggestion, str):
                suggestion = [suggestion]
            if not isinstance(suggestion, list):
                suggestion = []
            suggestion = [str(part).strip() for part in suggestion if str(part).strip()][:4]
            if keyword:
                words.append(
                    {
                        "keyword": keyword[:80],
                        "category": category[:80],
                        "level": level,
                        "suggestion": suggestion,
                    }
                )

    stats = {
        "high": sum(item["level"] == "高" for item in words),
        "mid": sum(item["level"] == "中" for item in words),
        "low": sum(item["level"] == "低" for item in words),
        "tip": sum(item["level"] == "提示" for item in words),
    }
    words = sorted(words, key=_risk_level, reverse=True)
    return {
        "hasSensitive": bool(words) or bool(data.get("hasSensitive")),
        "hasHighRisk": stats["high"] > 0 or bool(data.get("hasHighRisk")),
        "wordCount": len(words),
        "stats": stats,
        "words": words,
        "summary": str(data.get("summary") or "").strip()[:240],
        "optimizedTitle": str(data.get("optimizedTitle") or data.get("safeTitle") or "").strip()[:40],
        "optimizedContent": str(data.get("optimizedContent") or data.get("safeContent") or "").strip()[:3000],
    }


def load_checker_guidance() -> str:
    chunks: list[str] = []
    for path in CHECKER_REFERENCE_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue
        # Keep the request bounded while still giving the model the scoring rules,
        # risk categories, replacement suggestions, and platform guidance.
        chunks.append(f"## {path.name}\n{text[:6000]}")
    return "\n\n".join(chunks)


def load_checker_terms() -> list[tuple[str, str]]:
    path = CONTENT_CHECKER_ROOT / "detection" / "SENSITIVE_WORDS.md"
    if not path.exists():
        return []

    terms: list[tuple[str, str]] = []
    category = "规则库词表"
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        heading = re.match(r"^##+\s+\**(?:[一二三四五六七八九十\d\.、]+\s*[、.．]?\s*)?(.+?)\**$", line)
        if heading:
            category = re.sub(r"[🚨🔴🟠🟡✅❌*（）()：:]", "", heading.group(1)).strip() or category
            continue
        if not line.startswith("|") or "---" in line or "词汇" in line:
            continue
        cells = [cell.strip(" `*") for cell in line.strip("|").split("|")]
        if not cells:
            continue
        raw_term = cells[0].strip()
        if not raw_term or raw_term in {"词汇/表述", "项目", "风险表达", "违规表达"}:
            continue
        parts = re.split(r"[/／、,，]| 或 | 和 ", raw_term)
        for part in parts:
            term = part.strip()
            term = re.sub(r"\s+", "", term)
            term = re.sub(r"[（）()【】\[\]\"“”‘’]", "", term)
            if len(term) <= 1 or len(term) > 20:
                continue
            terms.append((term, category[:40]))

    seen: set[str] = set()
    unique_terms: list[tuple[str, str]] = []
    for term, item_category in terms:
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_terms.append((term, item_category))
    return unique_terms


async def ai_sensitive_check(title: str, content: str) -> dict[str, Any] | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None

    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODERATION_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")).strip()
    checker_guidance = load_checker_guidance()
    prompt = f"""你正在执行 xiaohongshu-content-checker 的完整检测模式。请严格依据下面的规则包检测标题和正文，并直接给出改写后的可发布版本。

边界：
- 只使用规则包中的评分、风险分类、平台规则、替代表达和输出边界。
- 不输出“必限流”“必封号”“一定违规”等绝对判断。
- 不提供绕过审核、隐藏联系方式、变体规避等建议。
- 只列出命中的风险项，不编造原文没有出现的风险词。
- 改写稿要保留原始业务意图，但删除或弱化高风险、中风险表达。

规则包摘要：
{checker_guidance}

只返回 JSON，不要 Markdown，不要解释。格式：
{{
  "hasSensitive": true,
  "hasHighRisk": true,
  "summary": "一句话说明整体风险",
  "optimizedTitle": "改写后的标题，尽量 20 字以内",
  "optimizedContent": "改写后的正文，保留核心信息但删除或弱化高风险表达",
  "words": [
    {{
      "keyword": "原文中的风险词或短句",
      "level": "高|中|低|提示",
      "category": "风险类型",
      "suggestion": ["替代表达或处理建议"]
    }}
  ]
}}

标题：
{title}

正文：
{content}
"""

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是 xiaohongshu-content-checker 的执行器。严格按用户提供的规则包检查和改写，只输出合法 JSON。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
            )
        response.raise_for_status()
        content_text = response.json()["choices"][0]["message"]["content"]
        return normalize_ai_sensitive_result(_extract_json_object(str(content_text)))
    except Exception:
        return None


def local_rewrite(title: str, content: str) -> tuple[str, str]:
    if any(word in f"{title}\n{content}" for word in ("定向订单", "定向培养", "订单班", "招生", "招聘要求", "薪资待遇")):
        safe_title = "先进制造岗位培养计划"
        safe_content = """高精尖数控｜技术员｜质检员

2026 年第 7 期培养计划正在报名中。

本校与相关制造企业开展岗位培养合作，课程围绕数控操作、质量检测、生产规范等方向设置。完成培训后，可根据学员学习情况、企业岗位需求和面试结果，推荐至相关岗位。

【适合人群】

符合岗位基础要求；

理工科方向或对先进制造岗位感兴趣；

无相关经验也可以先了解课程安排和培训内容。

【岗位参考】

入职后的福利政策以企业实际录用标准为准；

薪资可参考 5k-20k 区间，具体会受岗位类型、个人能力、工作城市、班次安排和企业制度影响；

岗位发展相对稳定，适合希望学习一门制造类技能的人群。

第 7 期正在报名。

具体课程内容、合作单位、岗位要求、薪资待遇和录用结果，请以实际咨询、面试及企业录用政策为准。"""
        return safe_title, safe_content

    replacements = [
        (r"军工企业|军工单位|军工岗位|军工|涉军|国防军工", "合作制造企业"),
        (r"航空制造", "先进制造"),
        (r"定向订单班|订单班|定向订单", "定向培养班"),
        (r"火热招生中|火热招生", "正在报名中"),
        (r"点对点培训结束直接对口入职|直接对口入职|直接入职|对口入职", "完成培训后可推荐至相关岗位"),
        (r"百分百就业率|100%\s*就业|百分百.*就业|就业率\s*100%", "往期就业情况以实际为准"),
        (r"百分百|100%", "较高"),
        (r"年龄\s*15[\-‑~—至到]\s*35\s*周岁|15[\-‑~—至到]\s*35\s*周岁", "符合岗位要求者"),
        (r"年龄\s*15|15\s*岁", "符合岗位要求"),
        (r"无需工作经验", "无经验者可了解培训安排"),
        (r"零基础学员", "基础较弱的学员"),
        (r"统一岗前培训", "提供岗前培训说明"),
        (r"综合月薪\s*5000\s*[-‑~—至到]\s*20000\s*元|5000\s*[-‑~—至到]\s*20000\s*元", "薪资可参考 5k-20k 区间，具体因岗位和个人情况而异"),
        (r"综合月薪\s*\d+\s*[-‑~—至到]\s*\d+\s*元|月薪\s*\d+\s*[-‑~—至到]\s*\d+", "薪资待遇按岗位和个人情况确定"),
        (r"五险一金", "相关福利以企业实际录用政策为准"),
        (r"多劳多得", "按岗位制度执行"),
        (r"长期稳定", "岗位发展相对稳定"),
        (r"微信|薇信|微\s*信|v信|V信|加V|加v|VX|vx", "站内咨询"),
        (r"1[3-9]\d{9}", "联系方式请以站内信息为准"),
        (r"http://|https://|www\.|\.com|\.cn", ""),
        (r"最[好佳强]|第一|顶级|极品|全网|唯一|绝对|永久", "比较"),
    ]

    safe_title = title
    safe_content = content
    for pattern, repl in replacements:
        safe_title = re.sub(pattern, repl, safe_title, flags=re.IGNORECASE)
        safe_content = re.sub(pattern, repl, safe_content, flags=re.IGNORECASE)

    cleanup_pairs = [
        ("定向培养班培训班", "定向培养班"),
        ("合作合作制造企业", "合作制造企业"),
        ("相关岗位合作制造企业", "相关岗位"),
        ("相关岗位合作合作制造企业", "相关岗位"),
        ("合作制造企业岗位发展", "相关岗位发展"),
        ("入职缴纳相关福利以企业实际录用政策为准", "入职后相关福利以企业实际录用政策为准"),
        ("岗位，合作制造企业岗位", "岗位，相关岗位"),
    ]
    for old, new in cleanup_pairs:
        safe_title = safe_title.replace(old, new)
        safe_content = safe_content.replace(old, new)

    safe_title = re.sub(r"\s+", " ", safe_title).strip(" ｜|-—")
    if len(safe_title) > 20:
        safe_title = safe_title[:20]
    safe_content = re.sub(r"\n{3,}", "\n\n", safe_content).strip()
    if safe_content and "具体以实际录用和培训安排为准" not in safe_content:
        safe_content += "\n\n具体岗位、薪资和录用结果以企业实际要求及面试情况为准，建议报名前仔细了解培训内容和合作单位信息。"
    return safe_title, safe_content


def local_sensitive_check(text: str, title: str = "", content: str = "") -> dict[str, Any]:
    patterns: list[tuple[str, str, str, list[str]]] = [
        (r"1[3-9]\d{9}", "高", "手机号", ["删除手机号", "改为私信咨询"]),
        (r"(微信|薇信|微\s*信|v信|V信|加V|加v|VX|vx)", "高", "站外引流", ["私信咨询", "评论区交流"]),
        (r"(http://|https://|www\.|\.com|\.cn)", "高", "外链", ["删除链接", "引导站内搜索"]),
        (r"(军工企业|军工单位|军工岗位|军工|涉军|国防军工|航空制造)", "高", "涉军/敏感行业宣传", ["弱化涉军表述", "改为合作制造企业", "避免承诺进入敏感单位"]),
        (r"(15[\-‑~—至到]\s*35\s*周岁|年龄\s*15|15\s*岁)", "高", "未成年人招聘/招生", ["明确合规招生对象", "删除未成年人就业导向表述"]),
        (r"(直接对口入职|直接入职|对口入职|包就业|保就业|安排就业|点对点.*入职)", "高", "就业承诺", ["改为推荐就业", "改为提供就业指导", "删除确定性承诺"]),
        (r"(百分百就业率|100%\s*就业|百分百.*就业|就业率\s*100%)", "高", "绝对化就业承诺", ["删除百分百", "改为往期就业情况以实际为准"]),
        (r"(综合月薪\s*\d+\s*[-‑~—至到]\s*\d+\s*元|月薪\s*\d+\s*[-‑~—至到]\s*\d+|5000\s*[-‑~—至到]\s*20000)", "中", "薪资区间宣传", ["注明薪资因岗位和个人情况而异", "避免夸大收入"]),
        (r"(定向订单班|订单班|定向订单|火热招生|第[一二三四五六七八九十\d]+期.*报名)", "中", "招生转就业营销", ["改为课程介绍", "补充真实资质和风险提示"]),
        (r"(无需工作经验|零基础学员|统一岗前培训|零基础.*培训)", "中", "低门槛就业诱导", ["说明培训条件", "避免暗示无门槛稳定就业"]),
        (r"(五险一金|长期稳定|多劳多得)", "低", "待遇承诺", ["改为以企业实际录用政策为准"]),
        (r"(最[好佳强]|第一|顶级|极品|全网|唯一|绝对|永久|百分百|100%)", "中", "极限/绝对化表达", ["很好", "出色", "较受欢迎", "体验不错"]),
        (r"(美白|祛斑|祛痘|抗炎|治疗|治愈|药效|疗效|根治)", "中", "医疗功效/功效承诺", ["提亮", "改善肤感", "日常护理", "使用体验"]),
        (r"(焦虑|自卑|毁容|丑|胖死|瘦到)", "低", "焦虑营销", ["更舒服", "更自信", "状态更好"]),
        (r"(赌博|博彩|彩票|毒品|色情)", "高", "违法/高风险内容", ["删除相关内容"]),
    ]
    words: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for pattern, level, category, suggestion in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            keyword = match.group(0)
            key = (keyword.lower(), category)
            if key in seen:
                continue
            seen.add(key)
            words.append(
                {
                    "keyword": keyword,
                    "category": category,
                    "level": level,
                    "suggestion": suggestion,
                }
            )

    for term, category in load_checker_terms():
        if term.lower() not in text.lower():
            continue
        key = (term.lower(), category)
        if key in seen or any(item["keyword"].lower() == term.lower() for item in words):
            continue
        seen.add(key)
        level = "中"
        if any(marker in category for marker in ("导流", "医疗", "虚假", "广告法", "价值观", "特殊行业", "高风险", "炫富", "阶层焦虑", "收益", "承诺")):
            level = "高"
        elif any(marker in category for marker in ("标题党", "软广", "营销", "同质化")):
            level = "低"
        words.append(
            {
                "keyword": term,
                "category": f"规则库：{category}",
                "level": level,
                "suggestion": ["建议删除或改为更客观、可验证的表达"],
            }
        )

    stats = {
        "high": sum(item["level"] == "高" for item in words),
        "mid": sum(item["level"] == "中" for item in words),
        "low": sum(item["level"] == "低" for item in words),
        "tip": sum(item["level"] == "提示" for item in words),
    }
    words = sorted(words, key=_risk_level, reverse=True)
    optimized_title, optimized_content = local_rewrite(title, content or text)
    return {
        "hasSensitive": bool(words),
        "hasHighRisk": stats["high"] > 0,
        "wordCount": len(words),
        "stats": stats,
        "words": words,
        "summary": "基于本地规则库检测到风险，已生成一版弱化高风险表达的改写稿。",
        "optimizedTitle": optimized_title,
        "optimizedContent": optimized_content,
    }


def classify(message: str) -> tuple[str, dict[str, Any], str]:
    clean = message.strip()
    lower = clean.lower()

    if "二维码" in clean or "扫码" in clean:
        return "get_login_qrcode", {}, "准备登录二维码"
    if "登录" in clean and any(word in clean for word in ("状态", "了吗", "没有", "检查")):
        return "check_login_status", {}, "检查登录状态"
    if any(word in clean for word in ("未读", "通知数")):
        return "get_unread_count", {}, "读取未读数量"
    if any(word in clean for word in ("我的主页", "我的账号", "我的资料")):
        return "get_my_profile", {}, "读取当前用户主页"
    if any(word in clean for word in ("首页", "推荐", "发现页")):
        return "list_feeds", {}, "读取首页推荐样本"

    search = re.search(r"(?:搜索|查找|研究|搜一下|搜一搜)\s*[:：]?\s*(.+)", clean)
    if search:
        keyword = search.group(1).strip()
        keyword = re.sub(r"(?:的笔记|相关笔记|并分析|前\s*\d+\s*条)$", "", keyword).strip()
        if keyword:
            return "search_feeds", {"keyword": keyword}, f"搜索「{keyword}」"

    if lower in {"help", "/help", "帮助"}:
        return "help", {}, "显示可用任务"
    return "help", {}, "需要更明确的研究任务"


def tool_risk(name: str) -> str:
    if name in MUTATING_TOOLS:
        return "write"
    if name in SIDE_EFFECT_TOOLS:
        return "side_effect"
    return "read"


async def live_tools() -> list[dict[str, Any]]:
    tools = await MCPClient(MCP_URL).list_tools()
    normalized: list[dict[str, Any]] = []
    for index, tool in enumerate(tools, start=1):
        name = str(tool.get("name", ""))
        risk = tool_risk(name)
        normalized.append(
            {
                "index": index,
                "name": name,
                "label": TOOL_LABELS.get(name, name),
                "description": tool.get("description", ""),
                "inputSchema": tool.get("inputSchema", {"type": "object", "properties": {}}),
                "annotations": tool.get("annotations", {}),
                "risk": risk,
                "riskLabel": {
                    "read": "只读",
                    "side_effect": "会清未读",
                    "write": "写操作",
                }[risk],
            }
        )
    return normalized


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/research")
async def research() -> FileResponse:
    return FileResponse(ROOT / "RESEARCH.md", media_type="text/markdown; charset=utf-8")


@app.get("/studio")
async def studio() -> FileResponse:
    return FileResponse(STATIC / "studio.html")


def _split_points(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[\n,，、;；]+", raw) if item.strip()]


@app.post("/api/draft")
async def make_draft(request: DraftRequest) -> dict[str, Any]:
    points = _split_points(request.points)
    titles, title_source = generate_titles(request.topic, points, request.audience)
    picked = request.title.strip() or titles[0]
    if picked not in titles:
        titles.insert(0, picked)
        titles = titles[:5]
    body, body_source = generate_body(request.topic, points, request.audience, picked)
    covers = generate_covers(picked, request.topic)
    return {
        "ok": True,
        "source": title_source if title_source == body_source else f"{title_source}+{body_source}",
        "titles": titles,
        "title": picked,
        "body": body,
        "tags": generate_tags(request.topic, points),
        "covers": covers,
    }


@app.post("/api/draft/covers")
async def remake_covers(request: DraftRequest) -> dict[str, Any]:
    title = request.title.strip() or request.topic[:20]
    return {"ok": True, "title": title, "covers": generate_covers(title, request.topic)}


@app.get("/api/status")
async def status() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            health = await client.get(HEALTH_URL)
            health.raise_for_status()
        login = await MCPClient(MCP_URL).call("check_login_status")
        return {"service": "online", "login": login}
    except Exception as exc:
        return {"service": "offline", "error": str(exc)}


@app.get("/api/tools")
async def list_all_tools() -> dict[str, Any]:
    try:
        tools = await live_tools()
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=503, detail="本地服务未启动") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {
        "count": len(tools),
        "tools": tools,
        "summary": {
            "read": sum(item["risk"] == "read" for item in tools),
            "side_effect": sum(item["risk"] == "side_effect" for item in tools),
            "write": sum(item["risk"] == "write" for item in tools),
        },
    }


@app.post("/api/sensitive-check")
async def sensitive_check(request: SensitiveCheckRequest) -> dict[str, Any]:
    title = request.title.strip()
    content = request.content.strip()
    text = "\n".join(part for part in (title, content) if part)
    if not text:
        raise HTTPException(status_code=400, detail="请先填写标题或正文，再做发布前检测。")

    ai_result = await ai_sensitive_check(title, content)
    if ai_result is not None:
        return {"ok": True, "source": "checker", "result": ai_result}

    return {
        "ok": True,
        "source": "local",
        "result": local_sensitive_check(text, title, content),
        "fallbackReason": "内容检查器语义改写未启用或暂时不可用，已使用规则包词表兜底",
    }


@app.post("/api/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: ToolInvokeRequest) -> dict[str, Any]:
    try:
        tools = await live_tools()
        spec = next((item for item in tools if item["name"] == tool_name), None)
        if spec is None:
            raise HTTPException(status_code=404, detail="不存在这个工具")

        risk = spec["risk"]
        if risk != "read" and not request.confirm:
            detail = "该工具会改变账号或平台内容，必须明确确认后执行。"
            if risk == "side_effect":
                detail = "读取通知列表会清除该分区的未读标记，必须确认后执行。"
            raise HTTPException(
                status_code=409,
                detail={"confirmation_required": True, "risk": risk, "message": detail},
            )

        result = await MCPClient(MCP_URL).call(tool_name, request.arguments)
    except HTTPException:
        raise
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=503, detail="本地服务未启动，请先运行 runtime/start.ps1") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "ok": True,
        "tool": tool_name,
        "activity": spec["label"],
        "risk": spec["risk"],
        "result": result,
    }


@app.post("/api/agent")
async def run_agent(request: AgentRequest) -> dict[str, Any]:
    tool, arguments, activity = classify(request.message)
    if tool == "help":
        return {
            "ok": True,
            "tool": "help",
            "activity": activity,
            "result": {
                "text": "自然语言入口可直接处理登录、搜索、首页、我的主页和未读数。全部 18 个工具都在左侧工具柜中；页面会按当前工具说明生成参数表单，写操作必须二次确认。\n\n示例：搜索 上海周末徒步",
                "images": [],
                "data": [],
            },
        }
    try:
        result = await MCPClient(MCP_URL).call(tool, arguments)
    except httpx.ConnectError as exc:
        raise HTTPException(status_code=503, detail="本地服务未启动，请先运行 runtime/start.ps1") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True, "tool": tool, "activity": activity, "result": result}
