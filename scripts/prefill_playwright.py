#!/usr/bin/env python3
"""
v3 - Playwright (pré-remplissage sans submit)
- Ouvre la page du concours (config/selectors_*.yaml)
- Détecte si le formulaire est visible (FORM_VISIBLE) ou si la page est gated (GATED_LOGIN)
- Si FORM_VISIBLE : préremplit les champs (nom, prénom, email) à partir de data/profile.yaml
- Ne clique PAS sur "submit" (dry-run)
- Prend une capture d'écran et génère un log en Europe/Paris
"""

import datetime
import zoneinfo
from pathlib import Path
import sys
import yaml

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "profile.yaml"
SELECTORS_PATH = ROOT / "config" / "selectors_gulli_jurassic.yaml"  # adapte si tu testes corolle
LOG_FILE = ROOT / "data" / "logs" / "grattweb_jouets.log"
SHOT_DIR = ROOT / "data" / "screenshots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)

def ts_paris():
    tz = zoneinfo.ZoneInfo("Europe/Paris")
    return datetime.datetime.now(tz)

def log_line(status: str, contest: str, message: str):
    ts = ts_paris().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{status}] [{contest}] {message}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.open("a", encoding="utf-8").write(line + "\n")
    print(line)

def load_yaml(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    prof = load_yaml(PROFILE_PATH)
    cfg = load_yaml(SELECTORS_PATH)

    meta = cfg.get("meta", {})
    contest_name = f"{meta.get('site','grattweb.fr')} / {meta.get('type','instant_gagnant')}"
    url = cfg.get("form", {}).get("url")
    sels = cfg.get("selectors", {})

    if not url:
        log_line("ERROR", contest_name, "Aucune URL dans form.url")
        sys.exit(2)

    firstname = prof.get("profile", {}).get("firstname", "")
    lastname = prof.get("profile", {}).get("lastname", "")
    email = prof.get("profile", {}).get("email", "")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(locale="fr-FR", timezone_id="Europe/Paris")
        page = context.new_page()

        # navigation
        page.set_default_timeout(15000)
        try:
            page.goto(url, wait_until="domcontentloaded")
        except Exception as e:
            log_line("ERROR", contest_name, f"Navigation échouée: {e}")
            browser.close()
            sys.exit(3)

        # Détection formulaire
        def q(css):
            try:
                return page.locator(css).first
            except Exception:
                return None

        lastname_el   = q(sels.get("lastname"))
        firstname_el  = q(sels.get("firstname"))
        email_el      = q(sels.get("email"))
        terms_el      = q(sels.get("terms")) if sels.get("terms") else None
        submit_el     = q(sels.get("submit"))

        def is_visible(loc):
            try:
                return loc is not None and loc.count() > 0 and loc.first.is_visible()
            except Exception:
                return False

        form_visible = all([
            is_visible(lastname_el),
            is_visible(firstname_el),
            is_visible(email_el),
            is_visible(submit_el)
        ])

        # Si pas visible, on regarde si gated/login requis
        gated = False
        if not form_visible:
            txt = page.inner_text("body") if page.locator("body").count() else ""
            gate_markers = ["Inscrivez-vous", "identifiez-vous", "Se connecter", "Connexion", "Votre compte"]
            gated = any(m.lower() in txt.lower() for m in gate_markers)

        # Screenshots + logs
        state = "FORM_VISIBLE" if form_visible else ("GATED_LOGIN" if gated else "MISSING")
        png_name = f"snap_{ts_paris().strftime('%Y%m%d_%H%M%S')}_{state}.png"
        shot_path = SHOT_DIR / png_name
        try:
            page.screenshot(path=str(shot_path), full_page=True)
        except Exception:
            # fallback au viewport
            page.screenshot(path=str(shot_path))

        if form_visible:
            # Préremplissage sans submit
            try:
                if is_visible(lastname_el):
                    lastname_el.fill(lastname)
                if is_visible(firstname_el):
                    firstname_el.fill(firstname)
                if is_visible(email_el):
                    email_el.fill(email)
                # On coche CGU uniquement si visible et que c'est vraiment requis.
                if terms_el and is_visible(terms_el):
                    # On NE coche PAS automatiquement pour le POC si on ne sait pas si c'est requis.
                    pass
                log_line("INFO", contest_name, f"Préremplissage OK (sans submit) — screenshot: {shot_path}")
            except Exception as e:
                log_line("ERROR", contest_name, f"Erreur préremplissage: {e}")
                browser.close()
                sys.exit(4)

        elif gated:
            log_line("INFO", contest_name, f"GATED_LOGIN détecté — formulaire non visible — screenshot: {shot_path}")
        else:
            log_line("ERROR", contest_name, f"Formulaire introuvable (MISSING) — screenshot: {shot_path}")
            browser.close()
            sys.exit(5)

        browser.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
