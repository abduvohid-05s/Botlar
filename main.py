import asyncio
import os
import random
import threading
import time
from aiohttp import web
import requests
import telebot

# ==========================================
# 28 TA TOKEN (BOT_TOKEN env bo'sh bo'lsa zaxira)
# ==========================================
DEFAULT_TOKENS = [
    "8230491436:AAErxaPtJKHZWi70QCu4jc4P-PY9ZHsUnqU",
    "8614193525:AAHmPEuVyLGf9y_1Pk32Bi_7wOthGdoVTF0",
    "8684961175:AAF-EugA4UUMEnOKuNRGxHAg7L5UK-hA9xw",
    "8730555029:AAHuY0QSrgJ1OX6NSFriiP9otWK_0dyy1zc",
    "8780781642:AAFKuXw5lgJrmJotxdslvV6Y-_F7TKYPrkg",
    "8814897952:AAFCaOyieh7BZTFggOiAHT5iddfPKyevUxk",
    "8839585037:AAHiLdafW4gdJllq6XYcWVHEiMNOxvXIIDw",
    "8846195735:AAG31765-y8ZSpfWGB38xPFkwxwNKih0Wvc",
    "8892329293:AAE81rvRwv37Duklrgq80tdo9xULDTZM-3A",
    "8945662963:AAG3Aw1EV_5pQTWOnB213BZ9hsxOsabl4z4",
    "8974305632:AAFGZlf4pHflRsyDR7teKX38ZS4q4bwKWcM",
    "9002507003:AAG5fOIyqcOGEi5agEEHk9uqNzIS__zpiQI",
    "9016231632:AAHv58jUef2Zo0qXJcfP6qyXsh5_smbbMYk",
    "9020615009:AAEbV8864UbsaI5S7z09mmaxN9s9yUS71TE",
    "9046541800:AAE0uJ7Va1UYmpbeGYaZemWv7TPxbb5YR7c",
    "9047354676:AAHyXJC8YZ-e-5CLG21Bgb36vjT05yYCOhs",
    "9052775549:AAFEoNQAXssqicX_1LCs9hyoUXsNIlzaw8I",
    "9084504354:AAHwN2j_fcaIOD9KzkB3-zrCsHZwp8yS44w",
    "9102375823:AAHtgDq7J6r7_tCpasA53fQeNOy2ibNeny4",
    "9106448970:AAF3Ms3td81uNpUiIN1ZkwFBCY49NOcgaPA",
    "9107066681:AAEKWcbJY2ckePO3NCwx4cWXxTN7tL27wCM",
    "9108538820:AAFBoxnLW2TawAsHg4k88SfjcFLom6EXb-g",
    "9124393806:AAFXmO2kEWYyak2JGpRWRG2yrwBYr76JZ5A",
    "9130269855:AAFrwTbyhnlKYXy1ghjQQo5x2Zr9FxH93ec",
    "9168857205:AAE_y2wmhnRoDc1cdoilYeWsTx1paJXYOOU",
    "9185480863:AAFTjvMgJa9Xs8MK6rK6B0y9pwqHh-9pXt4",
    "9216423865:AAGIyGkodnrm5uqpoYq6Vt5_1-iopneJKmg",
    "9261820651:AAGjVBWAKpOthpSE8H4yn4OuSDYhdKJNzrc",
]

# Salbiy reaksiyalarsiz ro'yxat (48 ta)
REACTIONS = [
    "❤", "👍", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "👌", "🕊",
    "😍", "🐳", "💯", "🏆", "🍾", "💋", "👀", "😇", "🤝", "✍",
    "🤗", "🎅", "🎄", "☃", "🤪", "💘", "🦄", "😘", "❤‍🔥", "⚡",
    "😎", "🤣", "🤓", "👨‍💻", "🎃", "🫡", "😈", "🍓", "💅", "💊",
    "👾", "🆒", "🗿", "🤔", "🙏", "🌭", "🍌",
]

CHANNEL_CONTENT_TYPES = [
    "text", "photo", "video", "audio", "document",
    "voice", "video_note", "sticker", "animation",
    "poll", "location", "contact", "venue",
]

