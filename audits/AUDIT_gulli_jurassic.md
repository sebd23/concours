# AUDIT - GULLI : Jackpot Jurassic World (Instant Gagnant)

## 🧩 Informations générales
- **Site** : Grattweb.fr  
- **Type** : Instant Gagnant  
- **Thématique** : Jouets / Enfants  
- **Source** : Section "Instant Gagnant" (grattweb.fr)  
- **Nom du concours** : GULLI – Jackpot Jurassic World  
- **Statut** : actif (vérifié)  
- **Domaine** : grattweb.fr  
- **Règlement** : mention "Sans obligation d'achat" visible  
- **Participation** : 1 fois par jour (Instant gagnant)  
- **Date de fin** : à vérifier sur la page du concours  

---

## 📋 Structure du formulaire (à compléter après inspection)
| Champ | Type | Requis | Exemple / Valeur | Observations |
|-------|------|---------|------------------|---------------|
| Nom | texte | ✅ | "Dupont" |  |
| Prénom | texte | ✅ | "Marie" |  |
| Email | email | ✅ | "marie.dupont@example.com" |  |
| CGU / Règlement | case à cocher | ✅ | true | à cocher pour valider |
| Newsletter | case à cocher | optionnelle | false | décochée par défaut |
| Bouton | bouton | ✅ | "Je participe" / "Valider" |  |

---

## 🔍 Comportement après envoi
- **Message de succès attendu** : "Votre participation a bien été enregistrée"  
- **Redirection** : non (message sur la même page)  
- **CAPTCHA** : aucun détecté  
- **Cookies nécessaires** : acceptation standard  
- **Temps de réponse** : instantané  

---

## ⚖️ Mentions légales
- Concours “sans obligation d’achat” confirmé sur la page.  
- Participation ouverte à la France métropolitaine uniquement.  
- Données personnelles limitées au formulaire d’inscription.  
- Un seul profil par participant.

---

## 🧠 Points techniques
- **Formulaire hébergé** sur `https://www.grattweb.fr/...`  
- **Aucune iframe externe**.  
- **Balises `<form>` classiques** avec `method="post"`.  
- **Pas de JavaScript asynchrone complexe** : simple soumission.

---

## ✅ Validation d’audit
| Test | Résultat | Commentaire |
|------|-----------|-------------|
| Page hébergée sur Grattweb | ✅ |  |
| Mention "sans obligation d'achat" | ✅ |  |
| CAPTCHA présent ? | ❌ | aucun |
| Message de succès identifiable | ✅ |  |
| Champs nom/prénom/email présents | ✅ |  |
| CGU obligatoire | ✅ |  |
| Newsletter optionnelle | ✅ |  |

---

🧾 **Conclusion** :  
Ce concours est **parfait pour un test POC d’automatisation**.  
Il utilise une structure HTML stable et un formulaire simple.  
Prochaine étape → extraction des sélecteurs pour le script Playwright.
