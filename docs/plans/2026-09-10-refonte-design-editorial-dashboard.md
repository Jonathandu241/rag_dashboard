# Plan : Refonte design — coque dashboard éditoriale « Gorée AR »

## Objectif

Refondre l'interface web du back-office (une seule page, `templates/index.html`) pour
supprimer les marqueurs visuels « générés par IA » (dégradés, glassmorphism, or fluo
omniprésent, animations décoratives, vocabulaire pompeux) et adopter une **coque de
dashboard classique** — sidebar de navigation à gauche, topbar, zone de contenu — habillée
d'une **charte éditoriale/institutionnelle ancrée dans l'île de Gorée** (chaux, basalte,
laiton ; serif de titrage *Marcellus* + sans technique *IBM Plex Sans* ; zéro dégradé).

Le backend (`app.py`), les endpoints, les prompts BNF4 et le comportement Alpine existant
ne changent pas. On ajoute : un **toggle de thème clair/sombre** persistant, une **sidebar
repliable en tiroir sur mobile**, et une **troisième vue « Aide »** (statique, sans backend).

## Architecture

```
┌────────────┬────────────────────────────────────────────────┐
│  SIDEBAR   │  TOPBAR : titre de la vue courante      [☰] [☾] │
│  (gauche,  ├────────────────────────────────────────────────┤
│   240px)   │                                                │
│  Gorée AR  │   CONTENU (max ~1000px, aligné à gauche)        │
│            │                                                │
│  Corpus ◂  │   — vue 'corpus'  : KPI + nouveau fonds + liste │
│  Test      │   — vue 'test'    : formulaire playground BNF4  │
│  Aide      │   — vue 'aide'    : conventions du projet       │
│            │                                                │
│  ┈┈┈┈┈┈┈┈  │                                                │
│  Clé API ● │                                                │
└────────────┴────────────────────────────────────────────────┘

Mobile < 900px : sidebar masquée (translateX(-100%)), bouton ☰ dans la topbar
la fait glisser par-dessus le contenu + overlay. Fermeture : clic overlay OU
clic sur une entrée de nav.
```

État Alpine ajouté au composant `ragApp()` :
- `currentTab` : passe de 2 valeurs (`corpus` / `playground`) à 3 (`corpus` / `test` / `aide`).
  ⚠️ Renommage `playground` → `test` dans le HTML **et** partout où `app.js` le lit. Vérifié :
  `app.js` ne teste jamais `currentTab` par valeur (seul le HTML le fait via `x-show`), donc
  le renommage est purement HTML. `currentTab` est initialisé à `'corpus'` — inchangé.
- `sidebarOpen` (bool, défaut `false`) : état du tiroir mobile.
- `theme` (`'light'` | `'dark'`, lu depuis `localStorage` au démarrage, défaut `'light'`).
- `toggleTheme()` : bascule `theme`, écrit `localStorage`, applique/retire la classe `dark`
  sur `<html>`.

## Stack technique

- Python 3.12+ / FastAPI / Jinja2 (inchangé — aucun fichier `.py` modifié).
- Front : HTML5 + Tailwind CSS **via CDN** (config inline dans `<script>`, pas de build) +
  Alpine.js 3 + Lucide Icons. Toutes ces dépendances CDN existent déjà dans `index.html`.
- Google Fonts : *Marcellus* (déjà chargée) + **ajout** *IBM Plex Sans* (400, 500, 600) et
  *IBM Plex Mono* (400).
- Aucun test automatisé dans ce dépôt (cf. `CLAUDE.md`). La validation de chaque tâche est
  **manuelle** : lancer `python app.py`, ouvrir `http://127.0.0.1:8000`, vérifier le critère
  visuel décrit. Un fichier `test_call.py` existe mais ne teste que l'API Gemini, pas l'UI.

## Prérequis

- Dépendances installées : `pip install -r requirements.txt`.
- `.env` présent avec `GEMINI_API_KEY` (sinon l'app démarre mais `/api/stores` renvoie 400 —
  suffisant pour valider le rendu de la coque et de la vue Aide ; pour valider Corpus/Test
  avec des vraies données il faut une clé valide et au moins un store).
- Navigateur avec DevTools pour tester le responsive (< 900px) et `localStorage`.
- Ce plan modifie 5 fichiers, tous dans `templates/` et `static/` :
  - `templates/index.html` (refonte lourde)
  - `static/css/app.css` (nettoyage + tokens)
  - `static/js/app.js` (ajout état thème + sidebar)
  - `static/js/tailwind.config.js` (miroir de la config inline — non chargé par la page
    mais gardé cohérent, cf. `AGENTS.md` §6)
  - `CLAUDE.md` (mise à jour de la section charte) + `AGENTS.md` §2 (charte)

---

## Charte de référence (à respecter dans toutes les tâches)

### Couleurs — thème clair (défaut)

| Rôle              | Hex        | Usage                                             |
|-------------------|------------|--------------------------------------------------|
| `bg`              | `#F2EEE6`  | fond de page (chaux, tiré sable/gris)            |
| `surface`         | `#FBFAF6`  | fond sidebar, blocs de réponse, champs           |
| `ink`             | `#1E1B16`  | texte principal (brun-noir basalte)             |
| `muted`           | `#6B6459`  | libellés, méta, texte secondaire                |
| `line`            | `#D8D1C2`  | filets, bordures, séparateurs                    |
| `accent`          | `#9C7A24`  | bouton primaire, liens, bord onglet actif        |
| `accent-hover`    | `#856619`  | survol du bouton primaire                        |
| `danger`          | `#8A3B2E`  | suppression (texte + bord)                       |

### Couleurs — thème sombre (`html.dark`)

| Rôle              | Hex        |
|-------------------|------------|
| `bg`              | `#1A1815`  |
| `surface`         | `#232019`  |
| `ink`             | `#E8E2D4`  |
| `muted`           | `#9A9184`  |
| `line`            | `#3A352C`  |
| `accent`          | `#C9A64E`  |
| `accent-hover`    | `#D8B45E`  |
| `danger`          | `#C56B58`  |

