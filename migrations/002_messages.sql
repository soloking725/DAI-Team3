-- Direct 1:1 messaging between a DSO and a student.
-- Run this once in the Supabase SQL editor (after 001_init.sql).

create table if not exists messages (
  id           uuid primary key default gen_random_uuid(),
  college_id   uuid not null references colleges(id),
  sender_id    uuid not null references users(id),
  recipient_id uuid not null references users(id),
  body         text not null,
  created_at   timestamptz not null default now()
);

create index if not exists messages_college_idx on messages (college_id, created_at);
create index if not exists messages_sender_idx on messages (sender_id, created_at);
create index if not exists messages_recipient_idx on messages (recipient_id, created_at);

alter table messages enable row level security;

-- Defense-in-depth, same pattern as other tenant-scoped tables (see
-- migrations/001_init.sql) — the app itself enforces access with the
-- service-role client + explicit college_id/sender/recipient checks.
drop policy if exists messages_same_college on messages;
create policy messages_same_college on messages
  using (college_id::text = (auth.jwt() ->> 'college_id'));
