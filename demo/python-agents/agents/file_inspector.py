"""
BangOps Local & Cloud File Inspector
Provides standardized file inspection tools following Model Context Protocol (MCP) conventions.
Capable of reading local Excel resource sheets, vendor comparison sheets, project markdown, and synced cloud files.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import openpyxl

class FileInspector:
    def __init__(self, workspace_root: Optional[str] = None):
        if workspace_root is None:
            # Default to the BangOps repo root (demo/python-agents/agents -> repo root)
            self.workspace_root = Path(__file__).resolve().parents[3]
        else:
            self.workspace_root = Path(workspace_root)

    def list_files(self, sub_dir: str = "", pattern: str = "*") -> List[Dict[str, Any]]:
        """List files in a directory with metadata."""
        target_dir = self.workspace_root / sub_dir
        if not target_dir.exists():
            return []
        
        results = []
        for p in target_dir.glob(pattern):
            if p.is_file():
                results.append({
                    "name": p.name,
                    "rel_path": str(p.relative_to(self.workspace_root)),
                    "size_bytes": p.stat().st_size,
                    "suffix": p.suffix.lower()
                })
        return results

    def read_text_file(self, rel_path: str) -> str:
        """Read a text, markdown, or code file."""
        file_path = self.workspace_root / rel_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text(encoding="utf-8", errors="ignore")

    def read_resource_sheet_tasks(self, rel_path: str = "samples/Resource_Akash_Pai.xlsx") -> List[Dict[str, Any]]:
        """
        Parses task items from an employee's Resource Excel spreadsheet.
        Reads columns: Date, Client, Project, Title, Description, Status, Priority.
        """
        file_path = self.workspace_root / rel_path
        if not file_path.exists():
            raise FileNotFoundError(f"Resource sheet not found: {file_path}")

        wb = openpyxl.load_workbook(file_path, data_only=True)
        tasks = []
        
        if "Tasks" in wb.sheetnames:
            sheet = wb["Tasks"]
            headers = [cell.value for cell in sheet[1]]
            
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(row):
                    task_dict = {}
                    for h, val in zip(headers, row):
                        if h:
                            if hasattr(val, "strftime"):
                                task_dict[str(h)] = val.strftime("%Y-%m-%d")
                            else:
                                task_dict[str(h)] = val
                    tasks.append(task_dict)
        return tasks

    def read_employee_profile(self, rel_path: str = "samples/Resource_Akash_Pai.xlsx") -> Dict[str, Any]:
        """Extracts core profile details from the Resource Info sheet."""
        file_path = self.workspace_root / rel_path
        if not file_path.exists():
            return {}

        wb = openpyxl.load_workbook(file_path, data_only=True)
        profile = {}
        if "Resource Info" in wb.sheetnames:
            sheet = wb["Resource Info"]
            for row in sheet.iter_rows(min_row=1, max_col=2, values_only=True):
                if row[0] and row[1]:
                    val = row[1]
                    if hasattr(val, "strftime"):
                        val = val.strftime("%Y-%m-%d")
                    profile[str(row[0])] = val
        return profile


if __name__ == "__main__":
    inspector = FileInspector()
    print("Files found in samples/:", inspector.list_files("samples"))
    print("\nEmployee Profile:")
    print(inspector.read_employee_profile())
    print("\nTasks found:")
    tasks = inspector.read_resource_sheet_tasks()
    for t in tasks[:5]:
        print(" -", t.get("Client"), "|", t.get("Title"), f"[{t.get('Status')}]")