### Typographie

- **Marcellus** (`font-display`) : titre sidebar, titres de section, chiffres KPI, entrées de nav.
- **IBM Plex Sans** (`font-sans`) : corps, libellés, boutons, options de select.
- **IBM Plex Mono** (`font-mono`) : **uniquement** l'ID technique `fileSearchStores/…`.
- Échelle (px) : 13 / 14 / 16 / 20 / 28 / 36. Interligne corps : 1.6. Paragraphes d'aide ≤ 68 car.
- **Interdit** : `uppercase` + `tracking-wider` sur les libellés → casse phrase, `text-[13px]`,
  couleur `muted`.

### Style

- Rayon : `2px` partout (`rounded-sm` Tailwind = 2px). Jamais `rounded-lg/xl/2xl/full`.
- Séparation : filets `1px` couleur `line`. **Aucune** ombre portée sauf toast et tiroir mobile.
- **Interdit** : `bg-gradient-*`, `radial-gradient`, `backdrop-blur-*`, `animate-pulse`,
  `animate-bounce`, `shadow-amber-*`, `.gold-gradient-text`.
- **Autorisé** : `animate-spin` sur l'icône « actualiser » pendant `loading` ; `x-transition`
  sur toast + tiroir ; transition `colors` 120ms sur éléments cliquables.

### Vocabulaire FR (remplacements)

| Avant                                            | Après                                              |
|--------------------------------------------------|---------------------------------------------------|
| `GORÉE AR` + badge `RAG STUDIO`                  | `Gorée AR` (sidebar) / titre de vue dans la topbar |
| `Gestionnaire de Corpus Documentaire • …`        | *(supprimé)*                                        |
| onglet `Corpus & Stores`                         | `Corpus`                                            |
| onglet `Bac à sable (Test IA)`                   | `Test`                                              |
| `Stores Actifs` / `Documents Indexés` / `Modèle de RAG` | `Fonds` / `Documents` / `Modèle`            |
| `Créer un nouveau File Search Store`             | `Nouveau fonds`                                     |
| `Stores Documentaires Déployés`                  | *(pas de titre)*                                    |
| `Aucun File Search Store`                        | `Aucun fonds pour l'instant. Créez-en un ci-dessus pour y déposer des PDF.` |
| `API Connectée` (point vert pulsant)            | bas de sidebar : `Clé API` + point + `OK` / `absente` |
| `Bac à sable de Test RAG — Guide IA Gorée`       | `Test du guide`                                     |
| `Interrogation du RAG en cours...`              | `Recherche en cours…`                               |
| `Tester la réponse de l'Agent IA (Règles BNF4)` | `Envoyer la question`                               |
| `Réponse de l'Agent IA Gorée AR :`              | `Réponse`                                           |
| `🇫🇷 Français` / `🇬🇧 English` / `🇸🇳 Wolof`         | `Français` / `English` / `Wolof` (sans drapeaux)   |
| `Store Documentaire` (label select)             | `Fonds`                                             |
| `Store créé avec succès !` (toast)             | `Fonds créé.`                                       |
| `Store supprimé.`                               | `Fonds supprimé.`                                   |

---

## Tâches

> Chaque tâche est autonome et se valide visuellement. Faire un commit atomique par tâche.
> **Le dépôt n'est pas un dépôt git** (`git init` non fait). Si `git status` échoue, exécuter
> d'abord `git init && git add -A && git commit -m "chore: état initial avant refonte design"`
> puis créer `.gitignore` contenant `.env` et `__pycache__/` (le `.env` contient une vraie
> clé — ne jamais le committer). Sinon, ignorer les blocs `git` de chaque tâche.

---

### Tâche 1 : Préparer le dépôt et sauvegarder l'état actuel

**Fichiers concernés :**
- `.gitignore` (créer si absent)
- capture de l'existant : `docs/plans/_avant/` (créer)

**Actions :**
```bash
cd "C:/Projects/Python/rag_dashboard"

# 1. Init git si nécessaire
git rev-parse --is-inside-work-tree 2>/dev/null || git init

# 2. .gitignore — la clé API réelle est dans .env, NE JAMAIS la committer
cat > .gitignore <<'EOF'
.env
__pycache__/
*.pyc
EOF

# 3. Sauvegarde des 3 fichiers front avant refonte
mkdir -p docs/plans/_avant
cp templates/index.html         docs/plans/_avant/index.html.bak
cp static/css/app.css           docs/plans/_avant/app.css.bak
cp static/js/app.js             docs/plans/_avant/app.js.bak
cp static/js/tailwind.config.js docs/plans/_avant/tailwind.config.js.bak

# 4. Commit de l'état initial
git add -A
git commit -m "chore: sauvegarde de l'UI avant refonte design éditoriale"
```

**Critère de validation :**
- `git log --oneline` montre le commit initial.
- `docs/plans/_avant/` contient 4 fichiers `.bak`.
- `git status --ignored` liste `.env` comme ignoré.

**Commit :** inclus dans les actions ci-dessus.

---

### Tâche 2 : Charger les polices et poser les tokens CSS

**Fichiers concernés :**
- `static/css/app.css` (remplacer intégralement)

**Implémentation — remplacer tout le contenu de `static/css/app.css` par :**
```css
/* Charte "Gorée AR" — back-office corpus documentaire.
   Registre éditorial : chaux (bg), basalte (ink), laiton (accent). Zéro dégradé. */

:root {
  --bg: #F2EEE6;
  --surface: #FBFAF6;
  --ink: #1E1B16;
  --muted: #6B6459;
  --line: #D8D1C2;
  --accent: #9C7A24;
  --accent-hover: #856619;
  --danger: #8A3B2E;
}

html.dark {
  --bg: #1A1815;
  --surface: #232019;
  --ink: #E8E2D4;
  --muted: #9A9184;
  --line: #3A352C;
  --accent: #C9A64E;
  --accent-hover: #D8B45E;
  --danger: #C56B58;
}

body {
  background-color: var(--bg);
  color: var(--ink);
}

/* Longueur de ligne confortable pour les paragraphes d'aide */
.prose-help {
  max-width: 62ch;
  line-height: 1.6;
}

/* Barre latérale de l'onglet actif (filet laiton) */
.nav-link-active {
  box-shadow: inset 2px 0 0 0 var(--accent);
}

/* Respect de prefers-reduced-motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Implémentation — dans `templates/index.html`, remplacer le bloc `<link ... Marcellus ...>` par :**
```html
    <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap" rel="stylesheet">