RESTART_DELAY = 3
MAX_RESTARTS = 500
MAX_SEEN_SIZE = 5000
SEEN_TTL_SECONDS = 600

seen_lock = threading.Lock()
seen_messages = {}  # {(chat_id, message_id): timestamp}
http_local = threading.local()


def get_session():
    session = getattr(http_local, "session", None)
    if session is None:
        session = requests.Session()
        http_local.session = session
    return session


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def get_port():
    raw_port = (os.getenv("PORT") or "10000").strip()
    try:
        port = int(raw_port)
        return port if 1 <= port <= 65535 else 10000
    except ValueError:
        return 10000


def is_message_seen(chat_id, message_id):
    with seen_lock:
        return (chat_id, message_id) in seen_messages


def mark_and_claim_message(chat_id, message_id):
    """Postni eslab qoladi; birinchi marta ko'rilsa True, takror kelsa False qaytaradi."""
    now = time.time()
    key = (chat_id, message_id)
    with seen_lock:
        if len(seen_messages) >= MAX_SEEN_SIZE:
            expired = [k for k, ts in seen_messages.items() if now - ts > SEEN_TTL_SECONDS]
            for k in expired:
                del seen_messages[k]
            if len(seen_messages) >= MAX_SEEN_SIZE:
                seen_messages.clear()

        if key in seen_messages:
            return False

        seen_messages[key] = now
        return True


# ==========================================
# REAKSIYA YUBORUVCHI
# ==========================================
def send_reaction(token, chat_id, message_id, index):
    bot_id = token.split(":")[0]
    url = f"https://api.telegram.org/bot{token}/setMessageReaction"
    session = get_session()

    candidates = REACTIONS.copy()
    random.shuffle(candidates)

    time.sleep(index * 0.12)

    for emoji in candidates[:12]:
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}],
            "is_big": False,
        }

        for attempt in range(4):
            try:
                resp = session.post(url, json=payload, timeout=10)

                if resp.status_code == 200:
                    print(f"[{bot_id}] ✅ {emoji}")
                    return

                data = safe_json(resp)

                if resp.status_code == 429:
                    retry_after = data.get("parameters", {}).get("retry_after", 3)
                    print(f"[{bot_id}] ⏳ rate limit — {retry_after}s")
                    time.sleep(float(retry_after) + 0.5)
                    continue

                if resp.status_code == 400:
                    err = data.get("description", "")
                    if "REACTION_INVALID" in err or "message is not modified" in err.lower() or "reaction" in err.lower():
                        break
                    print(f"[{bot_id}] ⚠️ 400: {err}")
                    return

                if resp.status_code == 403:
                    err = data.get("description", "")
                    print(f"[{bot_id}] ⚠️ 403: {err}")
                    return

                print(f"[{bot_id}] ❌ HTTP {resp.status_code}")
                time.sleep(1)

            except requests.exceptions.Timeout:
                print(f"[{bot_id}] ⏱ timeout #{attempt + 1}")
                time.sleep(1.5)
            except Exception as e:
                print(f"[{bot_id}] 💥 {e}")
                time.sleep(1)

    print(f"[{bot_id}] 🔴 Reaksiya qo'yib bo'lmadi")


def trigger_all(chat_id, message_id, tokens):
    if not mark_and_claim_message(chat_id, message_id):
        return

    print(f"🎯 Trigger: chat={chat_id}, msg={message_id} -> {len(tokens)} ta bot")
    for idx, token in enumerate(tokens):
        threading.Thread(
            target=send_reaction,
            args=(token, chat_id, message_id, idx),
            daemon=True,
        ).start()


def delete_webhook(token):
    try:
        get_session().get(
            f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=True",
            timeout=5,
        )
    except Exception:
        pass


def attach_start_handler(bot):
    @bot.message_handler(commands=["start"])
    def on_start(msg):
        try:
            bot.send_message(msg.chat.id, "Bot ishlamoqda")
        except Exception:
            pass


