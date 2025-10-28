import streamlit as st
import pandas as pd
from io import BytesIO
import requests
from PIL import Image

# Page config
st.set_page_config(page_title="ChemoPAD Annotation Matcher", layout="wide")

# Initialize session state
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'matches' not in st.session_state:
    st.session_state.matches = {}
if 'edited_annotations' not in st.session_state:
    st.session_state.edited_annotations = {}
if 'edited_dataset' not in st.session_state:
    st.session_state.edited_dataset = {}

# Load data
@st.cache_data
def load_data():
    dataset = pd.read_csv('data/chemoPAD-dataset.csv')
    student = pd.read_csv('data/chemoPAD-student-annotations.csv')
    student['student_row_id'] = range(len(student))
    return dataset, student

dataset_df, student_df = load_data()

# Camera name mapping for fuzzy matching
CAMERA_MAPPING = {
    'nokia': 'HMD Global Nokia 2.3',
    'ipad': 'iPad',
    'pixel': 'Google Pixel 3a',
}

def normalize_camera(camera_value):
    if pd.isna(camera_value):
        return None
    camera_lower = str(camera_value).lower().strip()
    return CAMERA_MAPPING.get(camera_lower, camera_value)

def get_candidate_rows(student_row):
    pad_num = student_row['PAD#']
    candidates = dataset_df[dataset_df['sample_id'] == pad_num].copy()

    if len(candidates) == 0:
        return candidates

    student_camera = normalize_camera(student_row['Camera'])
    if student_camera:
        candidates['camera_match'] = candidates['camera_type_1'].apply(
            lambda x: 1 if str(x) == student_camera else 0
        )
    else:
        candidates['camera_match'] = 0

    candidates = candidates.sort_values('camera_match', ascending=False)
    return candidates

@st.cache_data
def load_image_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        return None
    return None

