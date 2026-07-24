-- NewsTide pSEO Pages Table
-- Run this once in your Supabase SQL editor before using the pSEO pipeline.

CREATE TABLE IF NOT EXISTS pseo_pages (
  id             uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  slug           text UNIQUE NOT NULL,
  template       text NOT NULL,           -- 'comparisons' | 'alternatives' | 'guides' | 'for-profession'
  entity_a       text NOT NULL,           -- primary entity (tool name, profession)
  entity_b       text,                    -- secondary entity (competitor, use case) — nullable
  keyword        text NOT NULL,
  keyword_hash   text UNIQUE NOT NULL,
  title          text NOT NULL,
  content        text NOT NULL,
  excerpt        text,
  reading_time   int  DEFAULT 5,
  image_gradient text DEFAULT 'linear-gradient(135deg,#0d1a2e,#1a0d2e)',
  lang           text DEFAULT 'en',
  published_at   timestamptz DEFAULT now(),
  updated_at     timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pseo_published  ON pseo_pages(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_pseo_template   ON pseo_pages(template);
CREATE INDEX IF NOT EXISTS idx_pseo_slug       ON pseo_pages(slug);
CREATE INDEX IF NOT EXISTS idx_pseo_entity_a   ON pseo_pages(entity_a);

ALTER TABLE pseo_pages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public read" ON pseo_pages;
CREATE POLICY "public read" ON pseo_pages FOR SELECT USING (true);

-- Helper: auto-update updated_at on row change
CREATE OR REPLACE FUNCTION update_pseo_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS pseo_updated_at_trigger ON pseo_pages;
CREATE TRIGGER pseo_updated_at_trigger
  BEFORE UPDATE ON pseo_pages
  FOR EACH ROW EXECUTE FUNCTION update_pseo_updated_at();
