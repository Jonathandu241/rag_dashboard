# AGENTS.md - Règles pour l'agent IA (Gorée AR - RAG Studio & Back-Office)

> Ce document définit les règles **fermes** et les conventions techniques que tout agent IA
> doit respecter lors de l'intervention sur le projet **Gorée AR - RAG Studio** (Back-Office d'administration).
> Ce projet s'inscrit dans un mémoire de Master 2 en Informatique de Gestion (UCAO-ISG).

---

## 1. Contexte et Rôle dans le Système d'Information

Dans le cadre du projet de médiation patrimoniale **Gorée AR**, le système d'information se compose de deux volets complémentaires :

```
┌────────────────────────────────────────────────────────────────────────┐
│             SYSTÈME D'INFORMATION GORÉE AR                             │
├───────────────────────────────┬────────────────────────────────────────┤
│   FRONT-OFFICE (Mobile Unity) │       BACK-OFFICE (Web Python)         │
│         Pour le Visiteur      │       Pour l'Administrateur/Historien  │
├───────────────────────────────┼────────────────────────────────────────┤
│ • Réalité Augmentée (Vuforia) │ • Création & Gestion des Stores RAG    │
│ • Chat vocal/texte (Gemini)   │ • Indexation / Upload / Drag&Drop PDF  │
│ • Fiches & Audios locaux      │ • Bac à sable de validation (BNF4)     │
│ • SQLite (100% Offline-first) │ • Liaison des IDs techniques SQLite    │
└───────────────────────────────┴────────────────────────────────────────┘
```

Ce dossier (`rag_dashboard`) constitue le **Back-Office d'Administration du Corpus Documentaire**. Il pilote l'infrastructure **Gemini File Search Tool** (Google GenAI) pour alimenter le RAG de niveau 2 sans nécessiter d'infrastructure externe lourde (serveur PHP/cron).

---

## 2. Stack Technique FIGÉE

- **Langage & Runtime :** Python 3.12+ (testé et validé sous Python 3.14 Windows)
- **Framework Web Backend :** FastAPI + Uvicorn (ASGI)
- **Moteur de Templates :** Jinja2
- **Frontend & UI :** HTML5, Tailwind CSS (via CDN, config inline), Alpine.js, Lucide Icons
- **Design System :** Charte graphique « Gorée AR » - **coque dashboard** (sidebar gauche
  Corpus / Documents / Bac à sable / Aide + topbar collante), **thème sombre uniquement**
  (`<html class="dark">`, pas de bascule). Namespace de couleurs `goree-*` : fond
  `#0B0D17`, surface `#13172B`, card `#1B203B`, bordure `rgba(232,200,74,.15)`, or
  `#E8C84A` / hover `#F4D665`, accent bleu `#3B82F6`. Dégradés radiaux or/bleu sur le
  fond (`static/css/app.css`), `gold-gradient-text`, cartes `rounded-xl`/`rounded-2xl`
  avec ombres colorées (`shadow-amber-500/10`), or utilisé librement, icônes Lucide
  partout, drapeaux emoji dans le sélecteur de langue, point vert pulsant « API
  Connectée ». Typographies : *Marcellus* (titres) et *Plus Jakarta Sans* (corps).
- **SDK & API Cloud :**
  - SDK officiel `google-genai` pour la gestion des `file_search_stores` (création, upload de PDF, suppression)
  - Requêtes HTTP REST directes (`urllib.request` ou `requests`) vers l'endpoint v1beta `generateContent` pour le bac à sable de test (garantissant un alignement 1:1 avec les appels `UnityWebRequest` de l'application mobile)
  - `supabase` (client `service_role`) pour l'archivage des PDF sources : bucket privé
    `corpus-pdfs` + table `public.corpus_documents` (projet `GoreeAR`). Optionnel - si `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` absents du `.env`, l'archivage et le
    bouton « Visualiser » sont simplement désactivés.
  - `bcrypt` + `itsdangerous` pour l'authentification (voir §3.3)
- **Modèle IA par défaut :** `gemini-3.5-flash-lite` (ultra-rapide < 2s, économique en tokens, support complet du File Search Tool)

---

## 2 bis. Base de Données Supabase (projet `GoreeAR`, `ubajzrbphbqoomtxoqsk`)

