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
C:/Users/vilme/AppData/Local/Programs/Python/Python313/python.exe manage.py bootstrap_app --excel liste_resto_eph.xlsx
python manage.py runserver
```

Version Python cible : `3.13.0` (voir [.python-version](.python-version)).

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
4. Après déploiement, ouvrir le Shell Render et injecter les données :

```bash
python manage.py bootstrap_app --json data_backup.json --clear
```

Ou si vous partez du fichier source Excel :

```bash
python manage.py bootstrap_app --excel liste_resto_eph.xlsx --clear
```

À chaque déploiement, Render exécute aussi `python manage.py setup_users` dans le build. Les comptes `admin`, `caisse` et `preparation` sont donc créés ou mis à jour automatiquement depuis les variables d'environnement Render.

## 📊 Backup & Migration

### Exporter une sauvegarde

```bash
# Excel (recommandé)
python manage.py export_data --format=excel --output=backup_prod.xlsx

# JSON
python manage.py export_data --format=json --output=backup_prod.json
```

### Restaurer une sauvegarde

```bash
# En local ou en production (Render Shell)
python manage.py import_data --file=backup_prod.xlsx

# Importer en effaçant les données existantes (TEST ONLY)
python manage.py import_data --file=backup_prod.xlsx --clear

# Bootstrap complet (migrations + users + import)
python manage.py bootstrap_app --json backup_prod.json --clear
```

**Voir [DATA_IMPORT_EXPORT.md](DATA_IMPORT_EXPORT.md) pour plus de détails.**

## Variables Render pour les comptes

- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`
- `DEFAULT_CAISSE_USERNAME`
- `DEFAULT_CAISSE_PASSWORD`
- `DEFAULT_PREPARATION_USERNAME`
- `DEFAULT_PREPARATION_PASSWORD`
