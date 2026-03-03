#!/usr/bin/env python3
"""
Generate reports.json for the index page
Scans docs/reports/ directory and creates a JSON index
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def scan_reports(reports_dir: Path) -> List[Dict]:
    """Scan reports directory and return list of reports"""
    reports = []
    
    if not reports_dir.exists():
        print(f"Reports directory does not exist: {reports_dir}")
        return reports
    
    for file in reports_dir.glob("*.html"):
        if not file.name.startswith("report_"):
            continue
        
        # Extract timestamp from filename (report_YYYYMMDD_HHMMSS.html)
        parts = file.stem.split("_")
        if len(parts) >= 3:
            date_str = parts[1]
            time_str = parts[2]
            
            try:
                date = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                display_date = date.strftime("%Y/%m/%d %H:%M")
            except ValueError:
                display_date = file.name
                date = None
        else:
            display_date = file.name
            date = None
        
        reports.append({
            "name": file.name,
            "path": f"reports/{file.name}",
            "displayDate": display_date,
            "timestamp": date.isoformat() if date else None
        })
    
    # Sort by timestamp (newest first)
    reports.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    
    return reports


def generate_json(reports: List[Dict], output_path: Path):
    """Generate reports.json file"""
    data = {
        "generatedAt": datetime.now().isoformat(),
        "totalReports": len(reports),
        "reports": reports
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {output_path} with {len(reports)} reports")


def main():
    """Main entry point"""
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    reports_dir = project_root / "docs" / "reports"
    output_path = reports_dir / "reports.json"
    
    print(f"Scanning reports in: {reports_dir}")
    
    # Scan and generate
    reports = scan_reports(reports_dir)
    generate_json(reports, output_path)
    
    print("✅ Index generation complete!")


if __name__ == "__main__":
    main()
