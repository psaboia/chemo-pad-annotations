# ChemoPAD Annotation Matcher

Flask-based web interface for matching annotations to dataset entries with visual verification and progress tracking.

## Overview

This tool helps match PAD annotations to the correct dataset entries by:
- Displaying PAD images from the dataset
- Showing candidate matches based on PAD# (sample_id)
- Allowing selection of correct matches with visual verification
- Adding notes and marking unmatched annotations
- Tracking progress across annotations
- Exporting merged CSV with all matched data and notes

## Data Structure

### Dataset CSV (`data/chemoPAD-dataset.csv`)
- 3,609 rows (images)
- 624 unique sample_ids
- Fields: `id`, `sample_id`, `sample_name`, `quantity`, `camera_type_1`, `url`, `hashlib_md5`, `image_name`

### Annotations CSV (`data/chemoPAD-student-annotations.csv`)
- 4,253 rows (annotations)
- 739 unique PAD#s
- Fields: `PAD#`, `Camera`, `Lighting`, `black/white background`, `API`, `Sample`, `mg concentration`, `% Conc`

### Field Mapping
- `sample_id` (dataset) ↔ `PAD#` (annotation)
- `sample_name` (dataset) ↔ `API` (annotation)
- `camera_type_1` (dataset) ↔ `Camera` (annotation)

## Installation

```bash
# Install dependencies
cd flask-app
uv add flask pandas pillow requests
```

## Usage

### 1. Start the Application

```bash
cd flask-app
uv run python -c "import app; app.app.run(host='127.0.0.1', port=5001)"
```

The app will open at **http://localhost:5001**

### 2. Navigate to Your API

1. Open the dashboard
2. Select an API (e.g., "Hydroxyurea (oral)")
3. Click "Enter" to view all annotations for that API
4. See the progress bar showing completion percentage

### 3. Match Annotations

For each annotation:

1. **Click "Edit"** on a row to open the matching interface
2. **Review Annotation Data** (left panel):
   - See the annotation's PAD#, Camera, API, Sample, and concentrations
3. **Review Candidates** (right panel):
   - Scroll through matching candidates from the dataset
   - Look at images to verify matches
4. **Select a Match**:
   - Click the **"Select"** button on the correct candidate
   - The card will turn green with a "✓ Selected" badge
5. **Add Notes** (optional):
   - Type in the Notes field to record observations
   - Click "Save Note" to persist
6. **Mark as No Match** (if applicable):
   - Click **"Mark as No Match"** if no suitable match exists
   - Button turns orange with "✓ No Match"
7. **Save Your Work**:
   - Click **"Save Match"** to record and move to next annotation
   - Or **"Skip"** to skip without saving

### 4. Export Results

When ready to export:

1. Go back to the PAD# List view
2. Click the **"Export"** button at the bottom
3. Download the CSV file

The exported CSV includes:
- All original annotation fields
- `matched_id`: The dataset entry ID (or "no_match" if marked as no match)
- `matched_sample_id`: The dataset sample ID
- Matched dataset information (sample_name, quantity, camera_type, etc.)
- `notes`: Any notes you added
- `missing_card`: Flag for missing dataset entries

## Features

### Automatic Matching
- Filters dataset rows by `sample_id` = `PAD#`
- Candidates sorted by relevance
- Visual preview of matching dataset images

### Visual Verification
- Displays PAD images directly from URLs
- Shows candidate cards with dataset information
- Easy-to-read layout with candidate details

### Annotation Features
- **Select Matches**: Click button to choose correct dataset entry
- **Mark as No Match**: For annotations with no suitable match
- **Add Notes**: Record observations and special cases
- **Session Persistence**: Progress automatically saved

### Progress Tracking
- Dashboard shows completion percentage per API
- Progress bar during annotation matching
- Visual status indicators (Complete, Partial, Not Started)
- Filter annotations by status

### Gallery Views

