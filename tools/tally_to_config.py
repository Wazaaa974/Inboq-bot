"""
tally_to_config.py — Inboq Onboarding Automation
=================================================
Lit la dernière soumission Tally (via export CSV Google Sheets)
et génère automatiquement :
  - clients/{client_id}_config.json
  - clients/{client_id}_system_prompt.txt

Usage :
    python tally_to_config.py responses.csv

Le CSV s'obtient depuis Google Sheets :
    Fichier → Télécharger → Valeurs séparées par des virgules (.csv)
"""

import csv
import json
import re
import sys
import os
from datetime import datetime


# ─────────────────────────────────────────────
# Mapping colonnes Tally → champs config
# Adapter les clés si les intitulés du formulaire changent
# ─────────────────────────────────────────────
COLUMN_MAP = {
    "nom_professionnel":   "Votre nom ou pseudo professionnel",
    "display_name":        "Nom d'affichage souhaité pour le bot",
    "email":               "Votre adresse email",
    "langue":              "Langue principale du bot",
    "services":            "Services proposés (nom, durée, prix)",
    "tarifs":              "Tarifs, moyens de paiement et politique d'annulation",
    "disponibilites":      "Jours et horaires de travail",
    "localisation":        "Ville, adresse et déplacements à domicile ?",
    "regles":              "Règles spécifiques (ce que vous acceptez et refusez)",
    "bienvenue":           "Message de bienvenue souhaité + ton du bot",
    "faq":                 "FAQ — listez 3 à 5 questions fréquentes avec leurs réponses",
    "liens":               "Liens Instagram, site web, téléphone (optionnel)",
}

LANG_CODES = {
    "Français": "fr",
    "English": "en",
    "Español": "es",
    "Nederlands": "nl",
    "Autre": "fr",
}


def slugify(text):
    """Transforme 'Marie Dupont' en 'marie_dupont'."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    return text


def read_last_submission(csv_path):
    """Lit la dernière ligne du CSV (= soumission la plus récente)."""
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("❌ Le fichier CSV est vide.")
        sys.exit(1)

    # On prend la dernière ligne = soumission la plus récente
    last = rows[-1]
    print(f"✅ {len(rows)} soumission(s) trouvée(s). Traitement de la dernière.")
    return last


def find_column(row, label):
    """Recherche une colonne par son label exact ou approché."""
    # Correspondance exacte d'abord
    if label in row:
        return row[label].strip()

    # Correspondance partielle (utile si Tally tronque les headers)
    for key in row.keys():
        if label[:30].lower() in key.lower():
            return row[key].strip()

    return ""


def build_config(row):
    """Construit le dictionnaire de config à partir d'une ligne Tally."""

    # Récupération des champs
    nom            = find_column(row, COLUMN_MAP["nom_professionnel"])
    display_name   = find_column(row, COLUMN_MAP["display_name"]) or f"Assistant de {nom}"
    email          = find_column(row, COLUMN_MAP["email"])
    langue_label   = find_column(row, COLUMN_MAP["langue"])
    services_raw   = find_column(row, COLUMN_MAP["services"])
    tarifs_raw     = find_column(row, COLUMN_MAP["tarifs"])
    dispo_raw      = find_column(row, COLUMN_MAP["disponibilites"])
    localisation   = find_column(row, COLUMN_MAP["localisation"])
    regles_raw     = find_column(row, COLUMN_MAP["regles"])
    bienvenue_raw  = find_column(row, COLUMN_MAP["bienvenue"])
    faq_raw        = find_column(row, COLUMN_MAP["faq"])
    liens_raw      = find_column(row, COLUMN_MAP["liens"])

    client_id = slugify(nom) if nom else f"client_{datetime.now().strftime('%Y%m%d%H%M')}"
    lang_code = LANG_CODES.get(langue_label, "fr")

    # Parsing services (format attendu : "Service — prix — durée" ou libre)
    services = []
    for line in services_raw.split("\n"):
        line = line.strip().lstrip("-•*").strip()
        if line:
            services.append({"description": line})

    # Parsing FAQ (format attendu : "Q: ... R: ...")
    faq = []
    faq_blocks = re.split(r'\n(?=Q\s*:|Question\s*:)', faq_raw, flags=re.IGNORECASE)
    for block in faq_blocks:
        block = block.strip()
        if not block:
            continue
        q_match = re.search(r'Q\s*[:\-]\s*(.+?)(?:\n|R\s*[:\-])', block, re.IGNORECASE | re.DOTALL)
        r_match = re.search(r'R\s*[:\-]\s*(.+)', block, re.IGNORECASE | re.DOTALL)
        if q_match and r_match:
            faq.append({
                "question": q_match.group(1).strip(),
                "answer": r_match.group(1).strip()
            })
        elif block:
            faq.append({"question": block, "answer": ""})

    # Message de bienvenue et ton
    welcome_msg = bienvenue_raw
    tone = "chaleureux et professionnel"
    if "\n" in bienvenue_raw:
        parts = bienvenue_raw.split("\n", 1)
        welcome_msg = parts[0].strip()
        tone = parts[1].strip() if len(parts) > 1 else tone

    config = {
        "client_id": client_id,
        "client_name": nom,
        "display_name": display_name,
        "email": email,
        "languages": {
            "primary": lang_code,
            "additional": []
        },
        "services_raw": services_raw,
        "services": services,
        "pricing_raw": tarifs_raw,
        "availability_raw": dispo_raw,
        "location_raw": localisation,
        "rules_raw": regles_raw,
        "welcome_message": welcome_msg or f"Bonjour ! Je suis l'assistant(e) de {nom}. Comment puis-je vous aider ?",
        "tone": tone,
        "faq": faq,
        "faq_raw": faq_raw,
        "links_raw": liens_raw,
        "plan": "starter",
        "max_monthly_responses": 500,
        "admin": {
            "telegram_chat_id": "A_RENSEIGNER_APRES_PREMIER_START",
            "notification_email": email
        },
        "generated_at": datetime.now().isoformat()
    }

    return config