Le projet Supabase héberge **aussi** le schéma de l'app mobile (`point_interet`, `routes`,
`traduction`, `utilisateur`, `route_*`). Le back-office ne possède que ce qui suit et **ne
doit jamais toucher au reste** :

| Objet | Rôle |
|---|---|
| Table `public.corpus_documents` | Lie un document Google File Search (`google_document_name`) à sa copie dans le bucket (`storage_path`) + `file_name`, `size_bytes`, `store_display_name`, `created_at`. |
| Table `public.admin_users` | Comptes admin : `email` (unique, insensible casse), `password_hash` (bcrypt), `full_name`, `is_active`, `last_login_at`. |
| Bucket privé `corpus-pdfs` | Copie des PDF sources, un objet par document : `<store_ref>/<uuid>.pdf`. |

Les deux tables ont **RLS activé, aucune policy, `SELECT` révoqué pour `anon` et
`authenticated`** : seul le backend y accède, avec la `service_role` key. Les hash bcrypt
et les URL de stockage ne transitent jamais vers le front. L'`INFO rls_enabled_no_policy`
des advisors Supabase est **volontaire** (verrou total assumé).

---

## 3. Règles de Sécurité et Clé API - Strictes

1. **Jamais de clé/secret en dur dans le code source** :
   - `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SESSION_SECRET`, `SESSION_COOKIE_SECURE` sont chargés depuis `.env` via `python-dotenv`.
   - Le fichier `.env` doit **toujours** être présent localement mais **exclu de tout versionnement Git** (`.gitignore`, ainsi que `uploads/`).
   - `SUPABASE_SERVICE_KEY` est la clé `service_role` (bypass RLS) : elle ne quitte jamais le backend, jamais exposée au navigateur ni au template.
2. **Affichage sécurisé sur l'interface** :
   - L'interface web ne doit jamais afficher la clé Gemini en clair (masquage obligatoire : `AQ...wdyg`). Aucune clé Supabase n'est transmise au front.
   - Le bucket `corpus-pdfs` est **privé** : la visualisation d'un PDF passe par une URL signée (expiration 1 h) générée côté serveur, jamais par un lien public.

### 3.1. Variables `.env` attendues

