import logging
import asyncio
import os
import datetime
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

class Settings(BaseSettings):
    bot_token: str
    clc_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Инициализация настроек
settings = Settings()

# Настройка логирования (формат времени, уровень, модуль и строка)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(msecs)03d | %(levelname)-8s | %(name)s | %(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
logger.info("Starting bot...")

# Инициализация бота и диспетчера
bot = Bot(token=settings.bot_token)
dp = Dispatcher()

# Хранилище данных пользователя: текущее состояние и история
user_data = {}    # временное хранение для сборки одной ссылки (на пользователя)
user_history = {} # история последних коротких ссылок (на пользователя)

# Предопределённые списки UTM-меток (можно вынести в настройки/JSON при необходимости)
UTM_SOURCES = [
    ("ВКонтакте", "vk"),
    ("Max", "max"),
    ("Instagram", "inst"),
    ("TikTok", "tiktok"),
    ("Одноклассники", "ok"),
    ("YouTube", "youtube"),
    ("Telegram", "telegram"),
    ("Pinterest", "pinterest"),
    ("Горбилет блог", "gorbilet_blog"),
    ("Сайт Горбилет", "site_GB")
]
UTM_MEDIUMS_PUBLICATIONS = [
    ("Пост Горбилет", "post_GB"),
    ("Пост театр", "post_teatr"),
    ("Пост дети", "post_deti"),
    ("Пост Москва", "post_msk"),
    ("Клип Москва", "clip_msk"),
    ("Пост тимы", "post_timy"),
    ("Клип ТР", "clip_TR"),
    ("Пост ТР", "post_TR")
]

UTM_MEDIUMS_MAILINGS = [
    ("Рассылка Горбилет", "rassilka_GB"),
    ("Рассылка театр", "rassilka_teatr"),
    ("Рассылка дети", "rassilka_deti"),
    ("Рассылка Москва", "rassilka_msk"),
    ("Рассылка ТР", "rassilka_tr"),
    ("Рассылка блог", "blog_rassilka")
]

UTM_MEDIUMS_STORIES = [
    ("Сторис Горбилет", "stories_GB"),
    ("Сторис театр", "stories_teatr"),
    ("Сторис тимы", "stories_timy"),
    ("Сторис дети", "deti"),
    ("Сторис Москва", "stories_msk"),
    ("Сторис ТР", "stories_TR")
]

UTM_MEDIUMS_CHANNELS = [
    ("Канал Москва", "kanal_msk"),
    ("Канал Горбилет", "kanal_GB"),
    ("Канал ТР", "kanal_TR")
]
# --- UTM_CAMPAIGN списки по группам ---
UTM_CAMPAIGNS_SPB = [
    ("Спектакли СПБ", "spektakl_spb"),
    ("Карелия СПБ", "kareliya_spb"),
    ("Автотуры СПБ", "avtexcursion_spb"),
    ("Пешие экскурсии СПБ", "peshexcursion_spb"),
    ("Пригород СПБ", "prigorod_spb"),
    ("Корабли СПБ", "korabli_spb"),
    ("Места СПБ", "mesta_spb"),
    ("Аквапарки СПБ", "akvapark_spb"),
    ("Аренда СПБ", "arenda_spb"),
    ("Другое СПБ", "other_spb"),
    ("Блог СПБ", "blog_spb"),
    ("Туры СПБ", "tury_spb"),
]

UTM_CAMPAIGNS_MSK = [
    ("Спектакли МСК", "spektakl_msk"),
    ("Экскурсии МСК", "excursion_msk"),
    ("Корабли МСК", "korabli_msk"),
    ("Места МСК", "mesta_msk"),
    ("Другое МСК", "other_msk"),
    ("Блог МСК", "blog_msk"),
    ("Блог рассылка МСК", "blog_rassilka_msk"),
]

UTM_CAMPAIGNS_TR = [
    ("Stories GB", "stories_GB"),
    ("Stories Театр", "stories_teatr"),
    ("Дзен Турция", "dzen_TR"),
    ("Блог Турция", "blog_TR"),
    ("Блог контент Турция", "blog_content_TR"),
    ("Блог рассылка Турция", "blog_rassilka_TR"),
]

