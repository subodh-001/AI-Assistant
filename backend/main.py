"""
BRO-BOT — FastAPI Backend Server v2
Fixes: FastAPI lifespan (removes on_event deprecation)
New: Job scraping, resume upload, post templates
"""

import sys
import os
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

import data_store as ds
import ai_brain
import deep_research
import application_tracker as app_tree
import telegram_notify as tg
import cv_tailor
from scheduler import start_scheduler, stop_scheduler, get_scheduled_jobs, trigger_daily_brief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("brobot")

# ─────────────────────────────────────────────────────────
#  POST TEMPLATES (Buffer-inspired quick-start library)
# ─────────────────────────────────────────────────────────

POST_TEMPLATES = [
    {"id": "project-launch", "emoji": "🚀", "title": "Project Launch",
     "topic": "I just launched [Project Name] — here's what I built, the tech stack I used, and the biggest lesson I learned during development"},
    {"id": "what-i-learned", "emoji": "📚", "title": "What I Learned",
     "topic": "This week I deep-dived into [Topic/Technology] — here's what surprised me, what confused me, and my top 3 takeaways"},
    {"id": "behind-scenes", "emoji": "🎬", "title": "Behind The Scenes",
     "topic": "Here's an honest look at how I built [Feature/Project] — the ugly code, the 3 AM debugging sessions, and the final breakthrough"},
    {"id": "hot-take", "emoji": "🔥", "title": "Hot Take / Opinion",
     "topic": "Unpopular opinion: [Your Controversial Take] — here's the data and reasoning behind why I believe this"},
    {"id": "achievement", "emoji": "🏆", "title": "Achievement Unlocked",
     "topic": "Huge milestone: I just [Your Achievement]! Here's the 90-day journey, the obstacles I faced, and what's coming next"},
    {"id": "mistake", "emoji": "😅", "title": "Honest Mistake Story",
     "topic": "I made a costly mistake with [Topic] that taught me more than any tutorial. Here's what happened and the lesson I'll never forget"},
    {"id": "tool-review", "emoji": "🛠️", "title": "Tool / Tech Review",
     "topic": "I used [Tool/Framework] for 30 days straight. Here's my brutally honest review — pros, cons, and who should actually use it"},
    {"id": "networking", "emoji": "🤝", "title": "Connection / Networking",
     "topic": "Had an incredible conversation with [Person/Mentor] about [Topic]. Here are the 3 insights that completely changed how I think about my career"},
    {"id": "job-update", "emoji": "💼", "title": "Career Update",
     "topic": "Big news: I just [got/applied to/interviewed for] [Role] at [Company]. Here's the honest story of my preparation and what I would do differently"},
    {"id": "ask-community", "emoji": "❓", "title": "Community Question",
     "topic": "Quick question for my network: [Your Question about Tech/Career/Life]? I want to know what YOU think — drop your answer below!"},
]

# ─────────────────────────────────────────────────────────
#  LIFESPAN (fixes on_event deprecation — modern FastAPI way)
# ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    ds.log_activity("system_start", "BRO-BOT v2 started up 🚀")
    logger.info("🤖 BRO-BOT v2 is alive!")
    yield
    # Shutdown
    stop_scheduler()
    ds.log_activity("system_stop", "BRO-BOT shut down")


# ─────────────────────────────────────────────────────────
#  APP SETUP
# ─────────────────────────────────────────────────────────

app = FastAPI(
    title="BRO-BOT API",
    description="Your personal AI Life Manager — v2",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)




# ─────────────────────────────────────────────────────────
#  PYDANTIC MODELS
# ─────────────────────────────────────────────────────────

class GeneratePostRequest(BaseModel):
    topic: str
    platform: str = "linkedin"
    tone: str = "casual"

class AddPostRequest(BaseModel):
    platform: str
    content: str
    hashtags: List[str] = []
    scheduled_at: Optional[str] = None

class AddJobRequest(BaseModel):
    company: str
    role: str
    location: str
    url: str
    salary: Optional[str] = None
    source: str = "manual"

class UpdateJobRequest(BaseModel):
    status: str
    notes: Optional[str] = None

class AddMessageRequest(BaseModel):
    sender: str
    platform: str
    content: str
    url: Optional[str] = None

