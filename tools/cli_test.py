# tools/cli_test.py
"""
Локальный CLI-тестер без Telegram.

Запуск из корня проекта:
    python -m tools.cli_test

Команды:
    /reset  — очистить историю диалога
    /exit   — выход
"""
import asyncio
import sys
from pathlib import Path

# чтобы 'app' импортировался, когда запускают из корня
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.memory.db import init_db
from app.memory import messages as msg_store
from app.services.chat import respond


async def main() -> None:
    await init_db()
    print("CLI-тестер ИИ-ассистента.")
    print("Пиши сообщение. /reset — очистить историю, /exit — выход.\n")

    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text == "/exit":
            break
        if text == "/reset":
            await msg_store.clear_messages()
            print("[history cleared]\n")
            continue

        try:
            answer = await respond(text)
        except Exception as e:
            print(f"[error] {type(e).__name__}: {e}\n")
            continue

        print(f"bot> {answer}\n")


if __name__ == "__main__":
    asyncio.run(main())