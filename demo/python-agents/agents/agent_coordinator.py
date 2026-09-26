"""
BangOps Agent Coordinator
Orchestrates multi-agent communication between:
1. FileInspector (Local & Cloud Filesystem MCP layer)
2. PersonalAgent (User-facing task assistant & daily reminder loop)
3. HRAgent (Studio-wide attendance, project health & failover)
"""

import json
from typing import Dict, Any, Optional
from agents.file_inspector import FileInspector
from agents.personal_agent import PersonalAgent
from agents.hr_agent import HRAgent

class AgentCoordinator:
    def __init__(self, employee_id: str = "akash.p@bangid.com", chat_webhook: Optional[str] = None):
        self.inspector = FileInspector()
        self.hr_agent = HRAgent(webhook_url=chat_webhook)
        self.personal_agent = PersonalAgent(employee_id=employee_id, hr_agent=self.hr_agent)

    def run_morning_briefing(self) -> Dict[str, Any]:
        """Triggers the morning task check-in flow."""
        print("\n==========================================")
        print("  BANGOPS: RUNNING MORNING TASK BRIEFING  ")
        print("==========================================")
        reminder = self.personal_agent.generate_morning_reminder()
        print(reminder["body"])
        print("\nAvailable User Actions:")
        for act in reminder["quick_actions"]:
            print(f"  [Button] {act['label']}")
        return reminder

    def simulate_sick_leave_scenario(self, reason: str = "High fever & headache") -> Dict[str, Any]:
        """
        Simulates employee reporting sick leave.
        Demonstrates PersonalAgent -> HRAgent autonomous coordination.
        """
        print("\n==========================================")
        print("  BANGOPS: SICK LEAVE & FAILOVER SCENARIO ")
        print("==========================================")
        print(f"Employee Action: Reporting sick leave ('{reason}')")
        
        result = self.personal_agent.report_sick_leave(notes=reason)
        print("\nPersonal Agent Response to Employee:")
        print(f"  \"{result['personal_message']}\"")
        
        print("\nHR Agent Autonomous Actions:")
        hr_data = result["hr_details"]
        print(f"  - Attendance Record Saved: {hr_data['attendance_record']['employee_name']} ({hr_data['attendance_record']['leave_type']})")
        print(f"  - Active Projects Impacted: {hr_data['impacted_projects_count']}")
        for reassignment in hr_data["reassignments"]:
            print(f"    * {reassignment['project_name']} ({reassignment['client']}) -> Covered by: {reassignment['temp_lead']}")
        
        return result

    def inspect_vendor_database(self) -> Dict[str, Any]:
        """Uses FileInspector to check local vendor comparison files."""
        print("\n==========================================")
        print("  BANGOPS: LOCAL FILE VENDOR INSPECTION   ")
        print("==========================================")
        files = self.inspector.list_files("samples")
        print(f"Found {len(files)} files in samples directory:")
        for f in files:
            print(f"  - {f['name']} ({f['size_bytes']} bytes)")
        return {"files": files}


if __name__ == "__main__":
    coordinator = AgentCoordinator()
    
    # 1. Inspect files
    coordinator.inspect_vendor_database()
    
    # 2. Run morning briefing
    coordinator.run_morning_briefing()
    
    # 3. Simulate sick leave & HR failover
    coordinator.simulate_sick_leave_scenario()
