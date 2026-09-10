# Gorée AR - RAG Studio (Back-Office)

Back-office d'administration du **corpus documentaire** de l'application mobile **Gorée AR**.
Il pilote l'infrastructure **Gemini File Search Tool** (Google GenAI) : création de stores
RAG, indexation de PDF historiques, test du comportement du guide IA, et archivage des
fichiers sources.

> Projet réalisé dans le cadre d'un mémoire de Master 2 en Informatique de Gestion (UCAO-ISG).

---

## Sommaire

- [Rôle dans le système Gorée AR](#rôle-dans-le-système-gorée-ar)
- [Fonctionnalités](#fonctionnalités)
- [Stack technique](#stack-technique)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration (`.env`)](#configuration-env)
- [Premier compte administrateur](#premier-compte-administrateur)
- [Lancement](#lancement)
- [Utilisation](#utilisation)
- [Architecture](#architecture)
- [Base de données Supabase](#base-de-données-supabase)
- [Routes HTTP](#routes-http)
- [Sécurité](#sécurité)
- [Déploiement](#déploiement)
- [Dépannage](#dépannage)
- [Structure du dépôt](#structure-du-dépôt)

---

## Rôle dans le système Gorée AR

```
┌───────────────────────────────┬────────────────────────────────────────┐
│   FRONT-OFFICE (Mobile Unity)  │       BACK-OFFICE (ce dépôt)           │
│         Pour le visiteur       │       Pour l'administrateur / historien │
├───────────────────────────────┼────────────────────────────────────────┤
│ • Réalité augmentée (Vuforia)  │ • Création & gestion des stores RAG    │
│ • Chat vocal/texte (Gemini)    │ • Upload & indexation de PDF          │
│ • Fiches & audios locaux       │ • Bac à sable de validation (BNF4)    │
│ • SQLite (offline-first)        │ • Archivage des PDF sources           │
└───────────────────────────────┴────────────────────────────────────────┘
```

Chaque store Google reçoit un identifiant technique (ex.
`fileSearchStores/goreemaisonesclaves-vxqxk0scxpj5`) que l'on copie depuis le dashboard vers
la colonne `nom_store_rag` de la table `Site` de la base SQLite de l'app mobile.

---

## Fonctionnalités

- **Corpus & Stores** - créer / supprimer des *File Search Stores*, un par monument ou salle
  de musée ; copier l'identifiant technique en un clic ; upload de PDF (indexation Google
  synchrone) ; liste paginée (2 stores, puis « Voir tous les stores »).
- **Documents** - vue transverse de tous les documents, groupée par store en sections
  repliables ; taille, date, état d'indexation ; **visualiser** le PDF source, **supprimer**.
- **Bac à sable (Test IA)** - interroger un store en direct avec le prompt système strict
  **BNF4** (refus hors périmètre, adaptation au profil visiteur, trilingue FR/EN/WO), avec
  un appel REST 1:1 identique à celui de l'app mobile.
- **Aide** - rappel des conventions du projet.
- **Authentification** - connexion obligatoire par comptes administrateurs (mots de passe
  bcrypt, session par cookie signé).
- **Archivage Supabase** - chaque PDF envoyé à Google est aussi copié dans un bucket privé,
  ce qui permet de le rouvrir (Google ne restitue pas les fichiers indexés).

---

## Stack technique

| Domaine | Choix |
|---|---|
| Langage / runtime | Python 3.12+ (testé sous 3.14, Windows) |
| Backend | FastAPI + Uvicorn (ASGI) |
| Templates | Jinja2 |
| Frontend | HTML5, Tailwind CSS (CDN, config inline), Alpine.js, Lucide Icons |
| RAG | Google GenAI - Gemini **File Search Tool** (chunking, embeddings, indexation, retrieval côté Google) |
| Modèle par défaut | `gemini-3.5-flash-lite` |
| Stockage fichiers + comptes | Supabase (bucket privé + Postgres) |
| Auth | `bcrypt` (hash) + `itsdangerous` (SessionMiddleware Starlette) |

Aucune base vectorielle locale, aucun worker, aucun build front.

---

## Prérequis

- **Python 3.12+**
- Une **clé API Google Gemini** avec accès au File Search Tool
- Un **projet Supabase** (pour l'archivage des PDF et les comptes admin)

---

## Installation

```bash
git clone <url-du-dépôt> rag_dashboard
cd rag_dashboard
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Configuration (`.env`)

Créer un fichier `.env` à la racine (jamais versionné) :

```dotenv
# --- Google Gemini ---
GEMINI_API_KEY=AQ.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- Supabase (archivage PDF + comptes admin) ---
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_KEY=<clé service_role, onglet Settings puis API du projet Supabase>

# --- Session ---
SESSION_SECRET=<chaîne aléatoire longue>        # ex : python -c "import secrets;print(secrets.token_urlsafe(48))"
SESSION_COOKIE_SECURE=false                       # true derrière HTTPS (production)
```

| Variable | Rôle | Obligatoire |
|---|---|---|
| `GEMINI_API_KEY` | File Search + génération | oui |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` | Archivage PDF **et** comptes admin | oui en pratique (sans, pas de connexion possible) |
| `SESSION_SECRET` | Signature du cookie de session | oui (sinon clé éphémère, sessions perdues au redémarrage) |
| `SESSION_COOKIE_SECURE` | `true` en HTTPS, `false` en local | défaut `false` |

La `SUPABASE_SERVICE_KEY` est la clé `service_role` (elle contourne les politiques RLS) :
elle ne quitte jamais le serveur, n'est jamais transmise au navigateur.

### Mise en place du schéma Supabase

Dans le SQL Editor du projet Supabase, exécuter :

```sql
-- Table de suivi des PDF archivés
create table public.corpus_documents (
    id                    uuid primary key default gen_random_uuid(),
    google_document_name  text not null unique,
    google_store_name     text not null,
    store_display_name    text,
    file_name             text not null,
    storage_path          text not null,
    size_bytes            bigint,
    mime_type             text default 'application/pdf',
    state                 text,
    created_at            timestamptz not null default now()
);
create index corpus_documents_store_idx   on public.corpus_documents (google_store_name);
create index corpus_documents_created_idx on public.corpus_documents (created_at desc);
alter table public.corpus_documents enable row level security;
revoke all on table public.corpus_documents from anon, authenticated;

-- Comptes administrateurs
create table public.admin_users (
    id             uuid primary key default gen_random_uuid(),
    email          text not null unique,
    password_hash  text not null,
    full_name      text,
    is_active      boolean not null default true,
    created_at     timestamptz not null default now(),
    last_login_at  timestamptz
);
create unique index admin_users_email_lower_idx on public.admin_users (lower(email));
alter table public.admin_users enable row level security;
revoke all on table public.admin_users from anon, authenticated;

notify pgrst, 'reload schema';
```

Puis créer le bucket privé **`corpus-pdfs`** (Storage > New bucket, *Public* décoché,
type de fichier `application/pdf`, limite 50 Mo).

> RLS est activé sans aucune politique : les deux tables sont accessibles uniquement au
> backend via la clé `service_role`. L'avertissement *« RLS enabled, no policy »* des
> advisors Supabase est **voulu**.

---

## Premier compte administrateur

Il n'y a pas d'inscription publique. Les comptes se créent en ligne de commande :

```bash
python create_admin.py votre.email@exemple.com "Votre Nom"
```

Le mot de passe est demandé de façon masquée (8 caractères minimum). Relancer la même
commande met à jour le mot de passe / le nom d'un compte existant.

---

## Lancement

```bash
python app.py
# ou : python -m uvicorn app:app --reload
```

Ouvrir <http://localhost:8000> → redirection vers `/login`.

---

## Utilisation

1. **Se connecter** avec un compte créé via `create_admin.py`.
2. **Corpus & Stores** : créer un store par lieu (`goree-maison-esclaves`,
   `goree-musee-salle1`, …), puis y déposer les PDF. L'indexation Google est synchrone :
   l'upload peut prendre quelques secondes.
3. Copier l'identifiant technique du store (bouton *copier*) vers la base SQLite de l'app
   mobile (`Site.nom_store_rag`).
4. **Bac à sable** : choisir un store, un profil (`touriste` / `eleve` / `universitaire`),
   une langue, poser une question et vérifier que la réponse respecte la règle BNF4.
5. **Documents** : parcourir, visualiser ou supprimer les documents de tous les stores.

> Les documents indexés **avant** l'activation de l'archivage Supabase apparaissent
> « non archivé » et n'ont pas de bouton *Visualiser* (Google ne restitue pas le fichier).

---

## Architecture

`app.py` est un back-office FastAPI mono-fichier. Deux chemins vers Google, volontairement
distincts :

1. **Gestion des stores / documents** - SDK officiel `google-genai`
   (`client.file_search_stores.*`). L'upload attend la fin de l'opération longue de Google
   avant de répondre. `documents.delete` nécessite `config={"force": True}`.
2. **Bac à sable** (`/api/playground/test`) - appel REST brut (`urllib.request`) vers
   `v1beta/models/{model}:generateContent`, identique à la requête `UnityWebRequest` de
   l'app mobile. Une liste de modèles est essayée dans l'ordre.

`construire_prompt_systeme(profil, langue)` génère le prompt système BNF4 ; il est le
portage direct de `GestionnaireContexte.cs` de l'app Unity - garder les deux alignés.

**Authentification** : le middleware `require_login` bloque toute route hors `/login`,
`/logout`, `/static/*`, `/favicon.ico` sans session (302 pour les pages, 401 JSON pour
`/api/*`). Il est enregistré **avant** `SessionMiddleware` pour s'exécuter **après** lui.

**Frontend** : une seule page (`templates/index.html`) en coque dashboard - sidebar
gauche (Corpus / Documents / Bac à sable / Aide), topbar collante avec le nom de
l'utilisateur et le bouton de déconnexion, tiroir mobile sous 1024 px. Toute l'interactivité
tient dans un composant Alpine.js `ragApp()` (`static/js/app.js`). Thème sombre uniquement,
charte « Gorée AR » (bleu nuit, or). `app.js` est chargé avec un paramètre `?v=N` :
**incrémenter N** dans `index.html` à chaque modification du fichier.

---

## Base de données Supabase

Le projet Supabase héberge **aussi** le schéma de l'app mobile (`point_interet`, `routes`,
`traduction`, `utilisateur`, `route_*`). Le back-office ne possède que :

| Objet | Contenu |
|---|---|
| `public.corpus_documents` | Lien document Google ↔ objet du bucket + métadonnées |
| `public.admin_users` | Comptes admin (email, hash bcrypt, `is_active`, `last_login_at`) |
| Bucket `corpus-pdfs` (privé) | Copie des PDF sources : `<store_ref>/<uuid>.pdf` |

**Ne pas toucher aux autres tables.**

---

## Routes HTTP

| Méthode | Route | Rôle | Auth |
|---|---|---|---|
| GET | `/login` | Page de connexion | publique |
| POST | `/login` | Vérifie identifiants, ouvre la session | publique |
| GET | `/logout` | Ferme la session | publique |
| GET | `/` | Interface (coque dashboard) | requise |
| GET | `/api/stores` | Liste stores + documents + stats | requise |
| POST | `/api/stores/create` | Crée un store | requise |
| POST | `/api/stores/delete` | Supprime un store (+ nettoyage bucket/table) | requise |
| POST | `/api/documents/upload` | Upload PDF → Google + copie Supabase | requise |
| POST | `/api/documents/delete` | Supprime un document (+ nettoyage) | requise |
| GET | `/api/documents/file?document_name=…` | 307 vers une URL signée (1 h) du PDF | requise |
| POST | `/api/playground/test` | Test RAG BNF4 (REST direct) | requise |

---

## Sécurité

- Aucun secret en dur : tout via `.env` (jamais commité).
- Mots de passe **bcrypt** ; jamais stockés ni renvoyés en clair.
- Session : cookie `goree_session` **httponly**, `SameSite=Lax`, `Secure` conditionnel
  (`SESSION_COOKIE_SECURE`), durée 8 h.
- Anti brute-force : 5 tentatives échouées / 5 min par IP → HTTP 429. Message d'erreur
  générique (« Identifiants invalides »).
- Bucket `corpus-pdfs` **privé** : la visualisation passe par une URL signée générée côté
  serveur, jamais un lien public.
- Tables Supabase du back-office : RLS activé, aucune politique, accès `anon` / `authenticated`
  révoqué → backend uniquement.

---

## Déploiement

En production derrière HTTPS :

1. `SESSION_COOKIE_SECURE=true` (**obligatoire**).
2. `SESSION_SECRET` fixé dans l'environnement d'hébergement (pas de valeur éphémère).
3. Servir derrière un reverse proxy (Nginx, Caddy, …) qui termine le TLS et transmet
   `X-Forwarded-For` (utilisé pour le rate-limit).
4. Lancer via un gestionnaire de process : `uvicorn app:app --host 0.0.0.0 --port 8000`
   (sans `--reload`).

---

## Dépannage

| Problème | Cause / solution |
|---|---|
| Redirigé en boucle vers `/login` | Session non posée : vérifier `SESSION_SECRET`, et le cookie du navigateur. |
| « Authentification indisponible : Supabase non configuré » | Renseigner `SUPABASE_URL` / `SUPABASE_SERVICE_KEY`. |
| Le clic sur un onglet ne fait rien | Cache navigateur sur `app.js` : rechargement forcé (Ctrl+Shift+R). Le paramètre `?v=N` évite que ça se reproduise. |
| `Cannot delete non-empty Document` | Déjà corrigé (`force=True`) ; si réintroduit, remettre `config={"force": True}`. |
| Un document affiche « non archivé » | Il a été indexé avant l'activation de l'archivage Supabase : réuploader pour obtenir une copie. |
| `python app.py` plante sous Windows | Résolu (emoji retirés des `print()`). Sinon : `python -m uvicorn app:app`. |

---

## Structure du dépôt

```
rag_dashboard/
├── app.py                 # Serveur FastAPI : auth, Google GenAI/REST, Supabase
├── create_admin.py        # CLI : création/réinitialisation d'un compte admin
├── test_call.py           # Diagnostic rapide de l'API Gemini File Search
├── requirements.txt
├── .env                   # Secrets (non versionné)
├── templates/
│   ├── index.html         # Interface principale (coque dashboard)
│   └── login.html         # Page de connexion (autonome)
├── static/
│   ├── css/app.css        # Fond, dégradés, focus, prefers-reduced-motion
│   └── js/
│       ├── app.js         # Composant Alpine `ragApp()`
│       └── tailwind.config.js  # Miroir de la config Tailwind inline
├── docs/plans/            # Plans d'implémentation
├── AGENTS.md              # Conventions fermes du projet
└── CLAUDE.md              # Contexte architecture + commandes
```
