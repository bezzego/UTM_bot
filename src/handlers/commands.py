from aiogram import F, Router, types
from aiogram.filters import Command

from src.config import settings
from src.keyboards.main_menu import build_main_menu_keyboard
from src.services.database import database
from src.state.user_state import pending_password_users


router = Router()


@router.message(Command("start"), flags={"auth_required": False})
async def cmd_start(message: types.Message) -> None:
    user_id = message.from_user.id

    if database.is_user_banned(user_id):
        pending_password_users.discard(user_id)
        await message.answer("⛔️ Доступ к боту запрещён.")
        return

    if database.is_user_authorized(user_id):
        pending_password_users.discard(user_id)
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

    if password == settings.bot_access_password:
        database.authorize_user(user_id)
        pending_password_users.discard(user_id)
        await message.answer(
            "✅ Пароль принят! Теперь вы можете пользоваться ботом.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    database.ban_user(user_id, reason="invalid_password")
    pending_password_users.discard(user_id)
    await message.answer("❌ Пароль неверный. Вы навсегда заблокированы.")


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
    for index, (original, _, short) in enumerate(history, start=1):
        text_lines.append(f"{index}. {short} — исходная: {original}")

    await message.answer("\n".join(text_lines))