| Variable | Rôle | Obligatoire |
|---|---|---|
| `GEMINI_API_KEY` | Clé Gemini (File Search + génération) | Oui |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` | Archivage PDF + comptes admin. Absents → archivage et « Visualiser » désactivés, mais **l'authentification l'est aussi** (comptes en base). | En pratique oui |
| `SESSION_SECRET` | Signature du cookie de session | Oui (sinon clé éphémère) |
| `SESSION_COOKIE_SECURE` | `true` derrière HTTPS, `false` en local | Défaut `false` |
### 3.3. Authentification obligatoire

- L'accès à la plateforme passe par une connexion (`/login`). Le middleware `require_login`
  refuse toute route hors `PUBLIC_PATHS` (`/login`, `/logout`, `/static/*`, `/favicon.ico`)
  sans session : **302** vers `/login` pour les pages, **401 JSON** pour `/api/*`.
- **Ordre des middlewares** : `require_login` est enregistré **avant** `SessionMiddleware`
  pour s'exécuter **après** lui (Starlette empile à l'envers). Ne pas réordonner.
- Comptes dans `public.admin_users`. Mots de passe **bcrypt** (module `bcrypt` directement,
  `passlib` 1.7.4 étant incompatible avec `bcrypt` 5.x, ne pas le réintroduire). Jamais en
  clair, jamais renvoyés au front.
- `POST /login` : vérifie email (insensible casse) + `is_active` + bcrypt, pose
  `session["user_id"]`, met à jour `last_login_at`. Erreur générique « Identifiants
  invalides ». Rate-limit en mémoire par IP : 5 échecs / 5 min → **429**.
- Session : cookie signé `goree_session` (httponly, `same_site=lax`,
  `https_only=SESSION_COOKIE_SECURE`), durée 8 h. Si `SESSION_SECRET` absent du `.env`, une
  clé éphémère est générée (sessions perdues au redémarrage) avec un avertissement.
- **Pas d'inscription publique.** Création / réinitialisation de compte via
  `python create_admin.py <email> "<Nom>"` (mot de passe demandé en masqué).
- **En production HTTPS** : `SESSION_COOKIE_SECURE=true` **obligatoire** et `SESSION_SECRET`
  fixé dans l'environnement d'hébergement.

---

## 4. Conventions d'Architecture RAG (File Search Stores)

### 4.1. Granularité des Stores (Option A - Cloisonnement strict)
- **Un Store distinct par monument ou par salle physique du musée** :
  - `goree-maison-esclaves`
  - `goree-musee-salle1` (Gorée et Visiteurs Célèbres)
  - `goree-musee-salle2` (Paléolithique / Néolithique)
  - etc.
- **Justification académique & technique** : Élimine le risque d'erreur humaine d'étiquetage et garantit l'étanchéité stricte entre les contextes historiques.

### 4.2. Liaison avec la Base SQLite locale (Unity)
- Google attribue à chaque store un identifiant technique universel du type :
  `fileSearchStores/goreemaisonesclaves-vxqxk0scxpj5`
- Cet identifiant est copiable en un clic depuis le dashboard et doit être inséré dans la colonne **`nom_store_rag`** de la table `Site` dans `goree_ar.db`.

### 4.3. Nommage des Fichiers lors de l'Upload
- Lors de l'envoi d'un PDF à Google via `upload_to_file_search_store`, toujours fournir le nom original :
  ```python
  config={"display_name": file.filename}
  ```
  afin d'éviter que le fichier ne soit nommé avec un nom temporaire anonyme (`tmp...pdf`).

---

## 5. Besoins Non-Fonctionnels (BNF) - Respect impératif

Tout agent travaillant sur le backend ou le bac à sable doit respecter :

- **BNF4 - Fiabilité historique et refus strict hors-périmètre :**
  - L'agent conversationnel ne doit répondre qu'à partir des documents du store et des faits historiques de Gorée / la traite négrière.
  - Si l'utilisateur pose une question hors-sujet (ex. *« Quelle est la capitale du Japon ? »*, météo, maths), **le prompt système doit contraindre l'IA à refuser poliment** en rappelant sa fonction exclusive de guide patrimonial de l'île.
- **Adaptation aux Profils UML :**
  - `touriste` : Récit chaleureux, immersif et équilibré.
  - `eleve` : Vocabulaire simple, pédagogique, direct, sans jargon.
  - `universitaire` : Analyse historiographique critique, mise en avant des sources et de la nuance archives/tradition orale.
- **Trilinguisme :**
  - Prise en charge des trois langues du projet : Français (`fr`), Anglais (`en`), Wolof (`wo`).

---

## 6. Structure des Fichiers du Projet

```
rag_dashboard/
├── AGENTS.md                  # Ce fichier de règles et conventions
├── CLAUDE.md                  # Contexte architecture + commandes (pour Claude Code)
├── app.py                     # Serveur FastAPI : auth, Google GenAI/REST, Supabase
├── create_admin.py            # Script CLI : création/réinitialisation d'un compte admin
├── test_call.py               # Diagnostic rapide de l'API Gemini File Search
├── requirements.txt           # Dépendances Python
├── .env                       # Secrets, non versionné (cf. §3.1)
├── templates/
│   ├── index.html             # Interface principale (coque dashboard, Tailwind + Alpine.js)
│   └── login.html             # Page de connexion (autonome, sans Alpine)
├── static/
│   ├── css/
│   │   └── app.css            # Fond, dégradés, focus-visible, prefers-reduced-motion
│   └── js/
│       ├── app.js             # Composant Alpine `ragApp()` (chargé avec ?v=N)
│       └── tailwind.config.js # Miroir de la config Tailwind inline
└── docs/plans/                # Plans d'implémentation (dont _avant/ : snapshots figés)
```

---

## 7. Commandes Utiles pour l'Agent

```bash
pip install -r requirements.txt          # dépendances
python app.py                            # serveur dev, http://localhost:8000, --reload
python create_admin.py <email> "<Nom>"   # créer/réinitialiser un compte admin (mdp masqué)
python test_call.py                      # diagnostic direct de l'API Gemini
```

Pas de suite de tests, de linter ni de build. `python app.py` fonctionne sous Windows
(les emoji des `print()` de démarrage ont été retirés) ; `python -m uvicorn app:app` aussi.
`app.js` étant chargé avec un cache-buster `?v=N`, **incrémenter N** dans `index.html` à
chaque modification de `app.js`.
