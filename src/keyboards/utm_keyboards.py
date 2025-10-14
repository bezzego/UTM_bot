from typing import Iterable, Sequence, Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_categories_keyboard(categories: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, (name, _) in categories.items():
        builder.add(InlineKeyboardButton(text=name, callback_data=f"add_category:{key}"))
    builder.adjust(1)
    return builder.as_markup()


def build_category_management_keyboard(category_key: str, items: Sequence[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="👁️ Посмотреть все метки",
            callback_data=f"view_category:{category_key}",
        )
    )

    for name, value in items:
        builder.add(
            InlineKeyboardButton(
                text=f"❌ Удалить {name}",
                callback_data=f"delete_item:{category_key}:{value}",
            )
        )

    builder.add(
        InlineKeyboardButton(
            text="⬅️ Назад к категориям",
            callback_data="back_to_categories",
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def build_sources_keyboard(sources: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, value in sources:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"src:{value}"))
    builder.adjust(3)
    return builder.as_markup()


def build_medium_groups_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📣 СММ (публикации)", callback_data="medgrp:publications")
    builder.button(text="📧 СММ (рассылка)", callback_data="medgrp:mailings")
    builder.button(text="📱 СММ IG (истории)", callback_data="medgrp:stories")
    builder.button(text="📡 СММ (каналы)", callback_data="medgrp:channels")
    builder.adjust(2)
    return builder.as_markup()


def build_medium_keyboard(items: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, value in items:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"med:{value}"))
    builder.add(InlineKeyboardButton(text="⬅ Назад", callback_data="back:medium"))
    builder.adjust(2)
    return builder.as_markup()


def build_campaign_groups_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📍 Санкт-Петербург", callback_data="campgrp:spb")
    builder.button(text="🏙 Москва", callback_data="campgrp:msk")
    builder.button(text="✈️ Турция и зарубежье", callback_data="campgrp:tr")
    builder.button(text="🌍 Регионы России", callback_data="campgrp:regions")
    builder.button(text="🌐 Зарубежные направления", callback_data="campgrp:foreign")
    builder.adjust(2)
    return builder.as_markup()


def build_campaign_keyboard(items: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, value in items:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"camp:{value}"))
    builder.add(InlineKeyboardButton(text="⬅ Назад", callback_data="back:campaign"))
    builder.adjust(2)
    return builder.as_markup()


def build_date_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Сегодня", callback_data="adddate:today")
    builder.button(text="✏️ Ввести дату", callback_data="adddate:manual")
    builder.button(text="❌ Не добавлять дату", callback_data="adddate:none")
    builder.adjust(2)
    return builder.as_markup()
