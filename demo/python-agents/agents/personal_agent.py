"""
BangOps Personal Agent
Represents an individual team member's private assistant.
- Reads personal profile & working style (soul.md)
- Inspects local files & resource sheets for tasks and deadlines
- Generates proactive daily morning reminders
- Communicates upward with the HR / Operations Agent when studio events occur (leave, blockers, credit logs)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from agents.file_inspector import FileInspector
from agents.hr_agent import HRAgent

class PersonalAgent:
    def __init__(self, employee_id: str = "akash.p@bangid.com", hr_agent: Optional[HRAgent] = None):
        self.employee_id = employee_id
        self.inspector = FileInspector()
        self.hr_agent = hr_agent or HRAgent()
        
        # Load profile
        self.profile = self.inspector.read_employee_profile()
        self.employee_name = self.profile.get("FullName", "Akash Pai")
        self.role = self.profile.get("Role", "Designer")
        
        # Persona constraints
        self.peak_hours = "10:00 - 14:00"
        self.nudge_budget_remaining = 2

    def check_daily_tasks(self) -> List[Dict[str, Any]]:
        """Reads the employee's local Excel Resource Sheet to fetch current tasks."""
        try:
            tasks = self.inspector.read_resource_sheet_tasks("samples/Resource_Akash_Pai.xlsx")
            return tasks
        except Exception as e:
            print(f"[PersonalAgent] Warning: Could not read resource sheet: {e}")
            return []

    def generate_morning_reminder(self) -> Dict[str, Any]:
        """
        Creates a proactive morning check-in and task reminder card.
        Strict rule: Maximum 2 nudges per day, no small talk.
        """
        tasks = self.check_daily_tasks()
        
        task_bullets = []
        for t in tasks:
            client = t.get("Client", "Studio")
            title = t.get("Title", "Untitled Task")
            status = t.get("Status", "Active")
            priority = t.get("Priority", "Normal")
            priority_mark = "[PRIORITY] " if priority == "Priority" else ""
            task_bullets.append(f"{priority_mark}[{client}] {title} ({status})")

        reminder_text = (
            f"Good morning, {self.employee_name.split()[0]}! Here is your focus list for today:\n\n"
            + ("\n".join(task_bullets) if task_bullets else "No active tasks flagged for today.")
        )

        reminder_card = {
            "title": f"Morning Focus • {self.employee_name}",
            "subtitle": f"{self.role} • Bang Design",
            "body": reminder_text,
            "tasks_count": len(tasks),
            "quick_actions": [
                {"label": "[OK] Feeling Good (Start Day)", "action": "CONFIRM_ATTENDANCE"},
                {"label": "[SICK] Sick Today (Take Leave)", "action": "REPORT_SICK_LEAVE"},
                {"label": "[LOG] Log Credits", "action": "OPEN_CREDIT_LOG"}
            ]
        }
        
        self.nudge_budget_remaining -= 1
        return reminder_card

    def report_sick_leave(self, notes: str = "Unwell / taking rest today") -> Dict[str, Any]:
        """
        Reports sick leave on behalf of the employee.
        Communicates directly with the HR / Operations Agent.
        """
        leave_event = {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "leave_type": "sick",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "notes": notes
        }

        # Inter-agent communication: Personal Agent -> HR Agent
        print(f"\n[PersonalAgent] -> Communicating with HRAgent for {self.employee_name}...")
        hr_response = self.hr_agent.process_leave_event(leave_event)

        acknowledgment = {
            "status": "confirmed",
            "personal_message": (
                f"Take care, {self.employee_name.split()[0]}! I have logged your sick leave for today.\n"
                f"I notified the HR Agent, and your active project coverage was automatically routed to your sub-owners."
            ),
            "hr_details": hr_response
        }
        return acknowledgment


if __name__ == "__main__":
    agent = PersonalAgent()
    print("=== MORNING REMINDER ===")
    reminder = agent.generate_morning_reminder()
    print(reminder["body"])
    print("\n=== REPORTING SICK LEAVE ===")
    ack = agent.report_sick_leave("High fever")
    print(ack["personal_message"])
    print("\nFailover Reassignments triggered by HR:")
    for r in ack["hr_details"]["reassignments"]:
        print(f" - {r['project_name']}: Covered by {r['temp_lead']}")