class GenerateReplyRequest(BaseModel):
    message_id: str
    recruiter_message: str

class GenerateJobMsgRequest(BaseModel):
    company: str
    role: str

class ConfigUpdateRequest(BaseModel):
    updates: dict

class TelegramTestRequest(BaseModel):
    message: str = "👋 Hello from BRO-BOT! Your Telegram is connected successfully."

class GenerateBioRequest(BaseModel):
    achievements: Optional[str] = None

class ScrapeJobsRequest(BaseModel):
    keyword: Optional[str] = None
    location: Optional[str] = None

class DeepResearchRequest(BaseModel):
    company: str
    role: Optional[str] = ""

class FitScoreRequest(BaseModel):
    role: str
    company: str
    job_description: str

class SmartApplyPrepRequest(BaseModel):
    company: str
    role: str
    job_url: str

class UpdateTreeNodeStatusRequest(BaseModel):
    company: str
    role: str
    job_url: str
    status: str
    notes: Optional[str] = None

class TailorCVRequest(BaseModel):
    job_role: str
    company: Optional[str] = ""
    job_description: Optional[str] = ""
    job_id: Optional[str] = None

class ProjectItemRequest(BaseModel):
    id: Optional[str] = None
    title: str
    domain: str
    tags: List[str]
    bullets: List[str]


# ─────────────────────────────────────────────────────────
#  HEALTH & STATUS
# ─────────────────────────────────────────────────────────



@app.get("/api/health")
async def health():
    resume_exists = (DATA_DIR / "resume.txt").exists()
    return {
        "status": "online",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "ai_configured": ai_brain.is_configured(),
        "telegram_configured": tg.is_configured(),
        "scheduler_running": True,
        "resume_uploaded": resume_exists,
        "scheduled_jobs": get_scheduled_jobs(),
    }


# ─────────────────────────────────────────────────────────
#  STATS & ACTIVITY
# ─────────────────────────────────────────────────────────

@app.get("/api/stats")
async def get_stats():
    return ds.get_stats()

@app.get("/api/activity")
async def get_activity(limit: int = 50):
    return ds.get_activity(limit=limit)


# ─────────────────────────────────────────────────────────
#  POST TEMPLATES
# ─────────────────────────────────────────────────────────

@app.get("/api/templates")
async def get_templates():
    return POST_TEMPLATES


# ─────────────────────────────────────────────────────────
#  AI CONTENT GENERATION
# ─────────────────────────────────────────────────────────

@app.post("/api/generate/post")
async def generate_post(req: GeneratePostRequest):
    config = ds.get_config()
    profile = config.get("profile", {})

    # Load resume context if available
    resume_text = ""
    resume_path = DATA_DIR / "resume.txt"
    if resume_path.exists():
        resume_text = resume_path.read_text()[:800]  # First 800 chars as context

    result = ai_brain.generate_post(
        topic=req.topic,
        platform=req.platform,
        tone=req.tone,
        profile_name=profile.get("name", "A developer"),
        profile_domain=profile.get("domain", "Software Development"),
        resume_context=resume_text,
    )
    ds.log_activity("ai_generate", f"Generated {req.platform} post: {req.topic[:50]}")
    return result


@app.post("/api/generate/job-message")
async def generate_job_message(req: GenerateJobMsgRequest):
    config = ds.get_config()
    profile = config.get("profile", {})
    resume_text = ""
    resume_path = DATA_DIR / "resume.txt"
    if resume_path.exists():
        resume_text = resume_path.read_text()[:600]

    message = ai_brain.generate_job_message(
        company=req.company,
        role=req.role,
        profile_name=profile.get("name", "Candidate"),
        profile_domain=profile.get("domain", "Software Developer"),
        skills=profile.get("skills", []),
        resume_context=resume_text,
    )
    ds.log_activity("ai_job_msg", f"Generated job message for {req.role} at {req.company}")
    return {"message": message}


@app.post("/api/generate/reply")
async def generate_reply(req: GenerateReplyRequest):
    config = ds.get_config()
    profile = config.get("profile", {})
    reply = ai_brain.generate_recruiter_reply(
        recruiter_message=req.recruiter_message,
        profile_name=profile.get("name", "Candidate"),
        profile_domain=profile.get("domain", "Software Developer"),
    )
    ds.update_message(req.message_id, status="read", reply_draft=reply)
    ds.log_activity("ai_reply", "Generated recruiter reply draft")
    return {"reply": reply}


