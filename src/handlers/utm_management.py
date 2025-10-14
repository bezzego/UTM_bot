import re

from aiogram import F, Router, types
from aiogram.filters import Command

from src.keyboards.utm_keyboards import (
    build_categories_keyboard,
    build_category_management_keyboard,
)
from src.services.utm_manager import utm_manager
from src.state.user_state import utm_editing_data


router = Router()


@router.message(Command("add"))
async def cmd_add(message: types.Message) -> None:
    user_id = message.from_user.id
    utm_editing_data[user_id] = {"step": None, "category": None}

    categories = utm_manager.get_all_categories()
    await message.answer(
        "🛠 Панель управления UTM-метками\n\n"
        "Выберите категорию для добавления новых меток:",
        reply_markup=build_categories_keyboard(categories),
    )


@router.callback_query(F.data.startswith("add_category:"))
async def select_add_category(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    category_key = callback.data.split(":", 1)[1]

    categories = utm_manager.get_all_categories()
    category_name = categories[category_key][0]

    utm_editing_data.setdefault(user_id, {})
    utm_editing_data[user_id].update({"category": category_key, "step": "waiting_name"})

    category_simple_key = category_key.split("_", 1)[1]
    existing_items = utm_manager.get_category_data(category_simple_key)

    if existing_items:
        items_text = "\n\n📋 Существующие метки:\n" + "\n".join(
            f"• {name} ({value})" for name, value in existing_items
        )
    else:
        items_text = "\n\n📭 В этой категории пока нет меток"

    await callback.message.edit_text(
        f"Выбрана категория: {category_name}\n"
        f"Теперь введите название новой метки (например: 'Новый источник'){items_text}\n\n"
        "Или нажмите кнопку ниже чтобы посмотреть все метки:",
        reply_markup=build_category_management_keyboard(category_key, existing_items),
    )


@router.message(lambda msg: utm_editing_data.get(msg.from_user.id, {}).get("step") == "waiting_name")
async def handle_utm_name(message: types.Message) -> None:
    user_id = message.from_user.id
    name = message.text.strip()

    if not name:
        await message.answer("Название не может быть пустым. Попробуйте еще раз:")
        return

    utm_editing_data[user_id]["name"] = name
    utm_editing_data[user_id]["step"] = "waiting_value"

    await message.answer(
        f"Отлично! Название: '{name}'\n\n"
        "Теперь введите значение для UTM-метки (только латинские буквы, цифры и нижние подчеркивания):\n"
        "Пример: new_source_2024"
    )


@router.message(lambda msg: utm_editing_data.get(msg.from_user.id, {}).get("step") == "waiting_value")
async def handle_utm_value(message: types.Message) -> None:
    user_id = message.from_user.id
    value = message.text.strip()

    if not re.match(r"^[a-z0-9_]+$", value):
        await message.answer(
            "Неверный формат! Используйте только:\n"
            "• латинские буквы в нижнем регистре\n"
            "• цифры\n"
            "• нижние подчеркивания\n\n"
            "Пример: new_source_2024\n"
            "Попробуйте еще раз:"
        )
        return

    user_state = utm_editing_data[user_id]
    category_key = user_state["category"]
    name = user_state["name"]

    category_simple_key = category_key.split("_", 1)[1]
    success = utm_manager.add_item(category_simple_key, name, value)

    if success:
        categories = utm_manager.get_all_categories()
        category_name = categories[category_key][0]

        await message.answer(
            "✅ Успешно добавлено!\n"
            f"Категория: {category_name}\n"
            f"Название: {name}\n"
            f"Значение: {value}\n\n"
            "Метка теперь доступна при создании ссылок!"
        )

        existing_items = utm_manager.get_category_data(category_simple_key)
        items_text = "\n".join(f"• {item_name} ({item_value})" for item_name, item_value in existing_items)

        await message.answer(
            f"📋 Обновленный список меток в категории:\n{items_text}",
            reply_markup=build_category_management_keyboard(category_key, existing_items),
        )
    else:
        await message.answer(
            "❌ Ошибка! Возможно, метка с таким значением уже существует.\n"
            "Попробуйте другое значение."
        )

    utm_editing_data[user_id] = {"step": None, "category": None}


@router.callback_query(F.data.startswith("view_category:"))
async def view_category_items(callback: types.CallbackQuery) -> None:
    category_key = callback.data.split(":", 1)[1]
    category_simple_key = category_key.split("_", 1)[1]

    categories = utm_manager.get_all_categories()
    category_name = categories[category_key][0]
    existing_items = utm_manager.get_category_data(category_simple_key)

    if existing_items:
        items_text = "\n".join(f"• {name} ({value})" for name, value in existing_items)
        text = f"📋 Все метки в категории '{category_name}':\n\n{items_text}"
    else:
        text = f"📭 В категории '{category_name}' пока нет меток"

    await callback.message.edit_text(
        text,
        reply_markup=build_category_management_keyboard(category_key, existing_items),
    )


@router.callback_query(F.data.startswith("delete_item:"))
async def delete_utm_item(callback: types.CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("❌ Ошибка!")
        return

    _, category_key, value = parts
    category_simple_key = category_key.split("_", 1)[1]

    success = utm_manager.delete_item(category_simple_key, value)
    if not success:
        await callback.answer("❌ Ошибка при удалении!")
        return

    await callback.answer("✅ Метка удалена!")

    categories = utm_manager.get_all_categories()
    category_name = categories[category_key][0]
    existing_items = utm_manager.get_category_data(category_simple_key)

    if existing_items:
        items_text = "\n".join(f"• {name} ({value})" for name, value in existing_items)
        text = f"📋 Все метки в категории '{category_name}':\n\n{items_text}"
    else:
        text = f"📭 В категории '{category_name}' пока нет меток"

    await callback.message.edit_text(
        text,
        reply_markup=build_category_management_keyboard(category_key, existing_items),
    )


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery) -> None:
    categories = utm_manager.get_all_categories()
    await callback.message.edit_text(
        "🛠 Панель управления UTM-метками\n\n"
        "Выберите категорию для добавления новых меток:",
        reply_markup=build_categories_keyboard(categories),
    )
