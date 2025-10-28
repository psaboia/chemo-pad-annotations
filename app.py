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

    # Add index to student data for tracking
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
    """Normalize camera names for comparison"""
    if pd.isna(camera_value):
        return None
    camera_lower = str(camera_value).lower().strip()
    return CAMERA_MAPPING.get(camera_lower, camera_value)

def get_candidate_rows(student_row):
    """Find candidate dataset rows for a student annotation"""
    pad_num = student_row['PAD#']

    # Filter by PAD# = sample_id
    candidates = dataset_df[dataset_df['sample_id'] == pad_num].copy()

    if len(candidates) == 0:
        return candidates

    # Add score for matching camera
    student_camera = normalize_camera(student_row['Camera'])
    if student_camera:
        candidates['camera_match'] = candidates['camera_type_1'].apply(
            lambda x: 1 if str(x) == student_camera else 0
        )
    else:
        candidates['camera_match'] = 0

    # Sort by camera match
    candidates = candidates.sort_values('camera_match', ascending=False)

    return candidates

def load_image_from_url(url):
    """Load and display image from URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        st.error(f"Error loading image: {e}")
    return None

# Header
st.title("ChemoPAD Annotation Matcher")
st.markdown("Match annotations to dataset entries and verify/edit information")

# Progress
total_students = len(student_df)
matched_count = len(st.session_state.matches)
st.progress(matched_count / total_students, text=f"Progress: {matched_count}/{total_students} matched")

# Navigation
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    if st.button("← Previous", disabled=st.session_state.current_index == 0):
        st.session_state.current_index -= 1
        st.rerun()

with col2:
    st.write(f"Annotation {st.session_state.current_index + 1} of {total_students}")

with col3:
    if st.button("Next →", disabled=st.session_state.current_index >= total_students - 1):
        st.session_state.current_index += 1
        st.rerun()

# Current student row
current_student = student_df.iloc[st.session_state.current_index]
student_row_id = current_student['student_row_id']

# Get candidate dataset rows
candidates = get_candidate_rows(current_student)

st.divider()

# Display annotation
st.subheader("Annotation Details")
st.markdown(f"**PAD#**: {current_student['PAD#']}")

# Editable annotation fields
with st.expander("Edit Annotation", expanded=False):
    edited_camera = st.selectbox(
        "Camera",
        options=['nokia', 'ipad', 'pixel', None],
        index=['nokia', 'ipad', 'pixel', None].index(current_student['Camera']) if current_student['Camera'] in ['nokia', 'ipad', 'pixel'] else 3,
        key=f"edit_camera_{student_row_id}"
    )

    edited_lighting = st.selectbox(
        "Lighting",
        options=['benchtop', 'lightbox', 'no light', None],
        index=['benchtop', 'lightbox', 'no light', None].index(current_student['Lighting (lightbox, benchtop, benchtop dark)']) if current_student['Lighting (lightbox, benchtop, benchtop dark)'] in ['benchtop', 'lightbox', 'no light'] else 3,
        key=f"edit_lighting_{student_row_id}"
    )

    edited_background = st.selectbox(
        "Background",
        options=['black', 'white', None],
        index=['black', 'white', None].index(current_student['black/white background']) if current_student['black/white background'] in ['black', 'white'] else 2,
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

# Display annotation info (read-only view)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Camera", current_student['Camera'] if pd.notna(current_student['Camera']) else "N/A")
with col2:
    st.metric("Lighting", current_student['Lighting (lightbox, benchtop, benchtop dark)'] if pd.notna(current_student['Lighting (lightbox, benchtop, benchtop dark)']) else "N/A")
with col3:
    st.metric("Background", current_student['black/white background'] if pd.notna(current_student['black/white background']) else "N/A")
with col4:
    st.metric("API", current_student['API'] if pd.notna(current_student['API']) else "N/A")
with col5:
    st.metric("Sample", current_student['Sample'] if pd.notna(current_student['Sample']) else "N/A")

col1, col2 = st.columns(2)
with col1:
    conc_val = current_student['mg concentration (w/w mg/mg or w/v mg/mL)']
    if pd.notna(conc_val):
        try:
            st.metric("mg concentration", f"{float(conc_val):.4f}")
        except:
            st.metric("mg concentration", str(conc_val))
    else:
        st.metric("mg concentration", "N/A")
with col2:
    pct_val = current_student['% Conc']
    if pd.notna(pct_val):
        try:
            st.metric("% Conc", f"{float(pct_val):.2f}")
        except:
            st.metric("% Conc", str(pct_val))
    else:
        st.metric("% Conc", "N/A")

st.divider()

# Display candidate matches
st.subheader(f"Candidate Dataset Rows ({len(candidates)} found)")

if len(candidates) == 0:
    st.warning(f"No dataset rows found with sample_id = {current_student['PAD#']}")
else:
    # Allow selection
    selected_id = st.radio(
        "Select the matching dataset row:",
        options=candidates['id'].tolist(),
        format_func=lambda x: f"ID: {x}",
        key=f"select_{student_row_id}",
        index=None
    )

    st.divider()

    # Display candidates with images
    for idx, (_, candidate) in enumerate(candidates.iterrows()):
        is_selected = (selected_id == candidate['id'])

        with st.container(border=True):
            if is_selected:
                st.success(f"✓ SELECTED - Dataset ID: {candidate['id']}")
            else:
                st.write(f"Dataset ID: {candidate['id']}")

            # Two columns: image and info
            col1, col2 = st.columns([1, 2])

            with col1:
                st.write("**Image:**")
                img = load_image_from_url(candidate['url'])
                if img:
                    st.image(img, width='stretch')
                else:
                    st.error("Failed to load image")
                st.caption(f"[View original]({candidate['url']})")

            with col2:
                st.write("**Dataset Information:**")
                info_col1, info_col2 = st.columns(2)

                with info_col1:
                    st.write(f"**ID**: {candidate['id']}")
                    st.write(f"**sample_id**: {candidate['sample_id']}")
                    st.write(f"**sample_name**: {candidate['sample_name']}")
                    st.write(f"**quantity**: {candidate['quantity']}")

                with info_col2:
                    st.write(f"**camera_type_1**: {candidate['camera_type_1']}")

                    # Highlight camera match
                    annotation_camera = normalize_camera(current_student['Camera'])
                    if annotation_camera == candidate['camera_type_1']:
                        st.success("✓ Camera matches annotation")
                    else:
                        st.warning(f"Camera differs (annotation: {current_student['Camera']})")

                # Allow editing dataset fields
                if is_selected:
                    with st.expander("Edit Dataset Fields", expanded=False):
                        new_camera = st.selectbox(
                            "camera_type_1",
                            options=['iPad', 'HMD Global Nokia 2.3', 'Google Pixel 3a', 'unknown'],
                            index=['iPad', 'HMD Global Nokia 2.3', 'Google Pixel 3a', 'unknown'].index(candidate['camera_type_1']) if candidate['camera_type_1'] in ['iPad', 'HMD Global Nokia 2.3', 'Google Pixel 3a', 'unknown'] else 3,
                            key=f"dataset_camera_{candidate['id']}"
                        )

                        new_sample_name = st.text_input(
                            "sample_name",
                            value=str(candidate['sample_name']),
                            key=f"dataset_name_{candidate['id']}"
                        )

                        new_quantity = st.number_input(
                            "quantity",
                            value=int(candidate['quantity']) if pd.notna(candidate['quantity']) else 0,
                            key=f"dataset_qty_{candidate['id']}"
                        )

st.divider()

# Confirm match button
if selected_id:
    if st.button("✓ Confirm Match and Save", type="primary"):
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

        st.success(f"Match saved! Annotation row {student_row_id} → Dataset ID {selected_id}")

        # Auto-advance to next
        if st.session_state.current_index < total_students - 1:
            st.session_state.current_index += 1
            st.rerun()
else:
    st.info("Select a dataset row above to confirm the match")

# Show matched status
if student_row_id in st.session_state.matches:
    st.info(f"This annotation is already matched to Dataset ID: {st.session_state.matches[student_row_id]}")

st.divider()

# Export section
st.subheader("Export Merged Data")
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Matched", len(st.session_state.matches))
with col2:
    st.metric("Remaining", total_students - len(st.session_state.matches))

if st.button("Export Merged CSV"):
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
                # No edits made, set edited columns to None or same as original
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

        # Convert to CSV
        csv = merged_df.to_csv(index=False)

        st.download_button(
            label="Download Merged CSV",
            data=csv,
            file_name="chemoPAD_merged_annotations.csv",
            mime="text/csv"
        )

        st.success(f"Ready to download {len(merged_rows)} matched rows!")
