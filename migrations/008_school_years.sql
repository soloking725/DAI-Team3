-- Entering year and expected graduation year, denormalized alongside the
-- other DSO-dashboard-filterable columns (visa_type, origin_country, etc. —
-- see shared/db.py's _denormalize()). Needed so a DSO can graduate an entire
-- cohort at once by year instead of one student at a time (see
-- bulk_graduate_by_year in shared/db.py). Nullable: existing students rows
-- predate this field and don't have it yet — shared/timeline_ui.py / the
-- "one more thing" prompt on pages/04_Ask_a_Question.py backfills it for
-- accounts that onboarded before this migration.
--
-- Run this once in the Supabase SQL editor (after 001-007).

alter table students add column if not exists entering_year int;
alter table students add column if not exists graduation_year int;
