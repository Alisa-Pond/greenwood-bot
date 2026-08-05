import re
from datetime import datetime
from zoneinfo import ZoneInfo

from telebot import types

from services.config import bot
from services.database import get_player, update_player
from services.utils import clean_skin_tones

from keyboards import get_scrolls_menu

print("📜 Модуль handlers/scrolls завантажено!")
