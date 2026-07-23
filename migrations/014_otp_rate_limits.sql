-- Server-side rate limit on OTP sends, keyed by the requested email's
-- *domain* rather than the individual email address.
--
-- Today nothing stops a script from hitting "Send code" for hundreds of
-- different not-necessarily-real addresses at an allowed domain
-- (jane1@colby.edu, jane2@colby.edu, ...) — shared/auth.py's existing
-- cooldown lives in st.session_state, which is trivially reset by opening a
-- new tab/incognito window, so it stops nothing. A per-email limit wouldn't
-- help either, since each fake address only gets hit once. This caps total
-- OTP sends *per domain* in a rolling window instead, which is what
-- actually bounds "iterate through many fake usernames at a known domain."
--
-- Run this once in the Supabase SQL editor (after 001-013).

create table if not exists otp_send_log (
  domain         text primary key,
  window_start   timestamptz not null default now(),
  request_count  int not null default 0
);

alter table otp_send_log enable row level security;

-- Service-role only (the app never queries this with a user's own JWT) —
-- deny-all default with no policy is intentional, same as audit_logs.