# Custom CSS for compact layout
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    .stButton button {
        width: 100%;
    }
    div[data-testid="stMetricValue"] {
        font-size: 0.9rem;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
    }
    .candidate-card {
        border: 2px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .candidate-card.selected {
        border-color: #00cc00;
        background-color: #f0fff0;
    }
</style>
""", unsafe_allow_html=True)

# Header with progress
total = len(student_df)
matched = len(st.session_state.matches)

col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
with col1:
    st.title("ChemoPAD Matcher")
with col2:
    st.metric("Progress", f"{matched}/{total}")
with col3:
    progress_pct = int((matched / total) * 100)
    st.metric("Complete", f"{progress_pct}%")
with col4:
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    with nav_col1:
        if st.button("⏮ First"):
            st.session_state.current_index = 0
            st.rerun()
    with nav_col2:
        if st.button("← Prev", disabled=st.session_state.current_index == 0):
            st.session_state.current_index -= 1
            st.rerun()
    with nav_col3:
        if st.button("Next →", disabled=st.session_state.current_index >= total - 1):
            st.session_state.current_index += 1
            st.rerun()

st.markdown("---")

# Get current annotation
current_student = student_df.iloc[st.session_state.current_index]
student_row_id = current_student['student_row_id']
candidates = get_candidate_rows(current_student)

# Main layout: Left side = Annotation, Right side = Candidates
left_col, right_col = st.columns([1, 2])

# LEFT SIDE: Annotation Details & Editing
with left_col:
    st.subheader(f"Annotation #{st.session_state.current_index + 1}")
    st.markdown(f"**PAD#**: `{current_student['PAD#']}`")

    # Check if already matched
    if student_row_id in st.session_state.matches:
        st.success(f"✓ Matched to Dataset ID: {st.session_state.matches[student_row_id]}")

    st.markdown("### Edit Fields")

    # Editable fields - all visible at once
    edited_camera = st.selectbox(
        "Camera",
        options=[None, 'nokia', 'ipad', 'pixel'],
        index=[None, 'nokia', 'ipad', 'pixel'].index(current_student['Camera']) if current_student['Camera'] in ['nokia', 'ipad', 'pixel'] else 0,
        key=f"edit_camera_{student_row_id}"
    )

    edited_lighting = st.selectbox(
        "Lighting",
        options=[None, 'benchtop', 'lightbox', 'no light'],
        index=[None, 'benchtop', 'lightbox', 'no light'].index(current_student['Lighting (lightbox, benchtop, benchtop dark)']) if current_student['Lighting (lightbox, benchtop, benchtop dark)'] in ['benchtop', 'lightbox', 'no light'] else 0,
        key=f"edit_lighting_{student_row_id}"
    )

    edited_background = st.selectbox(
        "Background",
        options=[None, 'black', 'white'],
        index=[None, 'black', 'white'].index(current_student['black/white background']) if current_student['black/white background'] in ['black', 'white'] else 0,
        key=f"edit_background_{student_row_id}"
    )

    edited_api = st.text_input(
        "API",
        value=str(current_student['API']) if pd.notna(current_student['API']) else "",
        key=f"edit_api_{student_row_id}"
    )

    edited_sample = st.text_input(
        "Sample",
        value=str(current_student['Sample']) if pd.notna(current_student['Sample']) else "",
        key=f"edit_sample_{student_row_id}"
    )

    col1, col2 = st.columns(2)
    with col1:
        edited_concentration = st.number_input(
            "mg concentration",
            value=float(current_student['mg concentration (w/w mg/mg or w/v mg/mL)']) if pd.notna(current_student['mg concentration (w/w mg/mg or w/v mg/mL)']) else 0.0,
            format="%.4f",
            key=f"edit_conc_{student_row_id}"
        )
    with col2:
        edited_pct_conc = st.number_input(
            "% Conc",
            value=float(current_student['% Conc']) if pd.notna(current_student['% Conc']) else 0.0,
            format="%.2f",
            key=f"edit_pct_{student_row_id}"
        )

# RIGHT SIDE: Candidate Images
with right_col:
    st.subheader(f"Candidates ({len(candidates)} found)")

    if len(candidates) == 0:
        st.warning(f"No dataset rows found with sample_id = {current_student['PAD#']}")
    else:
        # Get already matched dataset IDs
        already_matched_ids = set(st.session_state.matches.values())

        # Filter out already matched candidates
        available_candidates = candidates[~candidates['id'].isin(already_matched_ids)]

        if len(available_candidates) == 0:
            st.error("⚠️ All candidates for this PAD# have already been matched to other annotations!")
            st.info("Use navigation to review previous matches or skip this annotation.")
        else:
            # Show info about matched candidates
            matched_count = len(candidates) - len(available_candidates)
            if matched_count > 0:
                st.info(f"ℹ️ {matched_count} candidate(s) already matched to other annotations (hidden)")

            # Radio button for selection (only available candidates)
            selected_id = st.radio(
                "Select matching image:",
                options=available_candidates['id'].tolist(),
                format_func=lambda x: f"ID: {x}",
                key=f"select_{student_row_id}",
                index=None,
                horizontal=True
            )

            # Update candidates to only show available ones
            candidates = available_candidates

        st.markdown("---")

        # Display candidates in a compact grid (2 columns)
        for i in range(0, len(candidates), 2):
            cols = st.columns(2)

            for col_idx, (_, candidate) in enumerate(list(candidates.iterrows())[i:i+2]):
                with cols[col_idx]:
                    is_selected = (selected_id == candidate['id'])

                    # Card container
                    if is_selected:
                        st.markdown('<div class="candidate-card selected">', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="candidate-card">', unsafe_allow_html=True)

                    # Image
                    img = load_image_from_url(candidate['url'])
                    if img:
                        st.image(img, width='stretch')
                    else:
                        st.error("Failed to load")

                    # Info
                    st.markdown(f"**ID**: {candidate['id']}")
                    st.markdown(f"**Camera**: {candidate['camera_type_1']}")
                    st.markdown(f"**Sample**: {candidate['sample_name']}")
                    st.markdown(f"**Qty**: {candidate['quantity']}")

                    # Match indicator
                    annotation_camera = normalize_camera(current_student['Camera'])
                    if annotation_camera == candidate['camera_type_1']:
                        st.success("✓ Camera match")

                    st.markdown('</div>', unsafe_allow_html=True)

# Bottom action bar
st.markdown("---")
action_col1, action_col2, action_col3 = st.columns([2, 1, 1])

with action_col1:
    if selected_id:
        if st.button("✓ Confirm Match & Save", type="primary", use_container_width=True):
            # Check if this dataset ID is already matched to a different annotation
            already_matched_ids = set(st.session_state.matches.values())

            if selected_id in already_matched_ids:
                st.error(f"⚠️ Dataset ID {selected_id} is already matched to another annotation!")
            else:
                st.session_state.matches[student_row_id] = selected_id

                # Save edited annotation values
                st.session_state.edited_annotations[student_row_id] = {
                    'Camera': edited_camera,
                    'Lighting': edited_lighting,
                    'Background': edited_background,
                    'API': edited_api,
                    'Sample': edited_sample,
                    'mg_concentration': edited_concentration,
                    'pct_conc': edited_pct_conc
                }

                st.success(f"✓ Saved! Annotation {student_row_id} → Dataset ID {selected_id}")

                # Auto-advance
                if st.session_state.current_index < total - 1:
                    st.session_state.current_index += 1
                    st.rerun()
    else:
        st.info("👆 Select a candidate image above to confirm match")

with action_col2:
    if st.button("Skip", use_container_width=True):
        if st.session_state.current_index < total - 1:
            st.session_state.current_index += 1
            st.rerun()

with action_col3:
    if st.button("Export CSV", use_container_width=True):
        if len(st.session_state.matches) == 0:
            st.warning("No matches to export yet")
        else:
            # Create merged dataframe
            merged_rows = []
            for student_row_id, dataset_id in st.session_state.matches.items():
                student_row = student_df[student_df['student_row_id'] == student_row_id].iloc[0]
                dataset_row = dataset_df[dataset_df['id'] == dataset_id].iloc[0]

                merged_row = {
                    # Dataset fields
                    'id': dataset_row['id'],
                    'sample_id': dataset_row['sample_id'],
                    'sample_name': dataset_row['sample_name'],
                    'quantity': dataset_row['quantity'],
                    'camera_type_1': dataset_row['camera_type_1'],
                    'url': dataset_row['url'],
                    'hashlib_md5': dataset_row['hashlib_md5'],
                    'image_name': dataset_row['image_name'],

                    # Original annotation fields from CSV
                    'annotation_camera_original': student_row['Camera'],
                    'annotation_lighting_original': student_row['Lighting (lightbox, benchtop, benchtop dark)'],
                    'annotation_background_original': student_row['black/white background'],
                    'annotation_api_original': student_row['API'],
                    'annotation_sample_original': student_row['Sample'],
                    'annotation_mg_concentration_original': student_row['mg concentration (w/w mg/mg or w/v mg/mL)'],
                    'annotation_pct_conc_original': student_row['% Conc'],
                }

                # Add edited values if they exist
                if student_row_id in st.session_state.edited_annotations:
                    edited = st.session_state.edited_annotations[student_row_id]
                    merged_row.update({
                        'annotation_camera_edited': edited['Camera'],
                        'annotation_lighting_edited': edited['Lighting'],
                        'annotation_background_edited': edited['Background'],
                        'annotation_api_edited': edited['API'],
                        'annotation_sample_edited': edited['Sample'],
                        'annotation_mg_concentration_edited': edited['mg_concentration'],
                        'annotation_pct_conc_edited': edited['pct_conc'],
                    })
                else:
                    merged_row.update({
                        'annotation_camera_edited': None,
                        'annotation_lighting_edited': None,
                        'annotation_background_edited': None,
                        'annotation_api_edited': None,
                        'annotation_sample_edited': None,
                        'annotation_mg_concentration_edited': None,
                        'annotation_pct_conc_edited': None,
                    })
                merged_rows.append(merged_row)

            merged_df = pd.DataFrame(merged_rows)
            csv = merged_df.to_csv(index=False)

            st.download_button(
                label="📥 Download Merged CSV",
                data=csv,
                file_name="chemoPAD_merged_annotations.csv",
                mime="text/csv",
                use_container_width=True
            )
