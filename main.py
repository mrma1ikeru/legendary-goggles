import asyncio
import logging
import os

import aiohttp
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ==========================
# ИНИЦИАЛИЗАЦИЯ
# ==========================

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# ==========================
# ПЕРЕВОД НА РУССКИЙ
# ==========================

async def translate_to_russian(text):

    url = "https://translate.googleapis.com/translate_a/single"

    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "ru",
        "dt": "t",
        "q": text
    }

    async with aiohttp.ClientSession() as session:

        async with session.get(
            url,
            params=params
        ) as response:

            result = await response.json()

    translated = ""

    for item in result[0]:
        translated += item[0]

    return translated
# ==========================
# ХРАНЕНИЕ ДАННЫХ
# ==========================

user_languages = {}
user_favorites = {}


# ==========================
# ТЕКСТЫ
# ==========================

TEXTS = {
    "ru": {
        "choose_language": "🌍 Выберите язык:",
        "welcome": (
            "🍳 <b>Привет!</b>\n\n"
            "Я помогу найти рецепты из продуктов, которые есть у тебя в холодильнике.\n\n"
            "Напиши ингредиенты через запятую.\n\n"
            "Пример:\n"
            "<code>chicken, tomato, cheese</code>"
        ),
        "searching": "🔍 Ищу рецепты...",
        "nothing_found": "😔 Ничего не найдено.",
        "recipe": "🍽 <b>{}</b>\n\n<b>Инструкция:</b>\n{}",
        "favorites_empty": "⭐ У вас пока нет избранных рецептов.",
        "favorites_title": "⭐ <b>Избранные рецепты:</b>",
        "added_to_favorites": "✅ Рецепт добавлен в избранное!",
        "menu": "📋 Главное меню"
    },

    "en": {
        "choose_language": "🌍 Choose language:",
        "welcome": (
            "🍳 <b>Hello!</b>\n\n"
            "I will help you find recipes from ingredients in your fridge.\n\n"
            "Send ingredients separated by commas.\n\n"
            "Example:\n"
            "<code>chicken, tomato, cheese</code>"
        ),
        "searching": "🔍 Searching recipes...",
        "nothing_found": "😔 Nothing found.",
        "recipe": "🍽 <b>{}</b>\n\n<b>Instructions:</b>\n{}",
        "favorites_empty": "⭐ You don't have favorite recipes yet.",
        "favorites_title": "⭐ <b>Favorite recipes:</b>",
        "added_to_favorites": "✅ Recipe added to favorites!",
        "menu": "📋 Main menu"
    }
}


# ==========================
# КЛАВИАТУРЫ
# ==========================

language_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data="lang_ru"
            ),
            InlineKeyboardButton(
                text="🇬🇧 English",
                callback_data="lang_en"
            )
        ]
    ]
)


# Главное меню

def get_main_keyboard(lang: str):

    if lang == "ru":

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⭐ Избранное")],
                [KeyboardButton(text="🌍 Сменить язык")]
            ],
            resize_keyboard=True
        )

    else:

        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="⭐ Favorites")],
                [KeyboardButton(text="🌍 Change language")]
            ],
            resize_keyboard=True
        )

    return keyboard


# ==========================
# ПЕРЕВОД ТЕКСТА
# ==========================

async def translate_ingredients_to_english(text):

    url = "https://translate.googleapis.com/translate_a/single"

    params = {
        "client": "gtx",
        "sl": "ru",
        "tl": "en",
        "dt": "t",
        "q": text
    }

    async with aiohttp.ClientSession() as session:

        async with session.get(url, params=params) as response:

            result = await response.json()

    translated = ""

    for item in result[0]:
        translated += item[0]

    return translated


# ==========================
# СТАРТ
# ==========================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        TEXTS["ru"]["choose_language"],
        reply_markup=language_keyboard
    )


# ==========================
# ВЫБОР ЯЗЫКА
# ==========================

@dp.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):

    lang = callback.data.split("_")[1]

    user_languages[callback.from_user.id] = lang

    await callback.message.edit_text(
        TEXTS[lang]["welcome"]
    )

    await callback.message.answer(
        TEXTS[lang]["menu"],
        reply_markup=get_main_keyboard(lang)
    )

    await callback.answer()


