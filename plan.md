# Vera — Product Plan (B2C + B2B MVP)

*Supersedes the previous version of this file and `new_plan.md`. Both are folded in here; `new_plan.md` can be deleted once you're happy with this doc.*

## Direct answers first

- **Will it still run on Streamlit Cloud?** Yes, if the MVP is scoped the way this plan scopes it. Streamlit Cloud cannot run background workers, hold WebSocket connections, or persist local files across redeploys — that part of `new_plan.md` was correct. The fix isn't to leave Streamlit; it's to stop asking Streamlit to do those three things. Everything else (auth, database, file storage, per-college dashboards) works fine from inside a normal Streamlit request.
- **Can the backend "work"?** Yes, but "backend" for the MVP should mean **Supabase (managed Postgres + Auth + Storage), called directly from Streamlit** — not a separate FastAPI service. `new_plan.md` jumped straight to FastAPI + Redis + Celery + Vault + SAML, which is the right *eventual* architecture for a multi-college SaaS product but is roughly 10x the build for a one-school pilot. A dedicated API layer becomes worth it once a college wants to pull data into their own SIS, or once you have a second frontend — not before.
- **Privacy statement** — needs a real rewrite once accounts exist, because "no accounts or logins" (the current page's first line) becomes false. Draft copy is in [Privacy policy rewrite](#privacy-policy-rewrite) below, to ship in the same PR as auth.
- **What was wrong in the two source docs?** See [Corrections to the original plans](#corrections-to-the-original-plans) — mainly: `new_plan.md`'s "future" section (part 4) is written as if it's all needed at once; it isn't, and treating it that way would stall the pilot for months.

---

## Current state

Vera is a Streamlit prototype that walks an international student through onboarding (name, visa type, origin/destination country, school) and an extenuating-circumstances checklist, then shows a personalized visa timeline with an embedded RAG chatbot. Navigation (hamburger menu + a "Vera" brand link back to the timeline) is consistent across every page. Five older static info pages (F-1/J-1/M-1/Post-Arrival/About) share the same design system as onboarding.

The RAG knowledge base covers F-1/J-1/M-1 entering the US, sourced from USCIS, State Dept, SEVP, SSA, IRS. Retrieval supports a visa-type filter and an origin-country dimension (5 countries hand-authored so far) plus extenuating-circumstances guidance. There are **no user accounts** — a session is a random ID in the URL (`?vid=...`), persisted to `local/vera_sessions/<vid>.json`. No test suite, linter, or CI.

## MVP scope: what "MVP" means here

The MVP is **one pilot college**, not a general multi-tenant product. This is the single biggest scoping decision and it cascades into everything else — auth, data model, UI, and what infrastructure you actually need.

**Beachhead college.** Build and test against a placeholder ("Example College") in dev, but design every college-specific piece — `email_domain`, seeded `colleges` row, top origin countries below — to be trivially re-pointed at a real target like Colby. Nothing in the schema or auth flow should assume "Example College" beyond one row of config, so swapping in the real pilot school later is a data change, not a code change.

**Destination: US only.** Vera stays scoped to students entering the *United States* — this was already the de facto behavior (`shared/retrieval.py`'s content is exclusively USCIS/State Dept/SEVP/SSA/IRS, and `pages/16_Other_Visa_Coming_Soon.py` already catches non-F-1/J-1/M-1 intent) but should be made an explicit, permanent product boundary rather than a "coming soon" placeholder implying other destinations are on the roadmap. This matches the beachhead: American colleges are the buyer, so "entering the US" is the whole product, not a v1 subset of a bigger vision. Remove/repurpose the "coming soon" framing accordingly — it should read as "not supported" for non-US destinations rather than "not yet."

**In scope for MVP:**
- Google/email login for students and DSOs (Supabase Auth), gated by school email domain
- Real database (Supabase Postgres) replacing `local/*.json`
- A DSO dashboard: student roster, per-student current step, manual status override, simple filters
- School guide as a **download link only** (no PDF parsing/step-extraction in MVP)
- An announcements/message board DSOs can post to, students see on their timeline (replaces "emails get lost")
- Daily email reminders for overdue timeline steps, run via a scheduled GitHub Action (not inside Streamlit)
- Basic audit log (who viewed/edited which student record)
- Updated privacy policy + a short pilot-school Terms of Service / Data Processing note
- Post-visa / post-arrival steps added to the timeline template (explicitly called out as important for B2B in both source docs and currently missing — `shared/timeline_data.py` stops at "visa issued")
- **Origin-country (embassy/consulate) content, expanded to 15 countries.** Every country's F-1/J-1/M-1 applicants go through the *same* US-side process (USCIS/State Dept/SEVP), but the *origin*-side steps — which embassy/consulate handles it, typical interview wait times, local document requirements — genuinely differ per country, and retrieval already has an `origin_country` filter built for exactly this (`shared/retrieval.py`). Today only 5 countries have real content (`COMMON_ORIGIN_COUNTRIES` in `shared/countries.py`: India, China, Nigeria, Brazil, South Korea). MVP list, chosen for a mix of proven top-sender volume (IIE Open Doors data) and regional diversity, using this repo's existing spellings from `shared/countries.py`: **China, South Korea, India, Turkey, Germany, United Kingdom, Spain, France, Nigeria, Ghana, Argentina, Brazil, Mexico, Canada, Vietnam.** Rather than the ~190-country scrape `new_plan.md` implied, this covers the large majority of a typical liberal-arts college's international population without a global crawl — extend `ingest.py` with the same `travel.state.gov` embassy-subpage pattern used for the existing 5, and add all 15 to `COMMON_ORIGIN_COUNTRIES` so the onboarding dropdown surfaces exactly the countries that have real content. If the actual pilot college's student mix turns out to need a country not on this list, that's a small follow-up, not a redesign. Full global coverage stays [post-MVP](#post-mvp-roadmap).

**Explicitly out of scope for MVP** (deferred to [Post-MVP roadmap](#post-mvp-roadmap)):
- Multi-college self-serve signup, per-college branding/billing
- Any destination country besides the US
- PDF parsing into timeline steps
- Real-time push/WebSockets — announcements are pulled on page load/rerun, not pushed
- SIS integration / CSV bulk import / REST API for external systems
- Cohort/semester templating (one shared timeline template is fine for one pilot college's cohort)
- Redis, Celery, Vault, SAML/OIDC, Row-Level Security in Chroma — all real needs *at multi-college scale*, all unnecessary complexity at one-college scale
- Sub-roles within a DSO team (admin/editor/viewer) — one DSO role is enough for a pilot
- Origin-country content beyond the pilot college's actual student mix (full ~190-country coverage)

---

## Architecture for the MVP

```
Streamlit Cloud (frontend + all app logic, as today)
        │
        ├── Supabase Postgres  — students, colleges(=1 row), timeline_steps,
        │                        announcements, audit_logs
        ├── Supabase Auth      — email magic-link login, domain-restricted
        ├── Supabase Storage   — school guide PDF (link-only, no parsing)
        └── ChromaDB (local, as today) — RAG knowledge base, unchanged
                                          (no college_id filter needed yet — one tenant)

GitHub Actions (scheduled, outside Streamlit)
        ├── existing ingest.py / update_checker.py cron (already designed to run standalone)
        └── new: daily reminder script — queries Supabase for overdue steps,
                 sends email via Resend/SendGrid API
```

Why Supabase over raw AWS building blocks:
- One vendor for Postgres + Auth + Storage instead of three (Postgres host + OAuth app + S3/R2 bucket), which is a lot of manual console setup for a pilot.
- Supabase Auth's email magic-link flow needs **no Google Cloud OAuth app registration** — just an email domain allow-list. `new_plan.md` specified Google SSO via a manually-registered OAuth client; that's more setup for no real MVP benefit. Keep Google OAuth as a later option, not a blocker.
- `supabase-py` is called directly from Streamlit request code — no separate service to deploy, monitor, or auth against.

Why this still fits Streamlit Cloud's constraints:
- No background process runs *inside* Streamlit. The reminder job is a GitHub Action that talks to Supabase and the email API directly; Streamlit only ever reads what's already in the DB.
- No WebSocket requirement. Announcements are just rows in a table, read on each page load — acceptable latency for "DSO posted something," not acceptable for a chat-like experience, which nothing here requires.
- Streamlit Cloud's ephemeral filesystem stops being a problem because state moves to Supabase; `chroma_db/` remains local/ephemeral, which is fine since it's a rebuildable knowledge base, not user data.

---

## Data model (Supabase Postgres)

> **Implemented** — the authoritative version of this schema now lives in [`migrations/001_init.sql`](migrations/001_init.sql), with setup instructions in [`migrations/README.md`](migrations/README.md). The sketch below is kept for context; where the two differ, the migration file wins.
>
> **One deliberate change from the original sketch:** there is no separate `timeline_steps` table. A student's timeline lives inside a `students.full_state` JSONB column (the app's source of truth, round-trips losslessly), alongside *denormalized* columns — `visa_type`, `origin_country`, `current_step_key`, `current_step_status` — that the DSO dashboard filters and sorts on in SQL. This gives the dashboard the real SQL queries it needs without a second table that has to be kept in sync with the blob on every write, which was the main correctness risk in the original design. `shared/db.py::_denormalize()` is the single place that derives those columns, and it's called on every save.

Minimal schema for one pilot college — deliberately not designed for N colleges yet, but with enough headroom (`college_id` present everywhere) that adding a second college later is a data problem, not a schema rewrite.

```sql
colleges (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  email_domain  text not null,        -- e.g. 'colby.edu' — used to route Auth
  guide_pdf_url text                  -- Supabase Storage public/signed URL
)

users (
  id            uuid primary key references auth.users(id),
  college_id    uuid references colleges(id),
  role          text not null check (role in ('student','dso')),
  name          text,
  email         text not null
)

students (
  user_id           uuid primary key references users(id),
  visa_type         text,
  origin_country    text,
  destination       text,
  extenuating_flags jsonb default '[]',
  created_at        timestamptz default now()
)

timeline_steps (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid references users(id),
  step_key     text not null,          -- matches TIMELINE_TEMPLATES key
  status       text not null default 'upcoming',  -- upcoming/in_progress/complete
  updated_by   text not null default 'student',    -- 'student' | 'dso'
  updated_at   timestamptz default now()
)

announcements (
  id           uuid primary key default gen_random_uuid(),
  college_id   uuid references colleges(id),
  author_id    uuid references users(id),
  body         text not null,
  created_at   timestamptz default now()
)

audit_logs (
  id           uuid primary key default gen_random_uuid(),
  actor_id     uuid references users(id),
  action       text not null,          -- 'view_student' | 'edit_step' | 'export_csv' etc
  target_id    uuid,
  created_at   timestamptz default now()
)
```

Row-Level Security: turn it on with a simple `college_id = auth.jwt() ->> 'college_id'` policy on every table now, even with one college. It costs nothing to write today and means the schema is already safe if a second college is added later — this is the one piece of `new_plan.md`'s security section worth doing early rather than deferring, since it's cheap now and expensive to retrofit.

`shared/persistence.py` gets rewritten against this schema behind the same function names (`get_vera_state`, `save_session`, etc.) so the rest of the app — `vera_state.py`, `timeline.py`, `timeline_ui.py` — doesn't need to change its calling code, only its storage layer.

---

## Auth design

- Supabase Auth, email magic link. On first login, look up the user's email domain against `colleges.email_domain`; if it matches, create a `users` row with `role='student'`. DSOs are seeded manually (a hardcoded allow-list of DSO emails for the pilot, or a `role` flip done directly in the Supabase table editor) — no self-serve "become a DSO" flow for the MVP.
- Non-matching domains see "Not authorized for this pilot" — matches `new_plan.md`'s scoping, kept as-is.
- Session comes from Supabase's JWT, not the current `?vid=` URL param. `get_or_create_session_id()` in `shared/vera_state.py` is retired; `st.session_state` gets the authenticated user id instead.

## DSO dashboard

New page, `pages/20_DSO_Dashboard.py` (the `20_` prefix reserves a numeric block for admin-only pages, same convention the repo already uses for grouping — see [Site structure](#site-structure-for-the-mvp)). Visible only to `role='dso'`; hidden from the hamburger menu and chat for students.

- Roster table (`st.dataframe`): name, visa type, current step, last updated. Filter by step/status — this is a straightforward Postgres query (`WHERE college_id = ... AND status = ...`), not the "loop through 200 JSON files" problem `new_plan.md` correctly flagged against the *old* persistence layer.
- Per-student override: dropdown to change a step's status, writes `updated_by='dso'` so the UI can show "manually updated by your school" — adopts `new_plan.md`'s call to skip a full student-vs-DSO conflict workflow for MVP and just let DSO overrides win.
- Announcement composer: a text box that inserts a row into `announcements`. Students see the latest N announcements on their timeline page.
- Every dashboard view/edit action writes one row to `audit_logs` — cheap, and it's the single most-requested compliance feature colleges will ask about first.

## File storage

School guide PDF: DSO uploads once via the dashboard, stored in Supabase Storage, `colleges.guide_pdf_url` updated. Student timeline page shows a "Download your school's guide" button. `shared/pdf_guide.py`'s LLM-based step extraction is **not used** in the MVP flow — this sidesteps Streamlit Cloud's ~60s request timeout entirely, which is the correct call both source docs converged on.

## Communication & reminders

- **Announcements** (above) cover the "emails get lost" DSO→student case without needing real-time infra.
- **Reminders**: a new small script (`scripts/send_reminders.py`) queries Supabase for students whose current step has been `upcoming`/`in_progress` for >N days, and calls Resend or SendGrid's HTTP API directly. Scheduled via a GitHub Actions cron workflow (`.github/workflows/reminders.yml`), same pattern the repo could also use for `update_checker.py`. No Celery/Redis needed at this scale — a single scheduled script covers a pilot-sized student list.
- **Repetitive questions**: out of scope for MVP as an FAQ-caching layer (real feature, but not blocking), but the `announcements` board is a lightweight First step DSOs can use to broadcast an answer once instead of fielding it 40 times over email.

## Post-visa content

`shared/timeline_data.py`'s `TIMELINE_TEMPLATES` currently ends at "visa issued." Both source docs flag post-visa as important for B2B. For the MVP, extend each visa type's template with 3-5 post-arrival steps (SEVIS check-in, address update, on-campus employment authorization notes, etc.) sourced the same way existing steps are — this is content work using the existing pattern, not new architecture.

---

## Site structure for the MVP

Keep the existing conventions (`shared/` for logic, numeric-prefixed `pages/` for routes, `render_card`/`render_section` for static pages, `@st.fragment` for the chat widget) and extend them consistently rather than introducing a second style:

- `shared/db.py` — new module wrapping the Supabase client (`create_client`, one shared instance), all queries go through here rather than being scattered across pages.
- `shared/auth.py` — new module: `get_current_user()`, `require_role("dso")` guard used at the top of DSO-only pages, mirrors how `render_hamburger_menu()` is already called uniformly at the top of every page.
- `shared/persistence.py` — rewritten to call `shared/db.py` instead of `local/*.json`, same public function signatures so `vera_state.py`/`timeline.py`/`timeline_ui.py` don't need call-site changes.
- `pages/20_DSO_Dashboard.py` — new. Reserve `20-29` for admin/DSO-only pages so the numeric prefix continues to communicate page grouping the way it already does for onboarding (`10-12`) and utility pages (`13-16`).
- `pages/21_Announcements.py` *or* fold into the dashboard as a tab — lean toward a tab inside the dashboard rather than a new page, to avoid growing the hamburger menu with admin-only entries students should never see.
- `scripts/send_reminders.py` + `.github/workflows/reminders.yml` — new, outside the Streamlit app entirely, following the same "standalone script, not imported by the app" pattern already used by `ingest.py`/`update_checker.py`.
- `migrations/` — new directory holding the SQL from [Data model](#data-model-supabase-postgres) as versioned `.sql` files, run manually in the Supabase SQL editor for the MVP (a real migration tool like Alembic is post-MVP).
- Student-facing pages (`01-06`, `10-12`, `04` for chat+timeline) are otherwise **unchanged in structure** — auth swaps out the session-id plumbing underneath them, but the two-column chat+timeline layout, hamburger nav, and `@st.fragment` chat pattern all stay exactly as documented in `CLAUDE.md`.

This keeps one coherent design system and file-organization convention across both the B2C student flow and the new B2B dashboard, rather than the dashboard becoming a bolted-on second app.

---

## Privacy policy rewrite

`pages/14_Privacy.py` needs a rewrite once accounts ship — its current first line ("Vera doesn't use accounts or logins") becomes false. Draft replacement copy, to land in the same PR as the auth work:

> **Privacy**
> Vera uses your school email to sign you in. Here's what's stored, and who can see it.
>
> **Your account and profile** — Your name, school email, visa type, country of origin, destination, and any extenuating circumstances you flag are stored in Vera's database, linked to your school-issued login. Your school's international student office can see this information for students at your school — that's what makes the timeline and reminders work. Vera never shares it outside your school or sells it to anyone.
>
> **Your school's staff** — Your school's international student office (DSO) can view your timeline and update step statuses on your behalf (for example, if you email them a document directly). Every time staff view or edit a student's record, that access is logged.
>
> **Your school's guide** — If your school has uploaded a program guide, you'll see a download link to it. Vera doesn't read or extract content from it automatically.
>
> **Chat messages** — Questions you ask Vera are sent to Vera's language model provider to generate an answer, along with relevant official government context. [Decide for MVP: are chat messages persisted per-student for the DSO to review, or session-only as today? Recommendation below.]
>
> **What Vera doesn't do** — No third-party ad trackers, no data resale, no ID documents (like your I-20) collected or stored. Vera does not provide legal advice — see the disclaimer shown throughout the site.
>
> **Deleting your data** — You can request deletion of your account and data by contacting [pilot contact email]. We'll remove your personal data within 30 days.

**Open decision for you:** should chat history be visible to DSOs (useful for "what did this student ask, does staff need to follow up") or stay private/session-only like today (simpler, less privacy exposure, matches current promise)? This changes both the schema (a `chat_messages` table or not) and the privacy copy above. Recommend starting **private/session-only** for the MVP — matches the existing promise, avoids an extra sensitive-data table, and can be revisited if a pilot DSO specifically asks for it.

Alongside this, add a one-page **Data Processing note** for the pilot school (not full legal ToS) covering: what Vera stores, that it's not legal advice, and that staff are responsible for verifying anything before acting on it. A real Terms of Service / liability review is a legal task, not an engineering one — flag it to whoever owns that at Colby/DAI before onboarding a real pilot school with real student data.

---

## Corrections to the original plans

- **`new_plan.md`'s section 4 (A–J) reads as "needed for the future" but is written with the urgency of "needed now."** None of it blocks a one-college pilot: Celery/Redis background workers, SAML/OIDC, per-tenant billing, ChromaDB schema versioning, and SIS integration are real problems *at the point you have multiple paying colleges*, not before. Building them now would spend months on infrastructure no pilot user will ever exercise.
- **S3/R2 was specified for file storage; Supabase Storage is a better MVP fit** since you're already on Supabase for Postgres+Auth — one vendor, one set of credentials, no separate CORS/bucket configuration step.
- **Google OAuth app registration was listed as required manual setup; it isn't, for MVP.** Supabase's email magic-link auth needs no OAuth console work at all. Keep "Login with Google" as a nice-to-have, not a blocker — this removes an entire manual setup task from the MVP critical path.
- **RLS in Postgres and RLS-equivalent filtering in ChromaDB were treated as one problem; they're not, at MVP scale.** Postgres RLS is cheap to turn on now (do it). ChromaDB re-ingestion with a `college_id` filter is only necessary once there's a second college — deferred.
- **The rate-limiter concern ("resets on refresh") is real but not urgent at pilot scale.** A few dozen students asking a few questions a day won't need Redis; a simple per-user counter column in `users` (increment on each chat call, reset daily via the same GitHub Action that sends reminders) is enough for the MVP and avoids standing up Redis/Upstash early.
- **PDF parsing (`pdf_guide.py`) should be turned off, not fixed, for the MVP** — both source docs converge on this, and it's the right call: the underlying problem (Streamlit Cloud's ~60s timeout) isn't worth solving before there's a paying pilot asking for it.
- **"Absolutely no advice" note from `plan.md`'s Future Features list is already the system's design** (`SYSTEM_PROMPT` + `safeguards.py` per `CLAUDE.md`) — worth re-stating in the DSO-facing Data Processing note above so schools understand it's a hard product boundary, not a soft one.

## Remaining gaps found on final review

Smaller items that don't change the shape of the plan but should be handled during implementation, not skipped:

- **Escalation view was in both source docs' B2B roadmap but dropped out of this plan's DSO dashboard.** It's cheap given the data already modeled: `students.extenuating_flags` already exists, so add one filter/tab on the DSO dashboard — "students with flagged circumstances" — instead of deferring it post-MVP. Low effort, high value for a pilot DSO.
- **`shared/pdf_guide.py`'s LLM-extraction path should be deleted, not just unused**, once step 7 ships the link-only upload flow — per this repo's own convention (CLAUDE.md: no dead code, no backwards-compat shims), leaving it in place as an unreferenced code path would be exactly what to avoid, not a safe fallback.
- **`shared/db.py`'s Supabase client should be wrapped in `st.cache_resource`**, not created per-rerun — Streamlit reruns the whole script on every interaction, so an uncached client would reconnect constantly.
- **Destination dropdown in `shared/countries.py` still lists all ~190 countries even though the product is US-only.** Either trim `DESTINATION_COUNTRIES` down to just `["United States"]`, or keep the full list but make `pages/16_Other_Visa_Coming_Soon.py` explicitly say "not supported" rather than "coming soon" (per the destination-scope decision above) — pick one, don't leave the dropdown implying breadth the product doesn't have.
- **Edge case: a newly-admitted student may not have their school email yet** when they first want to start onboarding (F-1 prep often starts before enrollment is finalized). Domain-gated magic-link auth as scoped will block them. Worth deciding for the pilot: require the school email from day one (simplest, matches "beachhead college" scope, likely fine since a DSO can onboard students after acceptance), or allow a personal-email signup that a DSO later approves/links to a `college_id` (more flexible, more building). Recommend requiring school email for MVP and revisiting if the pilot DSO says it's a blocker.
- **No automated tests are added by this plan**, consistent with the repo's current state, but auth + a real DB is meaningfully riskier to hand-verify than the current prototype. At minimum, add one smoke script that exercises login → onboarding → DSO override → audit log write against a test Supabase project, even without a full test suite.

---

## Implementation plan (MVP, in order)

**Steps 1-3 and 5 are built** (see [Build status](#build-status) below). Remaining work starts at step 4.

1. ~~**Supabase project setup**~~ — SQL is written (`migrations/001_init.sql`) and documented (`migrations/README.md`); the *manual* part (create the project, run the SQL, seed the college, set secrets) is yours to do, ~1 hr.
2. ~~**`shared/db.py` + `shared/auth.py`**~~ — built. Email-OTP login rather than magic links (Streamlit can't read the URL fragment a magic link redirects with).
3. ~~**Rewrite `shared/persistence.py`**~~ — built as a *pluggable backend* rather than a hard cutover: Supabase when configured, local JSON otherwise. `shared/vera_state.py` needed no changes at all — the function signatures held.
4. **Onboarding flow update** (`pages/10_Trip_Details.py` etc.): gate the app behind login in hosted mode; the data already lands in the `students` table via the persistence layer.
5. ~~**DSO dashboard** (`pages/20_DSO_Dashboard.py`)~~ — built: roster, filters (including the flagged-circumstances filter), step override, announcement composer, audit writes.
6. **Student-side announcements**: show latest announcements on the timeline page (`pages/04_Ask_a_Question.py`).
7. **School guide upload → link-only**: rework `pages/12_School_Guide_Upload.py` to upload to Supabase Storage and set `guide_pdf_url`, drop the LLM-extraction path for MVP.
8. **Post-visa timeline steps**: extend `shared/timeline_data.py` templates.
9. **Origin-country content for the 15-country MVP list**: extend `ingest.py` with a per-country `travel.state.gov` scrape for China, South Korea, India, Turkey, Germany, United Kingdom, Spain, France, Nigeria, Ghana, Argentina, Brazil, Mexico, Canada, Vietnam; add the corresponding hand-authored guidance the way the existing 5 countries were done; update `COMMON_ORIGIN_COUNTRIES` in `shared/countries.py` to the full 15. This can run in parallel with steps 2-7 — it doesn't depend on the DB/auth work.
10. **Reminders script + GitHub Action**: `scripts/send_reminders.py`, Resend/SendGrid integration, `.github/workflows/reminders.yml`.
11. **Privacy page rewrite + Data Processing note**: update `pages/14_Privacy.py` per the draft above once the DB/auth land (so the copy describes what's actually true).
12. **Smoke test end-to-end on Streamlit Cloud**: login as student, complete onboarding, see timeline; login as DSO, see roster, post announcement, override a step, confirm audit log row written; confirm reminder script runs standalone via `python scripts/send_reminders.py` locally before trusting the scheduled Action.

## Build status

Foundation is in place and verified. The app runs in **local mode** exactly as before (no accounts, `local/*.json`) and flips to **hosted mode** the moment the Supabase env vars are set — no code changes needed to switch.

| File | State | Notes |
|---|---|---|
| `migrations/001_init.sql` | new | Full schema, indexes, `updated_at` trigger, RLS policies |
| `migrations/README.md` | new | Setup walkthrough + required env vars |
| `shared/config.py` | edited | Supabase config block + `is_supabase_configured()` |
| `shared/db.py` | new | Cached client, state read/write, roster, announcements, audit |
| `shared/auth.py` | new | Email-OTP login, `get_current_user()`, `require_role()`, local-mode bypass |
| `shared/persistence.py` | rewritten | Backend-pluggable behind unchanged signatures |
| `pages/20_DSO_Dashboard.py` | new | Roster, filters, step override, announcements |
| `requirements.txt` | edited | Added `supabase>=2.4.0` |

**Verified:** app boots and renders in local mode; DSO dashboard shows its access gate when unconfigured; full persistence round-trip (profile → trip → timeline → mark step complete → reload → delete) passes; `_denormalize()` handles the populated, empty, and all-steps-complete cases without crashing.

**Not verified** (needs your Supabase project): the hosted-mode paths — OTP login, real Postgres reads/writes, dashboard against live data. That's the smoke test in `migrations/README.md`.

**Structural decisions worth knowing:**
- *Pluggable persistence, not a hard cutover.* The app never breaks while the backend is half-configured, and the local prototype stays usable for demos.
- *Streamlit as trusted middleware.* It talks to Postgres with the service key and enforces access via explicit `college_id` filters + `require_role()`. RLS is written as defense-in-depth but isn't the authoritative check yet (it needs a JWT custom-claim hook — documented, post-MVP).
- *OTP codes over magic links*, because magic-link redirects put tokens in the URL fragment, which Streamlit can't read server-side.

## Open decisions needing your input

- Who is the pilot school, and do you have (or can you get) a DSO contact willing to test the dashboard?
- Resend vs SendGrid for reminder emails (either works; Resend has a simpler free tier).
- Chat history: private/session-only (recommended) vs. visible to DSOs — see [Privacy policy rewrite](#privacy-policy-rewrite).
- Who signs off on the Data Processing note / any real ToS before onboarding a pilot school with real student PII?

---

## Post-MVP roadmap

Condensed from both source documents — real needs once there's more than one college or the pilot wants to go further:

**B2C**
- Full visa-type coverage beyond F-1/J-1/M-1 (H-1B, OPT/CPT as guided flows)
- Full country coverage beyond the 5 hand-authored origin countries (generic per-country scraper against `travel.state.gov`, or on-demand scrape-and-cache)
- Richer extenuating-circumstances handling (attorney-escalation triggers, structured per-category checklists)
- Real mobile-first layout (today's two-column chat+timeline is desktop-oriented by design)
- Multi-language support

**B2B / infrastructure**
- Multi-college self-serve signup, white-label branding, per-college billing/rate limits (Redis-backed)
- Separate FastAPI REST API — once a college wants SIS integration (CSV import/export, webhooks) or you have a second frontend client
- PDF parsing back on, via an actual background job (not inside a Streamlit request) once there's demand
- Real-time announcements/chat via Supabase Realtime or Pusher, if pull-on-load latency stops being good enough
- Cohort/semester templating (`cohort_templates` + per-student cloned steps) once one shared template no longer fits
- ChromaDB → versioned collections with `college_id` filtering once there's a second college
- Circuit breaker / graceful degradation for LLM provider outages
- Prompt-injection hardening moved fully server-side once there's a real backend service to move it to
- Formal audit-log retention policy, soft-delete + 30-day hard-delete for GDPR/FERPA right-to-erasure at scale
- Sub-roles within a DSO team (admin/editor/viewer)
