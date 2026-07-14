# Vera — Product Plan (B2C + B2B)

## Current state (as of this update)

Vera is a Streamlit prototype that walks an international student through onboarding
(name, visa type, origin/destination country, school) and an extenuating-circumstances
checklist, then shows a personalized visa timeline with an embedded RAG chatbot.
Navigation (hamburger menu + a clickable "Vera" brand link back to the timeline) is now
consistent across every page, including the welcome screen. The five older static
info pages (F-1/J-1/M-1/Post-Arrival/About) are personalized with the user's name and
visa type and share the same design system as the newer onboarding flow.

The RAG knowledge base covers F-1/J-1/M-1 student visas entering the United States,
sourced from USCIS, State Department, SEVP, SSA, and IRS. Retrieval now supports a real
visa-type filter (previously just appended to the query text) and a country-of-origin
dimension, with hand-authored guidance for five origin countries (India, China, Nigeria,
Brazil, South Korea) and for common extenuating circumstances (214(b) denials, SEVIS
termination, financial hardship, medical/family emergencies, delayed documents). H-1B and
other visa types, and destinations other than the US, are captured as intent at onboarding
but routed to a "coming soon" page rather than given fabricated guidance.

There are no user accounts — a session is a random ID in the URL, persisted to local JSON.
There's no test suite, linter, or CI.

## B2C (student-facing) roadmap

1. **Full visa-type coverage.** Build real, sourced content and a timeline template for
   H-1B (and eventually OPT/CPT as their own guided flows, not just static blurbs) instead
   of the "coming soon" placeholder. Each new visa type needs its own `TIMELINE_TEMPLATES`
   entry, ingestion content, and static/info page — same pattern as F-1/J-1/M-1 today.
2. **Full country coverage.** Currently 5 origin countries have real embassy/reapplication
   guidance; ~190 don't. Two viable paths: (a) a generic per-country scraper against each
   country's `travel.state.gov`/embassy subpage (structurally uniform, so `fetch_page()` in
   `ingest.py` is likely reusable), or (b) an on-demand fallback that scrapes and caches a
   country's page the first time a user from that country signs up. Either way, retrieval
   already supports an `origin_country` filter — the gap is content, not plumbing.
3. **Richer extenuating-circumstances handling.** Today it's a checklist plus a
   confidence-gated guidance card. Next: explicit triggers to recommend attorney escalation
   for higher-severity flags (e.g. a second 214(b) denial, an active SEVIS termination),
   and structured re-application timelines/checklists per category instead of a single
   paragraph.
4. **Accounts.** No login exists — a session is a URL parameter. Fine for a prototype;
   not for production, where a user should be able to recover their timeline from a new
   device, and where storing name + visa history + extenuating circumstances under a
   guessable URL is a real privacy exposure once traffic grows.
5. **Mobile support.** `shared/theme.py` explicitly keeps the chat+timeline two-column
   layout side-by-side above ~700px and doesn't yet have a real mobile-first design for
   narrower viewports.
6. **Reminders/notifications.** The timeline tracks status but nothing proactively reminds
   a student about the SEVIS fee, DS-160, or an upcoming interview date — this needs actual
   dates (not just step order) and a notification channel (email at minimum).
7. **Multi-language support.** The audience is international students; the entire UI and
   RAG content is English-only today.

## B2B (college-facing) roadmap

1. **Admin dashboard.** International student offices need an aggregate view: which
   students (by cohort/program) are stuck at which timeline step, not just each student's
   own view. This requires a real notion of a "college" as a tenant and students as members
   of it — doesn't exist today (no accounts at all).
2. **Institutional school-guide management.** `pages/12_School_Guide_Upload.py` today is a
   one-off, per-session PDF upload. A college would upload its guide once and have it apply
   to every one of its students automatically, with a way to update it and have existing
   students' timelines re-sync.
3. **Roster import.** Bulk CSV/SIS import of incoming international students instead of each
   student self-registering from scratch — reduces onboarding friction and gives the college
   visibility from day one.
4. **Escalation view.** A filtered dashboard view surfacing which students have flagged
   extenuating circumstances (denials, SEVIS issues, hardship, emergencies) so an advisor can
   proactively reach out, rather than students only seeing this content themselves.
5. **White-label / branding.** Colleges buying this as a product will want their own logo/
   colors on the student-facing side; today the design system (`shared/theme.py`) is
   hardcoded to Vera's own brand.
6. **Auth & per-college data isolation.** A B2B dashboard fundamentally requires real
   login and roles (student vs. advisor vs. admin) plus strict per-college data isolation —
   the single biggest structural gap since there's currently no auth system at all.

## Cross-cutting gaps

- No test suite, linter, or CI (confirmed in CLAUDE.md) — as both roadmaps above grow the
  codebase, this becomes riskier to maintain without regressions.
- No accounts/auth of any kind — blocks both the B2C "recover my session" case and every
  B2B dashboard/escalation feature above.
- `local/` JSON-file persistence keyed by a URL parameter won't scale past a prototype —
  needs a real database once either B2C history or B2B multi-tenant dashboards are built.
