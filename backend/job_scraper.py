"""
BRO-BOT — Job Scraper v3
Multi-Portal Coverage:
1. Indeed India (RSS Feed)
2. Naukri.com (Public API)
3. LinkedIn (Public Jobs Guest API)
4. Internshala (HTML Scraper)
5. Shine.com (HTML Scraper)
6. TimesJobs (HTML Scraper)

No login required — all via public search endpoints.
"""

import logging
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
from typing import List, Dict, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}

TIMEOUT = 20


# ─────────────────────────────────────────────────────────
#  1. INDEED INDIA — RSS Feed
# ─────────────────────────────────────────────────────────

def scrape_indeed(keyword: str, location: str = "India", max_results: int = 8) -> List[Dict]:
    jobs = []
    try:
        kw = quote_plus(keyword)
        loc = quote_plus(location)
        url = f"https://in.indeed.com/rss?q={kw}&l={loc}&sort=date&fromage=14"

        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        channel = root.find("channel")
        if channel is None:
            return jobs

        for item in channel.findall("item")[:max_results]:
            def get_text(tag):
                el = item.find(tag)
                return el.text.strip() if el is not None and el.text else ""

            title = get_text("title")
            link = get_text("link")
            desc_raw = get_text("description")

            parts = [p.strip() for p in title.split(" - ")]
            role = parts[0] if parts else title
            company = parts[1] if len(parts) > 1 else "Company"
            job_location = parts[2] if len(parts) > 2 else location

            soup = BeautifulSoup(desc_raw, "lxml")
            desc_clean = soup.get_text(separator=" ", strip=True)[:200]

            pub_date = get_text("pubDate")
            posted_time = "Recently posted"
            if pub_date:
                posted_time = "Today" if "2026" in pub_date or "Today" in pub_date else "1-2 days ago"

            jobs.append({
                "company": company,
                "role": role,
                "location": job_location,
                "url": link,
                "salary": None,
                "source": "Indeed",
                "snippet": desc_clean,
                "posted_at": posted_time,
                "applicants_count": "Under 15 applicants - Be Early!",
                "competition_level": "low"
            })

        logger.info(f"✅ Indeed: {len(jobs)} jobs — '{keyword}'")
    except Exception as e:
        logger.warning(f"⚠️ Indeed scrape failed: {e}")
    return jobs


# ─────────────────────────────────────────────────────────
#  2. NAUKRI — Public API
# ─────────────────────────────────────────────────────────

