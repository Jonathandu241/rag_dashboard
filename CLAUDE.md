# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Authoritative project rules

`AGENTS.md` holds the firm project conventions: stack (§2), the Supabase DB layout (§2 bis: `corpus_documents`, `admin_users`, the `corpus-pdfs` bucket, and the mobile-app tables you must not touch), security incl. the `.env` table (§3.1) and the auth contract (§3.3), RAG store granularity (§4), BNF4 + trilingual (§5). Read it and follow it. This file adds architecture context and commands not covered there.

Key constraints from `AGENTS.md` worth repeating:
- Never hardcode a secret. `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SESSION_SECRET`, `SESSION_COOKIE_SECURE` are loaded from `.env` via `python-dotenv`; `.env` must never be committed.
- One File Search Store per monument / museum room (strict compartmentalization). Store display names follow `goree-<lieu>` (e.g. `goree-maison-esclaves`).
- Always pass `config={"display_name": file.filename}` on upload so Google doesn't name the doc after the temp file.
- The playground system prompt must enforce BNF4: refuse politely anything outside Gorée / the transatlantic slave trade; adapt tone to profile (`touriste` / `eleve` / `universitaire`); support `fr` / `en` / `wo`.
- No em/en dashes anywhere in the project: use a plain `-`. French comments and UI strings.

## Git

- Commit messages must **not** include a `Co-Authored-By` trailer. Plain messages only.

## Commands

```bash
pip install -r requirements.txt
python app.py                              # dev server on http://127.0.0.1:8000 with --reload
python create_admin.py <email> "<Nom>"     # create/reset an admin account (password prompted, hidden)
python test_call.py                        # one-shot Gemini File Search sanity check (edit the hardcoded store ID inside)
```

There is no test suite, linter, or build step. `test_call.py` is a manual diagnostic script, not an automated test.

## Architecture

Single-file FastAPI back-office (`app.py`) that administers Google's **Gemini File Search Tool** as the RAG backend - Google does the chunking, embedding, indexing, and retrieval; there is no local vector DB or worker.

Two distinct paths to Google, deliberately:

1. **Store & document management** - uses the official `google-genai` SDK (`client.file_search_stores.*`). Covers list, create, delete stores and upload/delete documents. Upload is **synchronous**: `upload_to_file_search_store` returns a long-running operation and the handler polls `client.operations.get(operation)` every 1.5s until `operation.done` before responding. Uploaded file is written to a `NamedTemporaryFile`, sent, then deleted (also in the error path). `documents.delete` needs `config={"force": True}` (a document with chunks is "non-empty").

2. **Playground / RAG query test** (`/api/playground/test`) - bypasses the SDK and does a raw `urllib.request` POST to the `v1beta/models/{model}:generateContent` REST endpoint. This is intentional: it mirrors 1:1 the `UnityWebRequest` calls the Gorée AR mobile app makes, so the back-office validates the exact same request shape. The handler tries a list of model names in order (`modeles` in `test_query`) and returns the first that yields text; if all fail it raises 500 with the last error. `file_search` is passed as a tool with `file_search_store_names`.

`construire_prompt_systeme(profil, langue)` builds the strict BNF4 system prompt and is a direct port of `GestionnaireContexte.cs` from the Unity app - keep the two aligned when either changes.

### Authentication

Every route is gated by the `require_login` HTTP middleware except `/login`, `/logout`, `/static/*`, `/favicon.ico` (`PUBLIC_PATHS`): no session → 302 to `/login` for pages, 401 JSON for `/api/*`. Middleware order matters - `require_login` is registered **before** `SessionMiddleware` so it runs **after** it (Starlette runs middleware in reverse registration order); don't reorder.