#### 🔬 Annotation Review Gallery
- **Purpose**: Quality review of PAD annotations organized by lighting conditions
- **Organization**: Groups images by lighting (lightbox, benchtop, no light)
- **Filters**: Lighting, camera type, background, API, match status
- **Features**: Lazy loading, full-size image preview, statistics
- **Use Case**: Review annotation quality across different lighting conditions

#### 📦 Lab Card Inventory
- **Purpose**: Browse and manage all project cards in the laboratory database
- **Organization**: Groups cards by API/drug name
- **Features**:
  - Shows both matched and unmatched cards
  - Hover displays Database ID and PAD ID (sample_id)
  - Quick Match button for direct navigation to matching interface
  - Mark cards with issues and provide descriptions
  - Filter by camera type, match status, and issue status
  - Export filtered results to CSV
- **Use Case**: Manage complete inventory of lab cards and track problematic cards

### Database Features
- **SQLite Database**: Reliable concurrent access with Write-Ahead Logging
- **Automatic Backups**: Created when completing PAD matching and on export
- **Manual Backups**: On-demand backup creation with retention policy
- **Data Integrity**: All operations are atomic and persistent
- **Issue Tracking**: Separate table for tracking cards with problems

## Technical Details

### Architecture

- **Frontend**: HTML/CSS/JavaScript with responsive design
- **Backend**: Flask web framework (Python)
- **Data Storage**:
  - Database: `/database/chemopad.db` (SQLite)
    - `matches` table: Maps annotation rows to dataset entries
    - `notes` table: Stores annotation notes
    - `invalid_cards` table: Tracks cards with issues
    - `backups` table: Records backup history
  - Backup files: `/database/backups/` folder (auto and manual backups)
  - Generated exports: `/exports/` folder (timestamped CSV files)
  - Source data: `/data/` folder (original CSV files)

### Matching Algorithm

1. **Filter by PAD#**: Find all dataset rows where `sample_id` equals the annotation's `PAD#`
2. **Sort by Relevance**: Display best matches first
3. **Visual Verification**: Users review images and information
4. **Manual Selection**: Users click "Select" to confirm match

### Why Manual Matching?

- Multiple images exist per `sample_id` (different cameras, lighting conditions)
- Field values may be incorrect or differ in naming conventions
- Users need visual verification against actual images
- Allows documentation of edge cases and notes

### Data Persistence

- Matches and notes are saved immediately to JSON files
- Progress is preserved across browser sessions
- No data is lost if the browser is closed
- Session folder is excluded from git (`.gitignore`)

## Notes

- Annotations (4,253 rows) exceed dataset entries (3,609 rows)
- Some PAD#s in the annotations CSV may not exist in dataset
- Some dataset rows may have multiple annotations
- Images are loaded from remote URLs (requires internet connection)

## Troubleshooting

**Server not starting**:
- Make sure you're in the `flask-app` directory
- Check that port 5001 is not in use: `lsof -ti:5001`
- Ensure dependencies are installed: `uv add flask pandas pillow requests`

**Images not loading**:
- Check internet connection
- Verify URL accessibility at https://pad.crc.nd.edu/
- Some remote images may be unavailable

**Missing PAD#s**:
- Some PAD#s may not exist in dataset
- Use "Mark as No Match" to document these cases
- Notes are helpful for tracking issues

**Progress lost**:
- Session data is automatically saved to `/session/` folder
- If data is lost, check that the session folder is not deleted
- Matches are saved as soon as "Save Match" is clicked

**Export issues**:
- Make sure `/exports/` folder has write permissions
- Check available disk space
- CSV will include all data from matches.json

## Documentation

### For VM Users
Access the app at: **http://pad-annotation.crc.nd.edu:8080/**

Quick start guide with visual references: **[quick-start.md](docs/quick-start.md)**

This guide covers:
- Step-by-step interface walkthrough
- How to access the app
- Login and authentication
- Quick matching workflow
- Exporting results

### For Development / Local Setup
Detailed user guide: **[user-guide.md](docs/user-guide.md)**

This guide covers:
- How to navigate the interface
- Step-by-step matching process
- Tips for better accuracy
- Common workflows
- Troubleshooting
