import random


print("🎁 Завантажуємо загальний каталог луту...")


# =========================================================
# НАЗВИ РІДКІСНОСТЕЙ
# =========================================================

RARITY_NAMES = {

    "common":
        "звичайний",

    "rare":
        "рідкісний",

    "very_rare":
        "дуже рідкісний",

    "legendary":
        "легендарний",
}


# =========================================================
# ЗАГАЛЬНИЙ КАТАЛОГ ЛУТУ
# =========================================================


LOOT_ITEMS = {

    # =====================================================
    # 🌊 ОСНОВНИЙ ПУЛ
    # =====================================================

    # -----------------------------------------------------
    # COMMON
    # -----------------------------------------------------

    "spotted_mushroom": {

        "name":
            "🍄 Гриб із фіолетовими цятками",

        "description":
            "",

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 20,
                "night": 10,
            },
    },


    "forest_bird_feather": {

        "name":
            "🪶 Пір'їна лісового птаха",

        "description":
            "",

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 20,
                "night": 10,
            },
    },


    "staff_like_branch": {

        "name":
            "🪵 Гілка, схожа на маленький посох",

        "description":
            "",

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 30,
                "night": 15,
            },
    },


    "rainbow_shell": {

        "name":
            "🐚 Райдужна мушля",

        "description":
            "Внутрішня повернхя переливається веселковими барвами",

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 30,
                "night": 15,
            },
    },


    "silver_algae": {

        "name":
            "🌿 Срібляста водорість",

        "description":
            "Таку рослину значно легше помітити вночі",

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 15,
                "night": 30,
            },
    },


    "pinch_of_star_dust": {

        "name":
            "✨ Дрібка зоряного пилу",

        "description":
            "",

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 5,
                "night": 12,
            },
    },


    "meteorite_like_stone": {

        "name":
            "☄️ Камінчик, схожий на уламок метеориту",

        "description":
            "",

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 15,
                "night": 15,
            },
    },


    # -----------------------------------------------------
    # RARE
    # -----------------------------------------------------

    "blue_glowing_moss": {

        "name":
            "🌿 Мох із блакитним відблиском",

        "description":
            "",

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 10,
                "night": 10,
            },
    },


    "old_astronomers_lens": {

        "name":
            "🔭 Лінза старого астронома",

        "description":
            "Крізь неї зорі здаються ближчими",

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 5,
                "night": 10,
            },
    },


    "sunken_map_fragment": {

        "name":
            "🗺️ Фрагмент затонулої мапи",

        "description":
            "Неможливо встановити, яку саме місцевість зображено на цьому фрагменті, але сумнівів немає: це частина старої мапи скарбів.",

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 10,
                "night": 7,
            },
    },


    "ancient_tree_bark": {

        "name":
            "🌳 Кора старого дерева",

        "description":
            "Здається, вона пам'ятає найдавніші часи",

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 10,
                "night": 10,
            },
    },

    # -----------------------------------------------------
    # VERY RARE
    # -----------------------------------------------------

    "staff_fragment": {

        "name":
            "🪄 Уламок посоха",

        "description":
            "При взятті артефакту до рук відчувається легке поколювання.",

        "rarity":
            "very_rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 3,
                "night": 3,
            },
    },


    "frozen_moonlight": {

        "name":
            "💎 Крапля застиглого місячного світла",

        "description":
            "",

        "rarity":
            "very_rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 1,
                "night": 4,
            },
    },


    "evergreen_leaf": {

        "name":
            "🍃 Листок, який не в'яне",

        "description":
            "",

        "rarity":
            "very_rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 4,
                "night": 3,
            },
    },


    # -----------------------------------------------------
    # LEGENDARY
    # -----------------------------------------------------

    "petrified_spark_of_life": {

        "name":
            "🌟 Скам'яніла іскра життя",

        "description":
            "Ходять легенди що саме з таких іскор зародився Грінвуд",

        "rarity":
            "legendary",

        "pools":
            ["main"],

        "weights":
            {
                "day": 0.1,
                "night": 0.1,
            },
    },


    "amber_bubble": {

        "name":
            "🟠 Бурштинова кулька",

        "description":
            "",

        "rarity":
            "legendary",

        "pools":
            ["main"],

        "weights":
            {
                "day": 0.3,
                "night": 0.3,
            },
    },


    "pearl_shell": {

        "name":
            "🐚 Мушля з перлиною",

        "description":
            "",

        "rarity":
            "legendary",

        "pools":
            ["main"],

        "weights":
            {
                "day": 1,
                "night": 1,
            },
    },


    # =====================================================
    # 🌌 НІЧНИЙ ПУЛ
    # =====================================================

    # -----------------------------------------------------
    # COMMON
    # -----------------------------------------------------

    "fragment_of_night_sky_scale": {

        "name":
            "🌌 Уламок лусочки нічного неба",

        "description":
            "Якщо уважно пригледітись, то в темному уламку ведніється мерехтіння. ",

        "rarity":
            "common",

        "pools":
            ["night"],

        "weights":
            {
                "night": 30,
            },
    },


    "night_bird_feather": {

        "name":
            "🪶 Перо нічного птаха",

        "description":
            "",

        "rarity":
            "common",

        "pools":
            ["night"],

        "weights":
            {
                "night": 25,
            },
    },


    "withered_moon_petal": {

        "name":
            "🌙 Зів'яла місячна пелюстка",

        "description":
            "Пелюстка випромінює срібне світло з настанням сутінок, що згасає з першим промінням світанку",

        "rarity":
            "common",

        "pools":
            ["night"],

        "weights":
            {
                "night": 21,
            },
    },


    # -----------------------------------------------------
    # RARE
    # -----------------------------------------------------

    "night_spark": {

        "name":
            "✨ Нічний блищик",

        "description":
            "Лелітка загублена чарівником-мандрівником.",

        "rarity":
            "rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 20,
            },
    },


    "night_butterfly_wing": {

        "name":
            "🦋 Крило нічного метелика",

        "description":
            "",

        "rarity":
            "rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 15,
            },
    },


    # -----------------------------------------------------
    # VERY RARE
    # -----------------------------------------------------

    "comet_tail_particle": {

        "name":
            "☄️ Частинка хвоста комети",

        "description":
            "Хтось намагався впіймати комету за її хвіст.",

        "rarity":
            "very_rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 5,
            },
    },


    "old_astronomers_blueprint": {

        "name":
            "📃 Креслення старого астронома",

        "description":
            "",

        "rarity":
            "very_rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 2,
            },
    },


    "star_fragment": {

        "name":
            "🌟 Зоряний фрагмент",

        "description":
            "Частинка небесної матерії, що випромінює м'яке світло.",

        "rarity":
            "very_rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 4,
            },
    },


    # =====================================================
    # 🌕 ПОВНЯ
    # =====================================================

    # -----------------------------------------------------
    # RARE
    # -----------------------------------------------------

    "moon_tear": {

        "name":
            "💧 Сльоза повні",

        "description":
            "Чия сльоза залишилася серед нічної тиші? І що стало причиною плачу? ",

        "rarity":
            "rare",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon": 25,
            },
    },


    "moon_bloom_flower": {

        "name":
            "🌸 Квітка місячного цвіту",

        "description":
            "Не в'януча кітка, що розкривається лише під повним місяцем",

        "rarity":
            "rare",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon": 25,
            },
    },


    # -----------------------------------------------------
    # VERY RARE
    # -----------------------------------------------------

    "lunar_crystal": {

        "name":
            "🔮 Місячний кристал",

        "description":
            "Крихітний кристал, який народжується під повним місяцем.",

        "rarity":
            "very_rare",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon": 10,
            },
    },


    "petrified_star_shadow": {

        "name":
            "🌌 Скам'яніла зоряна тінь",

        "description":
            "",

        "rarity":
            "very_rare",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon":2,
            },
    },


    # -----------------------------------------------------
    # LEGENDARY
    # -----------------------------------------------------

    "heart_of_full_moon": {

        "name":
            "🌕 Серце повні",

        "description":
            "Надзвичайно рідкісний уламок чистого місячного світла.",

        "rarity":
            "legendary",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon": 0.1,
            },
    },


    "letter_from_moon_to_sun": {

        "name":
            "💌 Лист від Місяця Сонцю",

        "description":
            "Таємничий лист, написаний срібним місячним світлом. По центру розташовується синя печатка.",

        "rarity":
            "legendary",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon": 0.1,
            },
    },


    # =====================================================
    # ❄️ СПЕЦІАЛЬНІ ПРЕДМЕТИ
    # =====================================================

    "ice_amulet": {

        "name":
            "❄️ Крижаний амулет",

        "description":
            "Одноразовий амулет, що береже свого власника від найближчого випадкового стягнення балів за невиконаний сувій або ритуал. Не потребує активації.",

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 7,
                "night": 7,
            },
    },

}