UTM_CAMPAIGNS_REGIONS = [
    ("Сочи", "sochi"),
    ("Казань", "kazan"),
    ("Калининград", "kaliningrad"),
    ("Нижний Новгород", "nn"),
    ("Анапа", "anapa"),
    ("Кисловодск", "kislovodsk"),
    ("Дагестан", "dagestan"),
    ("Осетия", "osetia"),
    ("Геленджик", "gelendghik"),
    ("Крым", "crimea"),
    ("Севастополь", "sevastopol"),
    ("Владикавказ", "vladikavkaz"),
    ("Ялта", "yalta"),
    ("Псков", "pskov"),
    ("Регионы", "regions"),
    ("Ярославль", "yar"),
    ("Кострома", "kostroma"),
    ("Суздаль", "suzdal"),
    ("Вологда", "vologda"),
    ("Рязань", "ryazan"),
    ("Краснодар", "krasnodar"),
    ("Петрозаводск", "petrozavodsk"),
    ("Ростов", "rostov"),
    ("Смоленск", "smolensk"),
    ("Выборг", "vuborg"),
    ("Великий Новгород", "veliky"),
]

UTM_CAMPAIGNS_FOREIGN = [
    ("Грузия", "georgia"),
    ("Абхазия", "abhazia"),
    ("Минск", "minsk"),
    ("Байкал", "baikal"),
    ("Мурманск", "murmansk"),
    ("Алматы", "almatu"),
    ("Новосибирск", "nsk"),
    ("Анталья", "antalya"),
    ("Тбилиси", "tbilisi"),
    ("Шарм-эль-Шейх", "sharmelsheikh"),
    ("Владивосток", "vladivostok"),
    ("Стамбул", "stambul"),
    ("Тула", "tula"),
    ("Коломна", "kolomna"),
    ("Баку", "baku"),
    ("Lead", "lead"),
]

# Обработчик команды /start – приветствие и запрос ссылки
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Отправьте мне ссылку, для которой нужно создать UTM-метки.")
    # (Опционально можно установить состояние FSM "ожидание ссылки")

# Обработчик текстового сообщения с ссылкой (если сообщение начинается с http:// или https://)
@dp.message(lambda msg: msg.text and (msg.text.startswith("http://") or msg.text.startswith("https://")))
async def handle_base_url(message: types.Message):
    user_id = message.from_user.id
    base_url = message.text.strip()
    # Сохранить базовую ссылку для пользователя
    user_data[user_id] = {"base_url": base_url}
    logger.info(f"Received base URL from user {user_id}: {base_url}")

    # Отправить инлайн-клавиатуру для выбора utm_source
    builder = InlineKeyboardBuilder()
    for name, val in UTM_SOURCES:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"src:{val}"))
    builder.adjust(3)  # по 3 кнопки в строке
    await message.answer("Выберите источник трафика (utm_source):", reply_markup=builder.as_markup())