# ==========================================
# UMUMIY POLLING LOOP
# ==========================================
def run_polling_loop(token, role_label, all_tokens=None, listen_channels=False, initial_delay=0.0):
    bot_id = token.split(":")[0]
    restarts = 0
    allowed_updates = (
        ["channel_post", "edited_channel_post", "message"]
        if listen_channels
        else ["message"]
    )
    num_threads = 4 if role_label == "MAIN" else (2 if listen_channels else 1)

    if initial_delay > 0:
        time.sleep(initial_delay)

    while restarts < MAX_RESTARTS:
        delete_webhook(token)
        bot = telebot.TeleBot(token, num_threads=num_threads)
        attach_start_handler(bot)

        if listen_channels and all_tokens:
            @bot.channel_post_handler(content_types=CHANNEL_CONTENT_TYPES)
            def on_post(msg, label=role_label, bid=bot_id, pool=all_tokens):
                if label != "MAIN" and not is_message_seen(msg.chat.id, msg.message_id):
                    print(f"[{label}:{bid}] 📨 ushlanmagan post — trigger!")
                trigger_all(msg.chat.id, msg.message_id, pool)

            @bot.edited_channel_post_handler(content_types=CHANNEL_CONTENT_TYPES)
            def on_edit(msg, pool=all_tokens):
                trigger_all(msg.chat.id, msg.message_id, pool)

        try:
            if listen_channels:
                print(f"[{role_label}:{bot_id}] 🟢 Polling #{restarts + 1}")
            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=20,
                interval=0,
                allowed_updates=allowed_updates,
            )
        except Exception as e:
            print(f"[{role_label}:{bot_id}] 💥 {e}")
        finally:
            try:
                bot.stop_polling()
            except Exception:
                pass

        restarts += 1
        if listen_channels:
            print(f"[{role_label}:{bot_id}] 🔄 {RESTART_DELAY}s dan so'ng qayta...")
        time.sleep(RESTART_DELAY)


# ==========================================
# WEB SERVER (Render / UptimeRobot uchun)
# ==========================================
async def handle_ping(request):
    return web.Response(text="Bot ishlamoqda")


async def start_web():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    app.router.add_get("/ping", handle_ping)
    port = get_port()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server :{port} da ishga tushdi")


def run_web():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_web())
    loop.run_forever()


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    env_tokens = os.getenv("BOT_TOKEN", "")
    parsed_env = [t.strip() for t in env_tokens.split(",") if t.strip()]
    tokens = list(dict.fromkeys(parsed_env)) if parsed_env else list(dict.fromkeys(DEFAULT_TOKENS))

    print(f"📋 Jami {len(tokens)} ta token yuklandi")

    # 1. aiohttp web-server
    threading.Thread(target=run_web, daemon=True).start()
    time.sleep(0.5)

    if tokens:
        # 2. Asosiy listener
        threading.Thread(
            target=run_polling_loop,
            args=(tokens[0], "MAIN"),
            kwargs={"all_tokens": tokens, "listen_channels": True, "initial_delay": 0.0},
            daemon=True,
        ).start()

        # 3. Backup listenerlar
        backup_count = min(2, max(0, len(tokens) - 1))
        for i in range(1, 1 + backup_count):
            threading.Thread(
                target=run_polling_loop,
                args=(tokens[i], "BACKUP"),
                kwargs={"all_tokens": tokens, "listen_channels": True, "initial_delay": float(2 + i)},
                daemon=True,
            ).start()

        # 4. Qolgan botlarda ham /start ishlashi uchun listener
        for extra_token in tokens[1 + backup_count:]:
            threading.Thread(
                target=run_polling_loop,
                args=(extra_token, "BOT"),
                kwargs={"listen_channels": False, "initial_delay": 1.5},
                daemon=True,
            ).start()

        print(f"🚀 1 asosiy + {backup_count} backup listener + {len(tokens)} ta /start handler faol")
    else:
        print("⚠️ Tokenlar ro'yxati bo'sh")

    while True:
        time.sleep(60)
