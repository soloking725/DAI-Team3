-- Makes the RLS policies in 001_init.sql (and every migration since) actually
-- enforceable, by populating the `college_id` custom claim they check via
-- `auth.jwt() ->> 'college_id'`. Without this, that claim is always null, so
-- those policies never match any row for any authenticated user — RLS is
-- "on" but silently a no-op, and the service-role client (which bypasses RLS
-- entirely) plus the college_id filters in shared/db.py are the only real
-- access control. This closes that gap: RLS becomes a genuine second,
-- independent layer, not just a dormant policy sitting on top of nothing.
--
-- This does NOT change how the app talks to Postgres — shared/db.py keeps
-- using the service key, and the college_id filters in shared/db.py remain
-- the primary, authoritative check. This is defense-in-depth: if a future
-- query in shared/db.py ever forgot a college_id filter, or if the anon key
-- is ever used for a direct client-side query later, RLS now independently
-- blocks cross-college access instead of silently allowing it.
--
-- Run this once in the Supabase SQL editor (after 001-008), THEN enable the
-- hook in the dashboard — see migrations/README.md for the manual step this
-- SQL alone can't do (Supabase Auth Hooks are wired up in the dashboard, not
-- via SQL).

-- security definer: this runs with the privileges of the function's OWNER
-- (whichever role runs this migration — typically postgres/the project
-- owner, which bypasses RLS), not the caller's (supabase_auth_admin).
-- That's required, not just convenient: `users` has RLS enabled with no
-- policy granting supabase_auth_admin access (see 001_init.sql), so without
-- security definer the lookup below would silently return no rows on every
-- login — the claim would stay null and this migration would look like it
-- worked while actually changing nothing.
-- set search_path = '' + fully-qualified names: the standard hardening for
-- security definer functions, so a role earlier in some other search_path
-- can't shadow `public.users` with a same-named table to hijack this lookup.
create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
  claims          jsonb;
  user_college_id uuid;
  user_role       text;
begin
  select college_id, role
    into user_college_id, user_role
  from public.users
  where id = (event->>'user_id')::uuid;

  claims := coalesce(event->'claims', '{}'::jsonb);

  if user_college_id is not null then
    claims := jsonb_set(claims, '{college_id}', to_jsonb(user_college_id::text));
  end if;
  if user_role is not null then
    claims := jsonb_set(claims, '{role}', to_jsonb(user_role));
  end if;

  return jsonb_set(event, '{claims}', claims);
end;
$$;

-- Supabase's Auth service (running as supabase_auth_admin) is the only
-- caller that should ever be able to invoke this — it runs on every token
-- issuance/refresh and its output becomes the JWT everything else trusts,
-- so nothing else (including the app's own authenticated/anon roles) should
-- be able to call it directly.
grant usage on schema public to supabase_auth_admin;
grant execute on function public.custom_access_token_hook to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook from authenticated, anon, public;
