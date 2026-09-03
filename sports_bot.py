import os
import json
import requests

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

STATE_FILE = "telegram_state.json"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass

    return {"offset": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def telegram_api(method, params=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    response = requests.get(url, params=params or {}, timeout=30)
    response.raise_for_status()
    return response.json()


def send_discord(content=None, file_bytes=None, filename=None):
    if file_bytes:
        files = {
            "file": (
                filename or "telegram_file",
                file_bytes
            )
        }

        data = {}

        if content:
            data["content"] = content

        response = requests.post(
            DISCORD_WEBHOOK,
            data=data,
            files=files,
            timeout=60
        )
    else:
        response = requests.post(
            DISCORD_WEBHOOK,
            json={"content": content or ""},
            timeout=30
        )

    response.raise_for_status()


def download_file(file_id):
    info = telegram_api(
        "getFile",
        {"file_id": file_id}
    )

    file_path = info["result"]["file_path"]

    url = (
        f"https://api.telegram.org/file/bot"
        f"{TELEGRAM_BOT_TOKEN}/{file_path}"
    )

    response = requests.get(
        url,
        timeout=60
    )

    response.raise_for_status()

    return response.content, file_path


def process_message(message):
    # Text
    text = message.get("text")

    if text:
        send_discord(text)

    # Caption attached to picture/video/file
    caption = message.get("caption")

    # Picture
    if message.get("photo"):
        photo = message["photo"][-1]

        file_id = photo["file_id"]

        file_bytes, file_path = download_file(file_id)

        filename = os.path.basename(file_path)

        send_discord(
            content=caption,
            file_bytes=file_bytes,
            filename=filename
        )

    # Video
    elif message.get("video"):
        video = message["video"]

        file_id = video["file_id"]

        file_bytes, file_path = download_file(file_id)

        filename = os.path.basename(file_path)

        send_discord(
            content=caption,
            file_bytes=file_bytes,
            filename=filename
        )

    # Document / other file
    elif message.get("document"):
        document = message["document"]

        file_id = document["file_id"]

        file_bytes, file_path = download_file(file_id)

        filename = document.get(
            "file_name",
            os.path.basename(file_path)
        )

        send_discord(
            content=caption,
            file_bytes=file_bytes,
            filename=filename
        )

    # Audio
    elif message.get("audio"):
        audio = message["audio"]

        file_id = audio["file_id"]

        file_bytes, file_path = download_file(file_id)

        filename = os.path.basename(file_path)

        send_discord(
            content=caption,
            file_bytes=file_bytes,
            filename=filename
        )

    # Voice message
    elif message.get("voice"):
        voice = message["voice"]

        file_id = voice["file_id"]

        file_bytes, file_path = download_file(file_id)

        filename = os.path.basename(file_path)

        send_discord(
            content=caption,
            file_bytes=file_bytes,
            filename=filename
        )


def main():
    state = load_state()

    offset = state.get("offset", 0)

    print("Checking Telegram...")

    updates = telegram_api(
        "getUpdates",
        {
            "offset": offset,
            "timeout": 10,
            "allowed_updates": json.dumps(
                ["message", "channel_post"]
            )
        }
    ).get("result", [])

    print(f"Found {len(updates)} update(s).")

    for update in updates:

        update_id = update["update_id"]

        message = (
            update.get("message")
            or update.get("channel_post")
        )

        if message:
            try:
                process_message(message)
                print("Sent Telegram message to Discord.")
            except Exception as e:
                print(f"Error: {e}")

        state["offset"] = update_id + 1

    save_state(state)

    print("Finished.")


if __name__ == "__main__":
    main()
