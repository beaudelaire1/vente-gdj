# Vente GDJ EEBC

Système de gestion pour restaurant éphémère et ventes ponctuelles.

## Stack

- **Backend** : Django 5.2
- **Frontend** : HTMX + Alpine.js + CSS premium
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **Déploiement** : Render

## Installation locale

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_users
python manage.py import_excel liste_resto_eph.xlsx
python manage.py runserver
```

## Utilisateurs par défaut

| Utilisateur | Mot de passe | Rôle |
|---|---|---|
| admin | admin2026! | Administrateur |
| caisse | caisse2026! | Caisse |
| preparation | prep2026! | Préparation |

## Interfaces

- `/` — Tableau de bord (admin)
- `/caisse/` — Interface caisse
- `/preparation/` — Interface préparation / distribution
- `/suivi/<token>/` — Consultation publique via QR code
- `/admin/` — Administration Django

## Import Excel

```bash
python manage.py import_excel chemin/vers/fichier.xlsx --event-name "Mon événement" --event-date 2026-03-28
```

## Déploiement Render

1. Créer un Web Service + PostgreSQL sur Render
2. Connecter le repo Git
3. Variables d'environnement configurées dans `render.yaml`
4. Après déploiement : `python manage.py setup_users` via le Shell Render
