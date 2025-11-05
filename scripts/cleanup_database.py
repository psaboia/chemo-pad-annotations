#!/usr/bin/env python3
"""
Database Cleanup Script for ChemoPAD Annotation Matcher
Removes all test data and resets the database to production-ready state
"""

import os
import sys

# Add flask-app to path (script is in scripts/, so go up one level)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'flask-app'))

import database

def cleanup_database():
    """Clean up all test data from database"""
    print("🧹 ChemoPAD Database Cleanup")
    print("=" * 50)

    # Get current state
    matches = database.get_all_matches()
    notes = database.get_all_notes()

    print(f"\nCurrent database state:")
    print(f"  - Matches: {len(matches)}")
    print(f"  - Notes: {len(notes)}")

    if len(matches) == 0 and len(notes) == 0:
        print("\n✅ Database is already clean!")
        return

    # Confirm cleanup
    print(f"\n⚠️  WARNING: This will delete:")
    print(f"  - {len(matches)} matches")
    print(f"  - {len(notes)} notes")
    print(f"  - All in-database backups")

    response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("❌ Cleanup cancelled")
        return

    # Perform cleanup
    print("\n🗑️  Cleaning database...")

    with database.get_db() as conn:
        match_count = conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0]
        note_count = conn.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
        backup_count = conn.execute('SELECT COUNT(*) FROM backups').fetchone()[0]

        print(f"  Deleting {match_count} matches...")
        conn.execute('DELETE FROM matches')

        print(f"  Deleting {note_count} notes...")
        conn.execute('DELETE FROM notes')

        print(f"  Clearing {backup_count} in-database backups...")
        conn.execute('DELETE FROM backups')

        conn.commit()

    # Verify cleanup
    matches = database.get_all_matches()
    notes = database.get_all_notes()

    print("\n✅ Database cleanup complete!")
    print(f"  Final state: {len(matches)} matches, {len(notes)} notes")

def cleanup_backup_files():
    """Clean up backup files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # Go up to project root
    backup_dir = os.path.join(base_dir, 'database', 'backups')

    if not os.path.exists(backup_dir):
        print("\n  No backup directory found")
        return

    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]

    if not backup_files:
        print("\n  No backup files to remove")
        return

    print(f"\n  Found {len(backup_files)} backup files")
    response = input("  Remove backup files? (yes/no): ").strip().lower()

    if response in ['yes', 'y']:
        for filename in backup_files:
            filepath = os.path.join(backup_dir, filename)
            os.remove(filepath)
            print(f"    Removed: {filename}")
        print("  ✅ Backup files removed")
    else:
        print("  Backup files kept")

def cleanup_export_files():
    """Clean up export CSV files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)  # Go up to project root
    exports_dir = os.path.join(base_dir, 'exports')

    if not os.path.exists(exports_dir):
        print("\n  No exports directory found")
        return

    export_files = [f for f in os.listdir(exports_dir) if f.endswith('.csv')]

    if not export_files:
        print("\n  No export files to remove")
        return

    print(f"\n  Found {len(export_files)} export files")
    response = input("  Remove export files? (yes/no): ").strip().lower()

    if response in ['yes', 'y']:
        for filename in export_files:
            filepath = os.path.join(exports_dir, filename)
            os.remove(filepath)
            print(f"    Removed: {filename}")
        print("  ✅ Export files removed")
    else:
        print("  Export files kept")

if __name__ == '__main__':
    try:
        cleanup_database()

        print("\n" + "=" * 50)
        print("Additional cleanup:")
        cleanup_backup_files()
        cleanup_export_files()

        print("\n" + "=" * 50)
        print("🎉 Cleanup complete! Database is ready for production.")

    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        sys.exit(1)