# Обработчик выбора источника (utm_source)
@dp.callback_query(F.data.startswith("src:"))
async def select_source(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    source_val = callback.data.split(":", 1)[1]
    # Сохранить выбранный источник
    if user_id in user_data:
        user_data[user_id]["utm_source"] = source_val
    else:
        user_data[user_id] = {"utm_source": source_val}
    logger.info(f"User {user_id} selected utm_source: {source_val}")

    await callback.answer()  # подтверждаем получение колбэка (убираем "часики")
    # Обновляем предыдущее сообщение (убираем клавиатуру и фиксируем выбор, опционально)
    await callback.message.edit_text(f"Источник (utm_source) выбран: {source_val}")

    builder = InlineKeyboardBuilder()
    builder.button(text="📣 СММ (публикации)", callback_data="medgrp:publications")
    builder.button(text="📧 СММ (рассылка)", callback_data="medgrp:mailings")
    builder.button(text="📱 СММ IG (истории)", callback_data="medgrp:stories")
    builder.button(text="📡 СММ (каналы)", callback_data="medgrp:channels")
    builder.adjust(2)
    await callback.message.answer("Выберите группу utm_medium:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("medgrp:"))
async def select_medium_group(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    group_val = callback.data.split(":", 1)[1]
    builder = InlineKeyboardBuilder()
    group_map = {
        "publications": UTM_MEDIUMS_PUBLICATIONS,
        "mailings": UTM_MEDIUMS_MAILINGS,
        "stories": UTM_MEDIUMS_STORIES,
        "channels": UTM_MEDIUMS_CHANNELS,
    }
    for name, val in group_map[group_val]:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"med:{val}"))
    builder.add(InlineKeyboardButton(text="⬅ Назад", callback_data="back:medium"))
    builder.adjust(2)
    await callback.message.edit_text(f"Вы выбрали группу: {group_val}")
    await callback.message.answer("Теперь выберите конкретную utm_medium:", reply_markup=builder.as_markup())

# Обработчик выбора типа трафика (utm_medium)
@dp.callback_query(F.data.startswith("med:"))
async def select_medium(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    medium_val = callback.data.split(":", 1)[1]
    # Сохранить выбранный тип трафика
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["utm_medium"] = medium_val
    logger.info(f"User {user_id} selected utm_medium: {medium_val}")

    await callback.answer()
    await callback.message.edit_text(f"Тип трафика (utm_medium) выбран: {medium_val}")

    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Санкт-Петербург", callback_data="campgrp:spb")
    builder.button(text="🏙 Москва", callback_data="campgrp:msk")
    builder.button(text="✈️ Турция и зарубежье", callback_data="campgrp:tr")
    builder.button(text="🌍 Регионы России", callback_data="campgrp:regions")
    builder.button(text="🌐 Зарубежные направления", callback_data="campgrp:foreign")
    builder.adjust(2)
    await callback.message.answer("Выберите группу utm_campaign:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("campgrp:"))
async def select_campaign_group(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    group_val = callback.data.split(":", 1)[1]
    builder = InlineKeyboardBuilder()
    group_map = {
        "spb": UTM_CAMPAIGNS_SPB,
        "msk": UTM_CAMPAIGNS_MSK,
        "tr": UTM_CAMPAIGNS_TR,
        "regions": UTM_CAMPAIGNS_REGIONS,
        "foreign": UTM_CAMPAIGNS_FOREIGN,
    }
    for name, val in group_map[group_val]:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"camp:{val}"))
    builder.add(InlineKeyboardButton(text="⬅ Назад", callback_data="back:campaign"))
    builder.adjust(2)
    await callback.message.edit_text(f"Вы выбрали группу кампаний: {group_val}")
    await callback.message.answer("Теперь выберите конкретную кампанию (utm_campaign):", reply_markup=builder.as_markup())

# Обработчик выбора кампании (utm_campaign)
@dp.callback_query(F.data.startswith("camp:"))
async def select_campaign(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    campaign_val = callback.data.split(":", 1)[1]
    # Сохранить выбранную кампанию
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["utm_campaign"] = campaign_val
    logger.info(f"User {user_id} selected utm_campaign: {campaign_val}")

    await callback.answer()
    await callback.message.edit_text(f"Кампания (utm_campaign) выбрана: {campaign_val}")

    # После выбора кампании спрашиваем — добавить дату (сегодня) или ввести вручную
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Сегодня", callback_data="adddate:today")
    builder.button(text="✏️ Ввести дату", callback_data="adddate:manual")
    builder.button(text="❌ Не добавлять дату", callback_data="adddate:none")
    builder.adjust(2)
    await callback.message.answer("Добавить дату в ссылку? Выберите один из вариантов:", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("adddate:"))
async def add_date_choice(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    choice = callback.data.split(":", 1)[1]
    if user_id not in user_data:
        user_data[user_id] = {}
    if choice == "today":
        # Используем локальную дату (без времени)
        today = datetime.date.today().isoformat()
        user_data[user_id]["additional_path"] = today
        await callback.answer()
        await generate_short_link(target="with_path", user_id=user_id, callback=callback)
    elif choice == "none":
        # Не добавлять дату — очищаем поле и генерируем ссылку без даты
        user_data[user_id].pop("additional_path", None)
        user_data[user_id].pop("awaiting_date", None)
        await callback.answer()
        await generate_short_link(target="no_date", user_id=user_id, callback=callback)
    else:
        # Ждём ввода даты от пользователя
        user_data[user_id]["awaiting_date"] = True
        await callback.answer()
        await callback.message.answer("Введите дату в формате YYYY-MM-DD (например: 2025-10-10)")


@dp.message(lambda msg: user_data.get(msg.from_user.id, {}).get("awaiting_date"))
async def handle_manual_date(message: types.Message):
    user_id = message.from_user.id
    date_str = message.text.strip()
    try:
        parsed = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        await message.answer("Неверный формат даты. Пожалуйста, введите в формате YYYY-MM-DD, например: 2025-10-10")
        return
    # Сохраняем дату и убираем флаг ожидания
    user_data[user_id]["additional_path"] = parsed.isoformat()
    user_data[user_id]["awaiting_date"] = False
    await generate_short_link(target="with_path", user_id=user_id, message=message)


async def generate_short_link(target, user_id, message=None, callback=None):
    # Собираем базовый URL и UTM-метки
    base_url = user_data[user_id].get("base_url", "")
    utm_source = user_data[user_id].get("utm_source")
    utm_medium = user_data[user_id].get("utm_medium")
    utm_campaign = user_data[user_id].get("utm_campaign")
    additional_path = user_data[user_id].get("additional_path", "").strip()

    # Добавляем utm-параметры и, при наличии даты, прикрепляем её как utm_date в query
    # Сначала сформируем базовую ссылку с utm_source/utm_medium/utm_campaign
    base_with_utms = build_utm_url(base_url, utm_source, utm_medium, utm_campaign)
    full_url = base_with_utms
    if additional_path:
        # Добавляем utm_date в query параметрах
        parsed = urlparse(base_with_utms)
        q = dict(parse_qsl(parsed.query))
        q.update({"utm_date": additional_path})
        new_query = urlencode(q, doseq=True)
        full_url = urlunparse(parsed._replace(query=new_query))

    logger.info(f"Full UTM URL for user {user_id}: {full_url}")
    logger.info(f"Sending to CLC: {full_url}")
    logger.debug("CLC request payload: %s", {"url": full_url})

    results = []
    try:
        short_url = await shorten_url(full_url, settings.clc_api_key)
    except Exception as e:
        logger.exception(f"CLC shorten exception for user {user_id}: {e}")
        err_text = "❌ Ошибка при обращении к сервису сокращения. Попробуйте позже."
        if message:
            await message.answer(err_text)
        elif callback:
            await callback.message.answer(err_text)
        return

    if short_url is None:
        logger.error("CLC shorten returned None for user %s, url=%s", user_id, full_url)
        err_text = "❌ Не удалось сократить ссылку. Попробуйте позже."
        if message:
            await message.answer(err_text)
        elif callback:
            await callback.message.answer(err_text)
        return

    # Сохраняем в истории
    history_list = user_history.get(user_id, [])
    history_list.append((base_url, full_url, short_url))
    user_history[user_id] = history_list[-50:]

    results.append((full_url, short_url, None))

    # Формируем текст с результатами для пользователя
    lines = ["✅ Результаты генерации ссылок:", f"🔗 Исходная:\n{base_url}"]
    for full_u, short_u, err in results:
        if short_u:
            lines.append("\n🧩 С UTM:\n" + full_u)
            lines.append("✂️ Сокращённая:\n" + short_u)
        else:
            lines.append("\n🧩 С UTM (не сокращена):\n" + full_u)
            lines.append("⚠️ Проблема: " + (err or "Неизвестная ошибка"))

    result_text = "\n\n".join(lines)

    webapp_button = InlineKeyboardButton(
        text="Открыть API GorBilet",
        web_app=types.WebAppInfo(url="https://api.gorbilet.com/v2/admin/")
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[webapp_button]])

    if message:
        await message.answer(result_text, reply_markup=keyboard)
    elif callback:
        await callback.message.answer(result_text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("back:"))
async def go_back(callback: types.CallbackQuery):
    _, target = callback.data.split(":", 1)
    if target == "medium":
        builder = InlineKeyboardBuilder()
        builder.button(text="📣 СММ (публикации)", callback_data="medgrp:publications")
        builder.button(text="📧 СММ (рассылка)", callback_data="medgrp:mailings")
        builder.button(text="📱 СММ IG (истории)", callback_data="medgrp:stories")
        builder.button(text="📡 СММ (каналы)", callback_data="medgrp:channels")
        builder.adjust(2)
        await callback.message.edit_text("Выберите группу utm_medium:")
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

    elif target == "campaign":
        builder = InlineKeyboardBuilder()
        builder.button(text="📍 Санкт-Петербург", callback_data="campgrp:spb")
        builder.button(text="🏙 Москва", callback_data="campgrp:msk")
        builder.button(text="✈️ Турция и зарубежье", callback_data="campgrp:tr")
        builder.button(text="🌍 Регионы России", callback_data="campgrp:regions")
        builder.button(text="🌐 Зарубежные направления", callback_data="campgrp:foreign")
        builder.adjust(2)
        await callback.message.edit_text("Выберите группу utm_campaign:")
        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

# Обработчик команды /history – вывод последних 5 созданных ссылок
@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    hist = user_history.get(user_id)
    if not hist:
        await message.answer("История пуста. Вы ещё не создавали ссылки.")
        return
    text_lines = ["Последние собранные ссылки:"]
    for i, (orig, full, short) in enumerate(hist, start=1):
        text_lines.append(f"{i}. {short} — (исходная: {orig})")
    await message.answer("\n".join(text_lines))

# Импорт функций из сервисных модулей
from src.services.utm_builder import build_utm_url
from src.services.clc_shortener import shorten_url

# Запуск бота
async def main():
    logger.info("Bot is polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())