# =========================================================
# ПУЛИ
# =========================================================

LOOT_POOLS = {

    "main":
        "Основний пул",

    "night":
        "Нічний пул",

    "full_moon":
        "Пул повні",

    "chapter_1":
        "Пул першої глави",

    "chapter_2":
        "Пул другої глави",

    "chapter_3":
        "Пул третьої глави",

    "special":
        "Особливий пул",

    "main_quest":
        "Пул основного квесту",
}


# =========================================================
# ОТРИМАТИ ПРЕДМЕТ
# =========================================================

def get_loot_item(item_id):

    return LOOT_ITEMS.get(
        item_id
    )


# =========================================================
# ОТРИМАТИ НАЗВУ
# =========================================================

def get_item_name(item_id):

    item = get_loot_item(
        item_id
    )

    if not item:

        return None

    return item.get(
        "name"
    )


# =========================================================
# ОТРИМАТИ АКТИВНІ ПУЛИ
# =========================================================
#
# conditions очікується від services.conditions.
#
# Підтримуються:
# night
# full_moon
# main_quest_active
# chapter
# special
#
# =========================================================

def get_available_pools(
    conditions=None
):

    conditions = (
        conditions
        or {}
    )

    pools = [
        "main"
    ]

    # -----------------------------------------------------
    # НІЧ
    # -----------------------------------------------------

    if conditions.get(
        "night"
    ):

        pools.append(
            "night"
        )

    # -----------------------------------------------------
    # ПОВНЯ
    # -----------------------------------------------------

    if conditions.get(
        "full_moon"
    ):

        pools.append(
            "full_moon"
        )

    # -----------------------------------------------------
    # ОСНОВНИЙ КВЕСТ
    # -----------------------------------------------------

    if conditions.get(
        "main_quest_active"
    ):

        pools.append(
            "main_quest"
        )

    # -----------------------------------------------------
    # ГЛАВА
    # -----------------------------------------------------

    chapter = conditions.get(
        "chapter"
    )

    if chapter:

        chapter_pool = (
            f"chapter_{chapter}"
        )

        if chapter_pool in LOOT_POOLS:

            pools.append(
                chapter_pool
            )

    # -----------------------------------------------------
    # ОСОБЛИВИЙ ПУЛ
    # -----------------------------------------------------

    if conditions.get(
        "special"
    ):

        pools.append(
            "special"
        )

    return list(
        dict.fromkeys(
            pools
        )
    )


