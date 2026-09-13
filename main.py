# =========================================================
# РЕЄСТРАЦІЯ HANDLERS
# =========================================================

import handlers.profile
import handlers.main_quest  # Переконайся, що файл або модуль підключено
import handlers.backpack

import handlers.my_quests.menu

# ---------------------------------------------------------
# ВИКОНАННЯ СПРАВ
# ---------------------------------------------------------

import handlers.complete_activity
import handlers.complete_scroll
import handlers.complete_ritual
import handlers.complete_plant
import handlers.complete_unplanned

# ---------------------------------------------------------
# СУВОЇ
# ---------------------------------------------------------

import handlers.my_quests.scrolls.menu
import handlers.my_quests.scrolls.create
import handlers.my_quests.scrolls.delete

# ---------------------------------------------------------
# РИТУАЛИ
# ---------------------------------------------------------

import handlers.my_quests.rituals.menu
import handlers.my_quests.rituals.create
import handlers.my_quests.rituals.delete

# ---------------------------------------------------------
# ТЕПЛИЦЯ
# ---------------------------------------------------------

import handlers.my_quests.greenhouse.menu
import handlers.my_quests.greenhouse.create
import handlers.my_quests.greenhouse.delete
import handlers.my_quests.greenhouse.archive

# ---------------------------------------------------------
# ЕКСПЕДИЦІЇ
# ---------------------------------------------------------

import handlers.my_quests.expedition.menu
import handlers.my_quests.expedition.start
import handlers.my_quests.expedition.timer
import handlers.my_quests.expedition.complete

print("🎉 Усі основні обробники підключені!")
