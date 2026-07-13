# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run the app:
```
streamlit run app.py
```

Install dependencies:
```
pip install -r requirements.txt
```

Rebuild the RAG knowledge base (ChromaDB at `chroma_db/`, collection `student_visa_documents`):
```
python ingest.py          # full re-scrape of USCIS/State Dept/SEVP/SSA/IRS + re-embed
python ingest.py --fast   # only re-scrape pages whose content hash changed
python ingest_static.py   # populate from hardcoded static content instead of live scraping
```

Check whether ingested source pages have changed since last scrape:
```
python update_checker.py
```

There is no test suite, linter, or build step configured in this repo.

Required environment variables (`.env`, gitignored — see `shared/config.py` for defaults):
`QWEN_API_KEY`, `QWEN_BASE_URL` (default `http://litellm.colby.edu:4000/v1`), `QWEN_MODEL` (default `qwen-3.6-27b`), `QWEN_MAX_TOKENS`, `QWEN_TEMPERATURE`. When deploying (e.g. Streamlit Community Cloud), set these as platform secrets/env vars rather than shipping `.env`.

## Architecture

This is a Streamlit multipage app called **Vera** — an AI visa-help agent for US international students (F-1/J-1/M-1), combining a RAG chatbot with an onboarding flow and a personal visa timeline. Streamlit's file-based routing means every file in `pages/` becomes a route automatically; the numeric prefix only affects default sidebar ordering (the sidebar itself is collapsed everywhere — navigation is a custom hamburger menu instead, see below).

**Two eras of pages coexist and share the same design system:**
- `app.py` is the Vera welcome screen (entry point). The onboarding wizard flow is `pages/10_Trip_Details.py` → `pages/12_School_Guide_Upload.py` → `pages/04_Ask_a_Question.py` (this last one is the main "Your Timeline" screen: compact chat on the left, scrollable visa timeline on the right — despite the filename, it's no longer a standalone Q&A page).
- `pages/01_F-1_Student_Visa.py`, `02_J-1_Exchange_Visitor.py`, `03_M-1_Vocational_Visa.py`, `05_Post_Visa_Guide.py`, `06_About.py` are older static informational pages, restyled to match Vera's look (hamburger menu, green accent, floating chat widget) but structurally simpler (built from `render_card`/`render_section` HTML helpers in `shared/components.py`).
- `pages/13_Help_Find_a_Lawyer.py`, `14_Privacy.py`, `15_Settings.py` are small standalone info/utility pages reachable only from the hamburger menu.

**Chat pipeline** (`shared/chatbot.py`, `shared/retrieval.py`, `shared/safeguards.py`, `shared/config.py`): `call_qwen_api()` always prepends the same `SYSTEM_PROMPT` (Vera's persona + a strict no-legal-advice contract) regardless of caller, so every LLM call site — the main chat, the compact `shared/chat_panel.py` widget, timeline enrichment, and PDF guide extraction — inherits the same safety rules and hidden-reasoning contract. The prompt requires the model to end private reasoning with a literal `FINAL ANSWER:` line; `shared/safeguards.strip_thinking()` splits on that marker (falling back to `<think>` tags / labeled-block regexes for older-style leaks) so chain-of-thought never reaches the user. Retrieval is confidence-gated via `check_confidence()` (cosine distance threshold) — low-confidence queries get a canned "I don't have that information" response rather than an ungrounded answer. `pages/04_Ask_a_Question.py`'s chat area uses the two-phase `is_processing`/`pending_question` session-state pattern so a "Thinking…" state renders before the actual (slow) API call happens on the following rerun.

**`shared/chat_panel.py`'s `render_chat_panel()` is wrapped in `@st.fragment`** and its `st.rerun()` calls use `scope="fragment"` — this is required so that asking a question only reruns the chat widget, not the entire page (the rest of the page, e.g. the timeline, would otherwise freeze/gray-out during every chat turn since Streamlit's default rerun is whole-script). Keep this pattern for any future interactive widget embedded alongside other content.

**Timeline system** (`shared/timeline_data.py`, `shared/timeline.py`, `shared/timeline_ui.py`, `shared/vera_state.py`): `timeline_data.TIMELINE_TEMPLATES` is the canonical, hardcoded source of truth for which steps exist per visa type and in what order — the LLM is never allowed to add/remove/reorder steps. `shared/timeline.enrich_current_step()` only rewrites a step's *detail text* via a retrieval-grounded, confidence-gated LLM call, and only for the current (first incomplete) step, once — this keeps per-page-load LLM calls to at most one instead of one per step (a full 7-step enrichment used to take minutes and wasn't resumable across reruns). Steps extracted from a school's PDF guide (`shared/pdf_guide.py`, via `pages/12_School_Guide_Upload.py`) are tagged `enriched: True` so they're never overwritten by generic enrichment — they already carry real, source-specific content. `shared/pdf_guide.py` requires the model's JSON response to be parsed strictly (with a `<think>`-block-aware fallback parser for stray reasoning text) and raises `PdfExtractionError` rather than ever fabricating steps when extraction fails or finds nothing.

**Persistence** (`shared/persistence.py`, `shared/vera_state.py`): there are no user accounts. A random session id lives in the URL as `?vid=...` (`get_or_create_session_id()`), and `st.session_state.vera` is mirrored to `local/vera_sessions/<vid>.json` on every mutation so trip details / timeline progress survive a hard page refresh. `local/` is gitignored.

**Styling**: `shared/styles.py`'s `GLOBAL_CSS` (legacy, hardcoded hex colors, `.block-container` max-width, hides Streamlit chrome) and `shared/theme.py`'s `get_vera_css()` (Tabler Icons webfont + CSS custom properties like `--bg-accent`/`--text-accent`/`--fill-primary` for the green accent) are both loaded on every page — `get_global_css()` first, then `get_vera_css()`. `shared/theme.py` also contains a media-query override forcing Streamlit's auto-stacking columns to stay side-by-side above phone widths (the chat+timeline two-column layout is meant for laptop/desktop, not mobile). When writing raw HTML into `st.markdown(..., unsafe_allow_html=True)`, avoid blank lines with leading whitespace inside the string — CommonMark parses those as an indented code block and escapes everything after it verbatim (this broke the timeline's last card once; keep multi-line HTML blocks either fully un-indented per line or built as single concatenated strings, as done in `shared/timeline_ui.py`).

**Navigation**: `shared/components.py`'s `render_hamburger_menu()` is the only nav pattern — a `st.popover` with links to the timeline, home, the visa-type-specific Forms page, Info, Help, Settings, and Privacy, plus a large clickable "Vera" brand link back to the timeline. `render_floating_chat()` renders a fixed-position `st.popover` (scoped via `key="vera_floating_chat"` + `.st-key-vera_floating_chat` CSS) containing the real `render_chat_panel()` widget, so chat is usable from any page without navigating away — it is not just a link.

**Root-level scripts** (`ingest.py`, `ingest_static.py`, `processing_times.py`, `update_checker.py`) are standalone, run manually, and are not imported by the Streamlit app at request time — they populate/refresh `chroma_db/` and small JSON caches (`ingest_cache.json`, `.processing_times_cache.json`, `.page_hashes_cache.json`) ahead of time.
