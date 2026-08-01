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
        
    # Очищаємо вхідний текст від кольорів шкіри емодзі
    cleaned_text = clean_skin_tones(text)
    # Тепер магічний вираз дозволяє пробіли всередині переліку днів тижня!
    match = re.match(r"^([^\w\s]+)\s+(\d+)\s+([а-я,\sієґу]+)\s+(.+)$", cleaned_text, re.IGNORECASE)
    
    if not match:
        msg = bot.send_message(
            message.chat.id, 
            "✨ <b>🪷Лілі Понд🪷</b>: Ой, щось пішло не так із чорнилом. Спробуй ще раз за моїм шаблоном або напиши `🔙 Назад до квестів`, щоб скасувати: \n`[Емодзі] [Кратність] [Бали] [Дедлайн ДД.ММ] [Опис]`",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_scroll)
        return
        
    emoji, max_count, xp_per_once, deadline, task_desc = match.groups()
    max_count = int(max_count)
    xp_per_once = int(xp_per_once)
    task_desc = task_desc.strip()
    
    if xp_per_once < 4 or xp_per_once > 14:
        msg = bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: Пам'ятай, що магічний ліміт балів за одне виконання має бути від 4 до 14! Спробуй ще раз ввести умови:")
        bot.register_next_step_handler(msg, process_create_scroll)
        return

    player = get_player(user_id)
    
    scrolls = player["quests"].get("scrolls", [])
    if any(clean_skin_tones(s["task"]).lower() == task_desc.lower() and s["done_count"] < s["max_count"] for s in scrolls):
        msg = bot.send_message(message.chat.id, f"<b>🪷Лілі Понд🪷</b>:  У твоїх хроніках уже є активний сувой з назвою \"{task_desc}\". Придумай іншу назву або заверши попередній квест ")
        bot.register_next_step_handler(msg, process_create_scroll)
        return

    new_scroll = {
        "emoji": emoji,
        "max_count": max_count,
        "done_count": 0,
        "xp_per_once": float(xp_per_once),
        "deadline": deadline,
        "task": task_desc
    }
    
    player["quests"]["scrolls"].append(new_scroll)
    update_player(user_id, player)
    
    bot.send_message(
        message.chat.id, 
        f"<b>🪷Лілі Понд🪷</b>: Новий сувой успішно запечатано у твою книгу квестів. Я нагадуватиму тобі про нього!\n\n{emoji} {task_desc}\n• Повторень: {max_count}\n• Сила кроку: {xp_per_once} XP\n• Термін: до {deadline}",
        parse_mode="HTML",
        reply_markup=get_scrolls_menu()
    )

