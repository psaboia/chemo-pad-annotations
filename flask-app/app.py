from flask import Flask, render_template, jsonify, request, send_file, session, redirect, url_for
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import logging
from functools import wraps
from werkzeug.middleware.proxy_fix import ProxyFix
import markdown

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'chemopad-secret-key-2024')

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # 30 minute timeout
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Get password from environment variable
PASSWORD = os.environ.get('CHEMOPAD_PASSWORD', 'chemopad2024')

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
matches = {}
notes = {}  # Store notes for each annotation  # {annotation_row_id: project_card_id}

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)

        if 'authenticated' not in session or not session['authenticated']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
    student_work_dir = os.path.join(base_dir, 'session')
    matches_file = os.path.join(student_work_dir, 'matches.json')
    if os.path.exists(matches_file):
        with open(matches_file, 'r') as f:
            global matches
            matches = json.load(f)
            # Convert keys to int, handle "no_match" special value
            matches = {int(k): (v if v == "no_match" else v) for k, v in matches.items()}

    # Load existing notes if any
    notes_file = os.path.join(student_work_dir, 'notes.json')
    if os.path.exists(notes_file):
        with open(notes_file, 'r') as f:
            global notes
            notes = json.load(f)
            # Convert keys to int
            notes = {int(k): v for k, v in notes.items()}

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with password authentication"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == PASSWORD:
            session['authenticated'] = True
            session.permanent = True
            logger.info("User successfully authenticated")
            return redirect(url_for('dashboard'))
        else:
            logger.warning("Failed login attempt")
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('login'))

@app.route('/help')
@login_required
def help():
    """Display help page from quick-start.md"""
    try:
        import re
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        help_file = os.path.join(base_dir, 'docs', 'quick-start.md')

        with open(help_file, 'r') as f:
            content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])

        # Rewrite image paths from 'figs/...' to '/static/img/help/...'
        html_content = re.sub(r'src="figs/([^"]+)"', r'src="/static/img/help/\1"', html_content)

        return render_template('help.html', content=html_content)
    except Exception as e:
        logger.error(f"Error loading help content: {e}")
        return render_template('help.html', content='<p>Help content not available</p>')

@app.route('/')
@login_required
def dashboard():
    """API Dashboard - Level 1"""
    # Group by API
    api_stats = []

    for api in annotations_df['API'].unique():
        if pd.isna(api):
            continue

        api_data = annotations_df[annotations_df['API'] == api]
        unique_pads = api_data['PAD#'].unique()

        # Count completed PAD#s (all rows for that PAD# are matched or marked as no_match)
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
@login_required
def pad_list(api_name):
    """PAD# List for specific API - Level 2"""
    # Reload matches from file to get latest data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_file = os.path.join(base_dir, 'session', 'matches.json')
    if os.path.exists(matches_file):
        with open(matches_file, 'r') as f:
            global matches
            matches = json.load(f)
            # Convert keys to int
            matches = {int(k): v for k, v in matches.items()}

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
@login_required
def match_page(api_name, pad_num):
    """Annotation Matching page - Level 3"""
    # Reload matches from file to get latest data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_file = os.path.join(base_dir, 'session', 'matches.json')
    if os.path.exists(matches_file):
        with open(matches_file, 'r') as f:
            global matches
            matches = json.load(f)
            # Convert keys to int
            matches = {int(k): v for k, v in matches.items()}

    # Reload notes from file to get latest data
    notes_file = os.path.join(base_dir, 'session', 'notes.json')
    if os.path.exists(notes_file):
        with open(notes_file, 'r') as f:
            global notes
            notes = json.load(f)
            # Convert keys to int
            notes = {int(k): v for k, v in notes.items()}

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

    # Prepare annotation rows with their matches and notes
    rows_data = []
    for idx, row in pad_annotations.iterrows():
        row_dict = row.to_dict()
        row_id = row['row_id']
        matched_id = matches.get(row_id)
        row_dict['matched_id'] = matched_id if matched_id != "no_match" else None
        row_dict['is_no_match'] = matched_id == "no_match"
        row_dict['notes'] = notes.get(row_id, '')
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
@login_required
def save_match():
    """Save a match between annotation row and project card"""
    # Reload matches from file first to avoid overwriting in multi-worker environment
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    student_work_dir = os.path.join(base_dir, 'session')
    matches_file = os.path.join(student_work_dir, 'matches.json')

    global matches
    if os.path.exists(matches_file):
        with open(matches_file, 'r') as f:
            matches = json.load(f)
            # Convert keys to int, handle "no_match" special value
            matches = {int(k): (v if v == "no_match" else v) for k, v in matches.items()}

    data = request.json
    row_id = int(data['row_id'])
    card_id = data.get('card_id')
    is_no_match = data.get('is_no_match', False)

    # Convert card_id to int if it's not None/empty and not a special value
    if card_id and card_id != "no_match":
        card_id = int(card_id)
        # Check if card_id is already used by another annotation
        if card_id in matches.values():
            return jsonify({'success': False, 'error': 'ID already matched to another annotation'})
        matches[row_id] = card_id
    elif is_no_match:
        # Mark as no match
        matches[row_id] = "no_match"
    elif row_id in matches:
        # Unmatching
        del matches[row_id]

    # Save matches to file
    # Create session directory if it doesn't exist
    if not os.path.exists(student_work_dir):
        os.makedirs(student_work_dir)

    with open(matches_file, 'w') as f:
        json.dump(matches, f, indent=2)

    return jsonify({'success': True})

