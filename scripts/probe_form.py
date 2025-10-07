#!/usr/bin/env python3
"""
v2 - Probe formulaire (lecture seule)
- Récupère la page concours (form.url depuis config/selectors_*.yaml)
- Vérifie l’accessibilité (HTTP 200)
- Contrôle la présence des sélecteurs (inputs, case CGU, bouton)
- N’ENVOIE AUCUNE DONNÉE (aucune soumission)
- Écrit logs + un petit rapport HTML

Dépendances: httpx, selectolax, pyyaml
"""

import sys, datetime
from pathlib import Path
import httpx
from selectolax.parser import HTMLParser
import yaml

ROOT = Path(__file__).resolve().parents[1]
SELECTORS_PATH = ROOT / "config" / "selectors_gulli_jurassic.yaml"
LOG_FILE = ROOT / "data" / "logs" / "grattweb_jouets.log"
REPORT_DIR = ROOT / "data" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def log_line(status, contest, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{status}] [{contest}] {message}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.open("a", encoding="utf-8").write(line + "\n")
    print(line)

def load_yaml(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

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
        with httpx.Client(follow_redirects=True, headers=headers, timeout=20) as client:
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

    # 2) Vérif sélecteurs
    checks = []
    def check(name, css):
        if not css: 
            return (name, False, "sélecteur manquant dans YAML")
        node = tree.css_first(css)
        return (name, node is not None, css)

    checks.append(check("lastname", sels.get("lastname")))
    checks.append(check("firstname", sels.get("firstname")))
    checks.append(check("email", sels.get("email")))
    checks.append(check("terms", sels.get("terms")))
    checks.append(check("submit", sels.get("submit")))

    ok = all(ok for _, ok, _ in checks)

    # 3) Rapport HTML
    today = datetime.date.today().isoformat()
    report_path = REPORT_DIR / f"probe_grattweb_jouets_{today}.html"
    rows = "\n".join(
        f"<tr><td>{name}</td><td>{'✅' if is_ok else '❌'}</td><td><code>{sel or ''}</code></td></tr>"
        for name, is_ok, sel in checks
    )
    report_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Probe Grattweb Jouets - {today}</title></head>
<body>
<h1>Probe Grattweb Jouets</h1>
<p>URL testée : <a href="{url}" target="_blank">{url}</a></p>
<table border="1" cellpadding="6" cellspacing="0">
<tr><th>Champ</th><th>Présent</th><th>Sélecteur</th></tr>
{rows}
</table>
</body></html>
"""
    report_path.write_text(report_html, encoding="utf-8")

    # 4) Logs
    if ok:
        log_line("INFO", contest_name, "Probe OK : tous les sélecteurs trouvés")
    else:
        manquants = [n for n, is_ok, _ in checks if not is_ok]
        log_line("ERROR", contest_name, f"Probe KO : sélecteurs manquants {manquants}")
        sys.exit(5)

if __name__ == "__main__":
    probe()
