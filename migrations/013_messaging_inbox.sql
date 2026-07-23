-- Messaging inbox support: per-thread read tracking (for unread badges/alerts)
-- and a length cap on message/announcement bodies (previously unbounded text,
-- which let a very long message or announcement bloat the page and the DB
-- row indefinitely).
-- Run this once in the Supabase SQL editor (after 001-012).

-- One row per (viewer, counterpart) pair, upserted whenever that viewer opens
-- the thread. Unread = messages from other_user_id newer than last_read_at
-- (or the whole thread, if no row exists yet) — cheaper than a per-message
-- read flag, and it's the same "last seen this conversation at T" model most
-- inbox UIs (Slack, Instagram DMs) use instead of per-message receipts.
create table if not exists thread_reads (
  user_id       uuid not null references users(id),
  other_user_id uuid not null references users(id),
  college_id    uuid not null references colleges(id),
  last_read_at  timestamptz not null default now(),
  primary key (user_id, other_user_id)
);

create index if not exists thread_reads_college_idx on thread_reads (college_id);

alter table thread_reads enable row level security;

-- Same dormant-until-JWT-claim-hook caveat as every other policy here (see
-- migrations/009 and the Row-Level Security note in migrations/README.md).
drop policy if exists thread_reads_own_row on thread_reads;
create policy thread_reads_own_row on thread_reads
  using (user_id::text = (auth.jwt() ->> 'sub'));

-- Bound both free-text bodies that were plain unbounded `text` before —
-- 4000 chars is generous for a support message/announcement but keeps a
-- single row (and a single rendered message) from growing without limit.
-- ("IF NOT EXISTS" isn't valid on ADD CONSTRAINT, so guard via pg_constraint
-- instead, to keep this file safely re-runnable like the rest of migrations/.)
--
-- Added NOT VALID: a plain ADD CONSTRAINT scans and rejects the *whole*
-- alter if even one existing row already exceeds 4000 chars, which is
-- exactly what happened the first time this was run against real data.
-- NOT VALID skips that historical scan — the constraint still applies to
-- every new insert/update from this point on (that's the actual goal: stop
-- new unbounded messages), it just doesn't retroactively fail on old rows.
-- If you want it fully enforced (including old rows), first find and trim
-- the offenders, then run:
--   alter table messages validate constraint messages_body_length;
--   alter table announcements validate constraint announcements_body_length;
-- Locate them first with something like:
--   select id, char_length(body) from messages where char_length(body) > 4000;
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'messages_body_length') then
    alter table messages add constraint messages_body_length check (char_length(body) <= 4000) not valid;
  end if;
  if not exists (select 1 from pg_constraint where conname = 'announcements_body_length') then
    alter table announcements add constraint announcements_body_length check (char_length(body) <= 4000) not valid;
  end if;
end $$;
