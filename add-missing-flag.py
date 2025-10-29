#!/usr/bin/env python3
"""
Add missing_card flag to chemoPAD-student-annotations.csv
A row is flagged as missing if its PAD# doesn't exist in project_cards.csv
"""

import pandas as pd
import os

# Set up paths
data_dir = 'data'
annotations_file = os.path.join(data_dir, 'chemoPAD-student-annotations.csv')
project_cards_file = os.path.join(data_dir, 'project_cards.csv')
output_file = os.path.join(data_dir, 'chemoPAD-student-annotations-with-flags.csv')

print(f"Loading annotations from {annotations_file}...")
annotations_df = pd.read_csv(annotations_file)
print(f"Loaded {len(annotations_df)} annotation rows")

print(f"\nLoading project cards from {project_cards_file}...")
project_cards_df = pd.read_csv(project_cards_file)
print(f"Loaded {len(project_cards_df)} project cards")

# Get unique PAD#s from project_cards (these are the ones we CAN match)
available_pads = set(project_cards_df['sample_id'].unique())
print(f"\nFound {len(available_pads)} unique PAD#s in project_cards")

# Check which annotation PAD#s are missing from project_cards
annotations_df['missing_card'] = ~annotations_df['PAD#'].isin(available_pads)

# Count missing
missing_count = annotations_df['missing_card'].sum()
missing_pads = annotations_df[annotations_df['missing_card']]['PAD#'].unique()

print(f"\nResults:")
print(f"- {missing_count} annotation rows have missing PAD#s")
print(f"- {len(missing_pads)} unique PAD#s are missing")
print(f"- {len(annotations_df) - missing_count} rows can be matched")

if len(missing_pads) > 0:
    print(f"\nMissing PAD#s: {sorted(missing_pads)}")

# Save the flagged file
print(f"\nSaving flagged annotations to {output_file}...")
annotations_df.to_csv(output_file, index=False)
print(f"Done! File saved with {len(annotations_df.columns)} columns")

# Show the columns for verification
print(f"\nColumns in the output file:")
for i, col in enumerate(annotations_df.columns, 1):
    print(f"  {i}. {col}")