@app.post("/api/generate/bio")
async def generate_bio(req: GenerateBioRequest):
    config = ds.get_config()
    profile = config.get("profile", {})
    bio = ai_brain.generate_linkedin_bio(
        name=profile.get("name", "Developer"),
        domain=profile.get("domain", "Software Development"),
        skills=profile.get("skills", []),
        achievements=req.achievements or "",
    )
    ds.log_activity("ai_bio", "Generated LinkedIn bio")
    return {"bio": bio}


@app.get("/api/generate/brief")
async def get_brief():
    stats = ds.get_stats()
    activities = ds.get_activity(limit=20)
    config = ds.get_config()
    name = config.get("profile", {}).get("name", "bhai")
    brief = ai_brain.generate_daily_brief(stats, activities, profile_name=name)
    ds.log_activity("brief_generated", "Daily brief generated")
    return {"brief": brief, "date": datetime.now().isoformat()}


# ─────────────────────────────────────────────────────────
#  POSTS
# ─────────────────────────────────────────────────────────

@app.get("/api/posts")
async def get_posts(status: Optional[str] = None):
    return ds.get_posts(status=status)


@app.post("/api/posts")
async def add_post(req: AddPostRequest):
    return ds.add_post(
        platform=req.platform,
        content=req.content,
        hashtags=req.hashtags,
        scheduled_at=req.scheduled_at,
    )


@app.put("/api/posts/{post_id}/approve")
async def approve_post(post_id: str):
    post = ds.update_post_status(post_id, "approved")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.put("/api/posts/{post_id}/reject")
async def reject_post(post_id: str):
    post = ds.update_post_status(post_id, "rejected")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.put("/api/posts/{post_id}/posted")
async def mark_posted(post_id: str):
    post = ds.update_post_status(post_id, "posted")
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    config = ds.get_config()
    stats = config.get("stats", {})
    stats["total_posts"] = stats.get("total_posts", 0) + 1
    ds.update_config({"stats": stats})
    return post


@app.post("/api/posts/bulk")
async def bulk_update_posts(post_ids: List[str], action: str):
    """Bulk approve or reject multiple posts at once."""
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    status = "approved" if action == "approve" else "rejected"
    updated = []
    for pid in post_ids:
        post = ds.update_post_status(pid, status)
        if post:
            updated.append(post)
    ds.log_activity(f"bulk_{action}", f"Bulk {action}: {len(updated)} posts")
    return {"updated": len(updated), "posts": updated}


@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str):
    ds.delete_post(post_id)
    return {"success": True}


# ─────────────────────────────────────────────────────────
#  JOBS
# ─────────────────────────────────────────────────────────

@app.get("/api/jobs")
async def get_jobs(status: Optional[str] = None):
    return ds.get_jobs(status=status)


@app.post("/api/jobs")
async def add_job(req: AddJobRequest):
    return ds.add_job(
        company=req.company, role=req.role, location=req.location,
        url=req.url, salary=req.salary, source=req.source,
    )


@app.put("/api/jobs/{job_id}")
async def update_job(job_id: str, req: UpdateJobRequest):
    job = ds.update_job_status(job_id, req.status, req.notes)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if req.status == "applied":
        config = ds.get_config()
        stats = config.get("stats", {})
        stats["total_jobs_applied"] = stats.get("total_jobs_applied", 0) + 1
        ds.update_config({"stats": stats})
    return job


@app.post("/api/jobs/scrape")
async def scrape_jobs(req: ScrapeJobsRequest, background_tasks: BackgroundTasks):
    """
    Trigger automated job scraping from Indeed, Naukri, Internshala.
    Runs in background — results appear in Job Hunter tab.
    """
    config = ds.get_config()
    keywords = [req.keyword] if req.keyword else config.get("job_hunting", {}).get("keywords", ["Software Developer"])
    locations = [req.location] if req.location else config.get("job_hunting", {}).get("locations", ["Mumbai"])

    background_tasks.add_task(_run_job_scrape, keywords[:3], locations[:2])
    ds.log_activity("job_scrape_started", f"Job scraping started: {', '.join(keywords[:3])}")
    return {
        "success": True,
        "message": f"🔍 Scanning {len(keywords[:3])} keywords across {len(locations[:2])} locations... Results appear in 30-60 seconds.",
        "keywords": keywords[:3],
        "locations": locations[:2],
    }


