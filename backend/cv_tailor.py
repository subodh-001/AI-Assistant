import os
import json
from pathlib import Path
from typing import Dict, Any, List
import google.generativeai as genai

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    # Prefer gemini-1.5-flash or gemini-2.0-flash
    return genai.GenerativeModel("gemini-3.6-flash")

def load_master_projects() -> List[Dict[str, Any]]:
    projects_file = DATA_DIR / "master_projects.json"
    if projects_file.exists():
        try:
            return json.loads(projects_file.read_text())
        except Exception:
            pass
    return []

def tailor_cv(
    job_role: str,
    company: str = "",
    job_description: str = "",
    base_resume_text: str = ""
) -> Dict[str, Any]:
    """
    Tailors the candidate's CV specifically for the target job role & JD.
    Selects top relevant projects, rewords bullets for ATS optimization,
    and formats into clean Markdown & HTML.
    """
    master_projects = load_master_projects()
    projects_context = json.dumps(master_projects, indent=2)

    if not base_resume_text:
        resume_file = DATA_DIR / "resume.txt"
        if resume_file.exists():
            base_resume_text = resume_file.read_text()

    model = get_gemini_model()
    
    if not model:
        # Fallback response if no API key configured
        return _build_fallback_cv(job_role, company, master_projects, base_resume_text)

    prompt = f"""
You are an expert ATS Resume Optimization Specialist & Executive Recruiter.

Target Job Role: {job_role}
Target Company: {company if company else 'Technology Company'}
Job Description / Requirements:
{job_description if job_description else 'Focus on software development, problem solving, full-stack development, AI/ML or relevant technical skills.'}

Candidate Base Resume:
{base_resume_text[:2000] if base_resume_text else 'Subodh Ram - MCA Graduate, Full-Stack & AI Developer.'}

Candidate's Master Project Portfolio:
{projects_context}

INSTRUCTIONS:
1. Analyze the Target Job Description and identify top ATS keywords, required skills, and core responsibilities.
2. Select EXACTLY 3 MOST RELEVANT projects from the Master Project Portfolio that align directly with this role ({job_role}).
3. For each project, provide 2 to 3 concise, high-impact bullet points highlighting keywords and measurable results. Keep the overall resume compact so it fits on EXACTLY 1 A4 PAGE when printed.
4. Provide a target ATS Match Score (out of 100) and list key matched skills.
5. Output ONLY valid JSON matching this exact structure:

{{
  "ats_match_score": 92,
  "tailored_headline": "Professional Title / Headline tailored to job",
  "professional_summary": "2 to 3 line impact summary customized for the job description.",
  "matched_keywords": ["Python", "FastAPI", "React", "AI/ML"],
  "selected_projects": [
    {{
      "title": "Project Title",
      "tags": ["Tech1", "Tech2"],
      "bullets": [
        "Tailored bullet point highlighting keywords...",
        "Tailored bullet point 2..."
      ]
    }}
  ],
  "technical_skills": {{
    "Languages": "Java, Python, JavaScript, HTML/CSS",
    "Frameworks & Libraries": "React.js, Node.js, Express.js, FastAPI, Spring Boot",
    "Databases & Cloud": "MongoDB, MySQL, Oracle DB, Firebase",
    "Developer Tools & Methods": "Git, Docker, REST APIs, System Architecture"
  }},
  "full_markdown_cv": "Complete formatted Markdown CV...",
  "key_ats_optimizations": [
    "Injected key skills: X, Y",
    "Emphasized project Z because of role match"
  ]
}}
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3
            )
        )
        data = json.loads(response.text)
        data["full_html_cv"] = generate_html_resume(data, base_resume_text)
        return data
    except Exception as e:
        print(f"Error calling Gemini for CV tailoring: {e}")
        return _build_fallback_cv(job_role, company, master_projects, base_resume_text)


def generate_html_resume(cv_data: Dict[str, Any], base_resume_text: str) -> str:
    """Generates clean, printable HTML layout of the tailored resume (Strict Single-Page Fit)."""
    headline = cv_data.get("tailored_headline", "Software Development Engineer")
    summary = cv_data.get("professional_summary", "")
    projects = cv_data.get("selected_projects", [])[:3]
    skills = cv_data.get("technical_skills", {})

    projects_html = ""
    for proj in projects:
        proj_title = proj.get("title", "")
        tags = ", ".join(proj.get("tags", []))
        bullets = "".join([f"<li>{b}</li>" for b in proj.get("bullets", [])[:3]])
        projects_html += f"""
        <div class="resume-item">
            <div class="resume-item-header">
                <span class="proj-title">{proj_title}</span>
                <span class="proj-tags">{tags}</span>
            </div>
            <ul class="resume-bullets">
                {bullets}
            </ul>
        </div>
        """

    skills_html = ""
    for cat, items in skills.items():
        skills_html += f"<p><strong>{cat}:</strong> {items}</p>"

    html = f"""
    <div class="tailored-cv-paper">
        <header class="cv-header">
            <h1 class="cv-name">SUBODH RAM</h1>
            <p class="cv-headline">{headline}</p>
            <p class="cv-contact">
                Mumbai, Maharashtra | +91-9076314255 | subodhram3350@gmail.com<br/>
                LinkedIn: subodhram | GitHub: subodh-001 | Portfolio: subodh-portfolio-zeta.vercel.app
            </p>
        </header>

        <section class="cv-section">
            <h2>PROFESSIONAL SUMMARY</h2>
            <p>{summary}</p>
        </section>

        <section class="cv-section">
            <h2>RELEVANT PROJECTS & EXPERIENCE</h2>
            {projects_html}
        </section>

        <section class="cv-section">
            <h2>TECHNICAL SKILLS</h2>
            <div class="cv-skills">
                {skills_html}
            </div>
        </section>

        <section class="cv-section">
            <h2>EDUCATION</h2>
            <p><strong>Master of Computer Application (MCA)</strong> — MPSTME, NMIMS University Mumbai (CGPA: 7.38/10)</p>
            <p><strong>Bachelor of Science in Information Technology (BSc IT)</strong> — Tolani College of Commerce Mumbai (CGPA: 8.28/10)</p>
        </section>
    </div>
    """
    return html


def _build_fallback_cv(job_role: str, company: str, master_projects: list, base_resume_text: str) -> Dict[str, Any]:
    """Provides a smart rule-based fallback CV when API key is offline."""
    role_lower = job_role.lower()
    selected = []
    for p in master_projects:
        tags_str = " ".join(p.get("tags", [])).lower()
        if ("ai" in role_lower or "machine learning" in role_lower or "python" in role_lower) and ("ai" in tags_str or "python" in tags_str or "machine learning" in tags_str):
            selected.append(p)
        elif ("blockchain" in role_lower or "web3" in role_lower) and ("blockchain" in tags_str or "smart contracts" in tags_str):
            selected.append(p)
        elif ("react" in role_lower or "frontend" in role_lower or "full-stack" in role_lower or "developer" in role_lower):
            if "react" in tags_str or "full-stack" in p.get("domain", "").lower():
                selected.append(p)
    
    if len(selected) < 3:
        selected = master_projects[:3]

    summary = f"Results-driven Software Engineer tailored for {job_role} role at {company if company else 'target company'}. Specialized in full-stack architecture, AI integrations, and scalable web solutions."
    
    cv_data = {
        "ats_match_score": 88,
        "tailored_headline": f"Software Engineer — {job_role}",
        "professional_summary": summary,
        "matched_keywords": [job_role, "Python", "React", "FastAPI", "Full-Stack"],
        "selected_projects": [
            {
                "title": p.get("title"),
                "tags": p.get("tags", []),
                "bullets": p.get("bullets", [])[:3]
            } for p in selected[:3]
        ],
        "technical_skills": {
            "Languages": "Java, Python, JavaScript, HTML/CSS",
            "Frameworks & Web": "React.js, Node.js, Express.js, FastAPI, Spring Boot",
            "Databases & Cloud": "MongoDB, MySQL, Oracle DB, Firebase",
            "Tools & Methods": "Git, Docker, REST APIs, Microservices"
        },
        "full_markdown_cv": f"# SUBODH RAM\n## {job_role}\n\n{summary}",
        "key_ats_optimizations": [
            f"Highlighted top {len(selected[:3])} relevant projects for {job_role}",
            "Aligned core skills with role demands"
        ]
    }
    cv_data["full_html_cv"] = generate_html_resume(cv_data, base_resume_text)
    return cv_data