def process_complete_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Повертаємось.", reply_markup=get_scrolls_menu())
        return
        
    task_clean = clean_skin_tones(text.strip())
    player = get_player(user_id)
    scrolls = player["quests"].get("scrolls", [])
    
    found_scroll = None
    for s in scrolls:
        if clean_skin_tones(s["task"]).strip().lower() == task_clean.lower() and s["done_count"] < s["max_count"]:
            found_scroll = s
            break
            
    if not found_scroll:
        bot.send_message(message.chat.id, "✨ <b>🪷Лілі Понд🪷</b>: Я не знайшла такого активного сувою у твоїх записах. Спробуй обрати з кнопок на клавіатурі!", reply_markup=get_scrolls_menu())
        return
        
    found_scroll["done_count"] += 1
    xp_to_add = found_scroll["xp_per_once"]
    
    sphere_key = None
    scroll_emoji = clean_skin_tones(found_scroll["emoji"])
    for key, sphere in player["spheres"].items():
        if clean_skin_tones(sphere["emoji"]) == scroll_emoji:
            sphere_key = key
            break
            
    lvl_up_text = ""
    if sphere_key:
        sphere = player["spheres"][sphere_key]
        sphere["xp"] = float(sphere["xp"]) + xp_to_add
        player["xp_total"] = float(player["xp_total"]) + xp_to_add
        
        while sphere["xp"] >= float(sphere["max_xp"]):
            sphere["xp"] -= float(sphere["max_xp"])
            sphere["lvl"] += 1
            sphere["max_xp"] += 5.0
            lvl_up_text += f"\n⚡️ <b>РІВЕНЬ📈</b>: Сфера {sphere['name']} піднялася до {sphere['lvl']} рівня! 🎉"
            
        new_global_lvl = int(float(player["xp_total"]) // 50) + 1
        if new_global_lvl > int(player["level"]):
            player["level"] = new_global_lvl
            lvl_up_text += f"\n🌟 <b>НОВИЙ РІВЕНЬ ГЕРОЯ!</b>: Твій рівень зріс до {new_global_lvl}! 🧙‍♂️"
            
    report = f"✨ <b>🪷Лілі Понд🪷</b>: Чудовий крок! Записую прогрес у твій сувой! \n\n{found_scroll['emoji']} {found_scroll['task']} ({found_scroll['done_count']}/{found_scroll['max_count']})\n🔋 Отримано: <b>+{xp_to_add:.1f} XP </b>!"
    
    if found_scroll["done_count"] == found_scroll["max_count"]:
        report += f"\n\n🎉 <b>СУВОЙ ПОВНІСТЮ ЗАВЕРШЕНО!</b>\n <b>🪷Лілі Понд🪷</b>:  Чудова робота! "
        
    if lvl_up_text:
        report += "\n\n────────────────────" + lvl_up_text
        
    update_player(user_id, player)
    bot.send_message(message.chat.id, report, parse_mode="HTML", reply_markup=get_scrolls_menu())

def process_delete_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Повертаємось.", reply_markup=get_scrolls_menu())
        return
        
    task_clean = clean_skin_tones(text.strip())
    player = get_player(user_id)
    scrolls = player["quests"].get("scrolls", [])
    
    new_scrolls = [s for s in scrolls if not (clean_skin_tones(s["task"]).strip().lower() == task_clean.lower() and s["done_count"] < s["max_count"])]
    
    if len(scrolls) == len(new_scrolls):
        bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>:  Хм, такого сувою немає на твоєму столі. Спробуй обрати з кнопок! ", reply_markup=get_scrolls_menu())
        return
        
    player["quests"]["scrolls"] = new_scrolls
    update_player(user_id, player)
    
    bot.send_message(message.chat.id, "🔥 Сувой безслідно згорів у синьому полум'ї. Цього завдання більше не існує.", reply_markup=get_scrolls_menu())
def process_create_ritual(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text in ["🔙 Назад до квестів", "🔙 Назад"]:
        bot.send_message(message.chat.id, "Повертаємось до свитку ритуалів.", reply_markup=get_rituals_menu())
        return
        
    cleaned_text = clean_skin_tones(text)
    
    # Розбиваємо рядок по пробілах
    parts = cleaned_text.split()
    
    # Нам потрібно мінімум 4 частини: [Емодзі] [Бали] [Дні...] [Назва...]
    if len(parts) < 4:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Ой, не вистачає деталей. Перевір формат і спробуй ще раз за шаблоном:\n<code>[Емодзі] [Бали] [Дні] [Назва]</code>»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    emoji = parts[0]
    
    # Перевіряємо бали
    try:
        xp = int(parts[1])
    except ValueError:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Другим параметром мають бути цифри (бали від 4 до 14). Спробуй ще раз:»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    if xp < 4 or xp > 14:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: Сила ритуалу має бути в межах від 4 до 14! Спробуй ще раз:", 
            parse_mode="HTML"
        ) 
        bot.register_next_step_handler(msg, process_create_ritual)
        return

    # Збираємо все, що йде ПІСЛЯ балів
    remaining_text = " ".join(parts[2:])
    valid_days = ["пн", "вт", "ср", "чт", "пт", "сб", "нд"]
    
    if remaining_text.lower().startswith("щодня"):
        final_days = valid_days
        task_desc = remaining_text[5:].strip()
    else:
        # Надійна розбірка днів (підтримує "пн,ср,пт", "пн, ср, пт", "пн ср пт")
        days_accumulated = []
        words = remaining_text.split()
        idx = 0
        
        for word in words:
            # Розбиваємо кожне слово по комах, якщо вони зклеєні (наприклад "пн,ср,пт")
            sub_tokens = [t.strip().lower() for t in word.split(",") if t.strip()]
            
            # Перевіряємо, чи всі елементи у слові є валідними днями
            if sub_tokens and all(t in valid_days for t in sub_tokens):
                for t in sub_tokens:
                    if t not in days_accumulated:
                        days_accumulated.append(t)
                idx += 1
            else:
                break # Зустріли назву справи!

        if not days_accumulated:
            msg = bot.send_message(
                message.chat.id, 
                "<b>🪷Лілі Понд🪷</b>: «Я не змогла розпізнати дні тижня (пн, вт...). Спробуй знову:»",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, process_create_ritual)
            return
            
        final_days = days_accumulated
        task_desc = " ".join(words[idx:]).strip()

    if not task_desc:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «А де ж сама назва ритуалу? Напиши умови ще раз, будь ласка:»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return

    player = get_player(user_id)
    rituals = player["quests"].get("rituals", [])
    
    if any(clean_skin_tones(r["task"]).lower() == task_desc.lower() for r in rituals):
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «У твоїй книзі вже є ритуал з такою назвою. Дай йому трохи інше ім'я:»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    new_ritual = {
        "emoji": emoji,
        "xp": float(xp),
        "days": final_days,
        "task": task_desc,
        "done_today": False
    }
    
    player["quests"]["rituals"].append(new_ritual)
    update_player(user_id, player)
    
    bot.send_message(
        message.chat.id,
        f"✅ <b>Новий щоденний ритуал закарбовано!</b>\n\n"
        f"{emoji} <b>{task_desc}</b>\n"
        f"• Нагорода: +{xp} XP\n"
        f"• Дні виконання: {', '.join(final_days)}",
        parse_mode="HTML",
        reply_markup=get_rituals_menu()
    )
