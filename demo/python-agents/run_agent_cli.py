"""
BangOps Agent System CLI
Interactive command-line tool to run Personal Agent and HR Agent workflows.

Usage:
  python run_agent_cli.py morning            # Run morning check-in & task reminder
  python run_agent_cli.py tasks              # Inspect local Resource Sheet tasks
  python run_agent_cli.py files              # List and inspect local files
  python run_agent_cli.py sick "<reason>"    # Report sick leave & trigger HR failover
  python run_agent_cli.py demo               # Run end-to-end full walkthrough
"""

import sys
from agents.agent_coordinator import AgentCoordinator

def main():
    coordinator = AgentCoordinator()
    
    if len(sys.argv) < 2 or sys.argv[1] == "demo":
        coordinator.inspect_vendor_database()
        coordinator.run_morning_briefing()
        coordinator.simulate_sick_leave_scenario("Seasonal viral fever")
        return

    cmd = sys.argv[1].lower()

    if cmd == "morning":
        coordinator.run_morning_briefing()
    elif cmd == "tasks":
        tasks = coordinator.personal_agent.check_daily_tasks()
        print(f"\nFound {len(tasks)} tasks in your local Resource Sheet:")
        for idx, t in enumerate(tasks, 1):
            p_tag = " [PRIORITY]" if t.get("Priority") == "Priority" else ""
            print(f" {idx}. [{t.get('Client')}] {t.get('Title')}{p_tag} - Status: {t.get('Status')}")
    elif cmd == "files":
        coordinator.inspect_vendor_database()
    elif cmd == "sick":
        reason = sys.argv[2] if len(sys.argv) > 2 else "Unwell today"
        coordinator.simulate_sick_leave_scenario(reason)
    else:
        print(f"Unknown command '{cmd}'. Available: morning, tasks, files, sick, demo")

if __name__ == "__main__":
    main()
