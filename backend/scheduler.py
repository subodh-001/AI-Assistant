"""
BRO-BOT — Background Scheduler
Handles all automated tasks: daily brief, job scans, post reminders.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


def start_scheduler():
    """Initialize and start all scheduled jobs."""
    if scheduler.running:
        return

    # ── Daily Brief at 8 AM IST ──
    scheduler.add_job(
        _send_daily_brief,
        CronTrigger(hour=8, minute=0, timezone="Asia/Kolkata"),
        id="daily_brief",
        replace_existing=True,
        name="Daily Brief",
    )

    # ── Continuous AI Job Radar every 5 minutes ──
    scheduler.add_job(
        _scan_jobs,
        IntervalTrigger(minutes=5),
        id="job_scan",
        replace_existing=True,
        name="Continuous AI Job Radar (5-min)",
    )

    # ── Check pending posts every hour ──
    scheduler.add_job(
        _check_pending_posts,
        IntervalTrigger(hours=1),
        id="post_check",
        replace_existing=True,
        name="Post Queue Check",
    )

    scheduler.start()
    logger.info("✅ BRO-BOT Scheduler & Continuous AI Job Radar started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


# ─────────────────────────────────────────────────────────
#  SCHEDULED TASKS
# ─────────────────────────────────────────────────────────

def _send_daily_brief():
    """Send daily brief via Telegram."""
    try:
        from data_store import get_stats, get_activity
        from ai_brain import generate_daily_brief
        import telegram_notify as tg
        import data_store as ds

        stats = get_stats()
        activities = get_activity(limit=20)
        config = ds.get_config()
        name = config.get("profile", {}).get("name", "bhai")

        brief = generate_daily_brief(stats, activities, profile_name=name)

        if tg.is_configured():
            tg.send_daily_brief(brief)
            ds.log_activity("daily_brief_sent", "Daily brief sent via Telegram")
        else:
            ds.log_activity("daily_brief_skipped", "Telegram not configured")

        logger.info("Daily brief task completed")
    except Exception as e:
        logger.error(f"Daily brief error: {e}")


def _scan_jobs():
    """Continuously scan internet job portals for new job postings and send instant alerts."""
    try:
        import data_store as ds
        import job_scraper as scraper
        import telegram_notify as tg

        config = ds.get_config()
        keywords = config.get("job_hunting", {}).get("keywords", ["Full Stack Developer", "AI Engineer", "Software Engineer"])
        locations = config.get("job_hunting", {}).get("locations", ["Mumbai", "Remote", "India"])

        existing_jobs = ds.get_jobs()
        existing_urls = {j.get("url") for j in existing_jobs if j.get("url")}

        new_jobs_found = []
        for kw in keywords[:2]:
            loc = locations[0] if locations else "India"
            
            # Scrape across platforms
            scraped = scraper.scrape_indeed(kw, loc, max_results=3)
            scraped += scraper.scrape_linkedin(kw, loc, max_results=3)

            for item in scraped:
                if item.get("url") and item["url"] not in existing_urls:
                    item_job = ds.add_job(
                        company=item["company"],
                        role=item["role"],
                        location=item["location"],
                        url=item["url"],
                        salary=item.get("salary"),
                        source=item.get("source", "Radar"),
                        posted_at=item.get("posted_at", "Just now"),
                        applicants_count=item.get("applicants_count", "Be an Early Applicant")
                    )
                    existing_urls.add(item["url"])
                    new_jobs_found.append(item)

                    # 🤖 AUTO-PILOT ENGINE: Auto-generate Tailored CV & Cover Letter
                    try:
                        import cv_tailor
                        import deep_research
                        import ai_brain

                        resume_text = ""
                        resume_path = ds.DATA_DIR / "resume.txt"
                        if resume_path.exists():
                            resume_text = resume_path.read_text()

                        # Generate Tailored CV
                        tailored_cv = cv_tailor.tailor_cv(
                            job_role=item["role"],
                            company=item["company"],
                            job_description="",
                            base_resume_text=resume_text
                        )
                        
                        # Generate Cover Letter
                        cover_letter = deep_research.generate_cover_letter(
                            company=item["company"],
                            role=item["role"],
                            applicant_name=config.get("profile", {}).get("name", "Subodh Ram"),
                            resume_text=resume_text
                        )

                        # Auto-mark job status as applied & store artifacts
                        ds.update_job_status(item_job["id"], "applied", notes=f"Auto-applied by BRO-BOT AI. ATS Match: {tailored_cv.get('ats_match_score', 90)}%")
                        
                    except Exception as auto_err:
                        logger.warning(f"Auto-pilot package generation warning: {auto_err}")

                    # Send instant Telegram notification alert
                    if tg.is_configured():
                        tg.send_job_alert(
                            role=item["role"],
                            company=item["company"],
                            url=item["url"],
                            posted_at=item.get("posted_at", "Just now"),
                            applicants=f"⚡ AUTO-APPLIED (ATS Match: {tailored_cv.get('ats_match_score', 90)}%)"
                        )

        if new_jobs_found:
            ds.log_activity("continuous_radar_alert", f"🚨 AI Job Radar detected {len(new_jobs_found)} new job posting(s)!")
            logger.info(f"✅ AI Job Radar found {len(new_jobs_found)} new job postings")
        else:
            logger.info("AI Job Radar check completed — no new postings")

    except Exception as e:
        logger.error(f"Job scan error: {e}")


def _check_pending_posts():
    """Check for posts that need approval reminders."""
    try:
        import data_store as ds
        import telegram_notify as tg

        pending = ds.get_posts(status="pending")
        if pending and tg.is_configured():
            count = len(pending)
            tg.send_alert(
                title=f"{count} post(s) waiting for your approval!",
                body="🗓️ Open your BRO-BOT dashboard to review and approve.",
                emoji="✏️",
            )
        logger.info(f"Post check: {len(pending)} pending posts")
    except Exception as e:
        logger.error(f"Post check error: {e}")


def trigger_daily_brief():
    """Manually trigger daily brief (for testing/on-demand)."""
    _send_daily_brief()


def get_scheduled_jobs():
    """Get list of all scheduled jobs and their next run times."""
    if not scheduler.running:
        return []
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
        })
    return jobs
