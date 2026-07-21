-- Persisted, per-user chat rate limiting.
--
-- shared/chat_panel.py already rate-limits via st.session_state, but that
-- counter is per-browser-session — a logged-in student opening a new tab (or
-- logging out and back in) gets a fresh, empty counter for free, since
-- st.session_state doesn't survive a new session. This table gives hosted-mode
-- users a counter that survives that, keyed by their durable user_id instead
-- of the ephemeral session. Local mode has no accounts to key on, so it's
-- unaffected and keeps using the session-only check.
--
-- Run this once in the Supabase SQL editor (after 001-005).

create table if not exists chat_rate_limits (
  user_id        uuid primary key references users(id) on delete cascade,
  window_start   timestamptz not null default now(),
  request_count  int not null default 0
);

alter table chat_rate_limits enable row level security;

-- Defense-in-depth, same pattern as other tenant-scoped tables — the app
-- enforces the actual limit with the service-role client in shared/db.py.
drop policy if exists chat_rate_limits_own_row on chat_rate_limits;
create policy chat_rate_limits_own_row on chat_rate_limits
  using (user_id::text = (auth.jwt() ->> 'sub'));
