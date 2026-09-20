"""
BRO-BOT — Application Tree Tracker
Manages structured company -> job application tree data in data/applications.json.
Provides full branch visualization data and timeline history.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
APPS_FILE = DATA_DIR / "applications.json"

logger = logging.getLogger(__name__)


def _load_apps() -> Dict[str, Any]:
    if not APPS_FILE.exists():
        initial = {"companies": {}}
        APPS_FILE.write_text(json.dumps(initial, indent=2))
        return initial
    try:
        return json.loads(APPS_FILE.read_text())
    except Exception as e:
        logger.error(f"Error loading applications.json: {e}")
        return {"companies": {}}


def _save_apps(data: Dict[str, Any]) -> None:
    APPS_FILE.write_text(json.dumps(data, indent=2))


def get_application_tree() -> Dict[str, Any]:
    """Returns full hierarchical tree of Companies -> Jobs -> Application Timeline."""
    return _load_apps()


def add_or_update_tree_job(
    company_name: str,
    role: str,
    url: str,
    location: str = "India",
    portal: str = "LinkedIn",
    salary: Optional[str] = None,
    status: str = "discovered",
    fit_score: int = 75,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Adds a job under its company branch in the application tree.
    Updates status & appends to timeline history.
    """
    data = _load_apps()
    companies = data.setdefault("companies", {})
    
    # Normalize company key
    comp_key = company_name.strip()
    company_node = companies.setdefault(comp_key, {
        "name": comp_key,
        "research": None,
        "jobs": []
    })

    # Search for existing job by URL or Role
    existing_job = None
    for job in company_node["jobs"]:
        if job.get("url") == url or (job.get("role").lower() == role.lower() and job.get("portal") == portal):
            existing_job = job
            break

    now_iso = datetime.now().isoformat()

    if existing_job:
        if existing_job["status"] != status:
            existing_job["status"] = status
            existing_job.setdefault("timeline", []).append({
                "status": status,
                "timestamp": now_iso,
                "notes": notes or f"Status changed to {status}"
            })
        if salary:
            existing_job["salary"] = salary
        if fit_score:
            existing_job["fit_score"] = fit_score
        target_job = existing_job
    else:
        job_id = f"app_{int(datetime.now().timestamp() * 1000)}"
        target_job = {
            "id": job_id,
            "role": role,
            "portal": portal,
            "url": url,
            "location": location,
            "salary": salary,
            "status": status,
            "fit_score": fit_score,
            "created_at": now_iso,
            "timeline": [
                {
                    "status": status,
                    "timestamp": now_iso,
                    "notes": notes or f"Discovered on {portal}"
                }
            ],
            "cover_letter": None,
            "connection_note": None
        }
        company_node["jobs"].append(target_job)

    _save_apps(data)
    return {"company": comp_key, "job": target_job}


def update_company_research(company_name: str, research_data: Dict[str, Any]) -> None:
    data = _load_apps()
    comp_key = company_name.strip()
    if comp_key in data.get("companies", {}):
        data["companies"][comp_key]["research"] = research_data
        _save_apps(data)


def update_job_artifacts(
    company_name: str,
    job_id: str,
    cover_letter: Optional[str] = None,
    connection_note: Optional[str] = None
) -> None:
    data = _load_apps()
    comp_key = company_name.strip()
    comp = data.get("companies", {}).get(comp_key)
    if comp:
        for job in comp.get("jobs", []):
            if job["id"] == job_id:
                if cover_letter:
                    job["cover_letter"] = cover_letter
                if connection_note:
                    job["connection_note"] = connection_note
                _save_apps(data)
                break
