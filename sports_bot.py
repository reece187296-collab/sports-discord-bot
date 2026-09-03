import os
import re
import json
import hashlib
import requests
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO

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

    return {
        "offset": 0,
        "processed": []
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def telegram_api(method, params=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    response = requests.get(url, params=params or {}, timeout=30)
    response.raise_for_status()
    return response.json()


def download_telegram_image(file_id):
    file_info = telegram_api("getFile", {"file_id": file_id})

    file_path = file_info["result"]["file_path"]

    url = (
        f"https://api.telegram.org/file/bot"
        f"{TELEGRAM_BOT_TOKEN}/{file_path}"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    return Image.open(BytesIO(response.content))


def improve_image(image):
    image = image.convert("L")

    # Make the text larger
    width, height = image.size
    image = image.resize((width * 2, height * 2))

    # Improve contrast
    image = ImageEnhance.Contrast(image).enhance(2)

    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)

    return image


def clean_ocr_text(text):
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        # Remove excessive spaces
        line = re.sub(r"[ \t]+", " ", line)

        lines.append(line)

    return "\n".join(lines)


def send_to_discord(text):
    payload = {
        "content": text
    }

    response = requests.post(
        DISCORD_WEBHOOK,
        json=payload,
        timeout=30
    )

    response.raise_for_status()


def process_image(file_id):
    print("Downloading Telegram picture...")

    image = download_telegram_image(file_id)

    print("Running OCR...")

    image = improve_image(image)

    text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    text = clean_ocr_text(text)

    if not text:
        print("No text found in picture.")
        return False

    print("OCR result:")
    print(text)

    discord_message = (
        "📺 **SPORTS LISTING OCR**\n\n"
        f"```text\n{text}\n```"
    )

    send_to_discord(discord_message)

    print("Sent OCR text to Discord.")

    return True


def get_image_file_id(message):
    # Telegram normal picture
    if message.get("photo"):
        return message["photo"][-1]["file_id"]

    # Telegram image sent as a document
    document = message.get("document")

    if document:
        mime_type = document.get("mime_type", "")

        if mime_type.startswith("image/"):
            return document["file_id"]

    return None


def main():
    state = load_state()

    offset = state.get("offset", 0)
    processed = state.get("processed", [])

    print("Checking Telegram...")

    data = telegram_api(
        "getUpdates",
        {
            "offset": offset,
            "timeout": 10,
            "allowed_updates": json.dumps(
                ["message", "channel_post"]
            )
        }
    )

    updates = data.get("result", [])

    print(f"Found {len(updates)} Telegram update(s).")

    for update in updates:

        update_id = update["update_id"]

        message = (
            update.get("message")
            or update.get("channel_post")
        )

        if not message:
            state["offset"] = update_id + 1
            continue

        file_id = get_image_file_id(message)

        if not file_id:
            state["offset"] = update_id + 1
            continue

        # Create a fingerprint so the same picture isn't sent twice
        fingerprint = hashlib.sha256(
            file_id.encode()
        ).hexdigest()

        if fingerprint in processed:
            print("Picture already processed.")
            state["offset"] = update_id + 1
            continue

        try:
            success = process_image(file_id)

            if success:
                processed.append(fingerprint)

                # Keep state file small
                processed = processed[-200:]

        except Exception as e:
            print(f"Error processing picture: {e}")

        state["offset"] = update_id + 1

    state["processed"] = processed

    save_state(state)

    print("Finished.")


if __name__ == "__main__":
    main()
