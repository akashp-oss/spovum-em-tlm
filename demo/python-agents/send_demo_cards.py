import urllib.request
import json
import os
import sys

webhook_url = os.environ.get("BANGOPS_CHAT_WEBHOOK", "")

def send_card(payload):
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status

vendor_payload = {
    "cardsV2": [
        {
            "cardId": "vendor_intel_demo",
            "card": {
                "header": {
                    "title": "BangOps Vendor Intelligence",
                    "subtitle": "3D Printing • SLA ABS Benchmark",
                    "imageUrl": "https://bangid.com/wp-content/uploads/2025/03/Bang-ID-Logo.png",
                    "imageType": "CIRCLE"
                },
                "sections": [
                    {
                        "header": "Top Recommended Supplier",
                        "widgets": [
                            {
                                "decoratedText": {
                                    "topLabel": "1st Choice (Best Price + Quality)",
                                    "text": "<b>Design Roots</b> (Bangalore)",
                                    "bottomLabel": "Quality: ★★★★☆ (4.5) • Turnaround: 3–4 Days",
                                    "wrapText": True
                                }
                            },
                            {
                                "decoratedText": {
                                    "topLabel": "Total Quote (Set of 1, incl. 18% GST)",
                                    "text": "<b>₹53,277</b> (Cheapest in Quote Comparison)",
                                    "wrapText": True
                                }
                            },
                            {
                                "decoratedText": {
                                    "startIcon": {"knownIcon": "CONFIRMATION_NUMBER_ICON"},
                                    "topLabel": "Cost Driver Warning",
                                    "text": "<b>⚠️ Spread Alert:</b> BOTAAT priced the front door panel at <b>₹81,240</b> (2x Design Roots ₹37,940). Avoid BOTAAT for large enclosure parts.",
                                    "wrapText": True
                                }
                            },
                            {
                                "buttonList": {
                                    "buttons": [
                                        {
                                            "text": "📁 Open Quote Doc",
                                            "onClick": {"openLink": {"url": "https://bangid.com/plans/"}}
                                        },
                                        {
                                            "text": "✉️ Draft RFQ Email",
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

if __name__ == "__main__":
    status = send_card(vendor_payload)
    print(f"Vendor Card Sent successfully with HTTP {status}")
