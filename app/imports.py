# app/imports.py
"""
Централизованный импорт. В остальных модулях пишем:
    from app.imports import *

Тяжёлые или специфичные пакеты (httpx, openai, ddgs, trafilatura)
импортируются ЛОКАЛЬНО в тех модулях, где они реально нужны.
"""

# --- стандартная библиотека ---
import os
import sys
import json
import asyncio
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, time, timedelta, date
from zoneinfo import ZoneInfo
from typing import Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field

# --- настройки ---
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Telegram ---
from aiogram import Bot, Dispatcher, F, Router, BaseMiddleware
from aiogram.types import (
    Message, CallbackQuery, TelegramObject,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    BotCommand, BotCommandScopeChat,
)
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode, ChatAction
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

# --- планировщик ---
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

# --- БД ---
import aiosqlite

# --- ретраи ---
from tenacity import retry, stop_after_attempt, wait_exponential