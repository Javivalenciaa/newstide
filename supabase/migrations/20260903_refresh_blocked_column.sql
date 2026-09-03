-- 2026-09-03 — Record articles the model declines to refresh.
--
-- On 2026-09-03 the content refresh picked two June articles about
-- synthetic-DNA monitoring. Anthropic's safety classifier declined both:
-- HTTP 200, stop_reason "refusal", empty content list, 0 output tokens. The
-- code read content[0] directly, so it surfaced as
--
--     ❌ Refresh failed: list index out of range
--
-- and, because nothing recorded the decline, those same two rows sort first
-- every morning (oldest first, no serp_tracking data) and would burn two of
-- the run's twelve Claude calls every single day, forever.
--
-- Retrying the same prompt produces the same decline, so the only fix is to
-- remember it. refresh_pipeline.py sets these on ClaudeDeclined and skips any
-- row where refresh_blocked_at is not null; it also works fine before this
-- migration is applied (it retries the query without the column).
--
-- Additive only: ADD COLUMN IF NOT EXISTS, no renames, no drops.

ALTER TABLE articles
  ADD COLUMN IF NOT EXISTS refresh_blocked_at     timestamptz,
  ADD COLUMN IF NOT EXISTS refresh_blocked_reason text;

ALTER TABLE finance_articles
  ADD COLUMN IF NOT EXISTS refresh_blocked_at     timestamptz,
  ADD COLUMN IF NOT EXISTS refresh_blocked_reason text;

-- To clear a block later (e.g. after rewriting the article by hand):
--   UPDATE articles
--   SET refresh_blocked_at = NULL, refresh_blocked_reason = NULL
--   WHERE slug_en = '<slug>';
--
-- To see what is currently blocked:
--   SELECT slug_en, refresh_blocked_at, refresh_blocked_reason
--   FROM articles WHERE refresh_blocked_at IS NOT NULL;