```

**Implémentation — dans `templates/index.html`, remplacer le bloc `<style>…</style>` du `<head>` par :**
```html
    <style>
      /* les tokens et le fond sont dans /static/css/app.css */
    </style>
    <link rel="stylesheet" href="/static/css/app.css">
```
(⚠️ Vérifier que `app.css` est bien servi : `app.mount("/static", ...)` existe déjà dans
`app.py`. L'ancien `index.html` **ne chargeait pas** `app.css` — cette ligne l'ajoute.)

**Commande à exécuter :**
```bash
python app.py
# ouvrir http://127.0.0.1:8000 — la page est cassée visuellement (normal),
# mais : fond crème #F2EEE6, texte brun foncé, aucune erreur 404 sur app.css
# (vérifier l'onglet Network des DevTools : /static/css/app.css → 200)
```

**Critère de validation :** `app.css` répond en 200 ; le fond de page est `#F2EEE6` ;
les polices IBM Plex se chargent (onglet Network → fonts.gstatic.com).

**Commit :**
```bash
git add templates/index.html static/css/app.css
git commit -m "style: tokens couleur clair/sombre + polices Marcellus/IBM Plex"
```

---

### Tâche 3 : Réécrire la config Tailwind inline (couleurs + polices)

**Fichiers concernés :**
- `templates/index.html` (bloc `<script>tailwind.config = {…}</script>` dans le `<head>`)
- `static/js/tailwind.config.js` (miroir)

**Implémentation — remplacer le bloc `tailwind.config` inline de `index.html` par :**
```html
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        display: ['Marcellus', 'serif'],
                        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
                        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
                    },
                    colors: {
                        bg: 'var(--bg)',
                        surface: 'var(--surface)',
                        ink: 'var(--ink)',
                        muted: 'var(--muted)',
                        line: 'var(--line)',
                        accent: 'var(--accent)',
                        'accent-hover': 'var(--accent-hover)',
                        danger: 'var(--danger)',
                    },
                    borderRadius: {
                        DEFAULT: '2px',
                        sm: '2px',
                        md: '2px',
                        lg: '2px',
                        xl: '2px',
                        '2xl': '2px',
                        full: '2px',
                    },
                },
            },
        }
    </script>
```
(Note : mapper toutes les échelles de `borderRadius` sur `2px` neutralise les
`rounded-xl`/`rounded-2xl` résiduels sans devoir tous les chasser — ceinture + bretelles.
Les tâches suivantes les remplacent quand même par `rounded-sm` pour la lisibilité.)

**Implémentation — remplacer `static/js/tailwind.config.js` par le même objet (sans les balises `<script>`), précédé du commentaire :**
```js
// Miroir de la config Tailwind inline de templates/index.html (non chargé par la page,
// gardé cohérent — cf. AGENTS.md §6). Toute modif ici doit être répercutée dans le <head>.
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                display: ['Marcellus', 'serif'],
                sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
                mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
            },
            colors: {
                bg: 'var(--bg)',
                surface: 'var(--surface)',
                ink: 'var(--ink)',
                muted: 'var(--muted)',
                line: 'var(--line)',
                accent: 'var(--accent)',
                'accent-hover': 'var(--accent-hover)',
                danger: 'var(--danger)',
            },
            borderRadius: {
                DEFAULT: '2px', sm: '2px', md: '2px', lg: '2px', xl: '2px', '2xl': '2px', full: '2px',
            },
        },
    },
};
```

**Commande à exécuter :**
```bash
python app.py
# La page reste cassée (markup pas encore refait) mais : plus aucune couleur "goree-*"
# n'est résolue → les éléments qui utilisaient bg-goree-surface deviennent transparents.
# C'est attendu. Vérifier qu'il n'y a pas d'erreur JS console liée à tailwind.config.
```

**Critère de validation :** pas d'erreur console ; `document.documentElement` a la classe
`dark` togglable à la main (`document.documentElement.classList.toggle('dark')`) et le fond
change entre `#F2EEE6` et `#1A1815`.

**Commit :**
```bash
git add templates/index.html static/js/tailwind.config.js
git commit -m "style: config Tailwind — tokens sémantiques, rayon 2px, polices"
```

---

### Tâche 4 : Ajouter l'état thème + sidebar dans `app.js`

**Fichiers concernés :**
- `static/js/app.js` (modifier `ragApp()` : ajouter propriétés + méthodes, adapter `init()`)

**Implémentation — dans `static/js/app.js`, modifier l'objet retourné par `ragApp()` :**

1. Ajouter ces propriétés juste après `currentTab: 'corpus',` :
```js
        sidebarOpen: false,
        theme: 'light',
```

2. Remplacer la méthode `init()` par :
```js
        init() {
            // Thème : lu depuis localStorage, appliqué à <html>
            try {
                this.theme = localStorage.getItem('goree-theme') || 'light';
            } catch (e) {
                this.theme = 'light';
            }
            this.applyTheme();
            this.fetchStores();
            this.$nextTick(() => lucide.createIcons());
        },

        applyTheme() {
            document.documentElement.classList.toggle('dark', this.theme === 'dark');
        },

        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            try {
                localStorage.setItem('goree-theme', this.theme);
            } catch (e) { /* stockage indisponible : la bascule reste valable pour la session */ }
            this.applyTheme();
            this.$nextTick(() => lucide.createIcons());
        },

        goTo(tab) {
            this.currentTab = tab;
            this.sidebarOpen = false;
        },
```

