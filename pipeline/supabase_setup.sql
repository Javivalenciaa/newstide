
CREATE TABLE IF NOT EXISTS articles (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  title text NOT NULL,
  slug text UNIQUE NOT NULL,
  content text NOT NULL,
  excerpt text,
  category text DEFAULT 'IA',
  author text DEFAULT 'Redacción NewsTide',
  keyword text,
  keyword_hash text UNIQUE,
  published_at timestamptz DEFAULT now(),
  reading_time int DEFAULT 5,
  featured boolean DEFAULT false,
  image_gradient text DEFAULT 'linear-gradient(135deg,#0d1a2e,#1a0d2e)'
);

CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_slug ON articles(slug);

ALTER TABLE articles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "public read" ON articles;
CREATE POLICY "public read" ON articles FOR SELECT USING (true);
