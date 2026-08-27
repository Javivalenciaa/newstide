-- NewsTide Supabase Setup
-- Run this in the Supabase SQL Editor to create the articles table

CREATE TABLE IF NOT EXISTS articles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL,
    slug text NOT NULL,
    content text NOT NULL,
    excerpt text,
    title_en text,
    slug_en text NOT NULL,
    content_en text,
    excerpt_en text,
    category text,
    author text,
    keyword text,
    keyword_hash text,
    reading_time integer,
    featured boolean DEFAULT false,
    image_gradient text,
    cover_image_url text,
    published_at timestamptz DEFAULT now(),
    created_at timestamptz DEFAULT now(),
    search_volume integer,
    keyword_difficulty integer,
    kw_score numeric,
    related_articles jsonb DEFAULT '[]'::jsonb
);

-- Create index on slug_en for faster lookups
CREATE INDEX IF NOT EXISTS idx_articles_slug_en ON articles(slug_en);

-- Create index on category for filtering
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);

-- Create index on published_at for sorting
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);

-- Create index on keyword_hash for deduplication
CREATE INDEX IF NOT EXISTS idx_articles_keyword_hash ON articles(keyword_hash);

-- Create index on related_articles for JSON queries
CREATE INDEX IF NOT EXISTS idx_articles_related_articles ON articles USING GIN (related_articles);

-- Finance articles table
CREATE TABLE IF NOT EXISTS finance_articles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL,
    slug text NOT NULL,
    content text NOT NULL,
    excerpt text,
    title_en text,
    slug_en text NOT NULL,
    content_en text,
    excerpt_en text,
    category text,
    author text,
    keyword text,
    keyword_hash text,
    reading_time integer,
    featured boolean DEFAULT false,
    image_gradient text,
    cover_image_url text,
    published_at timestamptz DEFAULT now(),
    created_at timestamptz DEFAULT now(),
    search_volume integer,
    keyword_difficulty integer,
    kw_score numeric,
    related_articles jsonb DEFAULT '[]'::jsonb
);

-- Create index on slug_en for faster lookups
CREATE INDEX IF NOT EXISTS idx_finance_articles_slug_en ON finance_articles(slug_en);

-- Create index on category for filtering
CREATE INDEX IF NOT EXISTS idx_finance_articles_category ON finance_articles(category);

-- Create index on published_at for sorting
CREATE INDEX IF NOT EXISTS idx_finance_articles_published_at ON finance_articles(published_at DESC);

-- Create index on keyword_hash for deduplication
CREATE INDEX IF NOT EXISTS idx_finance_articles_keyword_hash ON finance_articles(keyword_hash);

-- Create index on related_articles for JSON queries
CREATE INDEX IF NOT EXISTS idx_finance_articles_related_articles ON finance_articles USING GIN (related_articles);
