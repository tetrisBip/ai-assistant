# app/bot/keyboards.py
"""
Reply- и inline-клавиатуры.
Reply — постоянная клавиатура внизу.
Inline — кнопки под конкретным сообщением.
"""
from app.imports import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)


# =====================================================================
# REPLY-КЛАВИАТУРА (постоянная, внизу экрана)
# =====================================================================

BTN_CHAT = "👾 Обычный чат"
BTN_TASKS = "📋 Задачи"
BTN_PILLS = "Таблетки"
BTN_PROFILE = "👤 Профиль"
BTN_HELP = "❓ Помощь"


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CHAT), KeyboardButton(text=BTN_TASKS)],
            [KeyboardButton(text=BTN_PILLS), KeyboardButton(text=BTN_PROFILE)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Пиши сообщение или жми кнопку…",
    )


# =====================================================================
# INLINE-КНОПКИ
# =====================================================================

def profile_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Сбросить контекст диалога",
                callback_data="profile:reset_context",
            )],
            [InlineKeyboardButton(
                text="🗑 Очистить профиль",
                callback_data="profile:clear_facts",
            )],
        ]
    )


def confirm_clear_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠ Да, удалить всё", callback_data="profile:clear_facts_confirm"),
                InlineKeyboardButton(text="↩ Отмена", callback_data="profile:cancel"),
            ],
        ]
    )


def tasks_keyboard(tasks: list[dict]) -> InlineKeyboardMarkup | None:
    if not tasks:
        return None
    rows = []
    for t in tasks[:10]:
        short = t["text"][:40] + ("…" if len(t["text"]) > 40 else "")
        rows.append([
            InlineKeyboardButton(
                text=f"✅ #{t['id']} {short}",
                callback_data=f"task:done:{t['id']}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)