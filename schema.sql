-- =====================================================
-- NEW TABLES - Run these to create new tables
-- =====================================================

-- custom_mails table: stores custom emails for account generation
CREATE TABLE IF NOT EXISTS custom_mails (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    mail_type TEXT NOT NULL,
    refresh_token TEXT,
    client_id TEXT,
    email_data TEXT,
    imap_server TEXT,
    imap_port INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- registered_emails table: stores all successfully registered emails
CREATE TABLE IF NOT EXISTS registered_emails (
    id BIGSERIAL PRIMARY KEY,
    email_data TEXT NOT NULL,
    email TEXT,
    password TEXT,
    key TEXT NOT NULL,
    category TEXT DEFAULT 'registered',
    mail_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- ALTER existing tables - Run these to add new columns
-- =====================================================

-- Add mail_type column to mails table
ALTER TABLE mails ADD COLUMN IF NOT EXISTS mail_type TEXT;

-- =====================================================
-- INDEXES - Run these to create indexes
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_custom_mails_type ON custom_mails(mail_type);
CREATE INDEX IF NOT EXISTS idx_registered_emails_key ON registered_emails(key);
CREATE INDEX IF NOT EXISTS idx_registered_emails_created_at ON registered_emails(created_at);

-- =====================================================
-- ROW LEVEL SECURITY - Run these for custom_mails and registered_emails
-- =====================================================

ALTER TABLE custom_mails ENABLE ROW LEVEL SECURITY;
ALTER TABLE registered_emails ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist, then recreate
DROP POLICY IF EXISTS "Service role can do anything on custom_mails" ON custom_mails;
DROP POLICY IF EXISTS "Service role can do anything on registered_emails" ON registered_emails;

CREATE POLICY "Service role can do anything on custom_mails" ON custom_mails
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role can do anything on registered_emails" ON registered_emails
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
