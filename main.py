import asyncio
import os
import random
import time

import django
from asgiref.sync import sync_to_async
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv


load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin_panel.settings")
django.setup()

from movies.models import ContentItem, RequiredLink, RequiredLinkClick


BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

MIN_LINK_WAIT_SECONDS = 7
DELETE_AFTER_SECONDS = 30
REQUIRED_LINKS_COUNT = 6
BASE_WEB_URL = "https://app.freemoviestream.online"

USER_PROGRESS = {}


@sync_to_async
def get_item_by_code(code: str):
    try:
        item = ContentItem.objects.select_related("content").get(download_code=code)

        return {
            "content_title": item.content.title,
            "title": item.title,
            "storage_chat_id": item.storage_chat_id,
            "storage_message_id": item.storage_message_id,
            "download_code": item.download_code,
        }

    except ContentItem.DoesNotExist:
        return None


@sync_to_async
def get_random_required_links(limit: int = 6):
    links = list(RequiredLink.objects.filter(is_active=True))

    if not links:
        return []

    selected_links = links if len(links) <= limit else random.sample(links, limit)

    return [
        {
            "id": str(link.id),
            "title": link.title,
            "url": link.url,
        }
        for link in selected_links
    ]


@sync_to_async
def create_required_link_click(telegram_user_id: int, item_code: str, required_link_id: str):
    required_link = RequiredLink.objects.get(id=int(required_link_id))

    click = RequiredLinkClick.objects.create(
        telegram_user_id=telegram_user_id,
        item_code=item_code,
        required_link=required_link,
    )

    return str(click.token)


@sync_to_async
def get_opened_clicks_for_user(telegram_user_id: int, item_code: str):
    clicks = RequiredLinkClick.objects.filter(
        telegram_user_id=telegram_user_id,
        item_code=item_code,
        is_opened=True,
        opened_at__isnull=False,
    )

    return {
        str(click.required_link_id): click.opened_at
        for click in clicks
    }


def required_links_keyboard(code: str, links: list):
    buttons = []

    for index, link in enumerate(links, start=1):
        buttons.append([
            InlineKeyboardButton(
                text=f"Open link {index}",
                callback_data=f"open:{code}:{link['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="✅ Done",
            callback_data=f"done:{code}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def open_link_keyboard(tracking_url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open website", url=tracking_url)]
        ]
    )


async def delete_later(bot: Bot, chat_id: int, message_id: int, delay_seconds: int = 30):
    await asyncio.sleep(delay_seconds)

    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Deleted message {message_id} from chat {chat_id}")
    except Exception as e:
        print("Delete failed:", e)


@dp.message()
async def start_handler(message: Message):
    if not message.text or not message.text.startswith("/start"):
        return

    code = None
    parts = message.text.strip().split(maxsplit=1)

    if len(parts) > 1:
        code = parts[1].strip()

    print("START TEXT:", message.text)
    print("CODE:", code)

    if not code:
        await message.answer(
            "Welcome 👋\n\n"
            "Please enter from the download link on the website."
        )
        return

    item = await get_item_by_code(code)

    if not item:
        await message.answer(
            f"Movie not found.\n\n"
            f"Code received: {code}"
        )
        return

    selected_links = await get_random_required_links(REQUIRED_LINKS_COUNT)

    if not selected_links:
        await message.answer(
            "No required links are available right now.\n"
            "Please try again later."
        )
        return

    USER_PROGRESS[message.from_user.id] = {
        "start_time": time.time(),
        "code": code,
        "required_links": selected_links,
    }

    await message.answer(
        f"Movie: {item['content_title']}\n"
        f"Item: {item['title']}\n\n"
        f"You will receive {len(selected_links)} links.\n"
        f"Please open every link.\n\n"
        f"After opening each website, wait at least 10 seconds.\n"
        f"Then return here and press ✅ Done.\n\n"
        f"After completing all steps, the movie will be sent to you.",
        reply_markup=required_links_keyboard(code, selected_links)
    )


@dp.callback_query(F.data.startswith("open:"))
async def open_link_handler(callback: CallbackQuery):
    _, code, link_id = callback.data.split(":")
    user_id = callback.from_user.id

    progress = USER_PROGRESS.get(user_id)

    if not progress or progress["code"] != code:
        await callback.answer(
            "Please open the download link again from the website.",
            show_alert=True
        )
        return

    selected_links = progress["required_links"]

    link = next((item for item in selected_links if item["id"] == link_id), None)

    if not link:
        await callback.answer("Link not found.", show_alert=True)
        return

    token = await create_required_link_click(
        telegram_user_id=user_id,
        item_code=code,
        required_link_id=link_id,
    )

    tracking_url = f"{BASE_WEB_URL}/r/{token}/"
    link_number = selected_links.index(link) + 1

    await callback.message.answer(
        f"Link {link_number}/{len(selected_links)}\n\n"
        f"Tap the button below and open the website.\n"
        f"After opening it, stay there for at least 10 seconds.\n"
        f"Then come back and continue.",
        reply_markup=open_link_keyboard(tracking_url)
    )

    await callback.answer("Tracking link created ✅")


@dp.callback_query(F.data.startswith("done:"))
async def done_handler(callback: CallbackQuery):
    code = callback.data.split(":")[1]
    user_id = callback.from_user.id

    progress = USER_PROGRESS.get(user_id)

    if not progress or progress["code"] != code:
        await callback.answer(
            "Please open the download link again from the website.",
            show_alert=True
        )
        return

    selected_links = progress["required_links"]
    required_ids = {link["id"] for link in selected_links}

    opened_clicks = await get_opened_clicks_for_user(
        telegram_user_id=user_id,
        item_code=code,
    )

    opened_ids = set(opened_clicks.keys())
    missing_ids = required_ids - opened_ids

    if missing_ids:
        await callback.answer(
            f"You have not opened all websites yet.\n\n"
            f"{len(missing_ids)} link(s) remaining.",
            show_alert=True
        )
        return

    now = time.time()

    for link in selected_links:
        link_id = link["id"]
        opened_at = opened_clicks.get(link_id)

        if not opened_at:
            await callback.answer(
                "Some links were not opened correctly.",
                show_alert=True
            )
            return

        elapsed_link_time = now - opened_at.timestamp()

        if elapsed_link_time < MIN_LINK_WAIT_SECONDS:
            await callback.answer(
                "You spent too little time on the previous website.\n\n"
                "Please open it again and wait at least 10 seconds.",
                show_alert=True
            )
            return

    item = await get_item_by_code(code)

    if not item:
        await callback.message.answer("Movie not found.")
        return

    await callback.message.answer(
        "✅ Verified. Sending your movie...\n\n"
        f"⚠️ This file will be deleted after {DELETE_AFTER_SECONDS} seconds.\n"
        "Please forward it to your Saved Messages or your private chat."
    )

    sent_message = await callback.bot.copy_message(
        chat_id=callback.from_user.id,
        from_chat_id=item["storage_chat_id"],
        message_id=item["storage_message_id"],
    )

    asyncio.create_task(
        delete_later(
            bot=callback.bot,
            chat_id=callback.from_user.id,
            message_id=sent_message.message_id,
            delay_seconds=DELETE_AFTER_SECONDS
        )
    )

    await callback.answer()


async def main():
    print("Bot is running with ContentItem database and tracking links...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())