from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import json
import os
from datetime import datetime
import logging
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'chemopad-secret-key-2024')

# Add proxy fix for nginx
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add after_request handler to prevent caching of dynamic pages
@app.after_request
def add_cache_control(response):
    # Prevent caching for HTML pages (dynamic content)
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Global data storage
annotations_df = None
project_cards_df = None
matches = {}  # {annotation_row_id: project_card_id}

def load_data():
    """Load all CSV data"""
    global annotations_df, project_cards_df

    # Use absolute paths for production
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    # Load annotations (skip missing cards)
    annotations_file = os.path.join(data_dir, 'chemoPAD-student-annotations-with-flags.csv')
    annotations_df = pd.read_csv(annotations_file)
    annotations_df = annotations_df[annotations_df['missing_card'] != True].copy()
    annotations_df['row_id'] = range(len(annotations_df))

    # Load project cards
    project_cards_file = os.path.join(data_dir, 'project_cards.csv')
    project_cards_df = pd.read_csv(project_cards_file)

    logger.info(f"Loaded {len(annotations_df)} annotations from {annotations_file}")
    logger.info(f"Loaded {len(project_cards_df)} project cards from {project_cards_file}")

    # Load existing matches if any
    matches_file = os.path.join(data_dir, 'matches.json')
    if os.path.exists(matches_file):
        with open(matches_file, 'r') as f:
            global matches
            matches = json.load(f)
            # Convert keys to int
            matches = {int(k): v for k, v in matches.items()}

@app.route('/')
def dashboard():
    """API Dashboard - Level 1"""
    # Group by API
    api_stats = []

    for api in annotations_df['API'].unique():
        if pd.isna(api):
            continue

        api_data = annotations_df[annotations_df['API'] == api]
        unique_pads = api_data['PAD#'].unique()

        # Count completed PAD#s (all rows for that PAD# are matched)
        completed_pads = 0
        for pad in unique_pads:
            pad_rows = api_data[api_data['PAD#'] == pad]
            if all(row_id in matches for row_id in pad_rows['row_id']):
                completed_pads += 1

        api_stats.append({
            'name': api,
            'total_pads': len(unique_pads),
            'completed_pads': completed_pads,
            'progress': (completed_pads / len(unique_pads) * 100) if len(unique_pads) > 0 else 0
        })

    # Sort by name
    api_stats.sort(key=lambda x: x['name'])

    return render_template('dashboard.html', apis=api_stats)

@app.route('/api/<api_name>')
def pad_list(api_name):
    """PAD# List for specific API - Level 2"""
    api_data = annotations_df[annotations_df['API'] == api_name]

    pad_stats = []
    for pad in api_data['PAD#'].unique():
        pad_rows = api_data[api_data['PAD#'] == pad]
        matched_count = sum(1 for row_id in pad_rows['row_id'] if row_id in matches)

        # Get sample name from first row
        sample = pad_rows.iloc[0]['Sample'] if pd.notna(pad_rows.iloc[0]['Sample']) else ''

        pad_stats.append({
            'pad_num': int(pad),
            'sample': sample,
            'total_rows': len(pad_rows),
            'matched_rows': matched_count,
            'status': 'complete' if matched_count == len(pad_rows) else
                     'partial' if matched_count > 0 else 'not_started'
        })

    # Sort by PAD#
    pad_stats.sort(key=lambda x: x['pad_num'])

    # Calculate API progress
    completed_pads = sum(1 for p in pad_stats if p['status'] == 'complete')
    api_progress = {
        'total': len(pad_stats),
        'completed': completed_pads,
        'percentage': (completed_pads / len(pad_stats) * 100) if len(pad_stats) > 0 else 0
    }

    return render_template('pad_list.html',
                         api_name=api_name,
                         pads=pad_stats,
                         api_progress=api_progress)

@app.route('/match/<api_name>/<int:pad_num>')
def match_page(api_name, pad_num):
    """Annotation Matching page - Level 3"""
    # Get all annotation rows for this PAD#
    pad_annotations = annotations_df[
        (annotations_df['API'] == api_name) &
        (annotations_df['PAD#'] == pad_num)
    ].copy()

    # Get all project cards for this PAD# (sample_id)
    candidates = project_cards_df[
        project_cards_df['sample_id'] == pad_num
    ].copy()

    # Mark which candidates are already used
    used_ids = set(matches.values())
    candidates['is_used'] = candidates['id'].isin(used_ids)

    # Prepare annotation rows with their matches
    rows_data = []
    for idx, row in pad_annotations.iterrows():
        row_dict = row.to_dict()
        row_dict['matched_id'] = matches.get(row['row_id'])
        rows_data.append(row_dict)

    # Convert candidates to dict for JSON
    candidates_data = candidates.to_dict('records')

    # Calculate progress
    matched_count = sum(1 for r in rows_data if r['matched_id'])

    return render_template('match.html',
                         api_name=api_name,
                         pad_num=pad_num,
                         annotations=rows_data,
                         candidates=candidates_data,
                         matched_count=matched_count,
                         total_rows=len(rows_data))

@app.route('/api/save_match', methods=['POST'])
def save_match():
    """Save a match between annotation row and project card"""
    data = request.json
    row_id = int(data['row_id'])
    card_id = int(data['card_id']) if data['card_id'] else None

    # Check if card_id is already used
    if card_id and card_id in matches.values():
        return jsonify({'success': False, 'error': 'ID already matched to another annotation'})

    if card_id:
        matches[row_id] = card_id
    elif row_id in matches:
        # Unmatching
        del matches[row_id]

    # Save matches to file using absolute path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_file = os.path.join(base_dir, 'data', 'matches.json')
    with open(matches_file, 'w') as f:
        json.dump(matches, f, indent=2)

    return jsonify({'success': True})