# ==========================
# СМЕНА ЯЗЫКА
# ==========================

@dp.message(F.text.in_([
    "🌍 Сменить язык",
    "🌍 Change language"
]))
async def change_language(message: Message):

    await message.answer(
        "🌍 Language / Язык",
        reply_markup=language_keyboard
    )


# ==========================
# ИЗБРАННОЕ
# ==========================

@dp.message(F.text.in_([
    "⭐ Избранное",
    "⭐ Favorites"
]))
async def show_favorites(message: Message):

    user_id = message.from_user.id

    lang = user_languages.get(user_id, "ru")

    favorites = user_favorites.get(user_id, [])

    if not favorites:

        await message.answer(
            TEXTS[lang]["favorites_empty"]
        )

        return

    text = TEXTS[lang]["favorites_title"] + "\n\n"

    for recipe in favorites:
        text += f"• {recipe}\n"

    await message.answer(text)


# ==========================
# ПОИСК РЕЦЕПТОВ
# ==========================

@dp.message(F.text)
async def recipe_search(message: Message):

    user_id = message.from_user.id

    lang = user_languages.get(user_id, "ru")

    ingredients = message.text.strip()

    # Если выбран русский язык —
    # переводим ингредиенты в английский
    if lang == "ru":

        try:
            ingredients = await translate_ingredients_to_english(
                ingredients
            )

        except:
            await message.answer(
                "❌ Ошибка перевода ингредиентов."
            )
            return

    # Исключаем кнопки меню
    if ingredients in [
        "⭐ Избранное",
        "⭐ Favorites",
        "🌍 Сменить язык",
        "🌍 Change language"
    ]:
        return

    await message.answer(TEXTS[lang]["searching"])

    url = (
        "https://www.themealdb.com/api/json/v1/1/"
        f"filter.php?i={ingredients}"
    )

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as response:

            data = await response.json()

    meals = data.get("meals")

    if not meals:

        await message.answer(
            TEXTS[lang]["nothing_found"]
        )

        return

    meals = meals[:5]

    for meal in meals:

        meal_name = meal["strMeal"]
        meal_id = meal["idMeal"]
        meal_image = meal["strMealThumb"]

        detail_url = (
            "https://www.themealdb.com/api/json/v1/1/"
            f"lookup.php?i={meal_id}"
        )

        async with aiohttp.ClientSession() as session:

            async with session.get(detail_url) as response:

                detail_data = await response.json()

        recipe = detail_data["meals"][0]

        instructions = recipe["strInstructions"]

        # Перевод на русский
        if lang == "ru":

            try:
                instructions = await translate_to_russian(
                    instructions[:1500]
                )

                meal_name = await translate_to_russian(
                    meal_name
                )

            except:
                pass

        # Ограничение длины
        if len(instructions) > 1000:
            instructions = instructions[:1000] + "..."

        text = TEXTS[lang]["recipe"].format(
            meal_name,
            instructions
        )

        # Кнопка избранного
        favorite_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⭐ Save",
                        callback_data=f"fav_{meal_name}"
                    )
                ]
            ]
        )

        await message.answer_photo(
            photo=meal_image,
            caption=text,
            reply_markup=favorite_keyboard
        )


# ==========================
# ДОБАВЛЕНИЕ В ИЗБРАННОЕ
# ==========================

@dp.callback_query(F.data.startswith("fav_"))
async def add_to_favorites(callback: CallbackQuery):

    user_id = callback.from_user.id

    lang = user_languages.get(user_id, "ru")

    recipe_name = callback.data.replace("fav_", "")

    if user_id not in user_favorites:
        user_favorites[user_id] = []

    if recipe_name not in user_favorites[user_id]:
        user_favorites[user_id].append(recipe_name)

    await callback.answer(
        TEXTS[lang]["added_to_favorites"],
        show_alert=True
    )


# ==========================
# ЗАПУСК БОТА
# ==========================

async def main():

    print("Bot started!")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
