# app/bot/commands.py
from app.imports import (
    Router, Command, CommandStart, Message, CallbackQuery,
)
from app.memory import messages as msg_store
from app.memory.profile import (
    get_all_facts, set_fact, delete_fact, facts_to_prompt,
)
from app.services.tasks import list_tasks, complete_task, format_tasks, add_task
from app.services.pills import format_today_status
from app.bot.keyboards import (
    main_reply_keyboard,
    profile_actions_keyboard,
    confirm_clear_profile_keyboard,
    tasks_keyboard,
    BTN_CHAT, BTN_TASKS, BTN_PILLS, BTN_PROFILE, BTN_HELP,
)
from app.utils.logger import log

router = Router(name="commands")


HELP_TEXT = """<b>Что я умею:</b>

• Свободный диалог на любые темы — работа, быт, общие вопросы.
• Помню контекст разговора и факты о тебе.
• Помогаю по работе: Linux, сети, Docker, мониторинг, скрипты.
• Читаю файлы (txt, pdf, docx, xlsx, код).
• Ищу в интернете и читаю ссылки.
• Веду задачи.
• Напоминаю про таблетки в 12:10 и 22:20.
• В 22:00 спрашиваю, как прошёл день.

<b>Команды:</b>
/profile — показать, что я о тебе знаю
/remember ключ=значение — запомнить факт
/forget ключ — удалить факт
/reset — сбросить контекст диалога
/tasks — активные задачи
/add_task текст — добавить задачу
/done ID — закрыть задачу
/pills — статус таблеток за сегодня
/help — эта справка
"""


# =====================================================================
# /start, /help, /id
# =====================================================================

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    log.info("/start")
    await message.answer(
        "Привет. Я твой личный ассистент.\n\n"
        "Пиши что угодно — отвечу. Кнопки внизу — быстрый доступ.\n"
        "Подробнее: /help",
        reply_markup=main_reply_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_reply_keyboard())


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(f"Ваш user_id: <code>{message.from_user.id}</code>")


# =====================================================================
# Reply-кнопки
# =====================================================================

@router.message(lambda m: m.text == BTN_HELP)
async def btn_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_reply_keyboard())


@router.message(lambda m: m.text == BTN_CHAT)
async def btn_chat(message: Message) -> None:
    await message.answer(
        "Обычный режим. Пиши сообщение.",
        reply_markup=main_reply_keyboard(),
    )


@router.message(lambda m: m.text == BTN_TASKS)
async def btn_tasks(message: Message) -> None:
    await _show_tasks(message)


@router.message(lambda m: m.text == BTN_PILLS)
async def btn_pills(message: Message) -> None:
    await _show_pills(message)


@router.message(lambda m: m.text == BTN_PROFILE)
async def btn_profile(message: Message) -> None:
    await _show_profile(message)


# =====================================================================
# /profile и callback
# =====================================================================

async def _show_profile(message: Message) -> None:
    facts = await get_all_facts()
    if not facts:
        text = (
            "Пока я ничего о тебе не знаю.\n"
            "Используй <code>/remember ключ=значение</code>."
        )
    else:
        text = "<b>Что я о тебе знаю:</b>\n" + facts_to_prompt(facts)
    await message.answer(text, reply_markup=profile_actions_keyboard())


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    await _show_profile(message)


@router.message(Command("remember"))
async def cmd_remember(message: Message) -> None:
    args = (message.text or "").partition(" ")[2].strip()
    if not args or "=" not in args:
        await message.answer("Формат: <code>/remember ключ=значение</code>")
        return
    key, _, value = args.partition("=")
    key, value = key.strip(), value.strip()
    if not key or not value:
        await message.answer("И ключ, и значение должны быть непустыми.")
        return
    await set_fact(key, value)
    await message.answer(f"Запомнил: <b>{key}</b> = {value}")


