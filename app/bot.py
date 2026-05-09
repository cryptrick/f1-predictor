import logging
import re

from telegram import Message, MessageEntity, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from app.config import settings
from app.db import init_db
from app.services import ingest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("bot")

URL_RE = re.compile(r"https?://[^\s)\]>'\"]+")


def extract_urls(message: Message) -> list[str]:
    found: list[str] = []

    for msg in (message, message.reply_to_message):
        if msg is None:
            continue
        text = msg.text or msg.caption or ""
        entities = msg.entities or msg.caption_entities or []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_LINK and ent.url:
                found.append(ent.url)
            elif ent.type == MessageEntity.URL:
                found.append(text[ent.offset : ent.offset + ent.length])
        if text:
            found.extend(URL_RE.findall(text))

    seen: set[str] = set()
    uniq: list[str] = []
    for u in found:
        u = u.strip().rstrip(".,;)")
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def message_payload(message: Message) -> dict:
    return {
        "chat_id": message.chat_id,
        "message_id": message.message_id,
        "date": message.date.isoformat() if message.date else None,
        "text": message.text or message.caption,
        "forward_origin": message.forward_origin.to_dict() if message.forward_origin else None,
    }


async def handle_message(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None:
        return

    if settings.allowed_user_id_set and user.id not in settings.allowed_user_id_set:
        log.warning("rejecting user %s (%s)", user.id, user.username)
        return

    urls = extract_urls(message)
    if not urls:
        await message.reply_text("No URL found in that message.")
        return

    payload = message_payload(message)
    ids = [ingest(url, "telegram", payload=payload) for url in urls]
    await message.reply_text(f"Saved {len(ids)} link{'s' if len(ids) != 1 else ''}.")


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN not set")
    init_db()
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    log.info("bot starting (long-poll)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
