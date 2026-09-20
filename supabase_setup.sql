-- ============================================================
--  BRO-BOT — Supabase PostgreSQL Database Setup Schema
--  Copy and Paste this into Supabase SQL Editor and click RUN
-- ============================================================

-- 1. Master Projects Table
CREATE TABLE IF NOT EXISTS master_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    domain TEXT DEFAULT 'Software Engineering',
    tags TEXT[] DEFAULT '{}',
    bullets TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    location TEXT,
    url TEXT UNIQUE,
    salary TEXT,
    source TEXT DEFAULT 'manual',
    status TEXT DEFAULT 'new',
    posted_at TEXT,
    applicants_count TEXT,
    competition_level TEXT DEFAULT 'low',
    found_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Scheduled Posts Table
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    content TEXT NOT NULL,
    hashtags TEXT[] DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    scheduled_at TEXT,
    posted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Messages & Recruiter Drafts Table
CREATE TABLE IF NOT EXISTS recruiter_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender TEXT NOT NULL,
    company TEXT NOT NULL,
    platform TEXT DEFAULT 'LinkedIn',
    raw_message TEXT NOT NULL,
    ai_reply TEXT,
    status TEXT DEFAULT 'unread',
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Activity Log Table
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action TEXT NOT NULL,
    description TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
