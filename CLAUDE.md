# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Authoritative project rules

`AGENTS.md` holds the firm project conventions (stack, security, RAG store granularity, BNF4 requirements, trilingual support). Read it and follow it. This file only adds architecture context and commands not covered there.

Key constraints from `AGENTS.md` worth repeating:
- Never hardcode an API key. `GEMINI_API_KEY` is loaded from `.env` via `python-dotenv`; `.env` must never be committed.
- One File Search Store per monument / museum room (strict compartmentalization). Store display names follow `goree-<lieu>` (e.g. `goree-maison-esclaves`).
- Always pass `config={"display_name": file.filename}` on upload so Google doesn't name the doc after the temp file.
- The playground system prompt must enforce BNF4: refuse politely anything outside Gorée / the transatlantic slave trade; adapt tone to profile (`touriste` / `eleve` / `universitaire`); support `fr` / `en` / `wo`.

## Git

- Commit messages must **not** include a `Co-Authored-By` trailer. Plain messages only.

## Commands

```bash
pip install -r requirements.txt
python app.py          # dev server on http://127.0.0.1:8000 with --reload
python test_call.py    # one-shot Gemini File Search sanity check (edit the hardcoded store ID inside)
```

There is no test suite, linter, or build step. `test_call.py` is a manual diagnostic script, not an automated test.

## Architecture

Single-file FastAPI back-office (`app.py`, ~300 lines) that administers Google's **Gemini File Search Tool** as the RAG backend — there is no local vector DB, no separate worker, no external infra. Google does the chunking, embedding, indexing, and retrieval.

Two distinct paths to Google, deliberately:

1. **Store & document management** — uses the official `google-genai` SDK (`client.file_search_stores.*`). Covers list, create, delete stores and upload/delete documents. Upload is **synchronous**: `upload_to_file_search_store` returns a long-running operation and the handler polls `client.operations.get(operation)` every 1.5s until `operation.done` before responding. Uploaded file is written to a `NamedTemporaryFile`, sent, then deleted (also in the error path).

2. **Playground / RAG query test** (`/api/playground/test`) — bypasses the SDK and does a raw `urllib.request` POST to the `v1beta/models/{model}:generateContent` REST endpoint. This is intentional: it mirrors 1:1 the `UnityWebRequest` calls the Gorée AR mobile app makes, so the back-office validates the exact same request shape. The handler tries a list of model names in order (`modeles` in `test_query`) and returns the first that yields text; if all fail it raises 500 with the last error. `file_search` is passed as a tool with `file_search_store_names`.

`construire_prompt_systeme(profil, langue)` builds the strict BNF4 system prompt and is a direct port of `GestionnaireContexte.cs` from the Unity app — keep the two aligned when either changes.

### Frontend

Server renders one page: `templates/index.html` (Jinja2), styled with Tailwind (CDN) + the `static/js/tailwind.config.js` theme (Gorée AR charter: navy `#0B0D17`/`#13172B`, gold `#E8C84A`, fonts *Marcellus* / *Plus Jakarta Sans*). All interactivity is one Alpine.js component, `ragApp()` in `static/js/app.js` — tabs (`corpus` / playground), fetch calls to the `/api/*` endpoints via `FormData`, toasts, clipboard copy of store IDs. Icons via Lucide, re-rendered with `lucide.createIcons()` after DOM updates.

### How this fits the larger system

This repo is the **back-office** half of Gorée AR. The **front-office** is a Unity mobile app (Vuforia AR, offline-first SQLite `goree_ar.db`). The link between them: each Google store has a technical ID like `fileSearchStores/goreemaisonesclaves-vxqxk0scxpj5`, copied from this dashboard into the `nom_store_rag` column of the `Site` table in the app's SQLite DB.

## Notes

- App comments, prompts, and UI strings are in French — match that.
- The model names in `test_query`'s `modeles` list and in `test_call.py` are the project's chosen defaults; leave them as-is unless asked to change model selection.
- `get_client()` raises HTTP 400 (not 500) when `GEMINI_API_KEY` is missing — preserve that distinction.
