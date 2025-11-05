# VM Data Import Instructions

Follow these steps on the VM to clean the database and import data from the old export.

## Prerequisites

Make sure you're in the project directory and have the export file ready:
```bash
cd ~/chemo-pad-annotations
ls data/chemopad_matched_export_20251031_152453.csv  # Verify file exists
```

## Step 1: Pull Latest Changes

Get the latest scripts from the repository:
```bash
git pull origin main
```

This will update the scripts to the new `scripts/` directory structure.

## Step 2: Stop the Flask Application

Before modifying the database, stop the running Flask application:
```bash
pkill -f "python app_production.py"
```

Verify it stopped:
```bash
ps aux | grep app_production.py
```

## Step 3: Clean the Database

Run the cleanup script to remove all test data:
```bash
uv run python scripts/cleanup_database.py
```

**What it does:**
- Shows current database state (number of matches and notes)
- Asks for confirmation before deleting
- Removes all matches, notes, and in-database backups
- Optionally removes backup files and export CSVs

**What to answer:**
- First prompt (delete database data): Type `yes` or `y`
- Second prompt (remove backup files): Type `yes` or `y`
- Third prompt (remove export files): Type `no` or `n` (keep the import file!)

## Step 4: Import Data from Old Export

Run the import script with the old export file:
```bash
uv run python scripts/import_export_data.py data/chemopad_matched_export_20251031_152453.csv
```

**What it does:**
- Loads the old export CSV
- Validates all annot_ids exist in current data
- Validates all card_ids (matched_id) exist in project_cards
- Shows summary of what will be imported
- Reports any skipped entries
- Asks for confirmation before importing

**What to look for:**
- Number of valid matches and notes found
- Any warnings about skipped entries (annot_id or card_id not found)
- Final confirmation prompt

**What to answer:**
- Confirmation prompt: Type `yes` or `y` to proceed with import

**Expected results based on previous analysis:**
- Valid matches: 6 (from PAD #74962)
- Valid notes: 158
- The script will create a backup after successful import

## Step 5: Verify Import

Check the database state after import:
```bash
sqlite3 database/chemopad.db "SELECT COUNT(*) as matches FROM matches;"
sqlite3 database/chemopad.db "SELECT COUNT(*) as notes FROM notes;"
```

**Expected output:**
- matches: 6
- notes: 158

## Step 6: Restart the Flask Application

Start the Flask application again:
```bash
cd flask-app
nohup uv run python app_production.py > ../logs/app.log 2>&1 &
cd ..
```

Verify it started:
```bash
ps aux | grep app_production.py
tail -f logs/app.log  # Press Ctrl+C to exit
```

## Step 7: Verify in Web Interface

Open the web interface and verify:
```
http://pad-annotation.crc.nd.edu:8080/
```

1. Go to the Dashboard
2. Check that the progress bars show the imported matches
3. Open one of the imported annotations and verify the match is there
4. Check that notes are preserved

## Troubleshooting

### Import script shows "annot_id not in current data"
This means the old export has annotation IDs that don't exist in the current `chemoPAD-annotations-final.csv`. These will be skipped automatically.

### Import script shows "card_id not in project_cards"
This means the old export references project card IDs that don't exist in `project_cards.csv`. These matches will be skipped automatically.

### Flask won't start
Check the log file:
```bash
tail -50 logs/app.log
```

### Database locked error
Make sure Flask is stopped before running the scripts:
```bash
pkill -f "python app_production.py"
```

## Summary Commands (Quick Reference)

```bash
# 1. Pull latest code
git pull origin main

# 2. Stop Flask
pkill -f "python app_production.py"

# 3. Clean database
uv run python scripts/cleanup_database.py

# 4. Import data
uv run python scripts/import_export_data.py data/chemopad_matched_export_20251031_152453.csv

# 5. Verify
sqlite3 database/chemopad.db "SELECT COUNT(*) FROM matches; SELECT COUNT(*) FROM notes;"

# 6. Restart Flask
cd flask-app && nohup uv run python app_production.py > ../logs/app.log 2>&1 & cd ..
```

---

**Date:** November 2025
**Contact:** pmoreie@crc.nd.edu
