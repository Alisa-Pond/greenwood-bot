import os
import json
import random
import time
import re
import traceback
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from threading import Thread

import telebot
from telebot import types
from flask import Flask, request

telebot.logger.setLevel(logging.DEBUG)

app = Flask('')

@app.route('/')
def home():
    return "Greenwood Chronicles is alive!"
        


# Функція для "Квітка розквітла"
def process_harvest_plant(message):
    user_id = message.from_user.id
    task_name = message.text.strip()

    if task_name in ["🔙 Назад", "🔙 Назад до квестів"]:
        bot.send_message(message.chat.id, "Повертаємось до теплиці.", reply_markup=get_greenhouse_menu())
        return

    player = get_player(user_id)
    plants = player["quests"].get("plants", [])

    # Шукаємо рослину за назвою
    plant_to_remove = None
    for p in plants:
        if p["task"] == task_name:
            plant_to_remove = p
            break

    if plant_to_remove:
        plants.remove(plant_to_remove)
        save_player(user_id, player)

        bot.send_message(
            message.chat.id,
            f"🌺 <b>ВРОЖАЙ ЗІБРАНО!</b> 🌺\n\n"
            f"🌲Лісовик🌲: Оце так диво! Твоя рослина <b>{plant_to_remove['emoji']} {plant_to_remove['task']}</b> розквітла прекрасним цвітом!\n"
            f"Ти отримуєш заслужену гордість та магічну енергію!",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )
    else:
        bot.send_message(message.chat.id, "🌲Лісовик🌲: Я не знайшов такої рослини. Спробуй ще раз з меню.", reply_markup=get_greenhouse_menu())


# Функція для "Вирвати баобаб"
def process_remove_plant(message):
    user_id = message.from_user.id
    task_name = message.text.strip()

    if task_name in ["🔙 Назад", "🔙 Назад до квестів"]:
        bot.send_message(message.chat.id, "Повертаємось до теплиці.", reply_markup=get_greenhouse_menu())
        return

    player = get_player(user_id)
    plants = player["quests"].get("plants", [])

    plant_to_remove = None
    for p in plants:
        if p["task"] == task_name:
            plant_to_remove = p
            break

    if plant_to_remove:
        plants.remove(plant_to_remove)
        save_player(user_id, player)

        bot.send_message(
            message.chat.id,
            f"🪓 <b>БАОБАБ ВИРВАНО!</b>\n\n"
            f"🌲Лісовик🌲: Хрусь! Вирвали <b>{plant_to_remove['task']}</b> з корінням. "
            f"Тепер цей ґрунт знову чистий для нових SMART-цілей!",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )
    else:
        bot.send_message(message.chat.id, "🌲Лісовик🌲: Я не знайшов такого баобаба.", reply_markup=get_greenhouse_menu())
        
# --- ВЕБХУКИ ТА СЕРВЕР ---

@app.route('/' + str(BOT_TOKEN), methods=['POST'])
def getMessage():
    try:
        json_string = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print("❌ КРИТИЧНА ПОМИЛКА В ЛОГІЦІ БОТА:")
        print(traceback.format_exc())
        return "!", 200
        
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://greenwood-bot-yw5w.onrender.com/" + str(BOT_TOKEN))
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