3. Dans le toast `createStore()` : remplacer `"Store créé avec succès !"` par `"Fonds créé."`.
4. Dans `deleteStore()` : remplacer `"Store supprimé."` par `"Fonds supprimé."`.
5. Ne rien changer d'autre (les `fetch`, `uploadFile`, `deleteDocument`,
   `runPlaygroundTest`, `copyToClipboard` restent identiques).

**Commande à exécuter :**
```bash
python app.py
# Console DevTools :
#   > Alpine.$data(document.body).theme          → "light"
#   > Alpine.$data(document.body).toggleTheme()  → <html> reçoit/perd la classe "dark"
#   > localStorage.getItem('goree-theme')        → "dark" puis persiste au rechargement
```

**Critère de validation :** `toggleTheme()` bascule la classe `dark` sur `<html>` et
persiste dans `localStorage` après rechargement (F5). Aucune régression sur `fetchStores`.

**Commit :**
```bash
git add static/js/app.js
git commit -m "feat: état thème clair/sombre persistant + helper navigation sidebar"
```

---

### Tâche 5 : Construire la coque — sidebar gauche + topbar + overlay mobile

**Fichiers concernés :**
- `templates/index.html` (remplacer `<body>…</body>` — structure de coque uniquement,
  le contenu des vues est mis en place aux tâches 6–8)

**Implémentation — remplacer la balise `<body …>` et son contenu jusqu'à `</body>` par :**
```html
<body class="font-sans min-h-screen antialiased" x-data="ragApp()" x-init="init()">

  <!-- Overlay du tiroir mobile -->
  <div x-show="sidebarOpen" x-transition.opacity @click="sidebarOpen = false"
       class="fixed inset-0 bg-black/40 z-30 lg:hidden" style="display:none"></div>

  <div class="flex min-h-screen">

    <!-- ───────────── SIDEBAR ───────────── -->
    <aside
      class="fixed lg:static inset-y-0 left-0 z-40 w-60 shrink-0 bg-surface border-r border-line
             flex flex-col transition-transform duration-200
             -translate-x-full lg:translate-x-0"
      :class="sidebarOpen && '!translate-x-0'">

      <div class="h-14 flex items-center px-5 border-b border-line">
        <span class="font-display text-lg text-ink">Gorée AR</span>
      </div>

      <nav class="flex-1 py-3">
        <template x-for="item in [
            { id: 'corpus', label: 'Corpus' },
            { id: 'test',   label: 'Test' },
            { id: 'aide',   label: 'Aide' }
          ]" :key="item.id">
          <button
            @click="goTo(item.id)"
            class="w-full text-left px-5 py-2.5 font-display text-[15px] transition-colors"
            :class="currentTab === item.id
              ? 'text-ink nav-link-active'
              : 'text-muted hover:text-ink'"
            x-text="item.label"></button>
        </template>
      </nav>

      <div class="border-t border-line px-5 py-4 text-[13px] text-muted">
        <div class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-sm"
                :class="{{ 'true' if has_api_key else 'false' }} ? 'bg-accent' : 'bg-danger'"></span>
          <span>Clé API {{ 'OK' if has_api_key else 'absente' }}</span>
        </div>
        {% if has_api_key %}
        <p class="mt-1 font-mono text-[11px] text-muted/80">{{ api_key_masked }}</p>
        {% endif %}
      </div>
    </aside>

    <!-- ───────────── COLONNE PRINCIPALE ───────────── -->
    <div class="flex-1 min-w-0 flex flex-col">

      <!-- TOPBAR -->
      <header class="h-14 shrink-0 border-b border-line flex items-center gap-3 px-4 sm:px-6">
        <button @click="sidebarOpen = true" class="lg:hidden text-muted hover:text-ink" aria-label="Ouvrir le menu">
          <i data-lucide="menu" class="w-5 h-5"></i>
        </button>
        <h1 class="font-display text-lg text-ink"
            x-text="{ corpus: 'Corpus documentaire', test: 'Test du guide', aide: 'Aide' }[currentTab]"></h1>
        <button @click="toggleTheme()"
                class="ml-auto text-muted hover:text-ink transition-colors"
                :aria-label="theme === 'dark' ? 'Passer en clair' : 'Passer en sombre'">
          <i x-show="theme !== 'dark'" data-lucide="moon" class="w-5 h-5"></i>
          <i x-show="theme === 'dark'" data-lucide="sun" class="w-5 h-5" style="display:none"></i>
        </button>
      </header>

      <!-- CONTENU -->
      <main class="flex-1 px-4 sm:px-6 py-8">
        <div class="max-w-[1000px] mx-auto">

          <!-- VUE : CORPUS  (tâche 6) -->
          <div x-show="currentTab === 'corpus'" class="space-y-8">
            <p class="text-muted text-sm">Contenu Corpus — mis en place tâche 6.</p>
          </div>

          <!-- VUE : TEST  (tâche 7) -->
          <div x-show="currentTab === 'test'" class="space-y-6" style="display:none">
            <p class="text-muted text-sm">Contenu Test — mis en place tâche 7.</p>
          </div>

          <!-- VUE : AIDE  (tâche 8) -->
          <div x-show="currentTab === 'aide'" class="space-y-6" style="display:none">
            <p class="text-muted text-sm">Contenu Aide — mis en place tâche 8.</p>
          </div>

        </div>
      </main>
    </div>
  </div>

  <!-- TOAST -->
  <div x-show="toast.show" x-transition
       class="fixed bottom-6 right-6 z-50 bg-surface border border-line text-ink
              px-4 py-3 rounded-sm shadow-lg flex items-center gap-2"
       style="display:none">
    <i data-lucide="check" class="w-4 h-4 text-accent"></i>
    <span class="text-sm" x-text="toast.message"></span>
  </div>

  <script>lucide.createIcons();</script>
</body>
```

