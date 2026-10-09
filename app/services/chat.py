# app/services/chat.py
from typing import Callable, Awaitable

from app.llm import llm
from app.llm.prompts import build_system_prompt
from app.llm.tools import TOOLS
from app.llm.tool_executor import execute_tool
from app.memory import messages as msg_store
from app.utils.logger import log


MAX_TOOL_ITERATIONS = 4
PROGRESS_TOOLS = {
    "web_search": "🔍 ищу в интернете…",
    "read_url": "📖 читаю ссылку…",
    "read_file": "📄 читаю файл…",
    "list_dir": "📁 смотрю папку…",
}


async def respond(
    user_text: str,
    on_progress: Callable[[str], Awaitable[None]] | None = None,
) -> str:
    await msg_store.add_message("user", user_text)

    system = {"role": "system", "content": await build_system_prompt()}
    history = await msg_store.get_recent_messages(limit=8)

    messages = [system] + history
    tool_calls_made: list[str] = []
    search_cache: dict[str, str] = {}

    for iteration in range(MAX_TOOL_ITERATIONS):
        temp = 0.3 if iteration > 0 else 0.7

        result = await llm.chat(messages, tools=TOOLS, temperature=temp)
        content = result.get("content")
        calls = result.get("tool_calls") or []

        if not calls:
            answer = (content or "").strip() or "(пустой ответ модели)"
            await msg_store.add_message("assistant", answer)
            if tool_calls_made:
                log.info(f"tools used: {tool_calls_made}")
            return answer

        if on_progress:
            for tc in calls:
                msg = PROGRESS_TOOLS.get(tc["name"])
                if msg:
                    try:
                        await on_progress(msg)
                    except Exception as e:
                        log.warning(f"progress callback failed: {e}")
                    break

        messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"],
                    },
                }
                for tc in calls
            ],
        })

        for tc in calls:
            log.info(f"tool call: {tc['name']}({tc['arguments'][:200]})")
            tool_calls_made.append(tc["name"])

            cache_key = None
            if tc["name"] == "web_search":
                cache_key = tc["arguments"]
                if cache_key in search_cache:
                    log.info("web_search cache hit")
                    out = search_cache[cache_key]
                else:
                    out = await execute_tool(tc["name"], tc["arguments"])
                    search_cache[cache_key] = out
            else:
                out = await execute_tool(tc["name"], tc["arguments"])

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": out,
            })

    answer = "(слишком много вызовов инструментов, остановился)"
    await msg_store.add_message("assistant", answer)
    return answer