# =========================================================
# ПЕРЕВІРКА ДОСТУПНОСТІ ПРЕДМЕТА
# =========================================================

def is_item_available(
    item,
    conditions=None
):

    if not item:

        return False

    conditions = (
        conditions
        or {}
    )

    item_pools = (
        item.get(
            "pools",
            []
        )
        or []
    )

    if not item_pools:

        return False

    available_pools = (
        get_available_pools(
            conditions
        )
    )

    # -----------------------------------------------------
    # ПРЕДМЕТ ПОВИНЕН НАЛЕЖАТИ
    # ХОЧА Б ДО ОДНОГО АКТИВНОГО ПУЛУ
    # -----------------------------------------------------

    if not any(
        pool in available_pools
        for pool in item_pools
    ):

        return False

    # -----------------------------------------------------
    # ПОВНЯ
    # -----------------------------------------------------


    if (
        "full_moon" in item_pools
        and "main" not in item_pools
        and "night" not in item_pools
    ):

        if not conditions.get(
            "full_moon"
        ):

            return False

    # -----------------------------------------------------
    # НІЧ
    # -----------------------------------------------------
    

    if (
        "night" in item_pools
        and "main" not in item_pools
        and not conditions.get("night")
        and not conditions.get("full_moon")
    ):

        return False

    # -----------------------------------------------------
    # ПУЛ ГЛАВИ
    # -----------------------------------------------------
    #
    # Якщо предмет належить тільки chapter_X,
    # потрібна саме ця активна глава.
    #
    # -----------------------------------------------------

    chapter_pools = [
        pool
        for pool in item_pools
        if str(pool).startswith(
            "chapter_"
        )
    ]

    if chapter_pools:

        chapter = conditions.get(
            "chapter"
        )

        current_chapter_pool = (
            f"chapter_{chapter}"
            if chapter
            else None
        )

        if current_chapter_pool not in chapter_pools:

            # Якщо предмет одночасно належить
            # іншому активному пулу, він все ще може
            # бути доступним.

            other_active_pool = any(
                pool in available_pools
                for pool in item_pools
                if pool not in chapter_pools
            )

            if not other_active_pool:

                return False

    # -----------------------------------------------------
    # ОСНОВНИЙ КВЕСТ
    # -----------------------------------------------------
    #
    # Якщо предмет має ТІЛЬКИ main_quest,
    # потрібен активний основний квест.
    #
    # -----------------------------------------------------

    if (
        "main_quest" in item_pools
        and len(item_pools) == 1
    ):

        if not conditions.get(
            "main_quest_active"
        ):

            return False

    return True