Notes d'implémentation :
- La classe `dark` sur `<html>` est posée par `applyTheme()` (JS), donc **retirer** `class="dark"`
  de la balise `<html>` en haut du fichier → `<html lang="fr">`.
- `{{ 'true' if has_api_key else 'false' }}` est rendu côté Jinja avant Alpine — au runtime
  la classe est fixe (la clé ne change pas pendant la session). C'est voulu.
- Les `style="display:none"` sur les `x-show` initialement faux évitent le flash au chargement.

**Commande à exécuter :**
```bash
python app.py
# Desktop : sidebar visible à gauche (240px), 3 entrées, "Corpus" actif (filet laiton à gauche),
#           topbar avec titre "Corpus documentaire" + lune à droite.
# Cliquer Test / Aide : le titre de la topbar change, le placeholder change.
# Toggle lune/soleil : bascule clair/sombre, persiste au F5.
# DevTools < 900px : sidebar cachée, bouton ☰ visible → ouvre le tiroir + overlay,
#           clic overlay ou entrée => referme.
```

**Critère de validation :** navigation entre les 3 vues OK ; toggle thème OK et persistant ;
tiroir mobile ouvre/ferme correctement ; aucun dégradé / blur visible ; focus clavier visible
sur les boutons de nav (Tab).

**Commit :**
```bash
git add templates/index.html
git commit -m "feat: coque dashboard — sidebar gauche, topbar, tiroir mobile, 3 vues"
```

---

### Tâche 6 : Vue Corpus — KPI + création de fonds + liste des fonds

**Fichiers concernés :**
- `templates/index.html` (remplacer le bloc `<div x-show="currentTab === 'corpus'">…</div>`)

**Implémentation — remplacer le placeholder de la vue corpus par :**
```html
          <div x-show="currentTab === 'corpus'" class="space-y-10">

            <!-- KPI : 3 blocs plats séparés par filets verticaux -->
            <div class="flex border border-line divide-x divide-line">
              <div class="flex-1 px-5 py-4">
                <div class="font-display text-3xl text-ink" x-text="stats.total_stores">0</div>
                <div class="text-[13px] text-muted mt-1">Fonds</div>
              </div>
              <div class="flex-1 px-5 py-4">
                <div class="font-display text-3xl text-ink" x-text="stats.total_docs">0</div>
                <div class="text-[13px] text-muted mt-1">Documents</div>
              </div>
              <div class="flex-1 px-5 py-4">
                <div class="font-display text-xl text-ink mt-1">gemini-flash-lite</div>
                <div class="text-[13px] text-muted mt-1">Modèle</div>
              </div>
            </div>

            <!-- Nouveau fonds -->
            <section class="space-y-3">
              <h2 class="font-display text-xl text-ink">Nouveau fonds</h2>
              <form @submit.prevent="createStore()" class="flex flex-col sm:flex-row gap-3">
                <input type="text" x-model="newStoreName" required
                       placeholder="goree-musee-salle2"
                       class="flex-1 sm:max-w-xs bg-surface border border-line rounded-sm px-3 py-2
                              text-sm text-ink placeholder-muted/60
                              focus:outline-none focus:border-accent">
                <button type="submit" :disabled="loading"
                        class="bg-accent hover:bg-accent-hover text-bg font-medium text-sm
                               px-4 py-2 rounded-sm transition-colors disabled:opacity-50">
                  Créer le fonds
                </button>
              </form>
              <p class="prose-help text-[13px] text-muted">
                Un fonds par monument ou salle du musée (ex. Maison des Esclaves, Musée — Salle 1).
                Chaque fonds reçoit un identifiant à reporter dans la colonne
                <span class="font-mono">nom_store_rag</span> de la base <span class="font-mono">goree_ar.db</span>.
              </p>
            </section>

            <!-- Liste des fonds -->
            <section class="space-y-0">
              <div class="flex items-center justify-between pb-3 border-b border-line">
                <h2 class="font-display text-xl text-ink">Fonds documentaires</h2>
                <button @click="fetchStores()"
                        class="text-[13px] text-muted hover:text-ink flex items-center gap-1.5 transition-colors">
                  <i data-lucide="refresh-cw" class="w-3.5 h-3.5" :class="loading && 'animate-spin'"></i>
                  Actualiser
                </button>
              </div>

              <template x-if="stores.length === 0">
                <p class="prose-help text-sm text-muted py-8">
                  Aucun fonds pour l'instant. Créez-en un ci-dessus pour y déposer des PDF.
                </p>
              </template>

              <template x-for="store in stores" :key="store.name">
                <div class="py-6 border-b border-line">

                  <!-- En-tête du fonds -->
                  <div class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <h3 class="font-display text-lg text-ink" x-text="store.display_name"></h3>
                    <span class="text-[13px] text-muted" x-text="`${store.docs_count} document(s)`"></span>
                    <button @click="deleteStore(store.name, store.display_name)"
                            class="ml-auto text-[13px] text-danger hover:underline">
                      Supprimer
                    </button>
                  </div>

                  <!-- ID technique -->
                  <div class="flex items-center gap-2 mt-1.5">
                    <code class="font-mono text-[12px] text-muted break-all select-all" x-text="store.name"></code>
                    <button @click="copyToClipboard(store.name)" title="Copier l'identifiant"
                            class="text-muted hover:text-accent shrink-0">
                      <i data-lucide="copy" class="w-3.5 h-3.5"></i>
                    </button>
                  </div>

                  <!-- Documents -->
                  <div class="mt-4 space-y-1.5">
                    <template x-if="store.docs.length === 0">
                      <p class="text-[13px] text-muted">Aucun document indexé.</p>
                    </template>
                    <template x-for="doc in store.docs" :key="doc.name">
                      <div class="flex items-center gap-3 py-1.5 border-b border-line/60 last:border-0">
                        <i data-lucide="file-text" class="w-4 h-4 text-muted shrink-0"></i>
                        <span class="text-sm text-ink truncate flex-1" x-text="doc.display_name"></span>
                        <span class="text-[12px] text-muted" x-text="doc.state.toLowerCase()"></span>
                        <button @click="deleteDocument(doc.name)"
                                class="text-muted hover:text-danger" title="Retirer le document">
                          <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                      </div>
                    </template>
                  </div>

                  <!-- Dépôt PDF -->
                  <div class="mt-4">
                    <input type="file" accept=".pdf" :id="`file_${store.name}`" class="hidden"
                           @change="uploadFile(store.name, $event)">
                    <label :for="`file_${store.name}`"
                           class="block border border-dashed border-line rounded-sm px-4 py-4 text-center
                                  cursor-pointer hover:border-accent transition-colors">
                      <span class="text-[13px] text-muted">
                        Déposer un PDF — Google se charge de l'indexation et des embeddings
                      </span>
                    </label>
                  </div>

                </div>
              </template>
            </section>
          </div>
```

