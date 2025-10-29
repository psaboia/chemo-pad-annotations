# ChemoPAD Annotation Matcher - User Guide

## Overview

The ChemoPAD Annotation Matcher is a web-based interface that helps you match student annotations to dataset entries. You can review candidate matches, add notes, and export the results as a CSV file.

## Getting Started

### Starting the Application

The application should already be running on your system. To access it, open your web browser and go to:

```
http://localhost:5001
```

If the server is not running, start it with:

```bash
cd flask-app
uv run python -c "import app; app.app.run(host='127.0.0.1', port=5001)"
```

## Main Dashboard

When you first open the application, you'll see the **Dashboard** with a list of all available APIs (datasets).

**What you see:**
- API name (e.g., "Hydroxyurea (oral)")
- Total annotations count
- Progress bar showing completion percentage
- "Enter" button to start matching for that API

**How to use:**
1. Select an API you want to work on
2. Click the "Enter" button to view all annotations for that API

## Annotation List

After clicking "Enter" on an API, you'll see the **PAD# List** - all annotations that need to be matched.

**Table columns:**
- **PAD#**: The annotation row number
- **Sample**: Sample information from the student annotation
- **Status**: Shows if the annotation is Complete, Partial, or Not Started
- **Actions**: "Edit" button to start matching

**How to use:**
1. Find an annotation you want to work on
2. Click the "Edit" button to open the matching interface

**Filtering:**
- Use the **Filter** box to search for specific PAD# values
- Use the **Status** dropdown to filter by completion status

## Matching Interface

The matching interface is where you do the main work. It's divided into two sections:

### Left Panel: Annotation Details

Shows the student's annotation data:
- **PAD#**: Row identifier
- Original annotation fields (Camera, Lighting, Background, API, Sample, Concentrations)
- **Notes** text area for adding observations

**Edit Button:**
- Click "Edit" to modify the student annotation data

### Right Panel: Candidate Matches

Shows potential matches from the dataset:
- **Candidate Cards**: Each shows a dataset entry that might match the annotation
- **Card Status**:
  - **Green border + "Selected"**: This is your current selection
  - **Red "Used" badge**: Already matched to another annotation (cannot select)
  - **No badge**: Available to select

**For each candidate:**
- Card image (if available)
- Sample ID and information
- Camera type, quantity, and other details
- **"Select" button**: Click to select this candidate as the match

## How to Make a Match

### Step 1: Review Student Annotation

Look at the left panel and understand what the student annotated:
- Note the PAD#, camera type, API, and sample information

### Step 2: Review Candidates

Scroll through the candidate cards on the right to find a match:
- Compare the visual information (if images are available)
- Check if the camera type matches
- Verify the sample information

### Step 3: Select a Match

Click the **"Select"** button on the matching candidate card.

The card will turn green with a "✓ Selected" badge.

### Step 4: Optional - Add Notes

If you want to add observations or notes:

1. Click in the **Notes** text area on the left
2. Type your observations (e.g., "Image quality confirms match" or "Different camera type but same sample")
3. Click **"Save Note"** to save

### Step 5: Mark as No Match (if applicable)

If there's no matching candidate:

1. Click the **"Mark as No Match"** button at the bottom
2. The button will turn orange and show "✓ No Match"
3. You can still add notes if needed

### Step 6: Save Your Work

Click **"Save Match"** to save your selection.

The page will reload with the next annotation, and your match will be saved to the system.

## Navigation

**Navigate between annotations:**
- **"Save Match"** button: Saves current match and moves to the next annotation
- **"Skip"** button: Skips the current annotation without saving and moves to the next one

**Progress:**
- The progress bar at the top shows your completion percentage
- Check the overall API progress from the dashboard

## Exporting Results

When you're done matching (or want to export your progress):

### From the Annotation List:
1. Go back to the PAD# List view
2. Click the **"Export"** button at the bottom

### What gets exported:
A CSV file with:
- All original student annotation data
- **matched_id**: The dataset entry ID (or "no_match" if marked as no match)
- **matched_sample_id**: The dataset sample ID
- Matched dataset information (sample name, quantity, camera type, etc.)
- **notes**: Any notes you added
- **missing_card**: Flag indicating if the card was in dataset

The file is named: `chemopad_matched_export_YYYYMMDD_HHMMSS.csv`

## Data Storage

Your progress is automatically saved as you work:

- **Session data** (matches and notes) are stored in: `/session/` folder
  - `matches.json`: Your match selections
  - `notes.json`: Your notes

- **Generated exports** are stored in: `/exports/` folder
  - These are your downloaded CSV files with timestamps

## Tips for Better Matching

1. **Always compare images** when available - visual verification is key
2. **Check camera types** - different cameras of the same sample should be similar
3. **Use the zoom/inspect feature** if you need closer inspection of images
4. **Add notes** if there's any ambiguity or special observation
5. **Don't force matches** - if unsure, mark as "No Match" and move on
6. **Review before exporting** - make sure your matches look reasonable

## Common Issues

### Image not loading?
- Check your internet connection
- The images are loaded from the remote server, so connectivity is required

### Can't select a candidate?
- Check if it has a red "Used" badge - that means it's already matched to another annotation
- Only one annotation can match to each dataset entry

### Want to change a previous match?
- Go back to that annotation in the list
- Select a different candidate or mark as "No Match"
- Click "Save Match" to update

### Lost your progress?
- Your session is automatically saved
- Refresh the page to see your latest work
- Check the session folder if needed

## Getting Help

If you encounter issues:
1. Check the notes from your previous session
2. Review the exported CSV to see patterns in matches
3. Contact the system administrator for technical support

---

**Version**: Flask-based interface
**Last Updated**: October 2025
