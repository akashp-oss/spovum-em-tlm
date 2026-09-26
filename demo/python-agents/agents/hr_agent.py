"""
BangOps HR & Operations Agent
Responsible for studio-wide operational state:
- Attendance & leave tracking
- Sub-owner sickness failover & project coverage
- Studio broadcast notifications (Google Chat Card v2 / Telegram)
- Coordinating with individual Personal Agents
"""

import json
import os
import urllib.request
from typing import Dict, Any, List, Optional
from datetime import datetime

class HRAgent:
    def __init__(self, webhook_url: Optional[str] = None):
        # Default to Bang Design studio webhook if not provided
        self.webhook_url = webhook_url or os.environ.get("BANGOPS_CHAT_WEBHOOK", "")
        
        # In-memory studio state (in production, backed by Postgres / Supabase)
        self.attendance_records: List[Dict[str, Any]] = []
        self.active_projects: Dict[str, Dict[str, Any]] = {
            "P-102": {
                "name": "Nexa Mobile Architecture",
                "client": "Nexa",
                "owner_id": "akash.p@bangid.com",
                "owner_name": "Akash Pai",
                "sub_owner_id": "rahul.m@bangid.com",
                "sub_owner_name": "Rahul M",
                "status": "active",
                "deadline": "2026-09-30"
            },
            "P-117": {
                "name": "Z_Marketing Inbound SEO",
                "client": "Z_Marketing",
                "owner_id": "akash.p@bangid.com",
                "owner_name": "Akash Pai",
                "sub_owner_id": "design.lead@bangid.com",
                "sub_owner_name": "Design Lead",
                "status": "active",
                "deadline": "2026-10-05"
            }
        }

    def process_leave_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a leave or sickness event sent from a Personal Agent.
        Triggers automatic sub-owner failover for any active projects.
        """
        employee_id = event.get("employee_id")
        employee_name = event.get("employee_name", employee_id)
        leave_type = event.get("leave_type", "sick")
        date_str = event.get("date", datetime.now().strftime("%Y-%m-%d"))
        notes = event.get("notes", "")

        record = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "leave_type": leave_type,
            "date": date_str,
            "notes": notes,
            "logged_at": datetime.now().isoformat()
        }
        self.attendance_records.append(record)

        # Identify impacted projects
        impacted_projects = []
        reassignments = []
        for p_id, p_info in self.active_projects.items():
            if p_info.get("owner_id") == employee_id and p_info.get("status") == "active":
                impacted_projects.append(p_info)
                reassignments.append({
                    "project_id": p_id,
                    "project_name": p_info["name"],
                    "client": p_info["client"],
                    "temp_lead": p_info["sub_owner_name"],
                    "temp_lead_email": p_info["sub_owner_id"]
                })

        failover_summary = {
            "status": "success",
            "message": f"Leave recorded for {employee_name} ({leave_type.capitalize()}).",
            "attendance_record": record,
            "impacted_projects_count": len(impacted_projects),
            "reassignments": reassignments
        }

        # Build notification card
        card_payload = self.build_leave_failover_card(record, reassignments)
        failover_summary["card_payload"] = card_payload
        
        return failover_summary

    def build_leave_failover_card(self, record: Dict[str, Any], reassignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates Google Chat Card v2 for studio attendance and failover."""
        employee_name = record["employee_name"]
        leave_type = record["leave_type"].capitalize()

        reassignment_widgets = []
        for r in reassignments:
            reassignment_widgets.append({
                "decoratedText": {
                    "startIcon": {"knownIcon": "MEMBERSHIP"},
                    "topLabel": f"Project: {r['project_name']} ({r['client']})",
                    "text": f"<b>Assigned to Sub-Owner:</b> {r['temp_lead']}",
                    "bottomLabel": "Status: Temporary Coverage Active",
                    "wrapText": True
                }
            })

        if not reassignment_widgets:
            reassignment_widgets.append({
                "decoratedText": {
                    "topLabel": "Project Coverage",
                    "text": "No critical project milestones impacted today.",
                    "wrapText": True
                }
            })

        card = {
            "cardsV2": [
                {
                    "cardId": f"leave_failover_{record['employee_id']}",
                    "card": {
                        "header": {
                            "title": "BangOps Studio Attendance & Failover",
                            "subtitle": f"{employee_name} • {leave_type} Leave",
                            "imageUrl": "https://bangid.com/wp-content/uploads/2025/03/Bang-ID-Logo.png",
                            "imageType": "CIRCLE"
                        },
                        "sections": [
                            {
                                "header": "Attendance Notice",
                                "widgets": [
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "PERSON"},
                                            "topLabel": "Status Update",
                                            "text": f"<b>{employee_name}</b> is on {leave_type} leave today ({record['date']}).",
                                            "bottomLabel": f"Reason: {record['notes'] or 'Not specified'}",
                                            "wrapText": True
                                        }
                                    }
                                ]
                            },
                            {
                                "header": "Autonomous Project Reassignments",
                                "widgets": reassignment_widgets
                            }
                        ]
                    }
                }
            ]
        }
        return card

    def broadcast_to_chat(self, payload: Dict[str, Any]) -> bool:
        """Sends the card payload to the Google Chat space."""
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 201)
        except Exception as e:
            print(f"[HRAgent] Failed to broadcast to chat webhook: {e}")
            return False


if __name__ == "__main__":
    hr = HRAgent()
    demo_event = {
        "employee_id": "akash.p@bangid.com",
        "employee_name": "Akash Pai",
        "leave_type": "sick",
        "date": "2026-09-24",
        "notes": "Mild fever & headache, resting today"
    }
    result = hr.process_leave_event(demo_event)
    print("HR Processing Result:")
    print(json.dumps(result, indent=2))