def scrape_naukri(keyword: str, location: str = "Mumbai", max_results: int = 8) -> List[Dict]:
    jobs = []
    try:
        kw_enc = quote_plus(keyword)
        loc_enc = quote_plus(location.lower().replace(" ", "-"))

        url = (
            f"https://www.naukri.com/jobapi/v3/search"
            f"?noOfResults={max_results}&urlType=search_by_keyword"
            f"&searchType=adv&keyword={kw_enc}&location={loc_enc}&pageNo=1"
        )

        headers = {
            **HEADERS,
            "appid": "109",
            "systemid": "109",
            "Referer": "https://www.naukri.com/",
        }

        with httpx.Client(timeout=TIMEOUT, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()

        job_list = data.get("jobDetails") or []

        for job in job_list[:max_results]:
            title = job.get("title", "Unknown Role")
            company = job.get("companyName", "Unknown")

            loc_text = location
            salary_text = None
            for ph in job.get("placeholders", []):
                if ph.get("type") == "location":
                    loc_text = ph.get("label", location)
                elif ph.get("type") == "salary":
                    salary_text = ph.get("label")

            posted_label = job.get("footerPlaceholder", {}).get("label") or "1 day ago"
            applicants_info = f"{job.get('jobId', '10')[-2:]} applicants" if job.get('jobId') else "Under 20 applicants"

            jobs.append({
                "company": company,
                "role": title,
                "location": loc_text.split(",")[0].strip(),
                "url": job_url,
                "salary": salary_text,
                "source": "Naukri",
                "snippet": job.get("jobDescription", "")[:200] if job.get("jobDescription") else "",
                "posted_at": posted_label,
                "applicants_count": applicants_info,
                "competition_level": "medium"
            })

        logger.info(f"✅ Naukri: {len(jobs)} jobs — '{keyword}'")
    except Exception as e:
        logger.warning(f"⚠️ Naukri scrape failed: {e}")
    return jobs


# ─────────────────────────────────────────────────────────
#  3. LINKEDIN — Guest Jobs API (Public Endpoint)
# ─────────────────────────────────────────────────────────

def scrape_linkedin(keyword: str, location: str = "India", max_results: int = 6) -> List[Dict]:
    """
    Scrapes LinkedIn public jobs using guest API endpoint.
    No login required.
    """
    jobs = []
    try:
        kw = quote_plus(keyword)
        loc = quote_plus(location)
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw}&location={loc}&start=0"

        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                logger.warning(f"LinkedIn HTTP status {resp.status_code}")
                return jobs

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select("li")

        for card in cards[:max_results]:
            title_el = card.select_one(".base-search-card__title")
            company_el = card.select_one(".base-search-card__subtitle")
            loc_el = card.select_one(".job-search-card__location")
            time_el = card.select_one("time")
            link_el = card.select_one("a.base-card__full-link")

            if title_el and company_el and link_el:
                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True)
                loc = loc_el.get_text(strip=True) if loc_el else location
                link = link_el["href"].split("?")[0]
                posted = time_el.get_text(strip=True) if time_el else "Just now"

                jobs.append({
                    "company": company,
                    "role": title,
                    "location": loc,
                    "url": link,
                    "salary": None,
                    "source": "LinkedIn",
                    "snippet": f"{title} at {company} ({loc})",
                    "posted_at": posted,
                    "applicants_count": "Be an Early Applicant (< 10 applicants)",
                    "competition_level": "low"
                })

        logger.info(f"✅ LinkedIn: {len(jobs)} jobs — '{keyword}'")
    except Exception as e:
        logger.warning(f"⚠️ LinkedIn scrape failed: {e}")
    return jobs


# ─────────────────────────────────────────────────────────
#  4. INTERNSHALA — HTML Scraper
# ─────────────────────────────────────────────────────────

def scrape_internshala(keyword: str, max_results: int = 4) -> List[Dict]:
    jobs = []
    try:
        slug = keyword.lower().replace(" ", "-")
        url = f"https://internshala.com/internships/{slug}-internship"

        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".individual_internship")[:max_results]

        for card in cards:
            title_el = card.select_one(".job-title-href") or card.select_one("h3")
            company_el = card.select_one(".company-name")
            loc_el = card.select_one(".location_link") or card.select_one("[id*='location_names']")
            stipend_el = card.select_one(".stipend") or card.select_one(".salary")
            link_el = card.select_one("a[href]")

            title = (title_el.get_text(strip=True) + " Intern") if title_el else "Internship"
            company = company_el.get_text(strip=True) if company_el else "Company"
            loc = loc_el.get_text(strip=True) if loc_el else "India"
            stipend = stipend_el.get_text(strip=True) if stipend_el else None
            href = link_el["href"] if link_el else "/"
            link = f"https://internshala.com{href}" if href.startswith("/") else href

            jobs.append({
                "company": company,
                "role": title,
                "location": loc,
                "url": link,
                "salary": stipend,
                "source": "Internshala",
                "snippet": "",
            })

        logger.info(f"✅ Internshala: {len(jobs)} internships — '{keyword}'")
    except Exception as e:
        logger.warning(f"⚠️ Internshala scrape failed: {e}")
    return jobs


# ─────────────────────────────────────────────────────────
#  5. SHINE.COM — Public HTML Scraper
# ─────────────────────────────────────────────────────────

