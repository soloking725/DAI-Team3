-- Anonymized, aggregate-only record of a graduated student's cohort stats.
-- No name, email, or user_id — this table exists so a school can learn from
-- pattern-level data (which visa types/origins/steps students struggled with)
-- without retaining an individually identifiable record after graduation.
-- Written by shared/db.py's graduate_and_anonymize(), which immediately
-- hard-deletes the source student's account in the same operation.
-- Run this once in the Supabase SQL editor (after 001_init.sql, 002_messages.sql,
-- 003_college_guide_steps.sql).

create table if not exists graduation_aggregates (
  id                         uuid primary key default gen_random_uuid(),
  college_id                 uuid not null references colleges(id),
  visa_type                  text,
  origin_country             text,
  final_step_key             text,
  had_flagged_circumstances  boolean not null default false,
  cohort_year                int not null,
  created_at                 timestamptz not null default now()
);

create index if not exists graduation_aggregates_college_idx
  on graduation_aggregates (college_id, cohort_year);

alter table graduation_aggregates enable row level security;

drop policy if exists graduation_aggregates_same_college on graduation_aggregates;
create policy graduation_aggregates_same_college on graduation_aggregates
  using (college_id::text = (auth.jwt() ->> 'college_id'));
