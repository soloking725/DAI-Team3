-- Denormalizes the student-entered visa/passport expiration dates (already
-- stored client-side in vera_state.post_visa, see shared/reminders.py) onto
-- the students row, so the DSO roster can show and eventually filter/sort on
-- them — previously these dates existed only in each student's own
-- full_state blob and were invisible to their DSO. See shared/db.py's
-- _denormalize() and list_students().
--
-- Nullable: existing students rows predate this field and won't have it set
-- until the student next saves their post-visa dates.
--
-- Run this once in the Supabase SQL editor (after 001-009).

alter table students add column if not exists visa_expiration date;
alter table students add column if not exists passport_expiration date;