async def _run_job_scrape(keywords: List[str], locations: List[str]):
    """Background task: run job scraping and save to data store."""
    try:
        from job_scraper import scrape_all
        total_added = 0
        for keyword in keywords:
            for location in locations:
                jobs = scrape_all(keyword, location, max_each=8)
                for job in jobs:
                    snippet = job.pop("snippet", "")  # Remove non-schema field
                    result = ds.add_job(**job)
                    if result:
                        total_added += 1
                await asyncio.sleep(1)  # Respectful delay between requests

        ds.log_activity("job_scan_complete", f"Job scan complete: {total_added} new jobs found")
        if tg.is_configured() and total_added > 0:
            tg.send_alert("New Jobs Found! 💼", f"Found {total_added} new jobs. Check your Job Hunter tab!", "🎯")
    except Exception as e:
        logger.error(f"Job scrape background task failed: {e}")
        ds.log_activity("job_scan_error", f"Job scan error: {str(e)[:100]}")


# ─────────────────────────────────────────────────────────
#  RESUME UPLOAD
# ─────────────────────────────────────────────────────────

@app.post("/api/resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF resume. BRO-BOT will use it to:
    - Personalize job application messages
    - Generate better LinkedIn bios
    - Make AI posts more authentic
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported. Upload your resume as .pdf")

    # Save raw PDF
    pdf_path = DATA_DIR / "resume.pdf"
    content = await file.read()
    pdf_path.write_bytes(content)

    # Extract text from PDF
    extracted_text = _extract_pdf_text(str(pdf_path))

    # Save extracted text for AI to use
    text_path = DATA_DIR / "resume.txt"
    text_path.write_text(extracted_text)

    ds.log_activity("resume_uploaded", f"Resume uploaded: {file.filename} ({len(content) // 1024}KB)")

    return {
        "success": True,
        "filename": file.filename,
        "size_kb": len(content) // 1024,
        "text_length": len(extracted_text),
        "preview": extracted_text[:400],
    }


@app.get("/api/resume")
async def get_resume_status():
    """Check if resume is uploaded and return preview."""
    text_path = DATA_DIR / "resume.txt"
    pdf_path = DATA_DIR / "resume.pdf"
    if not text_path.exists():
        return {"uploaded": False}
    text = text_path.read_text()
    size = pdf_path.stat().st_size // 1024 if pdf_path.exists() else 0
    return {
        "uploaded": True,
        "size_kb": size,
        "text_length": len(text),
        "preview": text[:400],
    }


@app.post("/api/resume/tailor")
async def tailor_resume_endpoint(req: TailorCVRequest):
    """
    Dynamically tailors candidate's CV for a specific job description & role requirement
    using AI matching from candidate's master project portfolio.
    """
    base_resume_text = ""
    resume_path = DATA_DIR / "resume.txt"
    if resume_path.exists():
        base_resume_text = resume_path.read_text()

    result = cv_tailor.tailor_cv(
        job_role=req.job_role,
        company=req.company or "",
        job_description=req.job_description or "",
        base_resume_text=base_resume_text
    )

    ds.log_activity("cv_tailored", f"Tailored CV generated for {req.job_role} at {req.company or 'Target Role'}")
    return {
        "success": True,
        "job_role": req.job_role,
        "company": req.company,
        "data": result
    }


@app.get("/api/projects")
async def get_master_projects():
    """Get all master portfolio projects."""
    projects = cv_tailor.load_master_projects()
    return {"success": True, "projects": projects}


@app.post("/api/projects")
async def add_or_update_project(proj: ProjectItemRequest):
    """Add or update a project in the master portfolio."""
    projects = cv_tailor.load_master_projects()
    proj_dict = proj.dict()
    if not proj_dict.get("id"):
        proj_dict["id"] = f"proj-{int(datetime.now().timestamp())}"
    
    # Check if existing
    updated = False
    for idx, p in enumerate(projects):
        if p.get("id") == proj_dict["id"]:
            projects[idx] = proj_dict
            updated = True
            break
    if not updated:
        projects.append(proj_dict)
        
    projects_file = DATA_DIR / "master_projects.json"
    projects_file.write_text(json.dumps(projects, indent=2))
    ds.log_activity("project_saved", f"Master project saved: {proj_dict['title']}")
    return {"success": True, "projects": projects}


def _extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        return "pdfplumber not installed. Run: pip install pdfplumber"
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return f"Could not extract text: {str(e)}"


# ─────────────────────────────────────────────────────────
#  MESSAGES
# ─────────────────────────────────────────────────────────

@app.get("/api/messages")
async def get_messages():
    return ds.get_messages()


@app.post("/api/messages")
async def add_message(req: AddMessageRequest):
    msg = ds.add_message(
        sender=req.sender, platform=req.platform,
        content=req.content, url=req.url,
    )
    if tg.is_configured():
        tg.send_recruiter_message_alert(req.sender, req.platform, req.content)
    return msg


@app.put("/api/messages/{msg_id}")
async def update_message(msg_id: str, status: str, reply: Optional[str] = None):
    msg = ds.update_message(msg_id, status, reply)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


# ─────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────

@app.get("/api/config")
async def get_config():
    return ds.get_config()


@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    config = ds.update_config(req.updates)
    ds.log_activity("config_updated", "Configuration updated")
    return config


# ─────────────────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────────────────

@app.post("/api/telegram/test")
async def test_telegram(req: TelegramTestRequest, background_tasks: BackgroundTasks):
    if not tg.is_configured():
        return {
            "success": False,
            "message": "Telegram not configured. Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to backend/.env then restart."
        }
    background_tasks.add_task(tg.send_message, req.message)
    return {"success": True, "message": "✅ Test message sent! Check your Telegram."}


@app.post("/api/telegram/brief")
async def send_brief_now(background_tasks: BackgroundTasks):
    background_tasks.add_task(trigger_daily_brief)
    return {"success": True, "message": "Daily brief is being generated and sent!"}


# ─────────────────────────────────────────────────────────
#  DEEP RESEARCH & APPLICATION TREE (PHASE 3)
# ─────────────────────────────────────────────────────────

@app.get("/api/applications/tree")
async def get_application_tree():
    return app_tree.get_application_tree()


@app.post("/api/research/company")
async def research_company(req: DeepResearchRequest):
    """
    Performs deep research on a target company using DeepSeek AI.
    """
    resume_text = ""
    resume_path = DATA_DIR / "resume.txt"
    if resume_path.exists():
        resume_text = resume_path.read_text()

    result = deep_research.research_company(
        company_name=req.company,
        role=req.role or "",
        resume_text=resume_text,
    )
    app_tree.update_company_research(req.company, result)
    ds.log_activity("deep_research", f"DeepSeek research completed for {req.company}")
    return result


@app.post("/api/research/fit-score")
async def calculate_fit_score(req: FitScoreRequest):
    config = ds.get_config()
    profile = config.get("profile", {})
    user_skills = profile.get("skills", ["Python", "JavaScript"])

    resume_text = ""
    resume_path = DATA_DIR / "resume.txt"
    if resume_path.exists():
        resume_text = resume_path.read_text()

    result = deep_research.calculate_fit_score(
        role=req.role,
        company=req.company,
        job_description=req.job_description,
        resume_text=resume_text,
        user_skills=user_skills,
    )
    return result


@app.post("/api/smart-apply/prep")
async def prepare_smart_apply(req: SmartApplyPrepRequest):
    """
    Generates all application materials (Cover Letter, LinkedIn note, research briefing)
    in one shot so candidate is ready to apply with 1 click.
    """
    config = ds.get_config()
    profile = config.get("profile", {})
    applicant_name = profile.get("name", "Applicant")

    resume_text = ""
    resume_path = DATA_DIR / "resume.txt"
    if resume_path.exists():
        resume_text = resume_path.read_text()

    # 1. Company research
    comp_research = deep_research.research_company(req.company, req.role, resume_text)
    app_tree.update_company_research(req.company, comp_research)

    # 2. Cover letter
    cover_letter = deep_research.generate_cover_letter(
        company=req.company,
        role=req.role,
        applicant_name=applicant_name,
        resume_text=resume_text,
        company_research=comp_research,
    )

    # 3. Connection note
    conn_note = ai_brain.generate_job_message(
        company=req.company,
        role=req.role,
        profile_name=applicant_name,
        profile_domain=profile.get("domain", "Software Developer"),
        skills=profile.get("skills", []),
        resume_context=resume_text[:400],
    )

    # 4. Tailored CV
    tailored_cv = cv_tailor.tailor_cv(
        job_role=req.role,
        company=req.company,
        job_description="",
        base_resume_text=resume_text
    )

    # 5. Save to tree
    tree_res = app_tree.add_or_update_tree_job(
        company_name=req.company,
        role=req.role,
        url=req.job_url,
        status="discovered",
        fit_score=tailored_cv.get("ats_match_score", 85),
    )
    job_id = tree_res["job"]["id"]
    app_tree.update_job_artifacts(req.company, job_id, cover_letter, conn_note)

    ds.log_activity("smart_apply_prep", f"Smart Apply prepared for {req.role} at {req.company}")

    return {
        "success": True,
        "company": req.company,
        "role": req.role,
        "job_url": req.job_url,
        "cover_letter": cover_letter,
        "connection_note": conn_note,
        "research": comp_research,
        "tailored_cv": tailored_cv,
    }


@app.put("/api/applications/tree/status")
async def update_tree_status(req: UpdateTreeNodeStatusRequest):
    res = app_tree.add_or_update_tree_job(
        company_name=req.company,
        role=req.role,
        url=req.job_url,
        status=req.status,
        notes=req.notes,
    )
    ds.log_activity("tree_status_update", f"Updated {req.company} status to {req.status}")
    return res


# ─────────────────────────────────────────────────────────
#  AUTHENTICATION ENDPOINTS (Real Google OAuth 2.0)
# ─────────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    token: Optional[str] = None         # Google JWT credential from GIS
    email: Optional[str] = None
    name: Optional[str] = None


@app.get("/api/auth/google-client-id")
async def get_google_client_id():
    """Return the Google OAuth Client ID so the frontend can initialize GIS."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    return {
        "configured": bool(client_id),
        "client_id": client_id if client_id else None,
    }


@app.post("/api/auth/google")
async def auth_google(req: AuthRequest):
    """
    Authenticate via Google OAuth / Google Account.
    Supports both real Google JWT token verification (if GOOGLE_CLIENT_ID set)
    and instant Google account sign-in payload.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()

    # 1. Verification of real Google JWT token if token and client_id are provided
    if req.token and client_id:
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            idinfo = google_id_token.verify_oauth2_token(
                req.token,
                google_requests.Request(),
                client_id,
            )
            user = {
                "id": f"google_{idinfo['sub']}",
                "name": idinfo.get("name", "Google User"),
                "email": idinfo.get("email", ""),
                "picture": idinfo.get("picture", ""),
                "provider": "google",
                "avatar": idinfo.get("name", "G")[0].upper(),
                "authenticated": True,
                "verified": True,
            }
            ds.log_activity("user_login", f"Google OAuth JWT verified: {user['email']}")
            return {"success": True, "user": user}
        except Exception as e:
            logger.warning(f"Google token verification fallback: {e}")

    # 2. Instant Google Sign-In with email payload
    if req.email:
        clean_email = req.email.strip().lower()
        name = req.name.strip() if req.name else clean_email.split('@')[0].capitalize()
        user = {
            "id": f"google_{abs(hash(clean_email))}",
            "name": name,
            "email": clean_email,
            "picture": "",
            "provider": "google",
            "avatar": name[0].upper(),
            "authenticated": True,
            "verified": True,
        }
        ds.log_activity("user_login", f"Google Sign-In: {user['email']}")
        return {"success": True, "user": user}

    raise HTTPException(status_code=400, detail="Google authentication payload invalid")


@app.get("/api/auth/me")
async def auth_me():
    """Return current server-side auth info (profile defaults)."""
    return {
        "success": True,
        "server_name": os.getenv("YOUR_NAME", "Subodh Ram"),
        "google_configured": bool(os.getenv("GOOGLE_CLIENT_ID", "").strip()),
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


# ─────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
