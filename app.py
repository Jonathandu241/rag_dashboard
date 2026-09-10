import os
import time
import secrets
import tempfile
import json
import uuid
import urllib.request
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
import bcrypt
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from google import genai
from google.genai import types

# 1. Chargement de la variable d'environnement depuis le fichier .env
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- Supabase (stockage des PDF sources + table de suivi + comptes admin) ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_BUCKET = "corpus-pdfs"

# --- Authentification (session par cookie signé) ---
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
if not SESSION_SECRET:
    SESSION_SECRET = secrets.token_urlsafe(48)
    print("[!] SESSION_SECRET absent du .env : clé éphémère générée (les sessions "
          "seront invalidées à chaque redémarrage). Ajoutez SESSION_SECRET au .env.")

# Chemins accessibles sans être connecté
PUBLIC_PATHS = ("/login", "/logout", "/static", "/favicon.ico")

# Anti brute-force basique : {ip: [timestamps]} des tentatives échouées
_login_attempts: dict[str, list[float]] = {}
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300

_supabase = None


def get_supabase():
    """Client Supabase (service_role). None si non configuré - la copie des PDF
    et la visualisation sont alors simplement désactivées (dégradation gracieuse)."""
    global _supabase
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
        return None
    if _supabase is None:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase


SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)

app = FastAPI(title="Gorée AR - RAG Studio")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.middleware("http")
async def require_login(request: Request, call_next):
    """Refuse toute requête si la session ne porte pas d'utilisateur :
    redirection vers /login pour les pages, 401 JSON pour /api/*.
    Enregistré AVANT SessionMiddleware pour qu'il s'exécute APRÈS lui
    (Starlette exécute les middlewares dans l'ordre inverse de l'ajout)."""
    path = request.url.path
    if path.startswith(PUBLIC_PATHS) or request.session.get("user_id"):
        return await call_next(request)
    if path.startswith("/api/"):
        return JSONResponse({"detail": "Non authentifié."}, status_code=401)
    return RedirectResponse("/login", status_code=302)


# Ajouté APRÈS require_login → devient le middleware le plus externe → request.session
# est peuplé avant que require_login ne s'exécute.
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="goree_session",
    https_only=SESSION_COOKIE_SECURE,
    same_site="lax",
    max_age=60 * 60 * 8,  # 8 h
)


def get_client():
    """Initialise le client Google GenAI avec la clé d'environnement."""
    if not API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Variable d'environnement GEMINI_API_KEY introuvable dans le fichier .env."
        )
    return genai.Client(api_key=API_KEY)


