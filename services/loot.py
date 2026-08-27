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
    # 🌊 СТАВОК
    # =====================================================

    "rainbow_shell": {

        "name":
            "🐚 Райдужна мушля",

        "description":
            (
                "Мушля, внутрішня сторона якої "
                "переливається всіма кольорами "
                "ставкової води."
            ),

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


    "smooth_pond_stone": {

        "name":
            "🪨 Гладкий камінь зі ставкового дна",

        "description":
            (
                "Маленький гладкий камінь із візерунком, "
                "схожим на хвилі."
            ),

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 30,
                "night": 30,
            },
    },


    "silver_algae": {

        "name":
            "🌿 Срібляста водорість",

        "description":
            (
                "Тонка водорість, що ледь помітно "
                "мерехтить навіть без сонячного світла."
            ),

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 30,
                "night": 20,
            },
    },


    "water_feather": {

        "name":
            "🪶 Водяне перо",

        "description":
            (
                "Легке перо, яке чомусь не тоне у воді."
            ),

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 25,
                "night": 20,
            },
    },


    "pearl_shell": {

        "name":
            "🐚 Перламутрова мушля",

        "description":
            (
                "Рідкісна мушля з внутрішньою поверхнею "
                "кольору місячного світла."
            ),

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 10,
                "night": 12,
            },
    },


    "moon_algae": {

        "name":
            "🌿 Місячна водорість",

        "description":
            (
                "Водорість, яка набуває сріблястого "
                "сяйва після заходу сонця."
            ),

        "rarity":
            "rare",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 3,
                "night": 20,
                "full_moon": 35,
            },
    },


    "treasure_map_bottle": {

        "name":
            "🍾 Пляшка з мапою скарбів",

        "description":
            (
                "Стара пляшка, всередині якої лежить "
                "згорнутий фрагмент невідомої мапи."
            ),

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


    "frozen_moonlight": {

        "name":
            "💎 Крапля застиглого місячного світла",

        "description":
            (
                "Прозорий уламок, який холодний на дотик "
                "і світиться у темряві."
            ),

        "rarity":
            "very_rare",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 1,
                "night": 3,
                "full_moon": 12,
            },
    },


    "sunken_map_fragment": {

        "name":
            "🗺️ Фрагмент затонулої мапи",

        "description":
            (
                "Частина старої карти. На ній позначено "
                "місце, якого немає на жодній сучасній "
                "карті Грінвуду."
            ),

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


    # =====================================================
    # 🌲 ЛІС
    # =====================================================

    "strange_leaf": {

        "name":
            "🍂 Листок незвичайної форми",

        "description":
            (
                "Листок, краї якого утворюють майже "
                "ідеальний візерунок."
            ),

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


    "staff_like_branch": {

        "name":
            "🪵 Гілка, схожа на маленький посох",

        "description":
            (
                "Звичайна на вигляд гілка, яка "
                "підозріло добре лежить у руці."
            ),

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 25,
                "night": 20,
            },
    },


    "strange_acorn": {

        "name":
            "🌰 Дивний жолудь",

        "description":
            (
                "Жолудь із маленькою природною "
                "спіраллю на поверхні."
            ),

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


    "spotted_mushroom": {

        "name":
            "🍄 Гриб із фіолетовими цятками",

        "description":
            (
                "Невеликий гриб, який мурахи наполегливо "
                "рекомендують не куштувати."
            ),

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 25,
                "night": 20,
            },
    },


    "forest_feather": {

        "name":
            "🪶 Пір'їна лісового птаха",

        "description":
            (
                "Темна пір'їна з тонкою срібною смужкою."
            ),

        "rarity":
            "common",

        "pools":
            ["main"],

        "weights":
            {
                "day": 20,
                "night": 20,
            },
    },


    "old_staff_branch": {

        "name":
            "🪄 Гілка старого посоха",

        "description":
            (
                "У деревині видно сліди давньої магії."
            ),

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 10,
                "night": 12,
            },
    },


    "golden_leaf": {

        "name":
            "🍁 Золотий лист",

        "description":
            (
                "Листок, який не втрачає золотого кольору "
                "навіть після того, як його зірвали."
            ),

        "rarity":
            "rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 10,
                "night": 8,
            },
    },


    "blue_moss": {

        "name":
            "🌿 Мох із блакитним відблиском",

        "description":
            (
                "Мох, який світиться слабким блакитним "
                "світлом у темряві."
            ),

        "rarity":
            "rare",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 5,
                "night": 15,
            },
    },


    "rune_stone": {

        "name":
            "🪨 Камінь із руною",

        "description":
            (
                "Маленький камінь із символом, "
                "значення якого ще належить розгадати."
            ),

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


    "ancient_tree_bark": {

        "name":
            "🌳 Кора Старого Дерева",

        "description":
            (
                "Шматочок кори дерева, яке, за словами "
                "місцевих мешканців, пам'ятає більше за людей."
            ),

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


    "forgotten_staff_fragment": {

        "name":
            "🪄 Уламок забутого посоха",

        "description":
            (
                "Невеликий уламок старого магічного посоха. "
                "Здається, він усе ще зберігає частину сили."
            ),

        "rarity":
            "very_rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 2,
                "night": 3,
            },
    },


    "evergreen_leaf": {

        "name":
            "🍃 Листок, який не в'яне",

        "description":
            (
                "Листок, який залишається свіжим незалежно "
                "від того, скільки часу минуло."
            ),

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


    # =====================================================
    # 🌌 НЕБО ТА ЗОРІ
    # =====================================================

    "star_dust": {

        "name":
            "✨ Крихта зоряного пилу",

        "description":
            (
                "Маленька блискуча частинка, знайдена "
                "серед нічної трави."
            ),

        "rarity":
            "common",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 2,
                "night": 30,
            },
    },


    "night_feather": {

        "name":
            "🪶 Нічне перо",

        "description":
            (
                "Темне перо, на якому мерехтять "
                "маленькі цяточки, наче далекі зорі."
            ),

        "rarity":
            "common",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 1,
                "night": 30,
            },
    },


    "moon_fragment": {

        "name":
            "🌙 Срібний місячний уламок",

        "description":
            (
                "Маленький уламок невідомого походження, "
                "який відбиває місячне світло."
            ),

        "rarity":
            "common",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 2,
                "night": 30,
                "full_moon": 45,
            },
    },


    "sky_stone": {

        "name":
            "🔹 Небесний камінчик",

        "description":
            (
                "Незвичайний синюватий камінь, "
                "знайдений далеко від будь-яких гір."
            ),

        "rarity":
            "common",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 5,
                "night": 20,
            },
    },


    "comet_fragment": {

        "name":
            "☄️ Уламок комети",

        "description":
            (
                "Невеликий фрагмент небесного тіла, "
                "який пережив довгу подорож крізь темряву."
            ),

        "rarity":
            "rare",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 2,
                "night": 10,
            },
    },


    "star_dust_cluster": {

        "name":
            "✨ Згусток зоряного пилу",

        "description":
            (
                "Декілька крихт зоряного пилу, "
                "які незрозумілим чином тримаються разом."
            ),

        "rarity":
            "rare",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 1,
                "night": 10,
            },
    },


    "moonlight_box": {

        "name":
            "🌙 Скринька місячного світла",

        "description":
            (
                "Крихітна коробочка, всередині якої "
                "видно слабке срібне сяйво."
            ),

        "rarity":
            "rare",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 1,
                "night": 10,
                "full_moon": 20,
            },
    },


    "old_astronomers_lens": {

        "name":
            "🔭 Лінза старого астронома",

        "description":
            (
                "Стара лінза, крізь яку зорі здаються "
                "трохи ближчими."
            ),

        "rarity":
            "rare",

        "pools":
            ["main", "night"],

        "weights":
            {
                "day": 1,
                "night": 8,
            },
    },


    "comet_core_fragment": {

        "name":
            "☄️ Уламок кометного ядра",

        "description":
            (
                "Надзвичайно рідкісний уламок, "
                "що зберігає холод далекої "
                "космічної мандрівки."
            ),

        "rarity":
            "very_rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 3,
            },
    },


    "star_fragment": {

        "name":
            "🌟 Зоряний фрагмент",

        "description":
            (
                "Невелика частинка небесної матерії, "
                "яка випромінює м'яке світло."
            ),

        "rarity":
            "very_rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 3,
                "full_moon": 8,
            },
    },


    "piece_of_night_sky": {

        "name":
            "🌌 Крихта нічного неба",

        "description":
            (
                "Темний прозорий уламок, усередині якого "
                "видно крихітні зорі."
            ),

        "rarity":
            "very_rare",

        "pools":
            ["night"],

        "weights":
            {
                "night": 3,
                "full_moon": 10,
            },
    },


    # =====================================================
    # 🌕 ПОВНЯ
    # =====================================================

    "moon_tear": {

        "name":
            "💧 Сльоза повні",

        "description":
            (
                "Прозора крапля, яка не висихає "
                "і світиться холодним місячним сяйвом."
            ),

        "rarity":
            "rare",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon": 10,
            },
    },


    "lunar_crystal": {

        "name":
            "🔮 Місячний кристал",

        "description":
            (
                "Крихітний кристал, який з'являється "
                "лише під повним місяцем."
            ),

        "rarity":
            "very_rare",

        "pools":
            ["full_moon"],

        "weights":
            {
                "full_moon": 4,
            },
    },


    # =====================================================
    # ❄️ СПЕЦІАЛЬНІ ПРЕДМЕТИ
    # =====================================================

    "ice_amulet": {

        "name":
            "❄️ Крижаний амулет",

        "description":
            (
                "Невеликий амулет із прозорого льоду, "
                "який не тане навіть у теплих руках. "
                "Кажуть, він здатен зупинити хід "
                "невиконаного наказу на один день."
            ),

        "rarity":
            "very_rare",

        "pools":
            ["main"],

        "weights":
            {
                "day": 1,
                "night": 1,
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
