# Dossier des journaux (logs)

Ce dossier contient les journaux d'exécution du POC "Concours FR".

## Objectif
Les fichiers de log enregistrent les actions réalisées par les scripts :
- connexions au site Grattweb.fr,
- soumissions de formulaires,
- messages de confirmation détectés,
- erreurs éventuelles (connexion, CAPTCHA, etc.),
- date et heure de chaque tentative.

## Format attendu
Chaque ligne de log suit le format :
[YYYY-MM-DD HH:MM:SS] [STATUT] [CONCOURS] message...

### Exemples :

[2025-10-07 09:00:05] [INFO] [GULLI Jurassic] Début de la participation
[2025-10-07 09:00:07] [SUCCESS] [GULLI Jurassic] Participation validée
[2025-10-07 09:00:08] [END] Process terminé

## Structure du dossier
- `grattweb_jouets.log` → journal principal pour les concours enfants/jouets
- `errors.log` → erreurs et exceptions détectées

## Conservation
Les logs sont conservés 30 jours maximum.
Ils seront archivés ou supprimés automatiquement dans une version future du script.

---

📘 **Note :** Ce dossier ne contient pour l’instant aucun fichier exécutable.
Il servira uniquement de stockage pour les journaux produits par les tests d’automatisation.
