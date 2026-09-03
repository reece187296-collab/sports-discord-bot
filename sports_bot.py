import os
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = os.environ["https://discord.com/api/webhooks/1545042996767105144/mlJpwovcnRrUsQ7n49qNgKdi4sTbMAGqDAL28BbGg_WMDA-CWVxvWCigwBZEO1TlH--M"]

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
