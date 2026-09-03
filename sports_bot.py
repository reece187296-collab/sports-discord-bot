import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# SETTINGS
# =========================

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

THESPORTSDB_KEY = "123"

UK_TIMEZONE = ZoneInfo("Europe/London")

# =========================
# GET TODAY'S SPORTS
# =========================

today = datetime.now(UK_TIMEZONE).strftime("%Y-%m-%d")

url = (
    f"https://www.thesportsdb.com/api/v1/json/"
    f"{THESPORTSDB_KEY}/eventsday.php?d={today}"
)

response = requests.get(url, timeout=30)
response.raise_for_status()

data = response.json()

events = data.get("events") or []

# =========================
# BUILD DISCORD MESSAGE
# =========================

if not events:
    description = (
        f"No sports events were found for {today}."
    )
else:
    lines = []

    for event in events:

        sport = event.get("strSport", "Sport")
        league = event.get("strLeague", "")
        home = event.get("strHomeTeam", "")
        away = event.get("strAwayTeam", "")

        event_name = event.get("strEvent", "")

        if home and away:
            matchup = f"{home} vs {away}"
        elif event_name:
            matchup = event_name
        else:
            matchup = "Sports event"

        date_event = event.get("dateEvent", "")
        time_event = event.get("strTime", "")

        uk_time = "Time unavailable"

        if date_event and time_event:
            try:
                event_time = datetime.fromisoformat(
                    f"{date_event}T{time_event}"
                )

                uk_time = event_time.strftime("%H:%M")

            except ValueError:
                uk_time = time_event[:5]

        line = f"**{sport}** — {matchup}\n"

        if league:
            line += f"🏆 {league}\n"

        line += f"🕐 UK time: **{uk_time}**"

        lines.append(line)

    description = "\n\n".join(lines)

# =========================
# SEND TO DISCORD
# =========================

message = {
    "embeds": [
        {
            "title": "🇬🇧 UK Sports — Today",
            "description": description[:4000],
            "footer": {
                "text": "Sports data provided by TheSportsDB"
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

print("UK Sports update successfully sent to Discord!")
