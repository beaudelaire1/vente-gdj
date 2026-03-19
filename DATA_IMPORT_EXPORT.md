# 📊 Data Import/Export

This directory contains utilities for backing up and restoring database data.

## Commands

### Export Data

Export the entire database to Excel or JSON format for backup and migration.

**Excel format (recommended):**
```bash
python manage.py export_data --format=excel --output=my_backup.xlsx
```

**JSON format:**
```bash
python manage.py export_data --format=json --output=my_backup.json
```

**Auto-timestamped (default):**
```bash
python manage.py export_data
# Creates: data_20260318_223015.xlsx
```

### Import Data

Import data from Excel or JSON files back into the database.

**Import Excel:**
```bash
python manage.py import_data --file=my_backup.xlsx
```

**Import JSON:**
```bash
python manage.py import_data --file=my_backup.json
```

**Import with clear (dangerous!):**
```bash
python manage.py import_data --file=backup.xlsx --clear
# Clears all events, customers, orders, and logs before importing
```

## 📋 Supported Models

- **Events** — Campaigns/events (restaurant, sales, etc.)
- **Customers** — Registered customers
- **Orders** — Individual orders with full lifecycle
- **StatusLogs** — Order status change history

## 🔒 Production Usage

### Backup Before Production Deploy
```bash
python manage.py export_data --format=excel --output=backup_before_prod.xlsx
```

### Restore Data in Production
After deploying to Render and running migrations:

```bash
# SSH into Render service
python manage.py import_data --file=backup.xlsx
```

Or upload the backup file and use Django shell:
```bash
python manage.py shell
>>> from django.core.management import execute_from_command_line
>>> execute_from_command_line(['manage.py', 'import_data', '--file=backup.xlsx'])
```

## 📂 File Formats

### Excel Sheets Structure
- **Events** — ID, Name, Date, Description, Is Active, Created At
- **Customers** — ID, Name, Phone, Email, Created At
- **Orders** — Full order details (15 columns)
- **StatusLogs** — Status change tracking

### JSON Structure
```json
{
  "events": [...],
  "customers": [...],
  "orders": [...],
  "statuslogs": [...]
}
```

## ⚠️ Best Practices

1. **Regular backups** — Run export_data weekly/monthly
2. **Before migrations** — Always backup before Django migrations
3. **Version control** — Keep backup files locally, NOT in git (see .gitignore)
4. **Test imports** — Test import commands in development first
5. **Production safety** — Use `--clear` only in testing environments

## 🐛 Troubleshooting

**"File not found"** — Check file path is correct
```bash
python manage.py import_data --file=./backups/data.xlsx
```

**"Duplicate key error"** — Data already exists, omit `--clear` or delete old records
```bash
python manage.py import_data --file=backup.xlsx --clear
```

**"Event or Customer not found"** — Import dependencies in order:
1. Export from source
2. Check Events/Customers exist
3. Then import Orders
