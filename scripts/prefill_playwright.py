#!/usr/bin/env python3
"""
v3c - Playwright (pré-remplissage sans submit) — navigation robuste (retries)
- Ouvre la page concours avec UA desktop + headers
- Retries de navigation (3 tentatives, backoff)
- Détecte FORM_VISIBLE ou GATED_LOGIN
- Préremplissage sans submit si form visible
- Capture d'écran même en cas de lenteur
- Logs en Europe/Paris
"""

import datetime, time
import zoneinfo
from pathlib import Path
import sys, yaml
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "profile.yaml"
SELECTORS_PATH = ROOT / "config" / "selectors_gulli_jurassic.yaml"  # adapte si besoin
LOG_FILE = ROOT / "data" / "logs" / "grattweb_jouets.log"
SHOT_DIR = ROOT / "data" / "screenshots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)

UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def ts_paris():
    tz = zoneinfo.ZoneInfo("Europe/Paris")
    return datetime.datetime.now(tz)

def log_line(status: str, contest: str, message: str):
    ts = ts_paris().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{status}] [{contest}] {message}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)

def load_yaml(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def screenshot_robuste(page, state_label: str) -> Path:
    png = SHOT_DIR / f"snap_{ts_paris().strftime('%Y%m%d_%H%M%S')}_{state_label}.png"
    try:
        # désactiver animations
        try:
            page.add_style_tag(content="""
                *,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important;}
            """)
        except Exception:
            pass
        # attendre un peu
        try: page.wait_for_load_state("networkidle", timeout=20000)
        except Exception: pass
        try: page.wait_for_timeout(800)
        except Exception: pass

        page.screenshot(path=str(png), full_page=True, timeout=40000, animations="disabled", caret="hide")
    except Exception:
        try:
            page.screenshot(path=str(png), full_page=False, timeout=40000, animations="disabled", caret="hide")
        except Exception:
            # dernier recours : pas de screenshot
            pass
    return png

def navigate_with_retries(page, url: str, contest_name: str, max_attempts=3):
    # on utilise wait_until="load" (plus permissif) + attentes supplémentaires
    delays = [0, 2, 5]  # secondes
    last_err = None
    for attempt, delay in enumerate(delays[:max_attempts], start=1):
        if delay: time.sleep(delay)
        try:
            page.goto(url, wait_until="load", timeout=45000)
            # laisser le temps aux ressources lentes
            try: page.wait_for_load_state("networkidle", timeout=20000)
            except Exception: pass
            try: page.wait_for_timeout(800)
            except Exception: pass
            return True
        except Exception as e:
            last_err = e
            log_line("WARN", contest_name, f"Navigation tentative {attempt}/{max_attempts} échouée: {e}")
    if last_err:
        log_line("ERROR", contest_name, f"Navigation échouée après {max_attempts} tentatives: {last_err}")
    return False

def main():
    prof = load_yaml(PROFILE_PATH)
    cfg  = load_yaml(SELECTORS_PATH)

    meta = cfg.get("meta", {})
    contest_name = f"{meta.get('site','grattweb.fr')} / {meta.get('type','instant_gagnant')}"
    url  = cfg.get("form", {}).get("url")
    sels = cfg.get("selectors", {})

    if not url:
        log_line("ERROR", contest_name, "Aucune URL dans form.url")
        sys.exit(2)

    firstname = prof.get("profile", {}).get("firstname", "")
    lastname  = prof.get("profile", {}).get("lastname", "")
    email     = prof.get("profile", {}).get("email", "")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-animations",
                "--disable-renderer-backgrounding",
                "--force-color-profile=srgb",
                "--disable-features=PaintHolding"
            ],
        )
        context = browser.new_context(
            locale="fr-FR",
            timezone_id="Europe/Paris",
            device_scale_factor=1.0,
            viewport={"width": 1366, "height": 2200},
            ignore_https_errors=True,
            user_agent=UA_DESKTOP,
            extra_http_headers={
                "Accept-Language": "fr-FR,fr;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        page = context.new_page()
        page.set_default_timeout(40000)
        page.set_default_navigation_timeout(45000)

        ok = navigate_with_retries(page, url, contest_name, max_attempts=3)
        # on prend toujours une capture, même si la nav est capricieuse
        shot_path = screenshot_robuste(page, "AFTER_NAV")

        if not ok:
            log_line("ERROR", contest_name, f"Impossible de charger correctement la page — screenshot: {shot_path}")
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

        # Détection
        lastname_el  = q(sels.get("lastname"))
        firstname_el = q(sels.get("firstname"))
        email_el     = q(sels.get("email"))
        terms_el     = q(sels.get("terms")) if sels.get("terms") else None
        submit_el    = q(sels.get("submit"))

        form_visible = all([is_visible(lastname_el), is_visible(firstname_el), is_visible(email_el), is_visible(submit_el)])

        gated = False
        if not form_visible:
            try: body_txt = page.inner_text("body")
            except Exception: body_txt = ""
            gate_markers = ["Inscrivez-vous", "identifiez-vous", "Se connecter", "Connexion", "Votre compte"]
            gated = any(m.lower() in (body_txt or "").lower() for m in gate_markers)

        state = "FORM_VISIBLE" if form_visible else ("GATED_LOGIN" if gated else "MISSING")
        shot2 = screenshot_robuste(page, state)

        if form_visible:
            try:
                if is_visible(lastname_el):  lastname_el.fill(lastname)
                if is_visible(firstname_el): firstname_el.fill(firstname)
                if is_visible(email_el):     email_el.fill(email)
                log_line("INFO", contest_name, f"Préremplissage OK (sans submit) — screenshots: {shot_path.name}, {shot2.name}")
            except Exception as e:
                log_line("ERROR", contest_name, f"Erreur préremplissage: {e} — screenshots: {shot_path.name}, {shot2.name}")
                browser.close()
                sys.exit(4)
        elif gated:
            log_line("INFO", contest_name, f"GATED_LOGIN détecté — formulaire non visible — screenshots: {shot_path.name}, {shot2.name}")
        else:
            log_line("ERROR", contest_name, f"Formulaire introuvable (MISSING) — screenshots: {shot_path.name}, {shot2.name}")
            browser.close()
            sys.exit(5)

        browser.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
