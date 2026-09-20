"""
BRO-BOT — AI Brain v2
Improvements: retry logic, resume-aware generation, better prompts
"""

import os
import re
import time
import logging
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
logger = logging.getLogger(__name__)

_model = None

def _get_model():
    global _model
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None
    if _model is None:
        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel("gemini-3.6-flash")
    return _model


def _generate(prompt: str, max_retries: int = 3) -> str:
    """
    Send a prompt to Gemini with automatic retry on rate limits.
    Exponential backoff: 2s → 4s → 8s
    """
    model = _get_model()
    if not model:
        return "⚠️ Gemini API key not configured. Go to Settings → API Keys and add your key."

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            err_msg = str(e).lower()
            is_rate_limit = "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg
            is_last = attempt == max_retries - 1

            if is_rate_limit and not is_last:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning(f"Rate limit hit, retrying in {wait}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                logger.error(f"Gemini API error: {e}")
                if is_rate_limit:
                    return "❌ Gemini API rate limit hit. Please wait a minute and try again."
                return f"❌ AI Error: {str(e)}"

    return "❌ Max retries exceeded. Please try again shortly."


# ─────────────────────────────────────────────────────────
#  POST CONTENT GENERATOR (v2 — resume-aware + better prompts)
# ─────────────────────────────────────────────────────────

PLATFORM_GUIDES = {
    "linkedin": {
        "tone_hint": "professional yet conversational and human",
        "length": "150-250 words",
        "style": "Open with a hook, share the story/lesson, end with a question to drive comments",
        "hashtag_count": "5-8",
        "format": "Paragraphs with line breaks, no bullet points",
    },
    "instagram": {
        "tone_hint": "casual, energetic, and relatable",
        "length": "60-100 words",
        "style": "Punchy first line that stops the scroll, use emojis naturally, highly engaging",
        "hashtag_count": "20-25",
        "format": "Short punchy sentences, lots of line breaks, emojis between ideas",
    },
    "twitter": {
        "tone_hint": "witty, punchy, and memorable",
        "length": "Under 250 characters (strict limit!)",
        "style": "One strong idea. No fluff. Every word earns its place.",
        "hashtag_count": "1-2",
        "format": "Single paragraph or 1-2 lines maximum",
    },
}

TONE_GUIDES = {
    "professional": "formal, authoritative, educational — like a senior expert sharing wisdom",
    "casual": "warm, conversational, like texting a smart friend — approachable",
    "inspirational": "uplifting, story-driven, makes the reader feel something deeply",
    "funny": "clever humor, self-aware, witty observations that make people smirk",
}


def generate_post(
    topic: str,
    platform: str = "linkedin",
    tone: str = "casual",
    profile_name: str = "A developer",
    profile_domain: str = "Software Development",
    resume_context: str = "",
) -> dict:
    """Generate a platform-optimized social media post."""
    guide = PLATFORM_GUIDES.get(platform.lower(), PLATFORM_GUIDES["linkedin"])
    tone_desc = TONE_GUIDES.get(tone.lower(), TONE_GUIDES["casual"])

    resume_section = ""
    if resume_context.strip():
        resume_section = f"""
The person's resume context (use this to add authentic details):
---
{resume_context[:600]}
---"""

    prompt = f"""You are an elite social media ghostwriter for {profile_name}, a {profile_domain} professional.

Write a {platform.upper()} post about: "{topic}"
{resume_section}

PLATFORM RULES (follow strictly):
- Tone: {guide['tone_hint']} and {tone_desc}
- Length: {guide['length']}
- Style: {guide['style']}
- Format: {guide['format']}
- Hashtags: Exactly {guide['hashtag_count']} relevant hashtags

QUALITY RULES:
- First sentence MUST be a scroll-stopping hook (curiosity, bold statement, or surprising fact)
- No clichés: never say "I'm passionate about", "game-changer", "synergy", "leverage"
- Sound like a real human, not a corporate robot
- Include ONE specific detail or number that makes it credible
- {"Keep under 250 characters TOTAL including hashtags!" if platform == "twitter" else ""}

OUTPUT FORMAT (keep the === markers exactly):
===CONTENT===
[Post content without hashtags]

===HASHTAGS===
[Hashtags only, space-separated, e.g. #Tech #Dev #BuildInPublic]

===HOOK===
[Just the first sentence — the scroll-stopper]"""

    raw = _generate(prompt)

    content = _extract_section(raw, "CONTENT")
    hashtags_raw = _extract_section(raw, "HASHTAGS")
    hook = _extract_section(raw, "HOOK")
    hashtags = [t.strip() for t in hashtags_raw.split() if t.startswith("#")]

    if not content:
        content = raw

    return {
        "content": content.strip(),
        "hashtags": hashtags,
        "hook": hook.strip() if hook else content[:100],
        "platform": platform,
        "tone": tone,
        "topic": topic,
        "full_caption": f"{content.strip()}\n\n{' '.join(hashtags)}",
        "char_count": len(content.strip()) + len(' '.join(hashtags)) + 2,
    }


# ─────────────────────────────────────────────────────────
#  JOB APPLICATION MESSAGE GENERATOR (v2 — resume-aware)
# ─────────────────────────────────────────────────────────

def generate_job_message(
    company: str,
    role: str,
    profile_name: str = "Candidate",
    profile_domain: str = "Software Developer",
    skills: list = None,
    resume_context: str = "",
) -> str:
    """
    Generate a LinkedIn connection note for a job application.
    Inspired by Simplify's approach — personalized, not generic.
    """
    skills_str = ", ".join(skills or ["Python", "JavaScript", "React"])

    resume_section = ""
    if resume_context.strip():
        resume_section = f"""
Based on this resume context, pick 1-2 specific achievements to mention:
{resume_context[:400]}"""

    prompt = f"""Write a LinkedIn connection note for a job application.

Applicant: {profile_name}
Target: {role} at {company}
Skills: {skills_str}
{resume_section}

STRICT REQUIREMENTS:
- MAX 300 characters (LinkedIn connection note hard limit)
- Sound like a genuine human, NOT a template
- Mention the company by name
- Include 1 specific skill or achievement
- End with a clear, soft ask (portfolio/profile review, not "I need a job")
- NO clichés: "passionate about", "team player", "fast learner"

Write ONLY the message. No intro, no explanation."""
    return _generate(prompt)


# ─────────────────────────────────────────────────────────
#  RECRUITER REPLY GENERATOR (v2)
# ─────────────────────────────────────────────────────────

def generate_recruiter_reply(
    recruiter_message: str,
    profile_name: str = "Candidate",
    profile_domain: str = "Software Developer",
) -> str:
    """Draft a smart, professional reply to a recruiter message."""
    prompt = f"""A recruiter sent this message:
---
{recruiter_message}
---

Write a professional reply from {profile_name} ({profile_domain}).

RULES:
- Max 120 words
- Warm but professional — interested but not desperate
- If the role/company isn't mentioned, ask for details naturally
- Include availability for a call (Mon-Fri, specific hours)
- End with a question that shows genuine interest
- Sound like a real person, not a template

Write ONLY the reply message."""
    return _generate(prompt)


# ─────────────────────────────────────────────────────────
#  DAILY BRIEF GENERATOR (v2 — more detailed, friend-like)
# ─────────────────────────────────────────────────────────

def generate_daily_brief(stats: dict, activities: list, profile_name: str = "bhai") -> str:
    today = datetime.now().strftime("%A, %d %B %Y")
    hour = datetime.now().hour
    time_greeting = "Good morning" if hour < 12 else "Good evening" if hour >= 17 else "Hey"

    activity_lines = "\n".join([f"• {a['description']}" for a in activities[:15]]) or "• No activities logged yet"

    posts_pending = stats.get('posts', {}).get('pending', 0)
    posts_posted = stats.get('posts', {}).get('posted', 0)
    jobs_new = stats.get('jobs', {}).get('new', 0)
    jobs_applied = stats.get('jobs', {}).get('applied', 0)
    msgs_unread = stats.get('messages', {}).get('unread', 0)

    prompt = f"""{time_greeting}, I'm BRO-BOT — your personal AI assistant.

Write {profile_name}'s daily brief for {today}.

Today's data:
- Posts waiting for approval: {posts_pending}
- Posts published so far: {posts_posted}
- New jobs found by scanner: {jobs_new}
- Jobs applied to: {jobs_applied}
- Unread recruiter messages: {msgs_unread}

Recent activity log:
{activity_lines}

Write the brief EXACTLY like a caring, smart friend sending a WhatsApp message.
Rules:
- Use emojis throughout (1-2 per paragraph)
- Write in casual English (not formal, not Hinglish)
- Max 180 words
- 3-4 short paragraphs
- Open with a personalized greeting using {profile_name}'s name
- Give specific actionable advice based on the data
- Close with one motivational sentence
- If pending approvals exist, remind them!
- If unread messages exist, urgently mention it!"""

    return _generate(prompt)


# ─────────────────────────────────────────────────────────
#  LINKEDIN BIO GENERATOR (v2)
# ─────────────────────────────────────────────────────────

def generate_linkedin_bio(
    name: str,
    domain: str,
    skills: list,
    achievements: str = "",
) -> str:
    prompt = f"""Write a powerful LinkedIn "About" section.

Person: {name}
Domain: {domain}
Skills: {', '.join(skills) if skills else 'Not specified'}
Achievements/Context: {achievements or 'Student/Fresher building real-world projects'}

REQUIREMENTS:
- 150-200 words exactly
- First line is the hook — NOT "I am a {domain}". Use a bold statement or question.
- Second paragraph: story/background (2-3 sentences)
- Third paragraph: what you build/do and impact
- Final line: call to action (DM for X, open to Y, etc.)
- Confident but not arrogant
- Human, not ChatGPT-sounding

Write ONLY the bio text."""
    return _generate(prompt)


# ─────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────

def _extract_section(text: str, section: str) -> str:
    pattern = rf"==={section}===\s*(.*?)(?:===\w+===|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def is_configured() -> bool:
    return bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here")
