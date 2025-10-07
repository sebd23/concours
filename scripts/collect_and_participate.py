#!/usr/bin/env python3
"""
POC v1 - Collect & (simulated) Participate

But : simulation safe qui lit le profil + config et produit logs / CSV / rapport HTML.
Ne fait aucune requête réseau. Utile pour valider la chaîne "config -> action -> sortie".

Usage :
  python scripts/collect_and_participate.py --simulate
"""

import os
import sys
import yaml
import csv
import datetime
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Paths (conformes à la structure du repo)
PROFILE_PATH = ROOT / "data" / "profile.yaml"
SITE_CFG_PATH = ROOT / "config" / "sites" / "grattweb_jouets.yaml"
SELECTORS_PATH = ROOT / "config" / "selectors_gulli_jurassic.yaml"
LOG_DIR = ROOT / "data" / "logs"
EXPORT_DIR = ROOT / "data" / "exports"
REPORT_DIR = ROOT / "data" / "reports"

LOG_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "grattweb_jouets.log"

def load_yaml(p: Path):
    if not p.exists():
        raise FileNotFoundError(f"Fichier introuvable : {p}")
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def log_line(status: str, contest: str, message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{status}] [{contest}] {message}"
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)

def simulate_participation(profile: dict, site_cfg: dict, selectors: dict):
    """
    Simulation :
     - construit un enregistrement participation
     - évalue si 'terms' required and profile.accept_terms
     - retourne dict (titre, status, message, ts)
    """
    contest_title = selectors.get("meta", {}).get("site", "GULLI Jurassic")
    ts = datetime.datetime.now().isoformat()
    # check basic prerequisites
    accept_terms = profile.get("profile", {}).get("preferences", {}).get("accept_terms", True)
    if selectors.get("selectors", {}).get("terms") and not accept_terms:
        return {
            "contest": contest_title,
            "status": "ÉCHEC",
            "message": "CGU non acceptées dans le profil",
            "ts": ts
        }
    # Simulate success probabilistically (here toujours success for POC)
    return {
        "contest": contest_title,
        "status": "OK",
        "message": "Participation simulée - succès (dry-run)",
        "ts": ts
    }

def write_csv_row(row: dict):
    today = datetime.date.today().isoformat()
    out = EXPORT_DIR / f"concours_{today}.csv"
    file_exists = out.exists()
    header = ["date", "site", "contest", "status", "message", "profile_email"]
    with open(out, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if not file_exists:
            writer.writerow(header)
        writer.writerow([row["ts"], "grattweb.fr", row["contest"], row["status"], row["message"], row.get("profile_email","")])
    return out

def write_html_report(rows):
    today = datetime.date.today().isoformat()
    out = REPORT_DIR / f"grattweb_jouets_{today}.html"
    html = """<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Rapport Grattweb Jouets - {date}</title></head>
<body>
<h1>Rapport Grattweb Jouets - {date}</h1>
<table border="1" cellpadding="6" cellspacing="0">
<thead><tr><th>Heure</th><th>Concours</th><th>Statut</th><th>Message</th><th>Profil</th></tr></thead>
<tbody>
""".format(date=today)
    for r in rows:
        html += "<tr><td>{ts}</td><td>{contest}</td><td>{status}</td><td>{message}</td><td>{email}</td></tr>\n".format(
            ts=r["ts"], contest=r["contest"], status=r["status"], message=r["message"], email=r.get("profile_email",""))
    html += "</tbody></table>\n</body></html>"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out

def main(simulate=True):
    # Charge fichiers de config
    try:
        profile = load_yaml(PROFILE_PATH)
    except Exception as e:
        print("Erreur lecture profile :", e)
        sys.exit(1)
    try:
        site_cfg = load_yaml(SITE_CFG_PATH)
    except Exception as e:
        print("Erreur lecture config site :", e)
        sys.exit(1)
    try:
        selectors = load_yaml(SELECTORS_PATH)
    except Exception as e:
        print("Erreur lecture selectors :", e)
        sys.exit(1)

    # Log start
    contest_label = selectors.get("meta", {}).get("type", "instant_gagnant")
    log_line("INFO", "POC", f"Début du run (simulate={simulate}) - cible: {contest_label}")

    results = []
    # Pour le POC on simule une unique participation
    res = simulate_participation(profile, site_cfg, selectors)
    res["profile_email"] = profile.get("profile", {}).get("email", "")
    results.append(res)

    # Logging & outputs
    for r in results:
        if r["status"] == "OK":
            log_line("SUCCESS", r["contest"], r["message"])
        else:
            log_line("ERROR", r["contest"], r["message"])

    csv_path = write_csv_row(results[0])
    html_path = write_html_report(results)
    log_line("INFO", "POC", f"CSV écrit : {csv_path}")
    log_line("INFO", "POC", f"Rapport écrit : {html_path}")
    log_line("END", "POC", "Run terminé")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="POC collecte & participation (simulation)")
    parser.add_argument("--simulate", action="store_true", help="Effectuer un dry-run (par défaut)")
    parser.add_argument("--live", action="store_true", help="(non implémenté) Activer le mode live (réel) - NON DISPONIBLE")
    args = parser.parse_args()
    main(simulate=not args.live)
