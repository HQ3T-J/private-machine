# services/ai_engine.py — 桥接层：通过 API 客户端调用 AI
"""向后兼容模块：将 old services.ai_engine 调用重定向到 HTTP API"""

from api_client import APIClient


class AIConfig:
    def __init__(self, provider="openai", model="gpt-4o", api_key=""):
        self.provider = provider
        self.model = model
        self.api_key = api_key


def call_llm(config, messages) -> str:
    return "{}"


def parse_chat_log(text: str) -> list:
    """从粘贴的聊天记录拆分发言人"""
    import re
    result = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(.+?)[：:]", line)
        if m:
            result.append({"speaker": m.group(1), "content": line[m.end():].strip()})
        elif result:
            result[-1]["content"] += "\n" + line
    return result


def structure_speech(speaker, text, config=None) -> dict:
    return {"speaker": speaker, "yesterday": [text], "today": [], "blockers": []}


def summarize_meeting(structured_list, config=None) -> dict:
    return {"yesterday_collected": [], "today_collected": [], "blockers_collected": [],
            "action_items": []}


def run_pipeline(speeches, config=None) -> dict:
    return summarize_meeting(speeches, config)