# =========================================================
# ОТРИМАТИ ВАГУ ПРЕДМЕТА
# =========================================================

def get_item_weight(
    item,
    conditions=None
):

    if not item:

        return 0.0

    conditions = (
        conditions
        or {}
    )

    weights = (
        item.get(
            "weights",
            {}
        )
        or {}
    )

    # -----------------------------------------------------
    # ПОВНЯ
    # -----------------------------------------------------

    if conditions.get(
        "full_moon"
    ):

        if "full_moon" in weights:

            return float(
                weights[
                    "full_moon"
                ]
            )

    # -----------------------------------------------------
    # НІЧ
    # -----------------------------------------------------

    if conditions.get(
        "night"
    ):

        if "night" in weights:

            return float(
                weights[
                    "night"
                ]
            )

    # -----------------------------------------------------
    # ДЕНЬ
    # -----------------------------------------------------

    if "day" in weights:

        return float(
            weights[
                "day"
            ]
        )

    return 0.0


# =========================================================
# ОТРИМАТИ ДОСТУПНІ ПРЕДМЕТИ
# =========================================================

def get_available_items(
    conditions=None
):

    conditions = (
        conditions
        or {}
    )

    result = []

    for item_id, item in (
        LOOT_ITEMS.items()
    ):

        if not is_item_available(
            item,
            conditions
        ):

            continue

        weight = get_item_weight(
            item,
            conditions
        )

        if weight <= 0:

            continue

        result.append(
            (
                item_id,
                weight
            )
        )

    return result


# =========================================================
# 🎲 ROLL КОНКРЕТНОГО ПРЕДМЕТА
# =========================================================

# =========================================================

def roll_loot(
    conditions=None
):

    candidates = (
        get_available_items(
            conditions
        )
    )

    if not candidates:

        return None

    item_ids = [
        item_id
        for item_id, weight
        in candidates
    ]

    weights = [
        weight
        for item_id, weight
        in candidates
    ]

    return random.choices(
        item_ids,
        weights=weights,
        k=1
    )[0]


# =========================================================
# 🎲 КІЛЬКА ROLL ПРЕДМЕТІВ
# =========================================================


def roll_loot_many(
    amount,
    conditions=None
):

    try:

        amount = int(
            amount
        )

    except (
        TypeError,
        ValueError
    ):

        return []

    if amount <= 0:

        return []

    results = []

    for _ in range(
        amount
    ):

        item_id = roll_loot(
            conditions
        )

        if item_id:

            results.append(
                item_id
            )

    return results


# =========================================================
# ПЕРЕТВОРИТИ ID → НАЗВИ
# =========================================================

def loot_names(
    item_ids
):

    result = []

    for item_id in (
        item_ids
        or []
    ):

        name = get_item_name(
            item_id
        )

        if name:

            result.append(
                name
            )

    return result


# =========================================================
# ОБ'ЄДНАННЯ ОДНАКОВОГО ЛУТУ
# =========================================================

def group_loot(
    item_ids
):

    grouped = {}

    for item_id in (
        item_ids
        or []
    ):

        item = get_loot_item(
            item_id
        )

        if not item:

            continue

        name = item.get(
            "name"
        )

        if not name:

            continue

        if name not in grouped:

            grouped[name] = {

                "item_id":
                    item_id,

                "name":
                    name,

                "quantity":
                    0,
            }

        grouped[name][
            "quantity"
        ] += 1

    return list(
        grouped.values()
    )


# =========================================================
# ДОДАТИ ЛУТ ДО ІНВЕНТАРЮ
# =========================================================
#
# ПІДТРИМУЄ:
#
# старий:
# "🌿 Срібляста водорість"
#
# новий:
# "🌿 Срібляста водорість × 3"
#
# Якщо предмет уже є:
#
# × 3 + × 1
#
# стане:
#
# × 4
#
# =========================================================