def construire_prompt_systeme(profil: str = "touriste", langue: str = "fr") -> str:
    """Génère le prompt système strict (BNF4) calqué exactement sur GestionnaireContexte.cs"""

    # 1. Consigne d'adaptation au profil
    if profil == "eleve":
        consigne_profil = (
            "Le visiteur est un élève ou jeune apprenant. Utilise un vocabulaire accessible, pédagogique, "
            "vivant et captivant. Fais des phrases claires et directes sans jargon excessif."
        )
    elif profil == "universitaire":
        consigne_profil = (
            "Le visiteur est un chercheur ou universitaire. Fournis une analyse historique approfondie, "
            "en mettant en lumière les sources documentaires, la nuance historiographique (archives vs tradition mémorielle) "
            "et les dimensions géopolitiques."
        )
    else:  # touriste
        consigne_profil = (
            "Le visiteur est un touriste. Offre un récit équilibré, chaleureux, immersif "
            "qui valorise le patrimoine culturel et la dimension mémorielle de l'île de Gorée."
        )

    # 2. Consignes selon la langue
    if langue == "en":
        return f"""<role>
You are an expert cultural guide for Gorée Island (Senegal) in the Gorée AR mobile app. You are speaking with a {profil}.
</role>

<grounding_constraints_and_strict_refusal>
You are a strictly grounded assistant dedicated exclusively to the heritage, history, and memory of Gorée Island and the transatlantic slave trade.
1. Rely ONLY on the historical documents and facts provided in the knowledge store.
2. STRICT OUT-OF-SCOPE REFUSAL (BNF4 Rule): If the visitor asks a question that is NOT related to Gorée Island, its monuments, its history, its signares, or the slave trade (for example: capitals of other countries, unrelated world geography, weather, science, math, general pop culture), you MUST POLITELY REFUSE to answer. State clearly that your role is exclusively dedicated to guiding visitors through the history and heritage of Gorée Island, and invite them to ask a question about Gorée (e.g. Maison des Esclaves, Historical Museum, etc.).
3. Never invent dates, names, or historical facts.
</grounding_constraints_and_strict_refusal>

<profile_adaptation>
{consigne_profil}
</profile_adaptation>

<response_style>
Keep a warm, respectful, and dignified tone appropriate for a memorial heritage guide.
</response_style>"""

    elif langue == "wo":
        return f"""<role>
Yaw yaay guide culturel bu xarañ ci dëkk Gorée (Senegaal) ci application mobile Gorée AR. Yaa ngi waxtaan ak {profil}.
</role>

<grounding_constraints_and_strict_refusal>
1. Jëfandikool rekk xam-xam ak tegtal yi nekk ci dossier bi ci dëkk Gorée ak jaayum jaam yi.
2. REFUS STRICT (BNF4): Bu la nit ki laajee lu amul benn mbir ak Gorée, dëkk bi, monument yi, walla jaayum jaam yi (ni capitale leneen réew), nanga ko xamal ci kersa ne yaw guide bu Gorée rekk nga, te danga mëna wax rekk ci dëkk Gorée.
3. Bul inventé benn date walla tur.
</grounding_constraints_and_strict_refusal>"""

    else:  # fr
        return f"""<role>
Tu es un guide culturel expert de l'île de Gorée (Sénégal), intégré dans l'application mobile Gorée AR. Tu t'adresses à un {profil}.
</role>

<contraintes_ancrage_et_refus_strict>
Tu es un assistant strictement ancré sur le patrimoine, l'histoire de l'île de Gorée et de la traite négrière.
1. Appuie-toi UNIQUEMENT sur les documents historiques et faits fournis dans le store documentaire.
2. REFUS STRICT HORS PÉRIMÈTRE (Exigence BNF4) : Si la question posée ne concerne PAS l'île de Gorée, ses monuments (Maison des Esclaves, Musée Historique, Fort d'Estrées, Castel...), ses personnages historiques ou la traite négrière (par exemple : la capitale d'un pays étranger, la météo, des calculs mathématiques, des questions de culture générale sans lien avec Gorée), tu DOIS REFUSER POLIMENT de répondre. Rappelle avec courtoisie que ton rôle de guide est exclusivement dédié à la médiation patrimoniale et historique de l'île de Gorée, et invite le visiteur à poser une question sur l'île.
3. N'invente jamais de dates, de noms ou d'événements historiques.
</contraintes_ancrage_et_refus_strict>

<adaptation_profil>
{consigne_profil}
</adaptation_profil>

<style_de_reponse>
Adopte un ton chaleureux, digne, bienveillant et pédagogique, fidèle à la tradition des guides de mémoire de Gorée.
</style_de_reponse>"""


# ─────────────────────────── Authentification ───────────────────────────

def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limited(ip: str) -> bool:
    now = time.time()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < LOGIN_WINDOW_SECONDS]
    _login_attempts[ip] = attempts
    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_failed_attempt(ip: str):
    _login_attempts.setdefault(ip, []).append(time.time())


def _find_admin_by_email(email: str) -> Optional[dict]:
    sb = get_supabase()
    if sb is None:
        return None
    try:
        res = sb.table("admin_users").select("*").ilike("email", email.strip()).limit(1).execute()
        rows = res.data or []
        return rows[0] if rows else None
    except Exception:
        return None


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(
        request=request, name="login.html", context={"error": None, "email": ""}
    )


@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    ip = _client_ip(request)

    if _rate_limited(ip):
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"error": "Trop de tentatives. Réessayez dans quelques minutes.", "email": email},
            status_code=429,
        )

    if not SUPABASE_ENABLED:
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"error": "Authentification indisponible : Supabase non configuré.", "email": email},
            status_code=503,
        )

    admin = _find_admin_by_email(email)
    ok = bool(
        admin
        and admin.get("is_active")
        and admin.get("password_hash")
        and bcrypt.checkpw(password.encode("utf-8"), admin["password_hash"].encode("utf-8"))
    )
    if not ok:
        _record_failed_attempt(ip)
        return templates.TemplateResponse(
            request=request, name="login.html",
            context={"error": "Identifiants invalides.", "email": email},
            status_code=401,
        )

    request.session["user_id"] = admin["id"]
    request.session["user_email"] = admin["email"]
    request.session["user_name"] = admin.get("full_name") or admin["email"]
    _login_attempts.pop(ip, None)

    sb = get_supabase()
    if sb is not None:
        try:
            sb.table("admin_users").update(
                {"last_login_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", admin["id"]).execute()
        except Exception:
            pass

    return RedirectResponse("/", status_code=302)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


# ─────────────────────────── Pages & API ───────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    has_key = bool(API_KEY)
    masked_key = f"{API_KEY[:6]}...{API_KEY[-4:]}" if has_key and len(API_KEY) > 10 else "Non définie"

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "has_api_key": has_key,
            "api_key_masked": masked_key,
            "current_user_name": request.session.get("user_name", ""),
            "current_user_email": request.session.get("user_email", ""),
        }
    )