**Commande à exécuter :**
```bash
python app.py
# Avec une clé API valide + au moins un fonds : la vue Corpus affiche les 3 KPI,
# le formulaire de création, la liste des fonds avec ID mono + bouton copier,
# les documents en lignes, la zone de dépôt en filet tireté.
# Sans clé : les KPI restent à 0, un message d'erreur peut apparaître (alert JS existant) —
# vérifier au moins que la structure statique s'affiche correctement.
# Tester : créer un fonds → toast "Fonds créé." ; copier l'ID → toast "ID copié…".
```

**Critère de validation :** création/suppression de fonds fonctionnent (toasts corrects) ;
upload PDF fonctionne ; l'ID est en police mono et copiable ; aucune carte arrondie/ombrée,
seulement des filets ; responsive < 640px : le formulaire empile champ + bouton.

**Commit :**
```bash
git add templates/index.html
git commit -m "feat(corpus): KPI plats, création de fonds, liste en blocs à filets"
```

---

### Tâche 7 : Vue Test — formulaire playground BNF4 + réponse

**Fichiers concernés :**
- `templates/index.html` (remplacer le bloc `<div x-show="currentTab === 'test'">…</div>`)

**Implémentation — remplacer le placeholder de la vue test par :**
```html
          <div x-show="currentTab === 'test'" class="space-y-6" style="display:none">

            <div>
              <h2 class="font-display text-xl text-ink">Test du guide</h2>
              <p class="prose-help text-[13px] text-muted mt-1">
                Reproduit le comportement de l'application mobile : ancrage strict sur le fonds
                choisi, refus poli hors périmètre (règle BNF4), adaptation au profil du visiteur.
              </p>
            </div>

            <form @submit.prevent="runPlaygroundTest()" class="space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label class="block text-[13px] text-muted mb-1.5">Fonds</label>
                  <select x-model="selectedPlaygroundStore" required
                          class="w-full bg-surface border border-line rounded-sm px-3 py-2 text-sm text-ink
                                 focus:outline-none focus:border-accent">
                    <option value="">Choisir un fonds</option>
                    <template x-for="s in stores" :key="s.name">
                      <option :value="s.name" x-text="`${s.display_name} (${s.docs_count})`"></option>
                    </template>
                  </select>
                </div>
                <div>
                  <label class="block text-[13px] text-muted mb-1.5">Profil</label>
                  <select x-model="selectedProfil"
                          class="w-full bg-surface border border-line rounded-sm px-3 py-2 text-sm text-ink
                                 focus:outline-none focus:border-accent">
                    <option value="touriste">Touriste</option>
                    <option value="eleve">Élève</option>
                    <option value="universitaire">Universitaire</option>
                  </select>
                </div>
                <div>
                  <label class="block text-[13px] text-muted mb-1.5">Langue</label>
                  <select x-model="selectedLangue"
                          class="w-full bg-surface border border-line rounded-sm px-3 py-2 text-sm text-ink
                                 focus:outline-none focus:border-accent">
                    <option value="fr">Français</option>
                    <option value="en">English</option>
                    <option value="wo">Wolof</option>
                  </select>
                </div>
              </div>

              <div>
                <label class="block text-[13px] text-muted mb-1.5">Question du visiteur</label>
                <textarea x-model="playgroundQuestion" rows="3" required
                          placeholder="Quelle est l'histoire de la porte du voyage sans retour ?"
                          class="w-full bg-surface border border-line rounded-sm px-3 py-2 text-sm text-ink
                                 placeholder-muted/60 focus:outline-none focus:border-accent"></textarea>
              </div>

              <button type="submit" :disabled="playgroundLoading"
                      class="bg-accent hover:bg-accent-hover text-bg font-medium text-sm
                             px-4 py-2 rounded-sm transition-colors disabled:opacity-50">
                <span x-text="playgroundLoading ? 'Recherche en cours…' : 'Envoyer la question'"></span>
              </button>
            </form>

            <template x-if="playgroundAnswer">
              <div class="pt-5 border-t border-line space-y-3">
                <div class="flex flex-wrap items-baseline gap-x-4 gap-y-1">
                  <span class="text-[13px] text-muted">Réponse</span>
                  <span class="text-[12px] text-muted" x-text="`profil : ${selectedProfil}`"></span>
                  <span class="text-[12px] text-muted" x-text="`langue : ${selectedLangue}`"></span>
                  <span class="text-[12px] text-muted" x-text="`modèle : ${playgroundModel}`"></span>
                </div>
                <div class="bg-surface border border-line rounded-sm p-4 text-sm text-ink
                            leading-relaxed whitespace-pre-line" x-text="playgroundAnswer"></div>
              </div>
            </template>
          </div>
```

**Commande à exécuter :**
```bash
python app.py
# Vue Test : 3 selects (sans drapeaux), textarea, bouton "Envoyer la question".
# Avec clé + fonds : poser une question dans le périmètre → réponse affichée dans un bloc
# à filet, méta en gris sans pastille colorée.
# Poser une question hors périmètre ("capitale du Japon ?") → le modèle doit refuser (BNF4).
# < 640px : les 3 selects s'empilent.
```

