from aiogram import Router, types
from aiogram.filters import Command

from src.state.user_state import user_history


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    await message.answer("Привет! Отправьте мне ссылку, для которой нужно создать UTM-метки.")


@router.message(Command("history"))
async def cmd_history(message: types.Message) -> None:
    user_id = message.from_user.id
    history = user_history.get(user_id)
    if not history:
        await message.answer("История пуста. Вы ещё не создавали ссылки.")
        return

    text_lines = ["Последние собранные ссылки:"]
    for index, (original, full, short) in enumerate(history, start=1):
        text_lines.append(f"{index}. {short} — (исходная: {original})")
    await message.answer("\n".join(text_lines))
