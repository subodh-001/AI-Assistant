"""
BRO-BOT — Data Store
Simple JSON-based storage layer. No database needed.
"""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "data"
BASE_DIR.mkdir(exist_ok=True)

FILES = {
    "posts": BASE_DIR / "posts.json",
    "jobs": BASE_DIR / "jobs.json",
    "messages": BASE_DIR / "messages.json",
    "config": BASE_DIR / "config.json",
    "activity": BASE_DIR / "activity.json",
}


def _read(key: str):
    path = FILES[key]
    if not path.exists():
        return [] if key != "config" else {}
    with open(path, "r") as f:
        return json.load(f)


def _write(key: str, data):
    with open(FILES[key], "w") as f:
        json.dump(data, f, indent=2, default=str)


# ─────────────────────── POSTS ───────────────────────

def get_posts(status: str = None):
    posts = _read("posts")
    if status:
        return [p for p in posts if p.get("status") == status]
    return sorted(posts, key=lambda x: x.get("created_at", ""), reverse=True)


def add_post(platform: str, content: str, hashtags: list, scheduled_at: str = None):
    posts = _read("posts")
    post = {
        "id": str(uuid.uuid4()),
        "platform": platform,
        "content": content,
        "hashtags": hashtags,
        "status": "pending",  # pending | approved | rejected | posted
        "scheduled_at": scheduled_at,
        "created_at": datetime.now().isoformat(),
        "posted_at": None,
    }
    posts.append(post)
    _write("posts", posts)
    log_activity("post_created", f"New {platform} post created", {"post_id": post["id"]})
    return post


def update_post_status(post_id: str, status: str):
    posts = _read("posts")
    for p in posts:
        if p["id"] == post_id:
            p["status"] = status
            if status == "posted":
                p["posted_at"] = datetime.now().isoformat()
            _write("posts", posts)
            log_activity("post_" + status, f"Post {status}", {"post_id": post_id})
            return p
    return None


def delete_post(post_id: str):
    posts = _read("posts")
    posts = [p for p in posts if p["id"] != post_id]
    _write("posts", posts)


# ─────────────────────── JOBS ───────────────────────

def get_jobs(status: str = None):
    jobs = _read("jobs")
    if status:
        return [j for j in jobs if j.get("status") == status]
    return sorted(jobs, key=lambda x: x.get("found_at", ""), reverse=True)


def add_job(company: str, role: str, location: str, url: str, salary: str = None, source: str = "manual", posted_at: str = "Just now", applicants_count: str = "Be an Early Applicant", competition_level: str = "low"):
    jobs = _read("jobs")
    # Check if already exists
    for j in jobs:
        if j.get("url") == url:
            return j  # already tracked
    job = {
        "id": str(uuid.uuid4()),
        "company": company,
        "role": role,
        "location": location,
        "salary": salary,
        "url": url,
        "source": source,
        "posted_at": posted_at,
        "applicants_count": applicants_count,
        "competition_level": competition_level,
        "status": "new",  # new | saved | applied | rejected | interview
        "found_at": datetime.now().isoformat(),
        "applied_at": None,
        "notes": "",
    }
    jobs.append(job)
    _write("jobs", jobs)
    log_activity("job_found", f"New job: {role} at {company}", {"job_id": job["id"]})
    return job


def update_job_status(job_id: str, status: str, notes: str = None):
    jobs = _read("jobs")
    for j in jobs:
        if j["id"] == job_id:
            j["status"] = status
            if status == "applied":
                j["applied_at"] = datetime.now().isoformat()
            if notes:
                j["notes"] = notes
            _write("jobs", jobs)
            log_activity("job_" + status, f"Job {status}", {"job_id": job_id})
            return j
    return None


# ─────────────────────── MESSAGES ───────────────────────

def get_messages():
    return _read("messages")


def add_message(sender: str, platform: str, content: str, url: str = None):
    messages = _read("messages")
    msg = {
        "id": str(uuid.uuid4()),
        "sender": sender,
        "platform": platform,
        "content": content,
        "url": url,
        "status": "unread",  # unread | read | replied | ignored
        "received_at": datetime.now().isoformat(),
        "replied_at": None,
        "reply_draft": None,
    }
    messages.append(msg)
    _write("messages", messages)
    log_activity("message_received", f"New message from {sender} on {platform}", {"msg_id": msg["id"]})
    return msg


def update_message(msg_id: str, status: str, reply_draft: str = None):
    messages = _read("messages")
    for m in messages:
        if m["id"] == msg_id:
            m["status"] = status
            if reply_draft:
                m["reply_draft"] = reply_draft
            if status == "replied":
                m["replied_at"] = datetime.now().isoformat()
            _write("messages", messages)
            return m
    return None


# ─────────────────────── CONFIG ───────────────────────

def get_config():
    return _read("config")


def update_config(updates: dict):
    config = _read("config")
    # Deep merge
    def deep_merge(base, new):
        for k, v in new.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                deep_merge(base[k], v)
            else:
                base[k] = v
        return base
    config = deep_merge(config, updates)
    _write("config", config)
    return config


# ─────────────────────── ACTIVITY LOG ───────────────────────

def log_activity(event_type: str, description: str, meta: dict = None):
    path = FILES["activity"]
    if not path.exists():
        activities = []
    else:
        with open(path, "r") as f:
            activities = json.load(f)
    
    activities.append({
        "id": str(uuid.uuid4()),
        "type": event_type,
        "description": description,
        "meta": meta or {},
        "timestamp": datetime.now().isoformat(),
    })
    # Keep only last 200 entries
    activities = activities[-200:]
    with open(path, "w") as f:
        json.dump(activities, f, indent=2, default=str)


def get_activity(limit: int = 50):
    path = FILES["activity"]
    if not path.exists():
        return []
    with open(path, "r") as f:
        activities = json.load(f)
    return list(reversed(activities[-limit:]))


# ─────────────────────── STATS ───────────────────────

def get_stats():
    posts = _read("posts")
    jobs = _read("jobs")
    messages = _read("messages")
    config = _read("config")
    
    return {
        "posts": {
            "total": len(posts),
            "pending": len([p for p in posts if p["status"] == "pending"]),
            "approved": len([p for p in posts if p["status"] == "approved"]),
            "posted": len([p for p in posts if p["status"] == "posted"]),
        },
        "jobs": {
            "total": len(jobs),
            "new": len([j for j in jobs if j["status"] == "new"]),
            "applied": len([j for j in jobs if j["status"] == "applied"]),
            "interview": len([j for j in jobs if j["status"] == "interview"]),
        },
        "messages": {
            "total": len(messages),
            "unread": len([m for m in messages if m["status"] == "unread"]),
            "replied": len([m for m in messages if m["status"] == "replied"]),
        },
        "profile": config.get("profile", {}),
        "platforms_connected": len([
            p for p in config.get("posting", {}).get("platforms_enabled", [])
        ]),
    }