**Critère de validation :** l'appel `/api/playground/test` fonctionne, le libellé du bouton
passe à « Recherche en cours… » pendant le chargement, la réponse s'affiche ; aucune pastille
translucide colorée ; méta en texte gris simple.

**Commit :**
```bash
git add templates/index.html
git commit -m "feat(test): formulaire playground BNF4 sobre, réponse en bloc à filet"
```

---

### Tâche 8 : Vue Aide — conventions du projet

**Fichiers concernés :**
- `templates/index.html` (remplacer le bloc `<div x-show="currentTab === 'aide'">…</div>`)

**Implémentation — remplacer le placeholder de la vue aide par :**
```html
          <div x-show="currentTab === 'aide'" class="space-y-8 prose-help" style="display:none">

            <section class="space-y-2">
              <h2 class="font-display text-xl text-ink">Un fonds par lieu</h2>
              <p class="text-sm text-muted">
                Créez un fonds distinct pour chaque monument ou chaque salle physique du musée :
                <span class="font-mono text-[13px]">goree-maison-esclaves</span>,
                <span class="font-mono text-[13px]">goree-musee-salle1</span>,
                <span class="font-mono text-[13px]">goree-musee-salle2</span>…
                Ce cloisonnement évite les erreurs d'étiquetage et garde chaque contexte
                historique étanche.
              </p>
            </section>

            <section class="space-y-2">
              <h2 class="font-display text-xl text-ink">Reporter l'identifiant dans SQLite</h2>
              <p class="text-sm text-muted">
                Chaque fonds reçoit un identifiant technique du type
                <span class="font-mono text-[13px] break-all">fileSearchStores/goreemaisonesclaves-vxqxk0scxpj5</span>.
                Copiez-le depuis la vue Corpus et collez-le dans la colonne
                <span class="font-mono text-[13px]">nom_store_rag</span> de la table
                <span class="font-mono text-[13px]">Site</span>, base
                <span class="font-mono text-[13px]">goree_ar.db</span> de l'application Unity.
              </p>
            </section>

            <section class="space-y-2">
              <h2 class="font-display text-xl text-ink">Documents acceptés</h2>
              <p class="text-sm text-muted">
                PDF uniquement. À l'envoi, le nom d'origine du fichier est conservé.
                Google réalise le découpage, les embeddings et l'indexation ; l'opération
                peut prendre quelques secondes avant que le document passe à l'état
                <span class="font-mono text-[13px]">active</span>.
              </p>
            </section>

            <section class="space-y-2">
              <h2 class="font-display text-xl text-ink">Règle BNF4 — refus hors périmètre</h2>
              <p class="text-sm text-muted">
                Le guide ne répond qu'à partir des documents du fonds et des faits historiques
                de Gorée et de la traite négrière. Toute question sans lien (géographie
                générale, météo, calcul…) doit être poliment refusée. La vue Test permet de
                vérifier ce comportement avant de relier un fonds à l'application.
              </p>
            </section>
          </div>
```

**Commande à exécuter :**
```bash
python app.py
# Cliquer "Aide" dans la sidebar : 4 sections, titres Marcellus, texte gris,
# termes techniques en police mono, largeur de ligne limitée (~62ch), pas d'icône décorative.
```

**Critère de validation :** la vue Aide s'affiche, lisible, largeur de texte confortable,
cohérente avec le reste (mêmes tokens couleur, mêmes titres).

**Commit :**
```bash
git add templates/index.html
git commit -m "feat(aide): vue statique des conventions du projet"
```

---

### Tâche 9 : Passe de nettoyage et vérif accessibilité / responsive

**Fichiers concernés :**
- `templates/index.html`, `static/css/app.css` (retouches ponctuelles si besoin)

**Checklist à exécuter (cocher chaque point dans le navigateur) :**

