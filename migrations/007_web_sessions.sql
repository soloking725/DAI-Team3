-- Persisted "remember me" login sessions.
--
-- A full page reload opens a brand-new Streamlit connection, which wipes
-- st.session_state (and with it, the logged-in user) — there was previously
-- no way to survive that in hosted mode without re-entering a fresh OTP code.
-- This table backs a browser cookie holding only this random opaque token
-- (never the raw Supabase JWT/refresh token), so a leaked cookie can be
-- revoked here without touching Supabase Auth itself. See shared/auth.py.
--
-- Run this once in the Supabase SQL editor (after 001-006).

create table if not exists web_sessions (
  token       text primary key,
  user_id     uuid not null references users(id) on delete cascade,
  created_at  timestamptz not null default now(),
  expires_at  timestamptz not null
);

create index if not exists web_sessions_user_id_idx on web_sessions(user_id);

alter table web_sessions enable row level security;

-- Defense-in-depth, same pattern as other tables — the app enforces the
-- actual check with the service-role client in shared/db.py.
drop policy if exists web_sessions_own_row on web_sessions;
create policy web_sessions_own_row on web_sessions
  using (user_id::text = (auth.jwt() ->> 'sub'));