def add_loot_to_inventory(
    inventory,
    item_ids
):

    if not isinstance(
        inventory,
        list
    ):

        inventory = []

    if not item_ids:

        return inventory

    # -----------------------------------------------------
    # НОВИЙ ЛУТ
    # -----------------------------------------------------

    new_counts = {}

    for item_id in item_ids:

        name = get_item_name(
            item_id
        )

        if not name:

            continue

        new_counts[name] = (
            new_counts.get(
                name,
                0
            )
            + 1
        )

    if not new_counts:

        return inventory

    # -----------------------------------------------------
    # НОРМАЛІЗУЄМО СТАРИЙ ІНВЕНТАР
    # -----------------------------------------------------

    counts = {}

    for raw_item in inventory:

        if not raw_item:

            continue

        raw_item = str(
            raw_item
        )

        # -------------------------------------------------
        # НОВИЙ ФОРМАТ:
        #
        # "🌿 Срібляста водорість × 3"
        # -------------------------------------------------

        if " × " in raw_item:

            name, quantity = (
                raw_item.rsplit(
                    " × ",
                    1
                )
            )

            try:

                quantity = int(
                    quantity
                )

            except (
                TypeError,
                ValueError
            ):

                quantity = 1

        else:

            # -------------------------------------------------
            # СТАРИЙ ФОРМАТ:
            #
            # "🌿 Срібляста водорість"
            # -------------------------------------------------

            name = raw_item

            quantity = 1

        name = name.strip()

        if not name:

            continue

        counts[name] = (
            counts.get(
                name,
                0
            )
            + quantity
        )

    # -----------------------------------------------------
    # ДОДАЄМО НОВИЙ ЛУТ
    # -----------------------------------------------------

    for name, quantity in (
        new_counts.items()
    ):

        counts[name] = (
            counts.get(
                name,
                0
            )
            + quantity
        )

    # -----------------------------------------------------
    # ФОРМУЄМО ІНВЕНТАР
    # -----------------------------------------------------

    result = []

    for name, quantity in (
        counts.items()
    ):

        if quantity <= 0:

            continue

        result.append(
            f"{name} × {quantity}"
        )

    return result


# =========================================================
# ПОВНИЙ ЦИКЛ:
# КІЛЬКІСТЬ → ROLL ПРЕДМЕТІВ → ІНВЕНТАР
# =========================================================
#
# ВАЖЛИВО:
#
# amount сюди передає complete_*.
#
# Наприклад:
#
# generate_loot(
#     amount=2,
#     conditions=conditions,
#     inventory=player["inventory"]
# )
#
# зробить:
#
# 🎲 roll предмет №1
# 🎲 roll предмет №2
#
# =========================================================

def generate_loot(
    amount=1,
    conditions=None,
    inventory=None
):

    item_ids = roll_loot_many(
        amount,
        conditions
    )

    updated_inventory = (
        add_loot_to_inventory(
            inventory or [],
            item_ids
        )
    )

    grouped = group_loot(
        item_ids
    )

    return {

        "items":
            item_ids,

        "loot":
            grouped,

        "inventory":
            updated_inventory,
    }


# =========================================================
# ФОРМУВАННЯ ТЕКСТУ ЛУТУ
# =========================================================

def format_loot_text(
    grouped_loot
):

    if not grouped_loot:

        return ""

    lines = []

    for item in grouped_loot:

        name = item.get(
            "name"
        )

        quantity = int(
            item.get(
                "quantity",
                1
            )
        )

        if quantity > 1:

            lines.append(
                f"• {name} × {quantity}"
            )

        else:

            lines.append(
                f"• {name}"
            )

    return (
        "\n <b>Знайдено:</b>\n"
        + "\n".join(
            lines
        )
    )


# =========================================================
# ІНФОРМАЦІЯ ПРО ПРЕДМЕТ
# =========================================================

def get_item_info(
    item_id
):

    item = get_loot_item(
        item_id
    )

    if not item:

        return None

    rarity = item.get(
        "rarity",
        "common"
    )

    return {

        "id":
            item_id,

        "name":
            item.get(
                "name"
            ),

        "description":
            item.get(
                "description",
                ""
            ),

        "rarity":
            rarity,

        "rarity_name":
            RARITY_NAMES.get(
                rarity,
                "звичайний"
            ),

        "pools":
            item.get(
                "pools",
                []
            ),

        "weights":
            item.get(
                "weights",
                {}
            ),
    }
