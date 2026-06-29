-- Newsletter subscribers table
create table if not exists public.newsletter_subscribers (
  id          uuid primary key default gen_random_uuid(),
  email       text not null unique,
  created_at  timestamptz not null default now(),
  confirmed   boolean not null default false
);

-- Index for fast lookups
create index if not exists newsletter_subscribers_email_idx
  on public.newsletter_subscribers (email);

-- Row Level Security
alter table public.newsletter_subscribers enable row level security;

-- Only service role can read/write (API route uses service key)
create policy "service_only" on public.newsletter_subscribers
  using (false);
