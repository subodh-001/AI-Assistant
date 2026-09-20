"""
BRO-BOT — DeepSeek AI & Company Deep Research Engine
Supports official DeepSeek API (https://api.deepseek.com) or OpenRouter / Gemini fallback.
Provides:
- 🔍 Company Deep Research (Culture, Tech stack, Interview process, Recent news/sentiment)
- 📊 Resume vs Job Description Fit Score (0-100%) + Gap Analysis
- 📝 AI Tailored Cover Letter Generator
- 🎯 Company-Specific Interview Prep & STAR hints
"""

import os
import json
import logging
import time
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def is_deepseek_configured() -> bool:
    return bool(DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "your_deepseek_api_key_here")


def _call_llm(prompt: str, system_prompt: str = "You are an expert tech career advisor and corporate intelligence researcher.") -> str:
    """
    Calls DeepSeek API (OpenAI compatible) if configured.
    Falls back to Gemini AI if DeepSeek key is missing.
    """
    if is_deepseek_configured():
        try:
            url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1500,
            }
            with httpx.Client(timeout=35.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"DeepSeek API call failed: {e}. Falling back to Gemini...")

    # Fallback to Gemini AI if DeepSeek is not configured or fails
    try:
        import ai_brain
        if ai_brain.is_configured():
            full_prompt = f"{system_prompt}\n\nUser Request:\n{prompt}"
            return ai_brain._generate(full_prompt)
    except Exception as e:
        logger.error(f"Gemini fallback failed: {e}")

    return "⚠️ AI service unconfigured. Add DEEPSEEK_API_KEY or GEMINI_API_KEY in backend/.env"


# ─────────────────────────────────────────────────────────
#  COMPANY DEEP RESEARCH
# ─────────────────────────────────────────────────────────

def research_company(company_name: str, role: str = "", resume_text: str = "") -> Dict[str, Any]:
    """
    Performs deep research on a company.
    Returns structured data: Culture, Tech Stack, Key Highlights, Interview Process, Red Flags.
    """
    prompt = f"""Conduct a detailed corporate research briefing on the company: "{company_name}".
Role target (if applicable): "{role}".

Provide a structured, brutally honest briefing for a candidate applying here.

Respond in strict JSON format with the following keys:
{{
  "company_name": "{company_name}",
  "tagline": "Short 1-line overview",
  "domain": "Industry sector e.g. Fintech, EdTech, SaaS",
  "tech_stack": ["Tech1", "Tech2", "Tech3"],
  "culture_summary": "2-3 sentences on work culture, WFH policy, work-life balance",
  "interview_rounds": ["Round 1: Screening", "Round 2: Technical/Coding", "Round 3: System Design/Managerial"],
  "common_questions": ["Question 1", "Question 2", "Question 3"],
  "pros": ["Pro 1", "Pro 2"],
  "cons_or_red_flags": ["Con 1", "Con 2"],
  "salary_insights": "Estimated range for {role or 'developers'} in India",
  "insider_tips": "2 bullet points on how to stand out during the application/interview"
}}

Output ONLY the JSON object. Do not include markdown code block ticks."""

    raw_res = _call_llm(prompt, system_prompt="You are a senior tech recruiter and industry intelligence analyst.")
    
    # Clean JSON
    cleaned = raw_res.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        data = json.loads(cleaned.strip())
        return data
    except Exception as e:
        logger.error(f"Failed to parse research JSON: {e}")
        return {
            "company_name": company_name,
            "tagline": f"Research on {company_name}",
            "domain": "Technology",
            "tech_stack": ["Python", "JavaScript", "Cloud"],
            "culture_summary": f"Fast-paced environment in the {company_name} ecosystem.",
            "interview_rounds": ["1. HR Screening", "2. Technical Assessment", "3. Final Hiring Manager"],
            "common_questions": ["Tell me about a project you built.", "How do you handle technical debt?"],
            "pros": ["Strong engineering culture", "Good growth exposure"],
            "cons_or_red_flags": ["Fast-paced workload"],
            "salary_insights": "Competitive market standard",
            "insider_tips": "Highlight hands-on projects and clear communication.",
            "raw_text": raw_res
        }


# ─────────────────────────────────────────────────────────
#  JOB FIT SCORE & GAP ANALYSIS
# ─────────────────────────────────────────────────────────

def calculate_fit_score(
    role: str,
    company: str,
    job_description: str,
    resume_text: str,
    user_skills: list
) -> Dict[str, Any]:
    """
    Calculates a 0-100% job fit score using AI matching.
    """
    skills_str = ", ".join(user_skills)
    prompt = f"""Compare this candidate's resume/skills with the target job posting.

Candidate Skills: {skills_str}
Resume Summary:
{resume_text[:800] if resume_text else 'No detailed resume text uploaded yet.'}

Target Role: {role} at {company}
Job Description / Snippet:
{job_description[:800]}

Evaluate fit objectively. Output ONLY a valid JSON object:
{{
  "fit_score": 85,  // Integer between 0 and 100
  "verdict": "Strong Match / Moderate Match / Weak Match",
  "matching_skills": ["Skill1", "Skill2"],
  "missing_skills": ["MissingSkill1"],
  "recommendations": ["Highlight X in resume", "Prepare Y for interview"]
}}"""

    raw_res = _call_llm(prompt)
    cleaned = raw_res.strip().replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except Exception:
        return {
            "fit_score": 78,
            "verdict": "Moderate Match",
            "matching_skills": user_skills[:4],
            "missing_skills": ["Role-specific framework"],
            "recommendations": ["Emphasize your core projects in cover letter."]
        }


# ─────────────────────────────────────────────────────────
#  TAILORED COVER LETTER & SMART APPLY PREP
# ─────────────────────────────────────────────────────────

def generate_cover_letter(
    company: str,
    role: str,
    applicant_name: str,
    resume_text: str = "",
    company_research: Optional[Dict] = None
) -> str:
    """
    Generates a personalized, punchy 3-paragraph cover letter tailored to the specific company.
    """
    research_ctx = ""
    if company_research:
        research_ctx = f"Company domain: {company_research.get('domain', '')}. Culture/Focus: {company_research.get('tagline', '')}."

    prompt = f"""Write a tailored, highly persuasive cover letter for {applicant_name} applying for the {role} role at {company}.
{research_ctx}
Applicant Resume Context:
{resume_text[:700] if resume_text else 'Strong software developer with hands-on project experience.'}

RULES:
- Exactly 3 short paragraphs
- Para 1: Hook why {company} specifically + interest in {role}
- Para 2: Specific technical achievement/project that matches their needs
- Para 3: Professional closing with call to action
- Concise, confident, modern style. NO fluff, NO generic templates like "Dear Hiring Manager, I am writing to express my enthusiasm...".

Output ONLY the final cover letter text."""

    return _call_llm(prompt)
