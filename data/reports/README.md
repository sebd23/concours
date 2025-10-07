# Dossier des rapports HTML

Ce dossier contient les rapports quotidiens générés par les scripts du projet **Concours FR**.

## Objectif
Chaque rapport présente un **résumé clair des participations effectuées** :
- date du jour,
- concours joués,
- résultats (succès / échec),
- message de confirmation reçu,
- temps d'exécution.

Ces rapports seront accessibles en HTML pour une lecture rapide depuis le navigateur.

---

## Exemple de rapport attendu
**Nom du fichier :**
grattweb_jouets_2025-10-07.html

**Contenu minimal :**
```html
<h1>Rapport de participation - Grattweb Jouets</h1>
<p>Date : 2025-10-07</p>
<table>
  <tr><th>Concours</th><th>Résultat</th><th>Message</th><th>Heure</th></tr>
  <tr><td>GULLI Jurassic</td><td>✅ Succès</td><td>Participation enregistrée</td><td>09:00:07</td></tr>
</table>
Structure prévue

grattweb_jouets_YYYY-MM-DD.html → rapport journalier (auto-généré)

index.html → vue synthétique des 7 derniers jours (à venir)

README.md → ce fichier d’explication

Conservation

Les rapports HTML sont conservés 30 jours.
Ils peuvent être exportés en PDF ou archivés automatiquement via GitHub Actions.
📘 Note :
Les rapports seront produits par le script generate_report.py (non encore créé à ce stade).
Aucune donnée personnelle sensible n’est affichée dans ces fichiers.

---

### 💾 Étapes

1️⃣ Sur GitHub → **Add file → Create new file**  
2️⃣ Nom du fichier : `data/reports/README.md`  
3️⃣ Colle le contenu ci-dessus.  
4️⃣ Commit avec un message :  


