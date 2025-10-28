# ChemoPAD Annotation Matcher

Web-based interface for matching student annotations to dataset entries with visual verification.

## Overview

This tool helps students match their PAD annotations to the correct dataset entries by:
- Displaying PAD images from the dataset
- Showing candidate matches based on PAD# (sample_id)
- Allowing verification and editing of both student and dataset fields
- Exporting merged CSV with all fields

## Data Structure

### Dataset CSV (`data/chemoPAD-dataset.csv`)
- 3,609 rows (images)
- 624 unique sample_ids
- Fields: `id`, `sample_id`, `sample_name`, `quantity`, `camera_type_1`, `url`, `hashlib_md5`, `image_name`

### Student Annotations CSV (`data/chemoPAD-student-annotations.csv`)
- 4,253 rows (annotations)
- 739 unique PAD#s
- Fields: `PAD#`, `Camera`, `Lighting`, `black/white background`, `API`, `Sample`, `mg concentration`, `% Conc`

### Field Mapping
- `sample_id` (dataset) ↔ `PAD#` (student)
- `sample_name` (dataset) ↔ `API` (student)
- `camera_type_1` (dataset) ↔ `Camera` (student)

## Installation

```bash
# Initialize project (already done)
uv init

# Install dependencies (already done)
uv add pandas streamlit pillow requests
```

## Usage

### 1. Start the Application

```bash
uv run streamlit run app.py
```

The app will open at http://localhost:8501

### 2. Match Annotations

For each student annotation:

1. **View Student Data**: See the current annotation with PAD#, Camera, Lighting, Background, API, and concentrations
2. **View Candidates**: The app shows all dataset rows with matching `sample_id` (PAD#)
3. **Review Images**: Each candidate displays the actual PAD image
4. **Compare Fields**: Check if Camera, API, etc. match between student and dataset
5. **Edit if Needed**:
   - Expand "Edit Student Annotation" to correct student fields
   - Expand "Edit Dataset Fields" (after selecting) to correct dataset fields
6. **Select Match**: Use radio button to select the correct dataset row
7. **Confirm**: Click "Confirm Match and Save" to record the match
8. **Navigate**: Use Previous/Next buttons or auto-advance after confirming

### 3. Export Results

When matching is complete:

1. Check the progress meter (shows matched/total)
2. Click "Export Merged CSV"
3. Download the merged CSV file

The merged CSV includes:
- All original dataset fields (id, sample_id, sample_name, quantity, camera_type_1, url, hashlib_md5, image_name)
- All student annotation fields (prefixed with `student_`)

## Features

### Automatic Matching
- Filters dataset rows by `sample_id` = `PAD#`
- Fuzzy matches camera names (nokia ↔ HMD Global Nokia 2.3, ipad ↔ iPad, pixel ↔ Google Pixel 3a)
- Prioritizes camera matches in candidate list

### Visual Verification
- Displays PAD images directly from URLs
- Shows images side-by-side with dataset information
- Provides links to view original full-size images

### Editing Capabilities
- Edit student annotations (Camera, Lighting, Background, API, concentrations)
- Edit dataset fields (camera_type_1, sample_name, quantity)
- All edits saved with the match

### Progress Tracking
- Progress bar shows completion percentage
- Counters show matched vs remaining annotations
- Navigation preserves match state

## Technical Details

### Matching Algorithm

1. **Filter by PAD#**: Find all dataset rows where `sample_id` equals the student's `PAD#`
2. **Score by Camera**: Assign higher scores to rows with matching camera types
3. **Sort Candidates**: Display best matches first
4. **Manual Selection**: Student confirms the correct match visually

### Why Manual Matching?

- Multiple images exist per `sample_id` (different cameras, conditions)
- Field values may be incorrect or differ in naming
- Students need to verify against actual images
- Allows correction of both student and dataset errors

### Session State

The app maintains:
- `current_index`: Position in student annotation list
- `matches`: Dictionary of `student_row_id` → `dataset_id` mappings
- `edited_student`: Modified student annotations
- `edited_dataset`: Modified dataset fields

## Notes

- Student annotations (4,253 rows) exceed dataset entries (3,609 rows)
- Some PAD#s in student CSV may not exist in dataset
- Some dataset rows may have multiple student annotations
- Images are loaded from remote URLs (requires internet connection)

## Troubleshooting

**Images not loading**:
- Check internet connection
- Verify URL accessibility at https://pad.crc.nd.edu/

**Missing PAD#s**:
- Some student PAD#s may not exist in dataset
- Skip and note for manual review

**Performance**:
- Large images may load slowly
- Consider reducing image quality if needed
