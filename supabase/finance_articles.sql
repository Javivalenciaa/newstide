-- ═══════════════════════════════════════════════════════════════════
-- NewsTide — finance_articles table
-- Personal Finance vertical (US, English-only)
-- Run this in the Supabase SQL Editor (project: newstide)
-- ═══════════════════════════════════════════════════════════════════

-- 1. TABLE
create table if not exists public.finance_articles (
  id               uuid primary key default gen_random_uuid(),
  title            text not null,
  slug             text not null,
  content          text,
  excerpt          text,
  title_en         text,
  slug_en          text,
  content_en       text,
  excerpt_en       text,
  category         text,
  author           text,
  keyword          text,
  keyword_hash     text,
  reading_time     integer,
  featured         boolean default false,
  image_gradient   text,
  cover_image_url  text,
  published_at     timestamptz not null default now(),
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- 2. INDEXES
create index if not exists finance_articles_published_at_idx
  on public.finance_articles (published_at desc);

create index if not exists finance_articles_category_idx
  on public.finance_articles (category);

create index if not exists finance_articles_slug_en_idx
  on public.finance_articles (slug_en);

create index if not exists finance_articles_keyword_hash_idx
  on public.finance_articles (keyword_hash);

-- 3. AUTO updated_at TRIGGER
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists finance_articles_updated_at on public.finance_articles;
create trigger finance_articles_updated_at
  before update on public.finance_articles
  for each row execute procedure public.set_updated_at();

-- 4. RLS (Row Level Security) — allow read-only from anon, write from service role
alter table public.finance_articles enable row level security;

-- Drop existing policies if re-running
drop policy if exists "Allow public read" on public.finance_articles;
drop policy if exists "Allow service write" on public.finance_articles;

create policy "Allow public read"
  on public.finance_articles
  for select
  to anon, authenticated
  using (true);

create policy "Allow service write"
  on public.finance_articles
  for all
  to service_role
  using (true)
  with check (true);
