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
        

# ----------------------------------------------------
# 📌 КРОК 2: Обробка створення рослини
# ----------------------------------------------------
def process_plant_creation(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Якщо натиснули кнопку скасування
    if text in ["🔙 Назад", "🔙 Назад до квестів", "/cancel"]:
        bot.send_message(
            message.chat.id, 
            "🌲Лісовик🌲: Хм, ну й добре. Менше бур'янів у теплиці!", 
            reply_markup=get_greenhouse_menu()
        )
        return

    # Розділяємо рядок за допомогою риски /
    parts = [p.strip() for p in text.split("/")]

    if len(parts) != 3:
        msg = bot.send_message(
            message.chat.id,
            "🌲Лісовик🌲: Грррм! Ти взагалі мене слухав? <b>Треба рівно дві риски / !</b>\n\n"
            "Напиши у форматі: <code>Емодзі / Назва цілі / ДД.ММ</code>\n"
            "Спробуй ще раз або натисни кнопку повернення:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_plant_creation)
        return

    raw_emoji, task, deadline = parts[0], parts[1], parts[2]

    # Чистимо тони шкіри
    emoji = raw_emoji
    for skin_tone, clean_emoji in replacements.items():
        emoji = emoji.replace(skin_tone, clean_emoji)

    valid_emojis = ["💪", "🧠", "🎨", "💵", "🤝"]
    if emoji not in valid_emojis:
        msg = bot.send_message(
            message.chat.id,
            "🌲Лісовик🌲: Що це за дивна магія? Використовуй тільки правильні смайлики: 💪, 🧠, 🎨, 💵, 🤝\nСпробуй ще раз:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_plant_creation)
        return

    # Зберігаємо рослину
    player = get_player(user_id)
    if "plants" not in player["quests"]:
        player["quests"]["plants"] = []

    player["quests"]["plants"].append({
        "emoji": emoji,
        "task": task,
        "deadline": deadline
    })
    save_player(user_id, player)

    bot.send_message(
        message.chat.id, 
        f"🌲Лісовик🌲: Ну добре, закопали твоє зерно <b>{emoji} {task}</b>! Тепер поливай його своєю працею до {deadline}!", 
        parse_mode="HTML", 
        reply_markup=get_greenhouse_menu()
    )

    # Розділяємо рядок за допомогою риски /
    parts = [p.strip() for p in text.split("/")]

    if len(parts) != 3:
        msg = bot.send_message(
            message.chat.id,
            "🌲Лісовик🌲: Грррм! Ти взагалі мене слухав? <b>Треба рівно дві риски / !</b>\n\n"
            "Напиши у форматі: <code>Емодзі / Назва цілі / ДД.ММ</code>\n"
            "Спробуй ще раз або натисни кнопку повернення:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_plant_creation)
        return

    raw_emoji, task, deadline = parts[0], parts[1], parts[2]

    # Чистимо тони шкіри
    emoji = raw_emoji
    for skin_tone, clean_emoji in replacements.items():
        emoji = emoji.replace(skin_tone, clean_emoji)

    valid_emojis = ["💪", "🧠", "🎨", "💵", "🤝"]
    if emoji not in valid_emojis:
        msg = bot.send_message(
            message.chat.id,
            "🌲Лісовик🌲: Що це за дивна магія? Використовуй тільки правильні смайлики: 💪, 🧠, 🎨, 💵, 🤝\nСпробуй ще раз:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_plant_creation)
        return

    # Зберігаємо рослину
    player = get_player(user_id)
    if "plants" not in player["quests"]:
        player["quests"]["plants"] = []

    player["quests"]["plants"].append({
        "emoji": emoji,
        "task": task,
        "deadline": deadline
    })
    save_player(user_id, player)

    bot.send_message(
        message.chat.id, 
        f"🌲Лісовик🌲: Ну добре, закопали твоє зерно <b>{emoji} {task}</b>! Тепер поливай його своєю працею до {deadline}!", 
        parse_mode="HTML", 
        reply_markup=get_greenhouse_menu()
    )
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