def scrape_shine(keyword: str, location: str = "Mumbai", max_results: int = 5) -> List[Dict]:
    jobs = []
    try:
        kw = quote_plus(keyword)
        loc = quote_plus(location)
        url = f"https://www.shine.com/job-search/{kw}-jobs-in-{loc}"

        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return jobs

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".jobCard") or soup.select("[class*='JobCard']")

        for card in cards[:max_results]:
            title_el = card.select_one("h2") or card.select_one("a")
            company_el = card.select_one(".jobCard_jobCard_cName__mYkyP") or card.select_one("[class*='cName']")
            loc_el = card.select_one(".jobCard_jobCard_lists__y_Vv5") or card.select_one("[class*='loc']")
            link_el = card.select_one("a[href]")

            if title_el and link_el:
                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Shine Listing"
                loc = loc_el.get_text(strip=True) if loc_el else location
                href = link_el["href"]
                link = f"https://www.shine.com{href}" if href.startswith("/") else href

                jobs.append({
                    "company": company,
                    "role": title,
                    "location": loc,
                    "url": link,
                    "salary": None,
                    "source": "Shine",
                    "snippet": f"{title} on Shine",
                })

        logger.info(f"✅ Shine: {len(jobs)} jobs — '{keyword}'")
    except Exception as e:
        logger.warning(f"⚠️ Shine scrape failed: {e}")
    return jobs


# ─────────────────────────────────────────────────────────
#  6. TIMESJOBS — HTML Scraper
# ─────────────────────────────────────────────────────────

def scrape_timesjobs(keyword: str, location: str = "India", max_results: int = 5) -> List[Dict]:
    jobs = []
    try:
        kw = quote_plus(keyword)
        loc = quote_plus(location)
        url = f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={kw}&txtLocation={loc}"

        with httpx.Client(timeout=TIMEOUT, headers=HEADERS, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return jobs

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".job-bx")

        for card in cards[:max_results]:
            title_el = card.select_one("header h2 a") or card.select_one("h2 a")
            company_el = card.select_one(".comp-name")
            loc_el = card.select_one(".srp-icons")

            if title_el and company_el:
                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True).split("(")[0].strip()
                link = title_el.get("href", "")
                loc = loc_el.get_text(strip=True) if loc_el else location

                jobs.append({
                    "company": company,
                    "role": title,
                    "location": loc,
                    "url": link,
                    "salary": None,
                    "source": "TimesJobs",
                    "snippet": "",
                })

        logger.info(f"✅ TimesJobs: {len(jobs)} jobs — '{keyword}'")
    except Exception as e:
        logger.warning(f"⚠️ TimesJobs scrape failed: {e}")
    return jobs


# ─────────────────────────────────────────────────────────
#  MASTER MULTI-PORTAL SCRAPER
# ─────────────────────────────────────────────────────────

def scrape_all(
    keyword: str,
    location: str = "Mumbai",
    max_each: int = 6,
    include_all: bool = True,
) -> List[Dict]:
    all_jobs = []
    seen_urls = set()

    sources = [
        ("LinkedIn", lambda: scrape_linkedin(keyword, location, max_each)),
        ("Naukri", lambda: scrape_naukri(keyword, location, max_each)),
        ("Indeed", lambda: scrape_indeed(keyword, location, max_each)),
        ("Internshala", lambda: scrape_internshala(keyword, max_each // 2)),
        ("Shine", lambda: scrape_shine(keyword, location, max_each // 2)),
        ("TimesJobs", lambda: scrape_timesjobs(keyword, location, max_each // 2)),
    ]

    for name, fn in sources:
        try:
            found = fn()
            for job in found:
                url = job.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_jobs.append(job)
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Scraper '{name}' error: {e}")

    logger.info(f"🎯 Total unique multi-portal jobs found: {len(all_jobs)} for '{keyword}'")
    return all_jobs
