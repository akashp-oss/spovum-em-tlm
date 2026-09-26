import urllib.request
import json
import os

webhook_url = os.environ.get("BANGOPS_CHAT_WEBHOOK", "")

# Ultra-clean, minimal, zero-slop card
minimal_card = {
    "cardsV2": [
        {
            "cardId": "clean_morning_checkin",
            "card": {
                "sections": [
                    {
                        "widgets": [
                            {
                                "decoratedText": {
                                    "topLabel": "BANG DESIGN",
                                    "text": "Morning Akash. Are you coming into the studio today?",
                                    "wrapText": True
                                }
                            },
                            {
                                "buttonList": {
                                    "buttons": [
                                        {
                                            "text": "In Studio",
                                            "onClick": {"openLink": {"url": "https://bangid.com"}}
                                        },
                                        {
                                            "text": "Working Remote",
                                            "onClick": {"openLink": {"url": "https://bangid.com"}}
                                        },
                                        {
                                            "text": "Out Sick / Leave",
                                            "onClick": {"openLink": {"url": "https://bangid.com"}}
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        }
    ]
}

req = urllib.request.Request(
    webhook_url,
    data=json.dumps(minimal_card).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    print("Clean card status:", resp.status)
