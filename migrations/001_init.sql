-- Vera hosted-mode schema (B2B MVP)
-- Run this once in the Supabase SQL editor for a new project.
--
-- Design: one pilot college for the MVP, but college_id is present on every
-- tenant-scoped table so adding a second college later is a data change, not a
-- schema rewrite. The student's app state is stored as a JSON blob in
-- students.full_state (the app's source of truth) plus denormalized columns the
-- DSO dashboard filters on in SQL.

create extension if not exists "pgcrypto";

-- Colleges ------------------------------------------------------------------
create table if not exists colleges (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  email_domain  text not null unique,          -- e.g. 'colby.edu'
  guide_pdf_url text,
  created_at    timestamptz not null default now()
);

-- App-level users (1:1 with Supabase auth.users) ---------------------------
create table if not exists users (
  id          uuid primary key references auth.users(id) on delete cascade,
  college_id  uuid not null references colleges(id),
  role        text not null default 'student' check (role in ('student','dso')),
  name        text default '',
  email       text not null,
  created_at  timestamptz not null default now()
);

-- Student state -------------------------------------------------------------
-- full_state is the app's vera-state blob; the other columns are denormalized
-- from it on every save (see shared/db.py) for fast dashboard filtering.
create table if not exists students (
  user_id             uuid primary key references users(id) on delete cascade,
  college_id          uuid not null references colleges(id),
  visa_type           text,
  origin_country      text,
  destination         text,
  school              text,
  current_step_key    text,
  current_step_status text,
  extenuating_flags   jsonb not null default '{}'::jsonb,
  full_state          jsonb not null default '{}'::jsonb,
  updated_at          timestamptz not null default now()
);

create index if not exists students_college_idx on students (college_id);
create index if not exists students_step_idx     on students (college_id, current_step_key);

-- Keep updated_at fresh on every write.
create or replace function set_updated_at() returns trigger as $$
begin new.updated_at = now(); return new; end;
$$ language plpgsql;

drop trigger if exists students_updated_at on students;
create trigger students_updated_at before update on students
  for each row execute function set_updated_at();

-- Announcements (DSO -> students) ------------------------------------------
create table if not exists announcements (
  id         uuid primary key default gen_random_uuid(),
  college_id uuid not null references colleges(id),
  author_id  uuid references users(id),
  body       text not null,
  created_at timestamptz not null default now()
);
create index if not exists announcements_college_idx on announcements (college_id, created_at desc);

-- Audit log (append-only) ---------------------------------------------------
create table if not exists audit_logs (
  id         uuid primary key default gen_random_uuid(),
  actor_id   uuid references users(id),
  action     text not null,               -- 'login' | 'view_roster' | 'edit_step' | ...
  target_id  uuid,
  detail     jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists audit_actor_idx on audit_logs (actor_id, created_at desc);

-- Row-Level Security --------------------------------------------------------
-- Defense-in-depth. The app talks to Postgres with the SERVICE key (which
-- bypasses RLS) and enforces access with explicit college_id filters + role
-- checks in shared/auth.py. These policies matter if you ever expose the ANON
-- key to the browser or add per-user JWT access. They assume a 'college_id'
-- custom claim in the JWT — add a Supabase auth hook to populate it before
-- relying on them (see migrations/README.md).
alter table colleges     enable row level security;
alter table users        enable row level security;
alter table students     enable row level security;
alter table announcements enable row level security;
alter table audit_logs   enable row level security;

-- Example tenant-isolation policy (repeat pattern per table as needed):
drop policy if exists students_same_college on students;
create policy students_same_college on students
  using (college_id::text = (auth.jwt() ->> 'college_id'));

drop policy if exists announcements_same_college on announcements;
create policy announcements_same_college on announcements
  using (college_id::text = (auth.jwt() ->> 'college_id'));

-- Seed the pilot college (edit the values, then run). --------------------
-- insert into colleges (name, email_domain)
-- values ('Example College', 'example.edu')
-- on conflict (email_domain) do nothing;