@app.route('/api/export')
def export_data():
    """Export all matched data to CSV"""
    # Load ALL annotations including those with missing_card=True
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    annotations_file = os.path.join(base_dir, 'data', 'chemoPAD-student-annotations-with-flags.csv')
    all_annotations_df = pd.read_csv(annotations_file)

    # Create export dataframe - keep original annotation columns + missing_card flag
    original_columns = ['annot_id', 'PAD#', 'Camera', 'Lighting (lightbox, benchtop, benchtop dark)',
                       'black/white background', 'API', 'Sample',
                       'mg concentration (w/w mg/mg or w/v mg/mL)', '% Conc', 'missing_card']

    # Only keep original columns that exist
    keep_columns = [col for col in original_columns if col in all_annotations_df.columns]
    export_df = all_annotations_df[keep_columns].copy()

    # Add row_id only for rows that are matchable (missing_card=False)
    # This is needed to map to matches dictionary
    matchable_df = all_annotations_df[all_annotations_df['missing_card'] != True].copy()
    matchable_df['row_id'] = range(len(matchable_df))

    # Create mapping from original index to row_id
    index_to_rowid = dict(zip(matchable_df.index, matchable_df['row_id']))

    # Add matched_id column - map using the index_to_rowid mapping
    export_df['matched_id'] = None
    for idx in export_df.index:
        if idx in index_to_rowid:
            row_id = index_to_rowid[idx]
            if row_id in matches:
                export_df.at[idx, 'matched_id'] = matches[row_id]

    # Add matched_sample_id right after matched_id
    export_df['matched_sample_id'] = None

    # Add other project_cards fields for matched rows
    project_fields = ['sample_name', 'quantity', 'camera_type_1', 'deleted',
                     'date_of_creation', 'processed_file_location']
    for field in project_fields:
        export_df[f'matched_{field}'] = None

    # Add URL field (will be generated from processed_file_location)
    export_df['matched_url'] = None

    # Fill in project data for matched rows (only for rows with missing_card=False)
    for row_id, card_id in matches.items():
        if card_id in project_cards_df['id'].values:
            card_data = project_cards_df[project_cards_df['id'] == card_id].iloc[0]
            # Find the original index for this row_id
            orig_idx = matchable_df[matchable_df['row_id'] == row_id].index[0]

            # Add sample_id right after matched_id
            export_df.at[orig_idx, 'matched_sample_id'] = card_data.get('sample_id')

            # Add other fields
            for field in project_fields:
                if field in card_data:
                    export_df.at[orig_idx, f'matched_{field}'] = card_data[field]

            # Generate URL from processed_file_location
            if 'processed_file_location' in card_data and pd.notna(card_data['processed_file_location']):
                export_df.at[orig_idx, 'matched_url'] = f"https://pad.crc.nd.edu{card_data['processed_file_location']}"

    # Remove processed_file_location (we have URL instead) but keep missing_card column
    export_df = export_df.drop(columns=['matched_processed_file_location'], errors='ignore')

    # Convert ID columns to ensure they export as integers without decimals
    # We need to handle this specially for CSV export
    id_columns = ['annot_id', 'PAD#', 'matched_id', 'matched_sample_id']

    # Store original dtypes for restoration if needed
    for col in id_columns:
        if col in export_df.columns:
            # Convert column to object type first to prevent pandas auto-conversion
            # Handle NaN/None values carefully
            def format_id(x):
                # Check if value is NaN, None, or empty string
                if pd.isna(x) or x is None or (isinstance(x, str) and x == ''):
                    return ''
                # Convert to integer (removing any decimal) then to string
                try:
                    return str(int(float(x)))
                except (ValueError, TypeError):
                    return ''

            export_df[col] = export_df[col].apply(format_id)
            # Force object dtype to ensure strings aren't converted back to float
            export_df[col] = export_df[col].astype('object')

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = os.path.join(base_dir, 'data', f'chemopad_matched_export_{timestamp}.csv')

    # Export to CSV with special handling to preserve integer format
    # Use float_format to prevent .0 decimals, but since we converted to strings, this shouldn't be needed
    export_df.to_csv(filename, index=False, na_rep='')

    return send_file(filename, as_attachment=True, download_name=f'chemopad_export_{timestamp}.csv')

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    total_annotations = len(annotations_df)
    matched_annotations = len(matches)

    # Count completed PAD#s
    pad_groups = annotations_df.groupby('PAD#')
    completed_pads = 0
    total_pads = len(pad_groups)

    for pad, group in pad_groups:
        if all(row_id in matches for row_id in group['row_id']):
            completed_pads += 1

    return jsonify({
        'total_annotations': total_annotations,
        'matched_annotations': matched_annotations,
        'total_pads': total_pads,
        'completed_pads': completed_pads,
        'annotation_progress': (matched_annotations / total_annotations * 100) if total_annotations > 0 else 0,
        'pad_progress': (completed_pads / total_pads * 100) if total_pads > 0 else 0
    })

# Load data when module is imported (for gunicorn)
try:
    load_data()
    logger.info("Data loaded successfully on module import")
except Exception as e:
    logger.error(f"Failed to load data on module import: {e}")

if __name__ == '__main__':
    # For development only
    app.run(host='0.0.0.0', port=5000, debug=False)