- Accounts live in `public.admin_users` (Supabase, backend-only via `service_role`). Passwords are bcrypt (`bcrypt` module directly - `passlib` 1.7.4 is incompatible with `bcrypt` 5.x, don't reintroduce it).
- `POST /login` verifies email (case-insensitive) + `is_active` + bcrypt, sets `request.session["user_id"]`, bumps `last_login_at`. Generic "Identifiants invalides" on failure. In-memory per-IP rate limit: 5 failed attempts / 5 min → 429.
- `GET /logout` clears the session. `templates/login.html` is a standalone page (no `ragApp()`).
- `index.html` topbar shows `current_user_name` + a `/logout` link. `app.js` calls `_checkAuth(res)` after each `fetch` - a 401 redirects the browser to `/login`.
- Session cookie `goree_session`: httponly, `same_site=lax`, `https_only=SESSION_COOKIE_SECURE` (`.env`, `false` local / `true` behind HTTPS), 8 h. `SESSION_SECRET` from `.env`; if missing, an ephemeral key is generated (sessions drop on restart) with a warning.
- No signup page. Create accounts with `create_admin.py`.

### Supabase - source-PDF storage (optional)

Google File Search keeps chunks/embeddings but does **not** let you re-download the original PDF. To make the "Visualiser" button work, `app.py` keeps a copy of every uploaded PDF in Supabase:

- **Bucket** `corpus-pdfs` (private) - one object per document at `<store_ref>/<uuid>.pdf`.
- **Table** `public.corpus_documents` (project `GoreeAR`, `ubajzrbphbqoomtxoqsk`) - links `google_document_name` ↔ `storage_path` + `file_name`, `size_bytes`, `store_display_name`, `created_at`. RLS on, **no public policy**, `anon`/`authenticated` revoked: only the backend touches it, with the `service_role` key. Same lockdown applies to `public.admin_users`.
- `get_supabase()` returns `None` when `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` are absent → the copy step and the `has_local_file` flag are simply skipped (graceful degradation; docs indexed before this feature show `has_local_file: false`).
- Upload writes to Google, then best-effort copies to the bucket + inserts the row. Delete (document or whole store) cleans the bucket and the table too.
- `GET /api/documents/file?document_name=…` → 307 redirect to a 1 h signed URL. `/api/stores` docs carry `size_bytes`, `created_at`, `has_local_file`; stats carry `storage_enabled`.

### Frontend

Server renders one page: `templates/index.html` (Jinja2), styled with Tailwind (CDN) + an
inline `tailwind.config` under the `goree` color namespace (`bg #0B0D17`, `surface #13172B`,
`card #1B203B`, `border rgba(232,200,74,.15)`, `gold #E8C84A` / `goldHover #F4D665`,
`accent #3B82F6`). Dark theme only (`<html class="dark">`, forced - no toggle). "Gorée AR"
charter: deep navy ground with subtle radial gold/blue gradients (`static/css/app.css`),
gold accent used freely, `rounded-xl`/`rounded-2xl` cards with coloured glow shadows,
Lucide icons throughout, flag emoji in the language select. Fonts: *Marcellus* (display /
headings) + *Plus Jakarta Sans* (body).

Layout is a dashboard shell: fixed left sidebar (Corpus / Documents / Test / Aide nav, active
entry = gold pill), sticky topbar with the current view title, connected-user name and a
`/logout` link. Below 1024px the sidebar
collapses into a ☰ drawer with an overlay. All interactivity is one Alpine.js component,
`ragApp()` in `static/js/app.js` - `currentTab` (`corpus` / `documents` / `test` / `aide`),
`sidebarOpen`, `goTo()`, `showAllStores` + `visibleStores` getter (Corpus shows 2 stores
then a "Voir plus" toggle), `collapsedStores` + `toggleStoreSection()` (Documents view is
grouped by store into collapsible sections), `formatBytes`/`formatDate`/`openDocument`
helpers, plus the fetch calls to `/api/*`. `app.js` is loaded `defer` with a `?v=N`
cache-buster - bump N when you change it. Icons re-rendered via `lucide.createIcons()` after
DOM updates. `static/js/tailwind.config.js` mirrors the inline config and must be kept in sync.

### How this fits the larger system

This repo is the **back-office** half of Gorée AR. The **front-office** is a Unity mobile app (Vuforia AR, offline-first SQLite `goree_ar.db`). The link between them: each Google store has a technical ID like `fileSearchStores/goreemaisonesclaves-vxqxk0scxpj5`, copied from this dashboard into the `nom_store_rag` column of the `Site` table in the app's SQLite DB.

## Notes

- App comments, prompts, and UI strings are in French - match that. No em/en dashes anywhere - plain `-` only.
- The model names in `test_query`'s `modeles` list and in `test_call.py` are the project's chosen defaults; leave them as-is unless asked to change model selection.
- `get_client()` raises HTTP 400 (not 500) when `GEMINI_API_KEY` is missing - preserve that distinction.
- On Windows, `python app.py` works (emoji were removed from the startup `print()`s). `python -m uvicorn app:app` also works.
- Supabase project `GoreeAR` also hosts the **mobile app's** schema (`point_interet`, `routes`, `traduction`, …). The back-office only owns `corpus_documents`, `admin_users`, and the `corpus-pdfs` bucket - don't touch the rest. `admin_users` requires Supabase to be configured for login to work at all.
- Editing `static/js/app.js` requires bumping the `?v=N` cache-buster in `templates/index.html` (currently `?v=3`).
- `bcrypt` is used directly (not `passlib` - incompatible with `bcrypt` 5.x). `create_admin.py` is the only way to make accounts.