def _local_docs_index():
    """Renvoie un dict {google_document_name: row} depuis la table Supabase.
    Dict vide si Supabase n'est pas configuré ou en cas d'erreur."""
    sb = get_supabase()
    if sb is None:
        return {}
    try:
        res = sb.table("corpus_documents").select(
            "google_document_name, file_name, size_bytes, mime_type, created_at, storage_path"
        ).execute()
        return {r["google_document_name"]: r for r in (res.data or [])}
    except Exception:
        return {}


@app.get("/api/stores")
async def list_stores():
    """Récupère la liste complète des stores et des documents indexés.
    Enrichit chaque document avec les infos de la copie locale (Supabase) si disponible."""
    client = get_client()
    local = _local_docs_index()
    try:
        stores_raw = client.file_search_stores.list()
        stores_data = []
        total_docs = 0

        for s in stores_raw:
            docs_raw = client.file_search_stores.documents.list(parent=s.name)
            docs_list = []
            for d in docs_raw:
                meta = local.get(d.name, {})
                docs_list.append({
                    "name": d.name,
                    "display_name": d.display_name,
                    "state": str(d.state).replace("FileSearchDocumentState.", ""),
                    "size_bytes": meta.get("size_bytes"),
                    "created_at": meta.get("created_at"),
                    "has_local_file": bool(meta),
                })

            total_docs += len(docs_list)
            stores_data.append({
                "name": s.name,
                "display_name": s.display_name,
                "docs_count": len(docs_list),
                "docs": docs_list
            })

        return {
            "stores": stores_data,
            "stats": {
                "total_stores": len(stores_data),
                "total_docs": total_docs,
                "storage_enabled": SUPABASE_ENABLED,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stores/create")
async def create_store(display_name: str = Form(...)):
    """Crée un nouveau File Search Store."""
    client = get_client()
    try:
        store = client.file_search_stores.create(
            config=types.CreateFileSearchStoreConfig(display_name=display_name.strip())
        )
        return {"status": "ok", "store": {"name": store.name, "display_name": store.display_name}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stores/delete")
async def delete_store(store_name: str = Form(...)):
    """Supprime un store, tous ses documents, et les copies locales associées."""
    client = get_client()
    try:
        client.file_search_stores.delete(name=store_name, config={"force": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Nettoyage des copies locales (best effort)
    sb = get_supabase()
    if sb is not None:
        try:
            res = sb.table("corpus_documents").select("storage_path").eq("google_store_name", store_name).execute()
            paths = [r["storage_path"] for r in (res.data or [])]
            if paths:
                sb.storage.from_(SUPABASE_BUCKET).remove(paths)
            sb.table("corpus_documents").delete().eq("google_store_name", store_name).execute()
        except Exception:
            pass

    return {"status": "ok"}


@app.post("/api/documents/upload")
async def upload_document(store_name: str = Form(...), file: UploadFile = File(...)):
    """Upload un PDF : envoi à Google (chunking/embedding/indexation) + copie dans Supabase Storage."""
    client = get_client()
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")

    tmp_path = None
    try:
        content = await file.read()
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Envoi et indexation dans le File Search Store avec le nom de fichier d'origine
        operation = client.file_search_stores.upload_to_file_search_store(
            file_search_store_name=store_name,
            file=tmp_path,
            config={"display_name": file.filename}
        )

        # Attente synchrone que l'indexation soit terminée côté Google
        while not operation.done:
            time.sleep(1.5)
            operation = client.operations.get(operation)

        # Récupère le nom du document Google fraîchement créé (pour le lier à la copie locale)
        google_document_name = _find_document_name(client, store_name, file.filename)

        # display_name du store, pour dénormalisation dans la table de suivi
        store_display = None
        try:
            store_display = next(
                (s.display_name for s in client.file_search_stores.list() if s.name == store_name),
                None,
            )
        except Exception:
            pass

        # Copie du PDF source dans Supabase Storage + ligne de suivi (best effort)
        _store_local_copy(store_name, google_document_name, file.filename, content, store_display)

        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        return {"status": "ok", "filename": file.filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def _find_document_name(client, store_name: str, display_name: str) -> Optional[str]:
    """Retrouve le resource name du document qui vient d'être indexé, par display_name."""
    try:
        docs = client.file_search_stores.documents.list(parent=store_name)
        match = [d for d in docs if d.display_name == display_name]
        if match:
            # le plus récent en dernier dans la liste Google
            return match[-1].name
    except Exception:
        pass
    return None


def _store_local_copy(store_name: str, google_document_name: Optional[str], file_name: str,
                      content: bytes, store_display: Optional[str] = None):
    """Pousse le PDF dans le bucket et insère la ligne de suivi. Silencieux si Supabase absent."""
    sb = get_supabase()
    if sb is None or not google_document_name:
        return
    store_ref = store_name.split("/")[-1]
    storage_path = f"{store_ref}/{uuid.uuid4().hex}.pdf"
    try:
        sb.storage.from_(SUPABASE_BUCKET).upload(
            storage_path, content, {"content-type": "application/pdf", "upsert": "false"}
        )
        sb.table("corpus_documents").insert({
            "google_document_name": google_document_name,
            "google_store_name": store_name,
            "store_display_name": store_display,
            "file_name": file_name,
            "storage_path": storage_path,
            "size_bytes": len(content),
            "mime_type": "application/pdf",
            "state": "active",
        }).execute()
    except Exception:
        # rollback best effort de l'objet uploadé si l'insert a échoué
        try:
            sb.storage.from_(SUPABASE_BUCKET).remove([storage_path])
        except Exception:
            pass


@app.post("/api/documents/delete")
async def delete_document(document_name: str = Form(...)):
    """Supprime un document d'un store (Google) et sa copie locale (Supabase)."""
    client = get_client()
    try:
        # force=True : nécessaire pour supprimer un document déjà indexé (avec des chunks)
        client.file_search_stores.documents.delete(name=document_name, config={"force": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    sb = get_supabase()
    if sb is not None:
        try:
            res = sb.table("corpus_documents").select("storage_path").eq("google_document_name", document_name).execute()
            paths = [r["storage_path"] for r in (res.data or [])]
            if paths:
                sb.storage.from_(SUPABASE_BUCKET).remove(paths)
            sb.table("corpus_documents").delete().eq("google_document_name", document_name).execute()
        except Exception:
            pass

    return {"status": "ok"}


@app.get("/api/documents/file")
async def get_document_file(document_name: str):
    """Redirige vers une URL signée (1 h) du PDF source stocké dans Supabase Storage."""
    sb = get_supabase()
    if sb is None:
        raise HTTPException(status_code=404, detail="Stockage des fichiers non configuré.")
    try:
        res = sb.table("corpus_documents").select("storage_path, file_name").eq(
            "google_document_name", document_name
        ).limit(1).execute()
        rows = res.data or []
        if not rows:
            raise HTTPException(status_code=404, detail="Aucune copie locale pour ce document (indexé avant l'activation du stockage).")
        storage_path = rows[0]["storage_path"]
        signed = sb.storage.from_(SUPABASE_BUCKET).create_signed_url(storage_path, 3600)
        url = signed.get("signedURL") or signed.get("signedUrl")
        if not url:
            raise HTTPException(status_code=500, detail="Impossible de générer l'URL signée.")
        if url.startswith("/"):
            url = f"{SUPABASE_URL}/storage/v1{url}"
        return RedirectResponse(url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/playground/test")
def test_query(
    store_name: str = Form(...),
    question: str = Form(...),
    profil: str = Form("touriste"),
    langue: str = Form("fr")
):
    """Teste une requête en direct avec le File Search Tool et le prompt système strict BNF4."""
    if not API_KEY:
        raise HTTPException(status_code=400, detail="Clé API manquante.")

    prompt_systeme = construire_prompt_systeme(profil=profil, langue=langue)
    modeles = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.7-flash"]
    derniere_erreur = None

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": question}]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": prompt_systeme}
            ]
        },
        "tools": [
            {
                "file_search": {
                    "file_search_store_names": [store_name]
                }
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 600
        }
    }

    data_json = json.dumps(payload).encode("utf-8")

    for model in modeles:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        req = urllib.request.Request(
            url,
            data=data_json,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return {
                            "status": "ok",
                            "answer": parts[0]["text"],
                            "model": model,
                            "profil": profil,
                            "langue": langue
                        }
        except Exception as e:
            derniere_erreur = str(e)
            continue

    raise HTTPException(status_code=500, detail=f"Erreur lors de l'appel Gemini : {derniere_erreur}")


if __name__ == "__main__":
    import uvicorn
    if not API_KEY:
        print("[!] ATTENTION : GEMINI_API_KEY non trouvee dans le fichier .env.")
    else:
        print(f"[ok] Cle API chargee depuis .env ({API_KEY[:6]}...{API_KEY[-4:]})")
    print(f"[ok] Supabase Storage : {'active' if SUPABASE_ENABLED else 'non configure'}")
    print("[*] Lancement du Back-Office Goree AR sur http://localhost:8000")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
