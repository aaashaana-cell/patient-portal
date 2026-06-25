# ADHD Tool Handoff Context

## Current workspace

- Current project folder was originally: `/Users/shanuakshah/Downloads/files (3)`
- Intended new home: `/Users/shanuakshah/Developer/files (3)`

## What this tool does

This is an ADHD assessment toolkit with:

- a clinician-only HTML tool used to import patient response exports and compute derived scoring
- patient-facing HTML forms that export raw encrypted response files such as `.enc` and `.enc.txt`
- optional printable PDF and printable HTML versions of the forms

The active workflow is documented in `00_START_HERE/README_WORKFLOW.md`.

## Main workflow

1. Share a patient form from `00_START_HERE/2_SHARE_WITH_PATIENTS_RAW_ENC/`
2. Patient completes the form and sends back an exported `.enc` or `.enc.txt`
3. Open the clinician tool from `00_START_HERE/1_CLINICIAN_ONLY/`
4. Import the patient export into the clinician tool
5. The clinician tool recalculates derived ADHD scoring on import

## Important folders

- `00_START_HERE/1_CLINICIAN_ONLY/`
  - clinician HTML tool
  - `adhd_shared_scoring.js`
- `00_START_HERE/2_SHARE_WITH_PATIENTS_RAW_ENC/`
  - raw-response patient forms to share
- `00_START_HERE/3_OPTIONAL_PRINTABLE_PDFS/`
  - printable PDFs
- `00_START_HERE/4_OPTIONAL_PRINTABLE_HTML/`
  - printable HTML
- `ARCHIVE_OLD/`
  - older versions and backups
- `output/`
  - generated output assets
- `tmp/`
  - temporary files and generated scratch data

## Stack

- plain HTML for the main tool and forms
- JavaScript
- Node.js scripts in `.mjs`
- `npm` project with `playwright` as a dev dependency

Key root files:

- `package.json`
- `adhd_shared_scoring.js`
- `adhd_tool_logic_tests.mjs`
- `generate_printable_pdfs.mjs`
- `generate_static_pdfs.mjs`
- `build_single_file_patient_forms.mjs`

## What we worked on in this chat

- inspected the workspace and existing ADHD folder structure
- added a Downloads organizer script: `organize_downloads.mjs`
- added usage notes: `DOWNLOADS_ORGANIZER.md`
- added `npm run organize:downloads`
- ran the organizer on the real `~/Downloads`
- moved many top-level Downloads items into `~/Developer/downloads_organized`

## Important caveat discovered

The ADHD organizer matched older ADHD-like filenames from before the ADHD tool workflow actually started being used. You mentioned that this workflow only really started around December 2025, so ADHD-like files older than `2025-12` may be unrelated historical material rather than outputs of this tool.

Because of that, the older ADHD-like matches in:

- `~/Developer/downloads_organized/health/adhd/forms_and_reports/`

should be treated cautiously, especially anything before `2025-12`.

## Current organizer behavior

`organize_downloads.mjs`:

- scans the top level of `~/Downloads`
- moves ADHD patient exports into `health/adhd/patient_exports/YYYY-MM/`
- moves ADHD-like reports/forms into `health/adhd/forms_and_reports/YYYY-MM/`
- moves non-ADHD `.enc` files into `health/other_patient_exports/YYYY-MM/`
- groups other files by general category and month

## Known stale files (do not use)

- `00_START_HERE/1_CLINICIAN_ONLY/adhd_assessment_tool_with_dev_history (3).html` — older buggy clinician tool (wrong RAADS-R subscale maxes, total 194). Use `(4).html`.
- Repo-root `adhd_shared_scoring.js` — stale copy missing the RAADS-R engine block. The complete engine is `00_START_HERE/1_CLINICIAN_ONLY/adhd_shared_scoring.js`, which is what the clinician tools actually load. The root copy is gitignored and unpublished.
- Both clinician tools (`(4).html` ADHD and `asd_clinician_tool.html`) recompute RAADS-R from raw responses via the same `getSharedScoringEngine().raadsr.calculateScores()`, so they produce identical scores (verified: max vector = 240; subscales 117/42/21/60).
- If a tool's on-screen RAADS-R labels look old (0-97 / 0-42 / 0-13), that's a cached browser render — hard-refresh; the file is correct.

## Recommended next improvements

- add a date cutoff so ADHD matching only applies from `2025-12` onward
- optionally add a stricter ADHD export rule tied to known filenames produced by these specific forms
- optionally add a separate mode that only organizes `.enc` and `.enc.txt` patient exports without touching broader ADHD reference files
