#!/usr/bin/env python3
"""
v3b - Playwright (pré-remplissage sans submit) — robuste sur GitHub Actions
- Ouvre la page concours
- Détecte FORM_VISIBLE vs GATED_LOGIN
- Préremplit les champs (si visibles) SANS submit
- Capture d'écran robuste (timeouts augmentés, animations désactivées, fallback)
- Logs en Europe/Paris
"""

import datetime
import zoneinfo
from pathlib import Path
import sys
import yaml
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

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

def screenshot_robuste(page, shot_path: Path, state_label: str) -> Path:
    """Capture d'écran robuste avec désactivation d'animations et fallback."""
    png_name = f"snap_{ts_paris().strftime('%Y%m%d_%H%M%S')}_{state_label}.png"
    out = SHOT_DIR / png_name

    # Désactiver les animations CSS pour stabiliser le rendu
    try:
        page.add_style_tag(content="""
            *, *::before, *::after {
              animation: none !important;
              transition: none !important;
              caret-color: transparent !important;
            }
        """)
    except Exception:
        pass

    # Attendre réseau au repos + petit délai pour polices
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    try:
        page.wait_for_timeout(1200)
    except Exception:
        pass

    # Tentative full page
    try:
        page.screenshot(path=str(out), full_page=True, timeout=30000, animations="disabled", caret="hide")
        return out
    except PWTimeout:
        # Fallback viewport uniquement
        try:
            page.screenshot(path=str(out), full_page=False, timeout=30000, animations="disabled", caret="hide")
            return out
        except Exception:
            # Dernier fallback : petit délai puis retry
            page.wait_for_timeout(1000)
            page.screenshot(path=str(out), full_page=False, timeout=30000, animations="disabled", caret="hide")
            return out

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
    lastname  = prof.get("profile", {}).get("lastname", "")
    email     = prof.get("profile", {}).get("email", "")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=[
            "--disable-animations",
            "--disable-renderer-backgrounding",
            "--force-color-profile=srgb",
            "--disable-features=PaintHolding"
        ])
        context = browser.new_context(
            locale="fr-FR",
            timezone_id="Europe/Paris",
            device_scale_factor=1.0,
            viewport={"width": 1366, "height": 2000}
        )
        page = context.new_page()
        # timeouts plus généreux
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(30000)

        # Navigation
        try:
            page.goto(url, wait_until="domcontentloaded")
            # attendre un peu plus pour polices/scripts lents
            page.wait_for_load_state("networkidle", timeout=15000)
            page.wait_for_timeout(800)
        except Exception as e:
            log_line("ERROR", contest_name, f"Navigation échouée: {e}")
            browser.close()
            sys.exit(3)

        # Helpers
        def q(css):
            try:
                return page.locator(css).first
            except Exception:
                return None

        def is_visible(loc):
            try:
                return loc is not None and loc.count() > 0 and loc.first.is_visible()
            except Exception:
                return False

        # Détection des champs
        lastname_el  = q(sels.get("lastname"))
        firstname_el = q(sels.get("firstname"))
        email_el     = q(sels.get("email"))
        terms_el     = q(sels.get("terms")) if sels.get("terms") else None
        submit_el    = q(sels.get("submit"))

        form_visible = all([
            is_visible(lastname_el),
            is_visible(firstname_el),
            is_visible(email_el),
            is_visible(submit_el)
        ])

        # Gated ?
        gated = False
        if not form_visible:
            try:
                txt = page.inner_text("body")
            except Exception:
                txt = ""
            gate_markers = ["Inscrivez-vous", "identifiez-vous", "Se connecter", "Connexion", "Votre compte"]
            gated = any(m.lower() in (txt or "").lower() for m in gate_markers)

        state = "FORM_VISIBLE" if form_visible else ("GATED_LOGIN" if gated else "MISSING")
        shot_path = screenshot_robuste(page, SHOT_DIR, state)

        if form_visible:
            # Préremplissage sans submit
            try:
                if is_visible(lastname_el):
                    lastname_el.fill(lastname)
                if is_visible(firstname_el):
                    firstname_el.fill(firstname)
                if is_visible(email_el):
                    email_el.fill(email)
                # Ne pas cocher CGU automatiquement dans le POC
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