@router.message(Command("forget"))
async def cmd_forget(message: Message) -> None:
    key = (message.text or "").partition(" ")[2].strip()
    if not key:
        await message.answer("Формат: <code>/forget ключ</code>")
        return
    ok = await delete_fact(key)
    if ok:
        await message.answer(f"Удалил факт <b>{key}</b>.")
    else:
        await message.answer(f"Факт <b>{key}</b> не найден.")


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    await msg_store.clear_messages()
    await message.answer("Контекст диалога очищен. Профиль и задачи не тронуты.")


# =====================================================================
# Задачи
# =====================================================================

async def _show_tasks(message: Message) -> None:
    tasks = await list_tasks(only_open=True)
    if not tasks:
        await message.answer("Активных задач нет.")
        return
    text = "<b>Активные задачи:</b>\n<pre>" + format_tasks(tasks) + "</pre>"
    kb = tasks_keyboard(tasks)
    await message.answer(text, reply_markup=kb)


@router.message(Command("tasks"))
async def cmd_tasks(message: Message) -> None:
    await _show_tasks(message)


@router.message(Command("add_task"))
async def cmd_add_task(message: Message) -> None:
    text = (message.text or "").partition(" ")[2].strip()
    if not text:
        await message.answer("Формат: <code>/add_task текст задачи</code>")
        return
    task_id = await add_task(text)
    await message.answer(f"Задача <b>#{task_id}</b> добавлена.")


@router.message(Command("done"))
async def cmd_done(message: Message) -> None:
    arg = (message.text or "").partition(" ")[2].strip()
    if not arg.isdigit():
        await message.answer("Формат: <code>/done ID</code>")
        return
    ok = await complete_task(int(arg))
    if ok:
        await message.answer(f"Задача <b>#{arg}</b> закрыта.")
    else:
        await message.answer(f"Задача <b>{arg}</b> не найдена или уже закрыта.")


# =====================================================================
# Таблетки
# =====================================================================

async def _show_pills(message: Message) -> None:
    text = await format_today_status()
    await message.answer(text)


@router.message(Command("pills"))
async def cmd_pills(message: Message) -> None:
    await _show_pills(message)


# =====================================================================
# INLINE CALLBACKS (профиль, задачи)
# =====================================================================

@router.callback_query(lambda c: c.data and c.data.startswith("profile:"))
async def cb_profile(call: CallbackQuery) -> None:
    action = call.data.split(":", 1)[1]

    if action == "reset_context":
        await msg_store.clear_messages()
        await call.answer("Контекст очищен")
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await call.message.answer("Контекст диалога очищен. Профиль сохранён.")
        return

    if action == "clear_facts":
        await call.answer()
        try:
            await call.message.edit_reply_markup(
                reply_markup=confirm_clear_profile_keyboard()
            )
        except Exception:
            await call.message.answer(
                "Подтверди удаление профиля:",
                reply_markup=confirm_clear_profile_keyboard(),
            )
        return

    if action == "clear_facts_confirm":
        facts = await get_all_facts()
        for key in facts:
            await delete_fact(key)
        await call.answer("Профиль очищен")
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await call.message.answer("Все факты о тебе удалены.")
        return

    if action == "cancel":
        await call.answer("Отменено")
        try:
            await call.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return


@router.callback_query(lambda c: c.data and c.data.startswith("task:done:"))
async def cb_task_done(call: CallbackQuery) -> None:
    try:
        task_id = int(call.data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Некорректный ID")
        return

    ok = await complete_task(task_id)
    if not ok:
        await call.answer("Задача уже закрыта или не найдена")
        return

    await call.answer(f"Задача #{task_id} закрыта")

    tasks = await list_tasks(only_open=True)
    if not tasks:
        new_text = "<b>Активные задачи:</b>\n(нет активных задач)"
        new_kb = None
    else:
        new_text = "<b>Активные задачи:</b>\n<pre>" + format_tasks(tasks) + "</pre>"
        new_kb = tasks_keyboard(tasks)

    try:
        await call.message.edit_text(new_text, reply_markup=new_kb)
    except Exception as e:
        log.warning(f"edit_text failed: {e}")