def process_complete_ritual(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    # 1. Якщо гравець натиснув кнопку скасування
    if text in ["🔙 Назад до квестів", "🔙 Назад", "/start"]:
        bot.send_message(message.chat.id, "Повертаємось до свитку ритуалів.", reply_markup=get_rituals_menu())
        return

    player = get_player(user_id)
    rituals = player["quests"].get("rituals", [])
    
    clean_input = clean_skin_tones(text).lower()
    
    # 2. Пошук ритуалу за назвою
    found = None
    for r in rituals:
        task_name = clean_skin_tones(r.get("task", "")).lower()
        if task_name == clean_input:
            found = r
            break
    
    # Якщо назва трохи відрізняється — шукаємо за входженням
    if not found:
        for r in rituals:
            task_name = clean_skin_tones(r.get("task", "")).lower()
            if task_name in clean_input or clean_input in task_name:
                found = r
                break
        
    if not found:
        bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Хм, я не знайшла ритуалу з такою назвою у твоєму списку. Обирай із запропонованих кнопок нижче!»", 
            reply_markup=get_rituals_menu(),
            parse_mode="HTML"
        )
        return
        
    if found.get("done_today", False):
        bot.send_message(
            message.chat.id, 
            f"<b>🪷Лілі Понд🪷</b>: «Ритуал <b>{found['task']}</b> вже закарбований як виконаний на сьогодні!»", 
            reply_markup=get_rituals_menu(),
            parse_mode="HTML"
        )
        return
        
    # 3. Зараховуємо виконання
    found["done_today"] = True
    earned_xp = float(found.get("xp", 5.0))
    player["xp_total"] += earned_xp
    
    # Нараховуємо XP у відповідні сфери
    ritual_emoji = found.get("emoji", "")
    for char in ritual_emoji:
        if char in player.get("spheres", {}):
            player["spheres"][char] += earned_xp
            
    update_player(user_id, player)
    
    # 👇 ОЦІ РЯДКИ ТЕПЕР МЕДИЧНО ТОЧНО ВСЕРЕДИНІ ФУНКЦІЇ (МАЮТЬ ВІДСТУП)
    bot.send_message(
        message.chat.id, 
        f"✅ <b>Ритуал виконано!</b>\n\n"
        f"{ritual_emoji} <b>{found['task']}</b> успішно завершено!\n"
        f"✨ Тобі зараховано <b>+{earned_xp} XP</b> у загальний досвід!", 
        reply_markup=get_rituals_menu(),
        parse_mode="HTML"
    )

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
