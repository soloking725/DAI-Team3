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
   recorded when a DSO marks a student graduated), and
   `migrations/005_reminders_and_events.sql` (event-tagged announcements plus
   DSO-authored custom reminders) — same process, run once each.

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
`shared/auth.py`. The policies only take effect if you later expose the anon key
to the browser or issue per-user JWTs — and they assume a `college_id` custom
claim in the JWT, which requires a Supabase **auth hook** to populate. That hook
is a post-MVP item; for the pilot, the app-level checks are the authoritative
control.

## Smoke test after setup

- Sign in with a `@example.edu` email → get code → verify → land on the timeline.
- Sign in with a DSO email (in `DSO_EMAILS`) → open `pages/20_DSO_Dashboard.py` →
  see the roster, override a step, post an announcement.
- Confirm rows land in `students`, `announcements`, and `audit_logs` in the
  Supabase table editor.
