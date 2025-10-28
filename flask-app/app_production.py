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

# Global data storage
annotations_df = None
project_cards_df = None
matches = {}  # {annotation_row_id: project_card_id}

def load_data():
    """Load all CSV data"""
    global annotations_df, project_cards_df

    # Load annotations (skip missing cards)
    annotations_df = pd.read_csv('../data/chemoPAD-student-annotations-with-flags.csv')
    annotations_df = annotations_df[annotations_df['missing_card'] != True].copy()
    annotations_df['row_id'] = range(len(annotations_df))

    # Load project cards
    project_cards_df = pd.read_csv('../data/project_cards.csv')

    logger.info(f"Loaded {len(annotations_df)} annotations")
    logger.info(f"Loaded {len(project_cards_df)} project cards")

    # Load existing matches if any
    if os.path.exists('../data/matches.json'):
        with open('../data/matches.json', 'r') as f:
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

    # Save matches to file
    with open('../data/matches.json', 'w') as f:
        json.dump(matches, f, indent=2)

    return jsonify({'success': True})

@app.route('/api/export')
def export_data():
    """Export all matched data to CSV"""
    # Create export dataframe
    export_df = annotations_df.copy()

    # Add matched_id column
    export_df['matched_id'] = export_df['row_id'].map(matches)

    # Add project_cards fields for matched rows
    project_fields = ['sample_name', 'quantity', 'camera_type_1', 'deleted', 'date_of_creation']
    for field in project_fields:
        export_df[f'project_{field}'] = None

    # Fill in project data for matched rows
    for row_id, card_id in matches.items():
        if card_id in project_cards_df['id'].values:
            card_data = project_cards_df[project_cards_df['id'] == card_id].iloc[0]
            idx = export_df[export_df['row_id'] == row_id].index[0]

            for field in project_fields:
                if field in card_data:
                    export_df.at[idx, f'project_{field}'] = card_data[field]

    # Remove internal row_id column
    export_df = export_df.drop(columns=['row_id'])

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'../data/chemopad_matched_export_{timestamp}.csv'
    export_df.to_csv(filename, index=False)

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

if __name__ == '__main__':
    load_data()
    # Production server should use gunicorn, not Flask dev server
    app.run(host='0.0.0.0', port=5000, debug=False)