"""
BRO-BOT — Telegram Notification System
Sends daily briefs and alerts to the user's Telegram.
"""

import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(
        TELEGRAM_BOT_TOKEN
        and TELEGRAM_CHAT_ID
        and TELEGRAM_BOT_TOKEN != "your_telegram_bot_token_here"
        and TELEGRAM_CHAT_ID != "your_telegram_chat_id_here"
    )


async def send_message_async(text: str, parse_mode: str = "HTML") -> bool:
    """Send a Telegram message asynchronously."""
    if not is_configured():
        logger.warning("Telegram not configured — skipping notification")
        return False

    try:
        from telegram import Bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=parse_mode,
        )
        logger.info("✅ Telegram message sent")
        return True
    except Exception as e:
        logger.error(f"❌ Telegram send failed: {e}")
        return False


def send_message(text: str) -> bool:
    """Synchronous wrapper to send a Telegram message."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, send_message_async(text))
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(send_message_async(text))
    except Exception as e:
        logger.error(f"❌ Telegram wrapper error: {e}")
        return False


def send_daily_brief(brief_text: str) -> bool:
    """Send the daily brief with nice formatting."""
    today = datetime.now().strftime("%d %b %Y")
    message = f"""🤖 <b>BRO-BOT Daily Brief</b> — {today}

{brief_text}

——————————————
<i>Powered by BRO-BOT 🚀</i>"""
    return send_message(message)


def send_alert(title: str, body: str, emoji: str = "🔔") -> bool:
    """Send a quick alert notification."""
    message = f"""{emoji} <b>{title}</b>

{body}

<i>{datetime.now().strftime('%H:%M')} · BRO-BOT</i>"""
    return send_message(message)


def send_post_reminder(platform: str, post_preview: str) -> bool:
    """Remind user that a post needs approval."""
    return send_alert(
        title=f"Post ready for {platform.upper()}!",
        body=f"✍️ Preview:\n<i>{post_preview[:200]}...</i>\n\n👉 Open dashboard to approve.",
        emoji="📢",
    )


def send_job_alert(role: str, company: str, url: str, posted_at: str = "Just now", applicants: str = "Be an Early Applicant") -> bool:
    """Notify user about a new matching job with rich metadata."""
    return send_alert(
        title=f"🚨 New Job Match: {company}",
        body=f"🎯 <b>Role:</b> {role}\n🏢 <b>Company:</b> {company}\n🕒 <b>Posted:</b> {posted_at}\n👥 <b>Applicants:</b> {applicants}\n\n👉 <b>Apply URL:</b> {url}",
        emoji="⚡",
    )


def send_recruiter_message_alert(sender: str, platform: str, preview: str) -> bool:
    """Alert user when a recruiter sends a message."""
    return send_alert(
        title=f"Recruiter message on {platform}! 💬",
        body=f"From: <b>{sender}</b>\n\n<i>{preview[:150]}...</i>\n\n👉 Open dashboard to reply.",
        emoji="📩",
    )
