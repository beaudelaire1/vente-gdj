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

### 1. Créer le service

- Créer un **Web Service** sur Render et connecter le repo Git
- **Option A** (simple) : créer aussi un **PostgreSQL** Render (plan Free)
- **Option B** (Supabase) : créer une base Supabase et copier l'URI de connexion
  - Utiliser le port **5432** (mode Session, compatible Gunicorn)
  - Format : `postgresql://postgres.XXXX:PASSWORD@host:5432/postgres`

### 2. Variables d'environnement

Vérifier dans le dashboard Render que ces variables sont bien définies :

| Variable | Valeur |
|---|---|
| `DJANGO_SECRET_KEY` | *(auto-générée par render.yaml)* |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://votre-app.onrender.com` |
| `DATABASE_URL` | *(auto depuis Render DB ou URI Supabase)* |
| `PYTHON_VERSION` | `3.13.0` |
| `DEFAULT_ADMIN_USERNAME` | `admin` |
| `DEFAULT_ADMIN_PASSWORD` | *(auto-générée ou personnalisée)* |
| `DEFAULT_CAISSE_USERNAME` | `caisse` |
| `DEFAULT_CAISSE_PASSWORD` | *(auto-générée ou personnalisée)* |
| `DEFAULT_PREPARATION_USERNAME` | `preparation` |
| `DEFAULT_PREPARATION_PASSWORD` | *(auto-générée ou personnalisée)* |

### 3. Premier déploiement

Le `build.sh` exécute automatiquement :
- `pip install` → dépendances
- `collectstatic` → fichiers statiques
- `migrate` → schéma de base de données
- `setup_users` → comptes admin, caisse, préparation

### 4. Import initial des données

Après le premier déploiement, ouvrir le **Shell Render** et lancer :

```bash
# Depuis un fichier Excel source
python manage.py bootstrap_app --skip-migrate --skip-users --excel liste_resto_eph.xlsx --clear \
  --event-name "Restaurant Éphémère GDJ EEBC" --event-date 2026-03-28

# Ou depuis une sauvegarde JSON
python manage.py bootstrap_app --skip-migrate --skip-users --json data_backup.json --clear
```

> **Attention** : `--clear` efface les données métier. Ne l'utiliser que pour l'import initial ou un reset volontaire.

### 5. Redéploiements suivants

Les redéploiements relancent `build.sh` qui applique les nouvelles migrations et met à jour les comptes. **Aucune donnée n'est effacée.**

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
