-- colleges and users had RLS *enabled* in 001_init.sql but no policy was ever
-- defined for either — every other tenant-scoped table (students,
-- announcements, messages, graduation_aggregates, custom_reminders) got a
-- same-college policy alongside `enable row level security`, but these two
-- were missed. With RLS on and no policy, Postgres denies all rows to any
-- non-service-role caller, which happens to be harmless today (the app only
-- ever reads these via the service-role client in shared/db.py, which
-- bypasses RLS regardless) — but it's an inconsistency worth closing so the
-- defense-in-depth layer actually covers every table uniformly, in case a
-- future code path ever queries with a user's own JWT via
-- shared/db.py::get_auth_client() instead of the service client.
--
-- Same caveat as every other policy in this schema (see migrations/009 and
-- migrations/README.md's Row-Level Security note): this only does anything
-- once the JWT college_id claim hook is enabled in the Supabase dashboard.
-- Until then these policies, like all the others, are dormant.
--
-- Run this once in the Supabase SQL editor (after 001-011).

drop policy if exists colleges_own_college on colleges;
create policy colleges_own_college on colleges
  for select
  using (id::text = (auth.jwt() ->> 'college_id'));

drop policy if exists users_same_college on users;
create policy users_same_college on users
  for select
  using (college_id::text = (auth.jwt() ->> 'college_id'));

-- audit_logs is deliberately left with RLS enabled and no policy (deny-all):
-- it's an internal record never meant to be read directly by a student or DSO
-- JWT, only via the service-role client. No policy needed here.
