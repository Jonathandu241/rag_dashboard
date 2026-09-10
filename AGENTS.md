# AGENTS.md — Règles pour l'agent IA (Gorée AR — RAG Studio & Back-Office)

> Ce document définit les règles **fermes** et les conventions techniques que tout agent IA
> doit respecter lors de l'intervention sur le projet **Gorée AR — RAG Studio** (Back-Office d'administration).
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
- **Frontend & UI :** HTML5, Tailwind CSS (via CDN), Alpine.js, Lucide Icons
- **Design System :** Charte graphique « Gorée AR » (Bleu nuit `#0B0D17` / `#13172B`, Or Gorée `#E8C84A`, typographies *Marcellus* et *Plus Jakarta Sans*)
- **SDK & API Cloud :** 
  - SDK officiel `google-genai` pour la gestion des `file_search_stores` (création, upload de PDF, suppression)
  - Requêtes HTTP REST directes (`urllib.request` ou `requests`) vers l'endpoint v1beta `generateContent` pour le bac à sable de test (garantissant un alignement 1:1 avec les appels `UnityWebRequest` de l'application mobile)
- **Modèle IA par défaut :** `gemini-3.5-flash-lite` (ultra-rapide < 2s, économique en tokens, support complet du File Search Tool)

---

## 3. Règles de Sécurité et Clé API — Strictes

1. **Jamais de clé API en dur dans le code source** :
   - La clé API Gemini est chargée depuis la variable d'environnement `GEMINI_API_KEY` via `python-dotenv`.
   - Le fichier `.env` doit **toujours** être présent localement mais **exclu de tout versionnement Git** (`.gitignore`).
2. **Affichage sécurisé sur l'interface** :
   - L'interface web ne doit jamais afficher la clé en clair (masquage obligatoire : `AQ...wdyg`).

---

## 4. Conventions d'Architecture RAG (File Search Stores)

### 4.1. Granularité des Stores (Option A — Cloisonnement strict)
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

## 5. Besoins Non-Fonctionnels (BNF) — Respect impératif

Tout agent travaillant sur le backend ou le bac à sable doit respecter :

- **BNF4 — Fiabilité historique et refus strict hors-périmètre :**
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
├── app.py                     # Serveur FastAPI + logique Google GenAI & REST
├── requirements.txt           # Dépendances Python nécessaires
├── .env                       # Clé GEMINI_API_KEY (non versionné)
├── templates/
│   └── index.html             # Interface web complète (Tailwind + Alpine.js)
├── static/
│   ├── css/
│   │   └── app.css            # Styles additionnels éventuels
│   └── js/
│       ├── app.js             # Logique applicative Alpine.js
│       └── tailwind.config.js # Configuration Tailwind du thème Gorée AR
└── test_call.py               # Script de diagnostic rapide de l'API Gemini
```

---

## 7. Commandes Utiles pour l'Agent

- **Installation des dépendances :**
  ```bash
  pip install -r requirements.txt
  ```
- **Lancement du serveur de développement :**
  ```bash
  python app.py
  ```
  *(Accessible par défaut sur `http://localhost:8000` avec rechargement automatique)*
- **Test de diagnostic direct de l'API :**
  ```bash
  python test_call.py
  ```
