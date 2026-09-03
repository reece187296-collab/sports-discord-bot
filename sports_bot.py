import os
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# Simple test message
message = {
    "embeds": [
        {
            "title": "🏆 Sports Bot Online",
            "description": "The sports Discord bot is working!",
            "color": 3066993,
            "footer": {
                "text": "Sports Bot"
            }
        }
    ]
}

response = requests.post(
    DISCORD_WEBHOOK,
    json=message,
    timeout=30
)

response.raise_for_status()

print("Message successfully sent to Discord!")
