-- Lets a DSO scope a custom reminder to a subset of their roster instead of
-- always broadcasting to every student at the college — e.g. a reminder that
-- only makes sense for F-1 students, or for students still on a specific
-- timeline step. Both columns are nullable and null means "everyone", so
-- every reminder created before this migration keeps behaving exactly as
-- before. See shared/db.py's create_custom_reminder()/list_custom_reminders().
--
-- Run this once in the Supabase SQL editor (after 001-010).

alter table custom_reminders add column if not exists target_visa_type text;
alter table custom_reminders add column if not exists target_step_key text;
