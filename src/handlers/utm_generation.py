import datetime
import logging
from typing import Optional, Sequence, Tuple

from aiogram import F, Router, types
from aiogram.types import InlineKeyboardButton

from src.config import settings
from src.keyboards.utm_keyboards import (
    build_campaign_groups_keyboard,
    build_campaign_keyboard,
    build_date_choice_keyboard,
    build_medium_groups_keyboard,
    build_medium_keyboard,
    build_sources_keyboard,
)
from src.services.clc_shortener import shorten_url
from src.services.utm_builder import build_utm_url
from src.services.utm_manager import utm_manager
from src.state.user_state import user_data, user_history
from src.utils.utm import build_utm_content_with_date, extract_action_slug


logger = logging.getLogger(__name__)
router = Router()


def get_utm_sources() -> Sequence[Tuple[str, str]]:
    return utm_manager.get_category_data("source")


MEDIUM_GROUPS_MAP = {
    "publications": "medium_publications",
    "mailings": "medium_mailings",
    "stories": "medium_stories",
    "channels": "medium_channels",
}

CAMPAIGN_GROUPS_MAP = {
    "spb": "campaign_spb",
    "msk": "campaign_msk",
    "tr": "campaign_tr",
    "regions": "campaign_regions",
    "foreign": "campaign_foreign",
}


def get_utm_mediums(group: str) -> Sequence[Tuple[str, str]]:
    category_key = MEDIUM_GROUPS_MAP.get(group)
    if not category_key:
        return []
    return utm_manager.get_category_data(category_key)


def get_utm_campaigns(group: str) -> Sequence[Tuple[str, str]]:
    category_key = CAMPAIGN_GROUPS_MAP.get(group)
    if not category_key:
        return []
    return utm_manager.get_category_data(category_key)


@router.message(F.text.regexp(r"^https?://"))
async def handle_base_url(message: types.Message) -> None:
    user_id = message.from_user.id
    base_url = message.text.strip()

    user_data[user_id] = {"base_url": base_url}
    logger.info("Received base URL from user %s: %s", user_id, base_url)

    sources = get_utm_sources()
    if not sources:
        await message.answer(
            "❌ Список utm_source пуст. Добавьте данные через команду /add."
        )
        return

    await message.answer(
        "Выберите источник трафика (utm_source):",
        reply_markup=build_sources_keyboard(sources),
    )


