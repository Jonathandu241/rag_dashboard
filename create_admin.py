"""Crée (ou met à jour) un compte administrateur du back-office RAG Studio.

Usage :
    python create_admin.py <email> "<Nom complet>"

Le mot de passe est demandé de façon masquée. Le hash bcrypt est stocké dans
la table Supabase `admin_users` (jamais le mot de passe en clair).
"""
import os
import sys
import getpass
from dotenv import load_dotenv
import bcrypt

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def main():
    if len(sys.argv) < 2:
        print("Usage : python create_admin.py <email> \"<Nom complet>\"")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    full_name = sys.argv[2].strip() if len(sys.argv) > 2 else email

    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
        print("[erreur] SUPABASE_URL / SUPABASE_SERVICE_KEY absents du .env.")
        sys.exit(1)

    pw1 = getpass.getpass("Mot de passe          : ")
    pw2 = getpass.getpass("Confirmer le mot de passe : ")
    if pw1 != pw2:
        print("[erreur] Les mots de passe ne correspondent pas.")
        sys.exit(1)
    if len(pw1) < 8:
        print("[erreur] Le mot de passe doit faire au moins 8 caractères.")
        sys.exit(1)

    pw_hash = bcrypt.hashpw(pw1.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    existing = sb.table("admin_users").select("id").ilike("email", email).limit(1).execute()
    if existing.data:
        sb.table("admin_users").update({
            "password_hash": pw_hash,
            "full_name": full_name,
            "is_active": True,
        }).eq("id", existing.data[0]["id"]).execute()
        print(f"[ok] Compte mis à jour : {email}")
    else:
        sb.table("admin_users").insert({
            "email": email,
            "password_hash": pw_hash,
            "full_name": full_name,
            "is_active": True,
        }).execute()
        print(f"[ok] Compte créé : {email}")


if __name__ == "__main__":
    main()
