# app/llm/tools.py
"""
Описания инструментов для function calling (формат OpenAI).
Реализация — в app/llm/tool_executor.py
"""

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Поиск в интернете. Используй, когда нужна свежая информация, "
                "факты, ссылки, новости, документация — всё, чего нет в твоих знаниях "
                "или что могло устареть."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Сколько результатов вернуть (1-10)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_url",
            "description": (
                "Скачать и прочитать содержимое веб-страницы по ссылке. "
                "Используй, когда пользователь дал URL и просит пересказать, "
                "объяснить, найти что-то в статье."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL страницы"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_task",
            "description": (
                "Сохранить рабочую задачу/напоминание о деле (НЕ таблетки — для таблеток "
                "есть отдельная система). Используй, когда пользователь говорит "
                "«запомни что надо сделать», «добавь задачу»."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Текст задачи"},
                    "deadline": {
                        "type": "string",
                        "description": "Срок в формате YYYY-MM-DD или YYYY-MM-DD HH:MM (опционально)",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Показать список активных задач пользователя.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Закрыть (отметить выполненной) задачу по её ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID задачи"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": (
                "Сохранить долгосрочный факт о пользователе: имя, привычки, "
                "рабочие проекты, предпочтения, аллергии, важные даты. "
                "Используй, когда пользователь сообщает что-то о себе, "
                "что стоит помнить и в следующих сессиях."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Короткий ключ (латиница, snake_case), напр. 'name', 'timezone', 'work_project'",
                    },
                    "value": {"type": "string", "description": "Значение факта"},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Прочитать локальный файл на сервере, где работает бот. "
                "Используй ТОЛЬКО если пользователь явно попросил прочитать файл "
                "по конкретному пути. Не пытайся читать системные файлы "
                "без явной просьбы."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Абсолютный путь к файлу"},
                    "max_chars": {
                        "type": "integer",
                        "description": "Максимум символов (по умолчанию 20000)",
                        "default": 20000,
                    },
                },
                "required": ["path"],
            },
        },
    },
]