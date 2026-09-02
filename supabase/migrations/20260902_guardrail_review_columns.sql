-- 2026-09-02 — Persist the pre-publish guardrail verdict.
--
-- Until now run_content_guardrails() only printed its verdict to the GitHub
-- Actions log. Nothing could query which articles were flagged, and the log
-- scrolls away, so "needs_review" meant nothing in practice: on 2026-09-02 all
-- three published articles were flagged and none was ever reviewed.
--
-- Additive only: ADD COLUMN IF NOT EXISTS, no renames, no drops. Existing rows
-- get needs_review = false, which is accurate — they were never evaluated
-- against the checks in their current form.

ALTER TABLE articles
  ADD COLUMN IF NOT EXISTS needs_review    boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS guardrail_flags text[]  NOT NULL DEFAULT '{}';

ALTER TABLE finance_articles
  ADD COLUMN IF NOT EXISTS needs_review    boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS guardrail_flags text[]  NOT NULL DEFAULT '{}';

-- Partial indexes: the flagged rows are the only ones ever queried, and they
-- are a small minority, so the index stays tiny.
CREATE INDEX IF NOT EXISTS articles_needs_review_idx
  ON articles (published_at DESC) WHERE needs_review;

CREATE INDEX IF NOT EXISTS finance_articles_needs_review_idx
  ON finance_articles (published_at DESC) WHERE needs_review;

-- How to read the queue afterwards:
--   SELECT published_at::date, title_en, guardrail_flags
--   FROM articles WHERE needs_review ORDER BY published_at DESC;
