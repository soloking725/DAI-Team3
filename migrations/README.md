# Vera hosted-mode setup (B2B MVP)

The app runs in **local mode** by default (no accounts, state in `local/*.json`).
Setting the Supabase environment variables switches it to **hosted mode**
(email-OTP login, Postgres backend, DSO dashboard). Nothing else in the app
changes — `shared/persistence.py` and `shared/auth.py` switch backends behind
stable function signatures.

## One-time setup

1. **Create a Supabase project** at https://supabase.com (free tier is enough for
   a pilot).

2. **Run the schema.** Open the project's SQL editor and paste all of
   `migrations/001_init.sql`, then run it. Also run, in order:
   `migrations/002_messages.sql` (DSO <-> student direct messaging),
   `migrations/003_college_guide_steps.sql` (admin-uploaded school guide steps),
   `migrations/004_graduation_aggregates.sql` (anonymized cohort stats
   recorded when a DSO marks a student graduated),
   `migrations/005_reminders_and_events.sql` (event-tagged announcements plus
   DSO-authored custom reminders),
   `migrations/006_chat_rate_limits.sql` (persisted per-user chat rate
   limiting), `migrations/007_web_sessions.sql` ("remember me" login
   persistence across page reloads), `migrations/008_school_years.sql`
   (entering/graduation year, for graduating a whole cohort at once),
   `migrations/009_jwt_college_claim.sql` (makes the RLS policies below
   actually enforceable — see the Row-Level Security note),
   `migrations/010_visa_passport_expiration.sql` (denormalizes student-entered
   visa/passport expiration dates onto the students row for the DSO roster),
   `migrations/011_reminder_targeting.sql` (lets a DSO scope a custom reminder
   to a visa type and/or timeline step instead of always broadcasting to
   everyone), `migrations/012_rls_completeness.sql` (adds the same-college
   RLS policy that `colleges` and `users` were missing — every other
   tenant-scoped table already had one), `migrations/013_messaging_inbox.sql`
   (per-thread read tracking for unread badges, plus a length cap on message/
   announcement bodies), and `migrations/014_otp_rate_limits.sql` (a
   per-domain rate limit on login-code sends, so a script can't cheaply spam
   codes to many fake usernames at an allowed domain) — same process, run
   once each.

3. **Seed your colleges.** A user's email domain decides which college they join,
   so you can run more than one — e.g. a throwaway test college alongside the
   real pilot school:
   ```sql
   insert into colleges (name, email_domain) values
     ('Example College', 'gmail.com'),      -- testing only; remove before launch
     ('Colby College',   'colby.edu');      -- the real pilot
   ```
   Students and DSOs only ever see data for the college their domain maps to, so
   the two stay isolated.

   > ⚠️ A public domain like `gmail.com` means *anyone* with a Gmail address can
   > sign in and land in that college. Fine while you're testing; delete that row
   > before real student data exists.

4. **Set environment variables** (in `.env` locally, or as Streamlit Cloud
   secrets in production):
   ```
   SUPABASE_URL=https://<project>.supabase.co
   SUPABASE_ANON_KEY=<anon public key>
   SUPABASE_SERVICE_KEY=<service_role key>   # server-side only, never ship to the browser
   ALLOWED_EMAIL_DOMAINS=gmail.com,colby.edu # who may request a login code
   DSO_EMAILS=you@gmail.com,dso@colby.edu    # these emails get the 'dso' role
   ```
   `ALLOWED_EMAIL_DOMAINS` is just a cheap guard so codes aren't emailed to
   arbitrary addresses; the authoritative check is the `colleges` lookup above.
   Leave it blank to skip the pre-check.
   Find the keys under **Project Settings → API**. Install the client with
   `pip install -r requirements.txt` (adds `supabase`).

5. **Enable email auth.** In Supabase **Authentication → Providers**, make sure
   Email is enabled. The app uses the 6-digit **OTP code** flow (not magic
   links), which works inside Streamlit without redirect handling.

## Row-Level Security note

`001_init.sql` enables RLS with `college_id`-based policies as defense-in-depth.
The app itself connects with the **service key** (which bypasses RLS) and
enforces isolation with explicit `college_id` filters + role checks in
`shared/auth.py` — that remains the primary, authoritative control; RLS is a
second, independent layer underneath it, not a replacement for it.

That second layer only actually does anything once the JWTs issued at login
carry a `college_id` claim, since that's what every policy above checks via
`auth.jwt() ->> 'college_id'`. **This now requires one manual step no SQL file
can do for you:**

1. Run `migrations/009_jwt_college_claim.sql` (defines the claim-populating
   function and grants Supabase's auth service permission to call it).
2. In the Supabase dashboard: **Authentication → Hooks → Customize Access
   Token (JWT) Claims hook** → hook type **Postgres** (not HTTPS — the
   function already lives in your database, there's no external endpoint)
   → select `public.custom_access_token_hook` → enable it.
3. Sign out and back in (existing sessions/cookies were issued before the
   claim existed, so they won't have it until a fresh token is minted) and
   confirm in a JWT decoder (e.g. jwt.io) that the token now has a
   `college_id` claim matching the signed-in user's college.

Until step 2 is done in the dashboard, the function sits there unused and the
policies stay exactly as dormant as before — the SQL migration alone doesn't
turn anything on.

## Smoke test after setup

- Sign in with a `@example.edu` email → get code → verify → land on the timeline.
- Sign in with a DSO email (in `DSO_EMAILS`) → open `pages/20_DSO_Dashboard.py` →
  see the roster, override a step, post an announcement.
- Confirm rows land in `students`, `announcements`, and `audit_logs` in the
  Supabase table editor.
