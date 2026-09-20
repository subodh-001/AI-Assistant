# 🤖 BRO-BOT — Personal AI Life Manager

> Your 24/7 AI assistant that handles social media, job hunting, recruiter replies, and sends you daily briefs like a smart friend.

---

## What BRO-BOT Does

| Feature | Description |
|---------|-------------|
| ✨ **Content Studio** | AI generates LinkedIn/Instagram/Twitter posts with captions & hashtags |
| 📋 **Post Queue** | Review, approve, reject posts before they go live |
| 💼 **Job Hunter** | Track job applications, generate personalized application messages |
| 💬 **Message Center** | Save recruiter messages, AI drafts professional replies |
| 📰 **Daily Brief** | AI-generated summary sent to your Telegram every morning |
| ⚙️ **Settings** | Configure everything from one dashboard |

---

## Quick Start

### Step 1 — Setup

```bash
cd "AI Assistent"
chmod +x start.sh
./start.sh
```

### Step 2 — Configure API Keys

Edit `backend/.env`:

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Get your keys:
- **Gemini API** (Free): https://aistudio.google.com/app/apikey
- **Telegram Bot**: Message @BotFather on Telegram → /newbot

### Step 3 — Open Dashboard

The script auto-opens your browser. Or manually:
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Manual Setup (without start.sh)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Start backend
python main.py

# Open frontend (separate terminal or just open in browser)
# open frontend/index.html
```

---

## Project Structure

```
AI Assistent/
├── backend/
│   ├── main.py          ← FastAPI server (all API endpoints)
│   ├── ai_brain.py      ← Gemini AI integration
│   ├── data_store.py    ← JSON storage layer
│   ├── telegram_notify.py ← Telegram bot
│   ├── scheduler.py     ← Automated background tasks
│   ├── requirements.txt
│   ├── .env.example     ← Copy to .env and fill keys
│   └── .env             ← Your actual API keys (gitignored)
├── frontend/
│   ├── index.html       ← Dashboard UI
│   ├── style.css        ← Design system
│   └── app.js           ← All frontend logic
├── data/
│   ├── posts.json       ← Post queue storage
│   ├── jobs.json        ← Job tracker storage
│   ├── messages.json    ← Messages storage
│   ├── config.json      ← Configuration
│   └── activity.json    ← Activity log
├── start.sh             ← One-command launcher
└── README.md
```

---

## Roadmap

- ✅ **Phase 1** — Dashboard + AI Content Studio + Job Tracker + Telegram Brief
- 🔜 **Phase 2** — LinkedIn auto-post, Instagram auto-post, Twitter/X posting
- 🔜 **Phase 3** — Job auto-scan (LinkedIn, Naukri, Indeed scraping)
- 🔜 **Phase 4** — Auto recruiter reply, email integration, full automation

---

## Tech Stack

- **Backend**: Python + FastAPI
- **AI**: Google Gemini 1.5 Flash (free tier!)
- **Notifications**: Telegram Bot API
- **Scheduler**: APScheduler
- **Frontend**: Vanilla HTML/CSS/JS (no build step!)
- **Storage**: JSON files (no database needed)

---

## Important Notes

⚠️ **LinkedIn automation** is done carefully to avoid account bans. BRO-BOT prepares everything — you click to confirm.

🔒 **API keys** stay in your `.env` file locally. Never commit to git.

💡 **First time?** Start with just the Gemini API key. Telegram is optional but makes the daily brief super useful!

---

*Made with ❤️ by BRO-BOT — your AI bestie*
