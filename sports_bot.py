import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# SETTINGS
# =========================

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

API_KEY = "123"

UK_TIMEZONE = ZoneInfo("Europe/London")

# =========================
# TODAY'S DATE
# =========================

today = datetime.now(UK_TIMEZONE).strftime("%Y-%m-%d")

# =========================
# GET UK SPORTS TV LISTINGS
# =========================

url = (
    f"https://www.thesportsdb.com/api/v1/json/"
    f"{API_KEY}/eventstv.php"
)

params = {
    "d": today,
    "a": "United_Kingdom"
}

response = requests.get(
    url,
    params=params,
    timeout=30
)

response.raise_for_status()

data = response.json()

events = data.get("tvevents") or []

# =========================
# BUILD DISCORD MESSAGE
# =========================

lines = []

for event in events:

    sport = event.get("strSport", "Sport")
    event_name = event.get("strEvent", "Sports event")
    channel = event.get("strChannel", "Channel not listed")

    event_date = event.get("dateEvent", "")
    event_time = event.get("strTime", "")

    uk_time = "Time not listed"

    if event_date and event_time:

        try:
            event_datetime = datetime.fromisoformat(
                f"{event_date}T{event_time}"
            )

            uk_time = event_datetime.strftime("%H:%M")

        except ValueError:
            uk_time = event_time[:5]

    lines.append(
        f"**{sport}**\n"
        f"🎟️ {event_name}\n"
        f"🕐 {uk_time} UK\n"
        f"📺 {channel}"
    )

# =========================
# NOTHING FOUND
# =========================

if not lines:

    description = (
        f"No UK sports TV listings were found for "
        f"{today}."
    )

else:

    description = "\n\n".join(lines)

# Discord embeds have a description limit.
description = description[:4000]

# =========================
# SEND TO DISCORD
# =========================

message = {
    "embeds": [
        {
            "title": "🇬🇧 UK Sports TV Listings",
            "description": description,
            "footer": {
                "text": "Listings provided by TheSportsDB"
            }
        }
    ]
}

discord_response = requests.post(
    DISCORD_WEBHOOK,
    json=message,
    timeout=30
)

discord_response.raise_for_status()

print("UK Sports TV listings sent successfully!")