@router.callback_query(F.data.startswith("src:"))
async def select_source(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    source_val = callback.data.split(":", 1)[1]

    user_data.setdefault(user_id, {})
    user_data[user_id]["utm_source"] = source_val
    logger.info("User %s selected utm_source: %s", user_id, source_val)

    await callback.answer()
    await callback.message.edit_text(f"Источник (utm_source) выбран: {source_val}")

    await callback.message.answer(
        "Выберите группу utm_medium:",
        reply_markup=build_medium_groups_keyboard(),
    )


@router.callback_query(F.data.startswith("medgrp:"))
async def select_medium_group(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    group_val = callback.data.split(":", 1)[1]

    mediums = get_utm_mediums(group_val)
    if not mediums:
        await callback.answer("В этой группе пока нет меток.", show_alert=True)
        return

    await callback.message.edit_text(f"Вы выбрали группу: {group_val}")
    await callback.message.answer(
        "Теперь выберите конкретную utm_medium:",
        reply_markup=build_medium_keyboard(mediums),
    )


@router.callback_query(F.data.startswith("med:"))
async def select_medium(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    medium_val = callback.data.split(":", 1)[1]

    user_data.setdefault(user_id, {})
    user_data[user_id]["utm_medium"] = medium_val
    logger.info("User %s selected utm_medium: %s", user_id, medium_val)

    await callback.answer()
    await callback.message.edit_text(f"Тип трафика (utm_medium) выбран: {medium_val}")
    await callback.message.answer(
        "Выберите группу utm_campaign:",
        reply_markup=build_campaign_groups_keyboard(),
    )


@router.callback_query(F.data.startswith("campgrp:"))
async def select_campaign_group(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    group_val = callback.data.split(":", 1)[1]

    campaigns = get_utm_campaigns(group_val)
    if not campaigns:
        await callback.answer("В этой группе пока нет меток.", show_alert=True)
        return

    await callback.message.edit_text(f"Вы выбрали группу кампаний: {group_val}")
    await callback.message.answer(
        "Теперь выберите конкретную кампанию (utm_campaign):",
        reply_markup=build_campaign_keyboard(campaigns),
    )


@router.callback_query(F.data.startswith("camp:"))
async def select_campaign(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    campaign_val = callback.data.split(":", 1)[1]

    user_data.setdefault(user_id, {})
    user_data[user_id]["utm_campaign"] = campaign_val
    logger.info("User %s selected utm_campaign: %s", user_id, campaign_val)

    await callback.answer()
    await callback.message.edit_text(f"Кампания (utm_campaign) выбрана: {campaign_val}")
    await callback.message.answer(
        "Добавить дату в utm_content? Выберите один из вариантов:",
        reply_markup=build_date_choice_keyboard(),
    )


@router.callback_query(F.data.startswith("adddate:"))
async def add_date_choice(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    choice = callback.data.split(":", 1)[1]

    user_data.setdefault(user_id, {})

    if choice == "today":
        today = datetime.date.today().isoformat()
        user_data[user_id]["date_for_utm"] = today
        await callback.answer()
        await generate_short_link(user_id, callback=callback)
        return

    if choice == "tomorrow":
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        user_data[user_id]["date_for_utm"] = tomorrow
        await callback.answer()
        await generate_short_link(user_id, callback=callback)
        return

    if choice == "dayafter":
        day_after_tomorrow = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()
        user_data[user_id]["date_for_utm"] = day_after_tomorrow
        await callback.answer()
        await generate_short_link(user_id, callback=callback)
        return

    if choice == "none":
        user_data[user_id].pop("date_for_utm", None)
        user_data[user_id].pop("awaiting_date", None)
        await callback.answer()
        await generate_short_link(user_id, callback=callback)
        return

    user_data[user_id]["awaiting_date"] = True
    await callback.answer()
    await callback.message.answer("Введите дату в формате YYYY-MM-DD (например: 2025-10-10)")


@router.message(lambda msg: user_data.get(msg.from_user.id, {}).get("awaiting_date"))
async def handle_manual_date(message: types.Message) -> None:
    user_id = message.from_user.id
    date_str = message.text.strip()

    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await message.answer(
            "Неверный формат даты. Пожалуйста, введите в формате YYYY-MM-DD, например: 2025-10-10"
        )
        return

    user_data[user_id]["date_for_utm"] = date_str
    user_data[user_id]["awaiting_date"] = False
    await generate_short_link(user_id, message=message)


async def generate_short_link(
    user_id: int,
    message: Optional[types.Message] = None,
    callback: Optional[types.CallbackQuery] = None,
) -> None:
    base_url = user_data[user_id].get("base_url", "")
    utm_source = user_data[user_id].get("utm_source")
    utm_medium = user_data[user_id].get("utm_medium")
    utm_campaign = user_data[user_id].get("utm_campaign")
    date_for_utm = user_data[user_id].get("date_for_utm", "").strip()

    base_slug = extract_action_slug(base_url)
    utm_content = build_utm_content_with_date(base_slug, date_for_utm)
    full_url = build_utm_url(base_url, utm_source, utm_medium, utm_campaign, utm_content)

    logger.info("Full UTM URL for user %s: %s", user_id, full_url)
    logger.info("Sending to CLC: %s", full_url)

    try:
        short_url = await shorten_url(full_url, settings.clc_api_key)
    except Exception as exc:  # pragma: no cover - network failure path
        logger.exception("CLC shorten exception for user %s: %s", user_id, exc)
        await _reply(
            message,
            callback,
            "❌ Ошибка при обращении к сервису сокращения. Попробуйте позже.",
        )
        return

    if short_url is None:
        logger.error("CLC shorten returned None for user %s, url=%s", user_id, full_url)
        await _reply(
            message,
            callback,
            "❌ Не удалось сократить ссылку. Попробуйте позже.",
        )
        return

    history_list = user_history.get(user_id, [])
    history_list.append((base_url, full_url, short_url))
    user_history[user_id] = history_list[-50:]

    lines = ["✅ Результаты генерации ссылок:", f"🔗 Исходная:\n{base_url}"]
    lines.append("\n🧩 С UTM:\n" + full_url)
    lines.append("✂️ Сокращённая:\n" + short_url)
    result_text = "\n\n".join(lines)

    webapp_button = InlineKeyboardButton(
        text="Открыть API GorBilet",
        web_app=types.WebAppInfo(url="https://api.gorbilet.com/v2/admin/"),
    )
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[webapp_button]])

    await _reply(message, callback, result_text, keyboard)


async def _reply(
    message: Optional[types.Message],
    callback: Optional[types.CallbackQuery],
    text: str,
    keyboard: Optional[types.InlineKeyboardMarkup] = None,
) -> None:
    if message:
        await message.answer(text, reply_markup=keyboard)
    elif callback:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("back:"))
async def go_back(callback: types.CallbackQuery) -> None:
    _, target = callback.data.split(":", 1)
    if target == "medium":
        await callback.message.edit_text("Выберите группу utm_medium:")
        await callback.message.edit_reply_markup(reply_markup=build_medium_groups_keyboard())
        return

    if target == "campaign":
        await callback.message.edit_text("Выберите группу utm_campaign:")
        await callback.message.edit_reply_markup(reply_markup=build_campaign_groups_keyboard())