def generate_system_prompt(config):
    """Génère le system prompt OpenAI à partir de la config."""

    nom          = config["client_name"]
    display      = config["display_name"]
    lang         = config["languages"]["primary"]
    services_raw = config["services_raw"]
    tarifs_raw   = config["pricing_raw"]
    dispo_raw    = config["availability_raw"]
    location     = config["location_raw"]
    regles_raw   = config["rules_raw"]
    welcome      = config["welcome_message"]
    tone         = config["tone"]
    faq_raw      = config["faq_raw"]
    liens_raw    = config["links_raw"]

    lang_instruction = {
        "fr": "Réponds toujours en français.",
        "en": "Always respond in English.",
        "es": "Responde siempre en español.",
        "nl": "Antwoord altijd in het Nederlands.",
    }.get(lang, "Réponds toujours en français.")

    prompt = f"""Tu es l'assistant(e) virtuel(le) de {nom}. Tu réponds aux clients potentiels sur Telegram en leur nom.

PROFIL :
- Nom d'affichage : {display}
- Langue : {lang_instruction}
{f"- Coordonnées / liens : {liens_raw}" if liens_raw else ""}

LOCALISATION ET DÉPLACEMENTS :
{location}

SERVICES ET TARIFS :
{services_raw}

INFORMATIONS TARIFAIRES ET PAIEMENT :
{tarifs_raw}

DISPONIBILITÉS :
{dispo_raw}

RÈGLES SPÉCIFIQUES :
{regles_raw}

FAQ :
{faq_raw}

MESSAGE DE BIENVENUE :
Quand un client envoie /start ou te contacte pour la première fois, réponds avec ce message :
"{welcome}"

INSTRUCTIONS DE COMPORTEMENT :
- Ton : {tone}
- Vouvoie toujours le client
- Réponds de façon courte et claire (3-5 lignes max)
- Si une information n'est pas dans ce profil, ne l'invente pas : propose de contacter {nom} directement
- Quand un prospect semble intéressé et a précisé une prestation + une date, envoie une notification à l'admin
- Si le client est irrespectueux, clôture poliment la conversation

FORMAT DE RÉPONSE :
- Messages courts et directs
- Pas de listes à puces sauf pour présenter les services
- Terminer en proposant de réserver ou en posant une question de qualification
"""
    return prompt.strip()


def save_outputs(config, prompt, output_dir="clients"):
    """Sauvegarde le JSON et le prompt dans le dossier clients/."""
    os.makedirs(output_dir, exist_ok=True)

    client_id = config["client_id"]

    # Sauvegarde JSON
    json_path = os.path.join(output_dir, f"{client_id}_config.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # Sauvegarde prompt
    prompt_path = os.path.join(output_dir, f"{client_id}_system_prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    return json_path, prompt_path


def main():
    if len(sys.argv) < 2:
        print("Usage : python tally_to_config.py responses.csv")
        print("Le CSV s'exporte depuis Google Sheets → Fichier → Télécharger → CSV")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not os.path.exists(csv_path):
        print(f"❌ Fichier introuvable : {csv_path}")
        sys.exit(1)

    print(f"\n📋 Lecture du fichier : {csv_path}")
    row = read_last_submission(csv_path)

    print("⚙️  Génération de la configuration...")
    config = build_config(row)

    print("🧠 Génération du system prompt...")
    prompt = generate_system_prompt(config)

    print("💾 Sauvegarde des fichiers...")
    json_path, prompt_path = save_outputs(config, prompt)

    print(f"""
✅ Terminé ! Fichiers générés :
   → {json_path}
   → {prompt_path}

📌 Prochaines étapes Railway :
   TELEGRAM_BOT_TOKEN   = [token reçu du client]
   OPENAI_API_KEY       = [ta clé OpenAI]
   ADMIN_CHAT_ID        = [à récupérer après le 1er /start]
   PROFESSIONAL_PROFILE = [contenu de {prompt_path}]
   WELCOME_MESSAGE      = {config['welcome_message'][:60]}...
""")


if __name__ == "__main__":
    main()
