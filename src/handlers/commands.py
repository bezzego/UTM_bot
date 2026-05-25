from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from src.keyboards.main_menu import build_main_menu_keyboard
from src.keyboards.settings import build_settings_keyboard
from src.services.database import database
from src.state.user_state import (
    pending_password_change_users,
    pending_password_users,
    pending_user_deletion,
)


router = Router()
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    localized = parsed.astimezone(MOSCOW_TZ)
    return localized.strftime("%Y-%m-%d %H:%M") + " МСК"


def _format_username(username: str | None) -> str:
    if not username:
        return "—"
    if " " in username:
        return username
    if username.startswith("@"):
        return username
    return f"@{username}"


@router.message(Command("start"), flags={"auth_required": False})
async def cmd_start(message: types.Message) -> None:
    user_id = message.from_user.id

    if database.is_user_banned(user_id):
        pending_password_users.discard(user_id)
        await message.answer("⛔️ Доступ к боту запрещён.")
        return

    if database.is_user_authorized(user_id):
        pending_password_users.discard(user_id)
        database.authorize_user(user_id, message.from_user.username)
        await message.answer(
            "👋 С возвращением! Выберите действие на клавиатуре.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    pending_password_users.add(user_id)
    await message.answer(
        "🔒 Бот доступен только для сотрудников.\n"
        "Введите пароль, чтобы начать работу.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


@router.message(lambda msg: msg.from_user.id in pending_password_users, flags={"auth_required": False})
async def handle_password(message: types.Message) -> None:
    user_id = message.from_user.id
    if not message.text:
        await message.answer("Пароль нужно отправить текстом.")
        return

    password = message.text.strip()

    current_password = database.get_bot_password()

    if password == current_password:
        database.authorize_user(user_id, message.from_user.username)
        pending_password_users.discard(user_id)
        await message.answer(
            "✅ Пароль принят! Теперь вы можете пользоваться ботом.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    attempts = database.increment_auth_attempts(user_id)
    remaining = max(0, 3 - attempts)

    if attempts >= 3:
        database.ban_user(user_id, message.from_user.username, reason="invalid_password")
        pending_password_users.discard(user_id)
        await message.answer("❌ Пароль неверный. Лимит попыток исчерпан, вы заблокированы.")
        return

    pending_password_users.add(user_id)
    await message.answer(f"❌ Пароль неверный. Осталось попыток: {remaining}.")


@router.message(lambda msg: msg.from_user.id in pending_password_change_users)
async def handle_new_bot_password(message: types.Message) -> None:
    user_id = message.from_user.id
    if not message.text:
        await message.answer("Пароль должен быть текстом. Попробуйте ещё раз.")
        return

    new_password = message.text.strip()
    if not new_password:
        await message.answer("Пароль не должен быть пустым. Введите другое значение.")
        return
    if new_password.casefold() == "отмена":
        pending_password_change_users.discard(user_id)
        await message.answer(
            "Действие отменено.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    database.update_bot_password(new_password)
    pending_password_change_users.discard(user_id)
    await message.answer(
        "🔐 Пароль обновлён. Сообщите команде о новых данных для доступа.",
        reply_markup=build_main_menu_keyboard(),
    )


@router.message(lambda msg: msg.from_user.id in pending_user_deletion)
async def handle_user_deletion(message: types.Message) -> None:
    user_id = message.from_user.id
    if not message.text:
        await message.answer("ID пользователя должен быть числом. Попробуйте снова.")
        return

    user_id_text = message.text.strip()
    if user_id_text.casefold() == "отмена":
        pending_user_deletion.discard(user_id)
        await message.answer("Удаление отменено.", reply_markup=build_main_menu_keyboard())
        return

    if not user_id_text.isdigit():
        await message.answer("ID пользователя должен содержать только цифры. Введите корректное значение.")
        return

    target_user_id = int(user_id_text)
    deleted = database.delete_user(target_user_id)
    pending_user_deletion.discard(user_id)

    if deleted:
        await message.answer(f"✅ Пользователь {target_user_id} удалён из базы.")
    else:
        await message.answer("Пользователь с таким ID не найден среди активных или заблокированных.")


@router.message(F.text == "Настройки")
async def show_settings(message: types.Message) -> None:
    user_id = message.from_user.id
    pending_password_change_users.discard(user_id)
    pending_user_deletion.discard(user_id)
    await message.answer(
        "⚙️ Настройки. Выберите действие:",
        reply_markup=build_settings_keyboard(),
    )


@router.callback_query(F.data == "settings:change_password")
async def start_password_change(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    pending_user_deletion.discard(user_id)
    pending_password_change_users.add(user_id)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "✏️ Отправьте новый пароль. Он заменит текущий. Чтобы отменить, напишите «Отмена»."
        )


@router.callback_query(F.data == "settings:view_users")
async def show_users(callback: types.CallbackQuery) -> None:
    await callback.answer()
    active_users = database.list_authorized_users()
    banned_users = database.list_banned_users()

    lines: list[str] = ["👥 Пользователи бота"]

    if active_users:
        lines.append("")
        lines.append("Активные:")
        for row in active_users[:50]:
            username = _format_username(row["username"])
            timestamp = _format_timestamp(row["authorized_at"])
            lines.append(f"• ID {row['user_id']} | {username} | доступ с {timestamp}")
        if len(active_users) > 50:
            lines.append("… показаны последние 50 записей")
    else:
        lines.append("")
        lines.append("Активные: —")

    if banned_users:
        lines.append("")
        lines.append("Заблокированные:")
        for row in banned_users[:50]:
            username = _format_username(row["username"])
            timestamp = _format_timestamp(row["banned_at"])
            reason = row["reason"] or "—"
            lines.append(
                f"• ID {row['user_id']} | {username} | блокирован {timestamp} | причина: {reason}"
            )
        if len(banned_users) > 50:
            lines.append("… показаны последние 50 записей")
    else:
        lines.append("")
        lines.append("Заблокированные: —")

    if callback.message:
        await callback.message.answer("\n".join(lines))


@router.callback_query(F.data == "settings:delete_user")
async def prompt_user_deletion(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    pending_password_change_users.discard(user_id)
    pending_user_deletion.add(user_id)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "🗑 Введите числовой ID пользователя, которого нужно удалить. Чтобы отменить, напишите «Отмена»."
        )


@router.callback_query(F.data == "settings:exit")
async def close_settings(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id
    pending_password_change_users.discard(user_id)
    pending_user_deletion.discard(user_id)
    await callback.answer("Настройки закрыты.")
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass


@router.message(F.text == "Отправить ссылку")
async def prompt_for_link(message: types.Message) -> None:
    await message.answer(
        "✍️ Пришлите ссылку, для которой нужно собрать UTM-метки. "
        "Она должна начинаться с http:// или https://"
    )


@router.message(F.text == "Посмотреть историю")
async def show_history(message: types.Message) -> None:
    user_id = message.from_user.id

    history = database.get_history(user_id, limit=20)
    if not history:
        await message.answer("Пока нет сохранённых ссылок. Сначала сгенерируйте UTM.")
        return

    text_lines = ["🧾 Последние сохранённые ссылки:"]
    for index, (original, utm_url) in enumerate(history, start=1):
        text_lines.append(f"{index}. {utm_url} — исходная: {original}")

    await message.answer("\n".join(text_lines))
