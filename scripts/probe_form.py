#!/usr/bin/env python3
"""
v2b - Probe formulaire (lecture seule, "gated-aware")
- GET la page concours (form.url)
- Si formulaire présent => OK (FORM_VISIBLE)
- Si pas de formulaire mais texte "Inscrivez-vous" / "identifiez-vous" ou un form de login => OK (GATED_LOGIN)
- Sinon => KO (MISSING)
- N'envoie aucune donnée.
"""

import sys, datetime, re
from pathlib import Path
import httpx
from selectolax.parser import HTMLParser
import yaml
import datetime
import zoneinfo  # (Python 3.9+)

ROOT = Path(__file__).resolve().parents[1]
# 👉 si tu veux tester Corolle plus tard, change ce chemin
SELECTORS_PATH = ROOT / "config" / "selectors_gulli_jurassic.yaml"
LOG_FILE = ROOT / "data" / "logs" / "grattweb_jouets.log"
REPORT_DIR = ROOT / "data" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

GATE_PATTERNS = [
    r"Inscrivez[-\s]?vous",
    r"identifiez[-\s]?vous",
    r"Se connecter",
    r"Connexion",
    r"Votre compte",
]

def log_line(status, contest, message):
    tz = zoneinfo.ZoneInfo("Europe/Paris")
    ts = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{status}] [{contest}] {message}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    print(line)

def load_yaml(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def check_gate(html_text: str, tree: HTMLParser) -> bool:
    txt = tree.text().strip() if tree.body else html_text
    for pat in GATE_PATTERNS:
        if re.search(pat, txt, flags=re.I):
            return True
    # présence probable d'un form de login
    if tree.css_first("form[action*='login'], form[action*='log_in'], form#login, form[name*='login']"):
        return True
    return False

def probe():
    cfg = load_yaml(SELECTORS_PATH)
    meta = cfg.get("meta", {})
    contest_name = f"{meta.get('site','grattweb.fr')} / {meta.get('type','instant_gagnant')}"
    url = cfg.get("form", {}).get("url")
    sels = cfg.get("selectors", {})

    if not url:
        log_line("ERROR", contest_name, "Aucune URL trouvée dans form.url")
        sys.exit(2)

    # 1) GET
    headers = {"User-Agent": "ConcoursFR-POC/1.0"}
    try:
        with httpx.Client(follow_redirects=True, headers=headers, timeout=25) as client:
            r = client.get(url)
            status = r.status_code
            if status != 200:
                log_line("ERROR", contest_name, f"HTTP {status} sur {url}")
                sys.exit(3)
            html = r.text
    except Exception as e:
        log_line("ERROR", contest_name, f"GET échoué: {e}")
        sys.exit(4)

    tree = HTMLParser(html)

    # 2) Vérif sélecteurs (si form est visible en clair)
    def exists(css):
        return bool(css and tree.css_first(css))

    checks = {
        "lastname": exists(sels.get("lastname")),
        "firstname": exists(sels.get("firstname")),
        "email": exists(sels.get("email")),
        "terms": exists(sels.get("terms")),
        "submit": exists(sels.get("submit")),
    }
    form_visible = all(checks.values())

    # 3) Détection d'un "gated login"
    gated = check_gate(html, tree)

    # 4) Rapport HTML
    today = datetime.date.today().isoformat()
    report_path = REPORT_DIR / f"probe_grattweb_jouets_{today}.html"
    def icon(b): return "✅" if b else "❌"
    rows = "".join(
        f"<tr><td>{k}</td><td>{icon(v)}</td></tr>" for k, v in checks.items()
    )
    state = "FORM_VISIBLE" if form_visible else ("GATED_LOGIN" if gated else "MISSING")
    report_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Probe Grattweb Jouets - {today}</title></head>
<body>
<h1>Probe Grattweb Jouets</h1>
<p>URL testée : <a href="{url}" target="_blank">{url}</a></p>
<p><strong>État détecté :</strong> {state}</p>
<table border="1" cellpadding="6" cellspacing="0">
<tr><th>Champ</th><th>Présent</th></tr>
{rows}
</table>
</body></html>
"""
    report_path.write_text(report_html, encoding="utf-8")

    # 5) Logs + code sortie
    if form_visible:
        log_line("INFO", contest_name, "Probe OK : FORM_VISIBLE (formulaire détecté)")
        sys.exit(0)
    elif gated:
        log_line("INFO", contest_name, "Probe OK : GATED_LOGIN (login requis, pas de formulaire en clair)")
        sys.exit(0)
    else:
        log_line("ERROR", contest_name, "Probe KO : MISSING (ni formulaire, ni message de garde)")
        sys.exit(5)

if __name__ == "__main__":
    probe()
