import logging
import asyncio
import os

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
    ("Instagram", "instagram"),
    ("TikTok", "tiktok"),
    ("Одноклассники", "ok"),
    ("YouTube", "youtube"),
    ("Telegram", "telegram"),
    ("Pinterest", "pinterest"),
    ("Горбилет блог", "gorbilet_blog"),
    ("Сайт Горбилет", "site_GB")
]
UTM_MEDIUMS_PUBLICATIONS = [
    ("ВКонтакте пост", "vk_post"),
    ("Instagram пост", "instagram_post"),
    ("Telegram пост", "telegram_post"),
    ("Pinterest пост", "pinterest_post"),
    ("Одноклассники пост", "ok_post"),
    ("YouTube публикация", "youtube_post"),
    ("Горбилет блог", "gorbilet_blog"),
    ("Сайт Горбилет", "site_GB"),
]
UTM_MEDIUMS_MAILINGS = [
    ("Email", "email"),
    ("VK Direct", "vk_direct"),
    ("TG Direct", "tg_direct"),
    ("WhatsApp", "wa"),
    ("Viber", "viber"),
    ("SMS", "sms"),
]
UTM_MEDIUMS_STORIES = [
    ("Instagram Stories", "instagram_story"),
    ("VK Stories", "vk_story"),
    ("Telegram Stories", "telegram_story"),
    ("YouTube Shorts", "youtube_shorts"),
]
UTM_MEDIUMS_CHANNELS = [
    ("Telegram канал", "telegram_channel"),
    ("YouTube канал", "youtube_channel"),
    ("VK канал", "vk_channel"),
    ("Pinterest канал", "pinterest_channel"),
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

    # Отправить клавиатуру для выбора utm_medium по группам с заголовками
    await callback.message.answer("Теперь выберите тип трафика (utm_medium):")

    # СММ (публикации)
    builder = InlineKeyboardBuilder()
    for name, val in UTM_MEDIUMS_PUBLICATIONS:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"med:{val}"))
    builder.adjust(2)
    await callback.message.answer("📣 СММ (публикации):", reply_markup=builder.as_markup())

    # СММ (рассылка)
    builder = InlineKeyboardBuilder()
    for name, val in UTM_MEDIUMS_MAILINGS:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"med:{val}"))
    builder.adjust(2)
    await callback.message.answer("📧 СММ (рассылка):", reply_markup=builder.as_markup())

    # СММ IG (истории)
    builder = InlineKeyboardBuilder()
    for name, val in UTM_MEDIUMS_STORIES:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"med:{val}"))
    builder.adjust(2)
    await callback.message.answer("📱 СММ IG (истории):", reply_markup=builder.as_markup())

    # СММ (каналы)
    builder = InlineKeyboardBuilder()
    for name, val in UTM_MEDIUMS_CHANNELS:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"med:{val}"))
    builder.adjust(2)
    await callback.message.answer("📡 СММ (каналы):", reply_markup=builder.as_markup())

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

    # Отправить клавиатуры кампаний по группам
    await callback.message.answer("Теперь выберите кампанию (utm_campaign):")

    # СПБ
    builder = InlineKeyboardBuilder()
    for name, val in UTM_CAMPAIGNS_SPB:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"camp:{val}"))
    builder.adjust(2)
    await callback.message.answer("📍 Санкт-Петербург:", reply_markup=builder.as_markup())

    # МСК
    builder = InlineKeyboardBuilder()
    for name, val in UTM_CAMPAIGNS_MSK:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"camp:{val}"))
    builder.adjust(2)
    await callback.message.answer("🏙 Москва:", reply_markup=builder.as_markup())

    # Турция и зарубежье
    builder = InlineKeyboardBuilder()
    for name, val in UTM_CAMPAIGNS_TR:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"camp:{val}"))
    builder.adjust(2)
    await callback.message.answer("✈️ Турция и зарубежье:", reply_markup=builder.as_markup())

    # Регионы России
    builder = InlineKeyboardBuilder()
    for name, val in UTM_CAMPAIGNS_REGIONS:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"camp:{val}"))
    builder.adjust(2)
    await callback.message.answer("🌍 Регионы России:", reply_markup=builder.as_markup())

    # Зарубежные направления
    builder = InlineKeyboardBuilder()
    for name, val in UTM_CAMPAIGNS_FOREIGN:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"camp:{val}"))
    builder.adjust(2)
    await callback.message.answer("🌐 Зарубежные направления:", reply_markup=builder.as_markup())

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

    # Сформировать полную UTM-ссылку
    base_url = user_data[user_id].get("base_url", "")
    full_url = build_utm_url(base_url, user_data[user_id]["utm_source"], user_data[user_id]["utm_medium"], campaign_val)
    logger.info(f"Full UTM URL for user {user_id}: {full_url}")
    # Отправить длинную ссылку на сокращение через API
    logger.info(f"Sending to CLC: {full_url}")
    logger.debug("CLC request payload: %s", {"url": full_url})

    try:
        short_url = await shorten_url(full_url, settings.clc_api_key)
    except Exception as e:
        logger.exception(f"CLC shorten exception for user {user_id}: {e}")
        await callback.message.answer("❌ Ошибка при обращении к сервису сокращения. Попробуйте позже.")
        return

    if short_url is None:
        logger.error("CLC shorten returned None for user %s, url=%s", user_id, full_url)
        # Обработка ошибки сокращения
        await callback.message.answer("❌ Не удалось сократить ссылку. Попробуйте позже.")
        return

    logger.info(f"Short URL for user {user_id}: {short_url}")
    # Сохранить в историю (оставляем только 5 последних записей)
    history_list = user_history.get(user_id, [])
    history_list.append((base_url, full_url, short_url))
    user_history[user_id] = history_list[-5:]

    # Отправить пользователю итоговый отчет с ссылками
    result_text = ("✅ Ссылка готова!\n\n"
                   f"🔗 Исходная:\n{base_url}\n\n"
                   f"🧩 С UTM:\n{full_url}\n\n"
                   f"✂️ Сокращённая:\n{short_url}")
    await callback.message.answer(result_text)

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