@app.route('/api/save_note', methods=['POST'])
@login_required
def save_note():
    """Save notes for an annotation row"""
    # Reload notes from file first to avoid overwriting in multi-worker environment
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    student_work_dir = os.path.join(base_dir, 'session')
    notes_file = os.path.join(student_work_dir, 'notes.json')

    global notes
    if os.path.exists(notes_file):
        with open(notes_file, 'r') as f:
            notes = json.load(f)
            # Convert keys to int
            notes = {int(k): v for k, v in notes.items()}

    data = request.json
    row_id = int(data['row_id'])
    note_text = data.get('note', '')

    if note_text:
        notes[row_id] = note_text
    elif row_id in notes:
        # Delete note if empty
        del notes[row_id]

    # Save notes to file
    # Create session directory if it doesn't exist
    if not os.path.exists(student_work_dir):
        os.makedirs(student_work_dir)

    with open(notes_file, 'w') as f:
        json.dump(notes, f, indent=2)

    return jsonify({'success': True})

@app.route('/api/export')
@login_required
def export_data():
    """Export all matched data to CSV"""
    # Reload notes and matches from files to get latest data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Reload matches
    matches_file = os.path.join(base_dir, 'session', 'matches.json')
    global matches
    if os.path.exists(matches_file):
        with open(matches_file, 'r') as f:
            matches = json.load(f)
            matches = {int(k): v for k, v in matches.items()}

    # Reload notes
    notes_file = os.path.join(base_dir, 'session', 'notes.json')
    global notes
    if os.path.exists(notes_file):
        with open(notes_file, 'r') as f:
            notes = json.load(f)
            notes = {int(k): v for k, v in notes.items()}

    # Load ALL annotations including those with missing_card=True
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

    # Add notes column for student observations
    export_df['notes'] = None

    # Fill in project data for matched rows (only for rows with missing_card=False)
    for row_id, card_id in matches.items():
        if card_id == "no_match":
            # For no_match annotations, still add the notes
            orig_idx = matchable_df[matchable_df['row_id'] == row_id].index[0]
            if row_id in notes:
                export_df.at[orig_idx, 'notes'] = notes[row_id]
            export_df.at[orig_idx, 'matched_id'] = "no_match"
        elif card_id in project_cards_df['id'].values:
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

            # Add notes if any
            if row_id in notes:
                export_df.at[orig_idx, 'notes'] = notes[row_id]

    # Add notes for rows that have notes but aren't in matches
    # This handles annotations with notes that haven't been matched or marked as no_match yet
    for row_id, note_text in notes.items():
        if row_id not in matches:
            # Find the original index for this row_id
            matching_rows = matchable_df[matchable_df['row_id'] == row_id]
            if len(matching_rows) > 0:
                orig_idx = matching_rows.index[0]
                export_df.at[orig_idx, 'notes'] = note_text

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
                # Check if value is "no_match" - special case to preserve
                if x == "no_match":
                    return "no_match"
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
    exports_dir = os.path.join(base_dir, 'exports')

    # Create exports directory if it doesn't exist
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)

    filename = os.path.join(exports_dir, f'chemopad_matched_export_{timestamp}.csv')

    # Export to CSV with special handling to preserve integer format
    # Use float_format to prevent .0 decimals, but since we converted to strings, this shouldn't be needed
    export_df.to_csv(filename, index=False, na_rep='')

    return send_file(filename, as_attachment=True, download_name=f'chemopad_export_{timestamp}.csv')

@app.route('/api/stats')
@login_required
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