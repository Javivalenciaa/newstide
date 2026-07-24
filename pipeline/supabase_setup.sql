CREATE TABLE IF NOT EXISTS articles (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  title text NOT NULL,
  slug text UNIQUE NOT NULL,
  content text NOT NULL,
  excerpt text,
  category text DEFAULT 'IA',
  author text DEFAULT 'Javier Valencia',
  keyword text,
  keyword_hash text UNIQUE,
  published_at timestamptz DEFAULT now(),
  reading_time int DEFAULT 5,
  featured boolean DEFAULT false,
  image_gradient text DEFAULT 'linear-gradient(135deg,#0d1a2e,#1a0d2e)',
  -- Internationalisation
  title_en text,
  content_en text,
  excerpt_en text,
  slug_en text UNIQUE,
  -- Media
  cover_image_url text,
  -- Timestamps
  updated_at timestamptz DEFAULT now(),
  -- Source attribution
  source_url text,
  source_name text,
  source_date timestamptz,
  source_excerpt text
);

CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_slug ON articles(slug);
CREATE INDEX IF NOT EXISTS idx_articles_slug_en ON articles(slug_en);

ALTER TABLE articles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public read" ON articles;
CREATE POLICY "public read" ON articles FOR SELECT USING (true);
