# app/llm/tool_executor.py
import asyncio
import json
from pathlib import Path

from app.services.web_search import search as web_search_sync, format_results
from app.services.url_reader import fetch_text
from app.services.tasks import add_task, list_tasks, complete_task, format_tasks
from app.services.file_reader import extract_text, FileReadError
from app.memory.profile import set_fact
from app.utils.logger import log


async def execute_tool(name: str, arguments: str) -> str:
    """
    Принимает имя инструмента и JSON-строку с аргументами.
    Возвращает строку-результат для LLM.
    """
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError as e:
        return f"(ошибка разбора аргументов: {e})"

    try:
        if name == "web_search":
            return await _web_search(args)
        if name == "read_url":
            return await _read_url(args)
        if name == "save_task":
            return await _save_task(args)
        if name == "list_tasks":
            return await _list_tasks(args)
        if name == "complete_task":
            return await _complete_task(args)
        if name == "remember":
            return await _remember(args)
        if name == "read_file":
            return await _read_file(args)
        if name == "list_dir":
            return await _list_dir(args)
        return f"(неизвестный инструмент: {name})"
    except Exception as e:
        log.exception(f"tool {name} failed")
        return f"(ошибка выполнения {name}: {type(e).__name__}: {e})"


# =====================================================================
# Инструменты
# =====================================================================

async def _web_search(args: dict) -> str:
    query = args.get("query", "").strip()
    if not query:
        return "(пустой запрос)"
    max_results = int(args.get("max_results", 5))
    results = await asyncio.to_thread(web_search_sync, query, max_results)
    return format_results(results)


async def _read_url(args: dict) -> str:
    url = args.get("url", "").strip()
    if not url:
        return "(пустой url)"
    return await asyncio.to_thread(fetch_text, url)


async def _save_task(args: dict) -> str:
    text = args.get("text", "").strip()
    if not text:
        return "(пустой текст задачи)"
    deadline = args.get("deadline") or None
    task_id = await add_task(text, deadline)
    suffix = f", срок: {deadline}" if deadline else ""
    return f"Задача #{task_id} сохранена: {text}{suffix}"


async def _list_tasks(args: dict) -> str:
    tasks = await list_tasks(only_open=True)
    return format_tasks(tasks)


async def _complete_task(args: dict) -> str:
    try:
        task_id = int(args.get("task_id"))
    except (TypeError, ValueError):
        return "(некорректный task_id)"
    ok = await complete_task(task_id)
    if ok:
        return f"Задача #{task_id} закрыта."
    return f"Задача #{task_id} не найдена или уже закрыта."


async def _remember(args: dict) -> str:
    key = args.get("key", "").strip()
    value = args.get("value", "").strip()
    if not key or not value:
        return "(нужны key и value)"
    await set_fact(key, value)
    return f"Запомнил: {key} = {value}"


async def _read_file(args: dict) -> str:
    path_str = args.get("path", "").strip()
    if not path_str:
        return "(пустой путь)"
    p = Path(path_str)
    max_chars = int(args.get("max_chars", 20000))
    try:
        text = await asyncio.to_thread(extract_text, p, max_chars)
        return f"Содержимое {path_str}:\n\n{text}"
    except FileReadError as e:
        return f"(не удалось прочитать: {e})"


async def _list_dir(args: dict) -> str:
    path_str = args.get("path", "").strip()
    if not path_str:
        return "(пустой путь)"
    p = Path(path_str)
    if not p.exists():
        return f"(путь не существует: {path_str})"
    if not p.is_dir():
        return f"(это не директория: {path_str})"
    try:
        entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        return f"(нет прав на чтение {path_str})"

    lines = []
    for e in entries[:200]:
        if e.is_dir():
            lines.append(f"[D] {e.name}/")
        else:
            try:
                size = e.stat().st_size
            except Exception:
                size = 0
            lines.append(f"[F] {e.name} ({size} б)")
    if len(entries) > 200:
        lines.append(f"...и ещё {len(entries) - 200} элементов")

    if not lines:
        return f"Содержимое {path_str}: (пусто)"
    return f"Содержимое {path_str}:\n" + "\n".join(lines)