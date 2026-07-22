-- Two additions for DSO-authored, in-account-only reminders/events (no
-- email/SMS yet — see shared/reminders.py):
--
-- 1. announcements gets an optional event_at timestamp, so a DSO can post
--    something as a dated event (an info session, a Q&A) instead of only a
--    plain, undated announcement — both render to students the same way
--    otherwise, just sorted/highlighted differently when event_at is set.
-- 2. custom_reminders is a new table for arbitrary DSO-authored reminders
--    with a due date (e.g. "report your enrolled courses by Sept 5",
--    "OPT unemployment limit tracking") — the generic version of the
--    hardcoded visa/passport expiration reminders every student already gets.
--
-- Run this once in the Supabase SQL editor (after 001-004).

alter table announcements add column if not exists event_at timestamptz;

create table if not exists custom_reminders (
  id          uuid primary key default gen_random_uuid(),
  college_id  uuid not null references colleges(id),
  author_id   uuid references users(id),
  title       text not null,
  detail      text not null,
  due_date    date not null,
  created_at  timestamptz not null default now()
);

create index if not exists custom_reminders_college_idx on custom_reminders (college_id, due_date);

alter table custom_reminders enable row level security;

drop policy if exists custom_reminders_same_college on custom_reminders;
create policy custom_reminders_same_college on custom_reminders
  using (college_id::text = (auth.jwt() ->> 'college_id'));
