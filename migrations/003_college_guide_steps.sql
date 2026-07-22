-- Admin-driven school guide: the DSO uploads and extracts the guide PDF once
-- per college (see pages/20_DSO_Dashboard.py), instead of every student
-- uploading their own copy (see pages/12_School_Guide_Upload.py, now a
-- local-mode-only fallback). Students inherit these steps automatically.
-- Run this once in the Supabase SQL editor (after 001_init.sql, 002_messages.sql).

alter table colleges add column if not exists guide_steps jsonb not null default '[]'::jsonb;