1. **Aucun résidu visuel « IA »** — rechercher dans `index.html` (Grep) :
   ```bash
   grep -nE 'gradient|backdrop-blur|animate-(pulse|bounce)|shadow-amber|goree-(bg|surface|card|gold|border|accent)|gold-gradient-text|uppercase|tracking-wider|rounded-(lg|xl|2xl|full)|🇫|🇬|🇸' templates/index.html static/css/app.css
   ```
   Résultat attendu : **aucune correspondance** (sauf `rounded-*` si tu as gardé la neutralisation
   Tailwind — dans ce cas c'est OK, mais préférer `rounded-sm` explicite).

2. **Thème** : bascule clair↔sombre sur les 3 vues, F5 → thème conservé. Contraste texte lisible
   dans les deux (vérifier `muted` sur `bg` : ratio ≥ 4.5:1 pour le texte courant — `#6B6459`
   sur `#F2EEE6` ≈ 4.7:1 OK ; `#9A9184` sur `#1A1815` ≈ 5.2:1 OK).

3. **Focus clavier** : `Tab` parcourt sidebar → topbar → contenu ; anneau de focus visible
   sur boutons, liens, champs (Tailwind met un ring par défaut sur `:focus-visible` pour les
   `<button>`/`<a>` ? Non — ajouter dans `app.css` si absent) :
   ```css
   :where(a, button, input, select, textarea, label[for]):focus-visible {
     outline: 2px solid var(--accent);
     outline-offset: 2px;
   }
   ```

4. **Responsive** : tester à 1280 / 900 / 640 / 375 px.
   - ≥ 1024px : sidebar fixe visible, pas de bouton ☰.
   - < 1024px : sidebar cachée, ☰ visible, tiroir + overlay OK, fermeture au clic entrée/overlay.
   - < 640px : formulaire « Nouveau fonds » empilé, 3 selects du Test empilés, KPI —
     **vérifier** que les 3 blocs KPI ne débordent pas ; si trop serrés, passer le conteneur
     KPI en `flex-col sm:flex-row` avec `divide-y sm:divide-y-0 sm:divide-x`.

5. **`prefers-reduced-motion`** : activer dans DevTools (Rendering → Emulate CSS
   prefers-reduced-motion: reduce) → plus aucune transition/anim (règle déjà dans `app.css`).

6. **Sans clé API** : renommer `.env` temporairement, relancer → l'app démarre, la coque
   s'affiche, bas de sidebar montre « Clé API absente » (point brique), la vue Aide reste
   consultable. Restaurer `.env` ensuite.

**Commande à exécuter :**
```bash
python app.py
# Parcourir la checklist ci-dessus point par point.
```

**Critère de validation :** les 6 points passent. Grep du point 1 propre.

**Commit :**
```bash
git add templates/index.html static/css/app.css
git commit -m "polish: focus visible, garde-fous responsive, passe anti-résidus"
```

---

### Tâche 10 : Mettre à jour la documentation (CLAUDE.md + AGENTS.md)

**Fichiers concernés :**
- `CLAUDE.md` (section « Frontend »)
- `AGENTS.md` (§2 « Stack Technique FIGÉE » — lignes Design System / Frontend)

**Implémentation — dans `CLAUDE.md`, remplacer le paragraphe de la sous-section `### Frontend` par :**
```markdown
### Frontend

Server renders one page: `templates/index.html` (Jinja2), styled with Tailwind (CDN) + an
inline `tailwind.config` using semantic color tokens (`bg`, `surface`, `ink`, `muted`,
`line`, `accent`, `danger`) backed by CSS custom properties in `static/css/app.css`. Light
theme by default; `html.dark` swaps the tokens. Editorial "Gorée" charter — chaux `#F2EEE6`
ground, basalte `#1E1B16` ink, laiton `#9C7A24` accent, no gradients, 2px radius, hairline
`#D8D1C2` dividers instead of shadows. Fonts: *Marcellus* (display / headings / KPI numbers),
*IBM Plex Sans* (body), *IBM Plex Mono* (store IDs only).

Layout is a dashboard shell: fixed left sidebar (Corpus / Test / Aide), thin topbar with the
current view title and a light/dark toggle. Below 1024px the sidebar collapses into a ☰
drawer with an overlay. All interactivity is one Alpine.js component, `ragApp()` in
`static/js/app.js` — `currentTab` (`corpus` / `test` / `aide`), `theme` (persisted in
`localStorage` under `goree-theme`), `sidebarOpen`, plus the existing fetch calls to `/api/*`.
`static/js/tailwind.config.js` mirrors the inline config and must be kept in sync.
```

**Implémentation — dans `AGENTS.md` §2, remplacer les deux puces `Frontend & UI` et `Design System` par :**
```markdown
- **Frontend & UI :** HTML5, Tailwind CSS (via CDN, config inline), Alpine.js, Lucide Icons
- **Design System :** Charte « Gorée AR » éditoriale — coque dashboard (sidebar gauche +
  topbar), thème clair par défaut + sombre (`html.dark`, persisté `localStorage`).
  Fond chaux `#F2EEE6` / `#1A1815`, encre basalte `#1E1B16` / `#E8E2D4`, accent laiton
  `#9C7A24` / `#C9A64E` (usage rare : bouton primaire, liens, onglet actif), brique
  `#8A3B2E` pour la suppression. Aucun dégradé, rayon 2px, séparation par filets `#D8D1C2`.
  Typographies : *Marcellus* (titres, chiffres), *IBM Plex Sans* (corps), *IBM Plex Mono*
  (identifiants de fonds uniquement). Tokens sémantiques Tailwind : `bg`, `surface`, `ink`,
  `muted`, `line`, `accent`, `accent-hover`, `danger`.
```

**Commande à exécuter :**
```bash
grep -n "IBM Plex\|chaux\|laiton\|dashboard" CLAUDE.md AGENTS.md
# Vérifier que les deux fichiers reflètent la nouvelle charte.
```

**Critère de validation :** `CLAUDE.md` et `AGENTS.md` décrivent la coque dashboard, le thème
clair/sombre, la palette éditoriale et les trois polices. Plus aucune mention de
`#0B0D17` / `Plus Jakarta Sans` / `RAG Studio` comme charte active.

**Commit :**
```bash
git add CLAUDE.md AGENTS.md
git commit -m "docs: charte design éditoriale + coque dashboard"
```

---

## Récapitulatif des tâches

| # | Titre | Fichiers | Type |
|---|-------|----------|------|
| 1 | Préparer le dépôt + sauvegarde | `.gitignore`, `docs/plans/_avant/` | infra |
| 2 | Tokens CSS + polices | `app.css`, `index.html` (head) | style |
| 3 | Config Tailwind inline + miroir | `index.html` (head), `tailwind.config.js` | style |
| 4 | État thème + sidebar dans Alpine | `app.js` | feat |
| 5 | Coque : sidebar + topbar + tiroir | `index.html` (body) | feat |
| 6 | Vue Corpus | `index.html` | feat |
| 7 | Vue Test | `index.html` | feat |
| 8 | Vue Aide | `index.html` | feat |
| 9 | Nettoyage + a11y + responsive | `index.html`, `app.css` | polish |
| 10 | Documentation | `CLAUDE.md`, `AGENTS.md` | docs |

---

## Exécution du plan

### Option A — Sous-agent par tâche (session courante)
Chaque tâche est confiée à un sous-agent dédié dans cette session.
Lancer avec : `/execute-plan docs/plans/2026-09-10-refonte-design-editorial-dashboard.md`

### Option B — Session parallèle (worktree isolé)
Exécuter le plan dans une branche isolée via la compétence `executing-plans`.
Lancer avec : `/executing-plans docs/plans/2026-09-10-refonte-design-editorial-dashboard.md`

### Option C — Manuel, tâche par tâche
Suivre les tâches 1→10 dans l'ordre, valider le critère de chaque tâche avant la suivante,
committer à chaque étape.
