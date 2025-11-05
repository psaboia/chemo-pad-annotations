#!/usr/bin/env python3
"""
Import Data from Old Export
Restores student matches and notes from a previous CSV export
"""

import os
import sys
import pandas as pd

# Add flask-app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask-app'))

import database

def import_export_data(export_file):
    """Import data from old export CSV"""

    print("📥 Importing Data from Old Export")
    print("=" * 60)

    # Get paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')

    # Handle both absolute/relative paths and filenames
    if os.path.isabs(export_file) or os.path.exists(export_file):
        # Full path provided or file exists in current directory
        export_path = export_file
    else:
        # Just filename, look in data/ directory
        export_path = os.path.join(data_dir, export_file)

    annotations_path = os.path.join(data_dir, 'chemoPAD-annotations-final.csv')
    project_cards_path = os.path.join(data_dir, 'project_cards.csv')

    # Verify files exist
    if not os.path.exists(export_path):
        print(f"❌ Error: Export file not found: {export_path}")
        return

    if not os.path.exists(annotations_path):
        print(f"❌ Error: Annotations file not found: {annotations_path}")
        return

    if not os.path.exists(project_cards_path):
        print(f"❌ Error: Project cards file not found: {project_cards_path}")
        return

    # Load data
    print(f"\n📂 Loading data files...")
    print(f"  - Old export: {export_file}")

    old_export = pd.read_csv(export_path)
    current_annotations = pd.read_csv(annotations_path)
    project_cards = pd.read_csv(project_cards_path)

    print(f"  ✓ Old export rows: {len(old_export)}")
    print(f"  ✓ Current annotations: {len(current_annotations)}")
    print(f"  ✓ Project cards: {len(project_cards)}")

    # Get valid annot_ids and card_ids
    valid_annot_ids = set(current_annotations['annot_id'].values)
    valid_card_ids = set(project_cards['id'].values)

    print(f"\n🔍 Analyzing data in old export...")

    # Find rows with data
    work_rows = []

    for idx, row in old_export.iterrows():
        annot_id = row.get('annot_id')
        matched_id = row.get('matched_id')
        notes = row.get('notes')

        # Check if annot_id is valid
        if pd.isna(annot_id):
            continue

        try:
            annot_id = int(annot_id)
        except (ValueError, TypeError):
            continue

        # Check if row has data
        has_match = pd.notna(matched_id) and str(matched_id).strip() != ''
        has_notes = pd.notna(notes) and str(notes).strip() != ''

        if has_match or has_notes:
            work_rows.append({
                'annot_id': annot_id,
                'matched_id': matched_id,
                'notes': notes,
                'has_match': has_match,
                'has_notes': has_notes
            })

    print(f"  Found {len(work_rows)} rows with data")

    # Categorize and validate
    stats = {
        'total_work': len(work_rows),
        'valid_matches': 0,
        'valid_notes': 0,
        'skipped_annot_id': 0,
        'skipped_card_id': 0,
        'imported_matches': 0,
        'imported_notes': 0
    }

    invalid_annot_ids = []
    invalid_card_ids = []
    import_queue = []

    print(f"\n✅ Validating data...")

    for work in work_rows:
        annot_id = work['annot_id']
        matched_id = work['matched_id']
        notes = work['notes']

        # Validate annot_id exists in current data
        if annot_id not in valid_annot_ids:
            invalid_annot_ids.append(annot_id)
            stats['skipped_annot_id'] += 1
            continue

        # Process match
        match_to_import = None
        if work['has_match']:
            matched_id_str = str(matched_id).strip()

            # Check if it's "no_match"
            if matched_id_str == "no_match":
                match_to_import = "no_match"
                stats['valid_matches'] += 1
            else:
                # Validate card_id exists in project_cards
                try:
                    card_id = int(float(matched_id_str))
                    if card_id in valid_card_ids:
                        match_to_import = card_id
                        stats['valid_matches'] += 1
                    else:
                        invalid_card_ids.append((annot_id, card_id))
                        stats['skipped_card_id'] += 1
                except (ValueError, TypeError):
                    invalid_card_ids.append((annot_id, matched_id_str))
                    stats['skipped_card_id'] += 1

        # Process notes
        notes_to_import = None
        if work['has_notes']:
            notes_to_import = str(notes).strip()
            stats['valid_notes'] += 1

        # Queue for import if we have valid data
        if match_to_import is not None or notes_to_import is not None:
            import_queue.append({
                'annot_id': annot_id,
                'match': match_to_import,
                'notes': notes_to_import
            })

    # Report validation results
    print(f"  ✓ Valid matches: {stats['valid_matches']}")
    print(f"  ✓ Valid notes: {stats['valid_notes']}")

    if stats['skipped_annot_id'] > 0:
        print(f"  ⚠️  Skipped (annot_id not in current data): {stats['skipped_annot_id']}")
        if len(invalid_annot_ids) <= 10:
            print(f"      annot_ids: {invalid_annot_ids}")
        else:
            print(f"      annot_ids: {invalid_annot_ids[:10]} ... and {len(invalid_annot_ids)-10} more")

    if stats['skipped_card_id'] > 0:
        print(f"  ⚠️  Skipped (card_id not in project_cards): {stats['skipped_card_id']}")
        if len(invalid_card_ids) <= 5:
            for annot_id, card_id in invalid_card_ids:
                print(f"      annot_id {annot_id} -> card_id {card_id}")
        else:
            for annot_id, card_id in invalid_card_ids[:5]:
                print(f"      annot_id {annot_id} -> card_id {card_id}")
            print(f"      ... and {len(invalid_card_ids)-5} more")

    # Confirm import
    if not import_queue:
        print(f"\n⚠️  No valid data to import!")
        return

    print(f"\n📊 Ready to import:")
    print(f"  - {sum(1 for item in import_queue if item['match'] is not None)} matches")
    print(f"  - {sum(1 for item in import_queue if item['notes'] is not None)} notes")

    response = input("\nProceed with import? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("❌ Import cancelled")
        return

    # Import to database
    print(f"\n💾 Importing to database...")

    for item in import_queue:
        annot_id = item['annot_id']

        # Import match
        if item['match'] is not None:
            try:
                database.save_match(annot_id, item['match'])
                stats['imported_matches'] += 1
            except Exception as e:
                print(f"  ❌ Error importing match for annot_id {annot_id}: {e}")

        # Import note
        if item['notes'] is not None:
            try:
                database.save_note(annot_id, item['notes'])
                stats['imported_notes'] += 1
            except Exception as e:
                print(f"  ❌ Error importing note for annot_id {annot_id}: {e}")

    # Create backup after import
    print(f"\n💾 Creating backup after import...")
    try:
        backup_file, backup_size = database.create_file_backup('import')
        print(f"  ✓ Backup created: {backup_file} ({backup_size} bytes)")
    except Exception as e:
        print(f"  ⚠️  Warning: Could not create backup: {e}")

    # Final summary
    print(f"\n" + "=" * 60)
    print(f"✅ Import Complete!")
    print(f"\nImported:")
    print(f"  - {stats['imported_matches']} matches")
    print(f"  - {stats['imported_notes']} notes")

    if stats['skipped_annot_id'] > 0 or stats['skipped_card_id'] > 0:
        print(f"\nSkipped:")
        if stats['skipped_annot_id'] > 0:
            print(f"  - {stats['skipped_annot_id']} rows (annot_id not in current data)")
        if stats['skipped_card_id'] > 0:
            print(f"  - {stats['skipped_card_id']} matches (card_id not in project_cards)")

    # Verify final state
    final_matches = database.get_all_matches()
    final_notes = database.get_all_notes()

    print(f"\nFinal database state:")
    print(f"  - Total matches: {len(final_matches)}")
    print(f"  - Total notes: {len(final_notes)}")

if __name__ == '__main__':
    # Default export file
    export_file = 'chemopad_matched_export_20251031_152453.csv'

    # Allow command line argument
    if len(sys.argv) > 1:
        export_file = sys.argv[1]

    try:
        import_export_data(export_file)
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
