# Downloads Organizer

This script helps clean the top level of `~/Downloads` and gives ADHD-related patient files their own destination inside `~/Developer`.

Default target:

- `~/Developer/downloads_organized/health/adhd/patient_exports/YYYY-MM/` for ADHD-related `.enc` and `.enc.txt`
- `~/Developer/downloads_organized/health/other_patient_exports/YYYY-MM/` for non-ADHD `.enc` and `.enc.txt`
- `~/Developer/downloads_organized/health/adhd/forms_and_reports/YYYY-MM/` for ADHD-related HTML, PDF, DOCX, CSV, TXT, and similar files
- Other files are grouped into folders like `documents`, `images`, `archives`, `apps_and_installers`, and `misc`

ADHD matching is intentionally conservative:

- Only files dated `2025-12` or later are sorted into ADHD-specific folders.
- ADHD patient exports must be encrypted files whose names match the current toolkit export names: `ASRS_`, `Wender_Scale_`, `BRIEF_A_`, `Behaviour_Self_`, `Behaviour_Parent_`, or `Behaviour_Informant_`.
- Older or non-matching `.enc` / `.enc.txt` files go to `health/other_patient_exports/YYYY-MM/` for manual review instead of being assumed to belong to this toolkit.
- Broader ADHD-like documents dated before `2025-12` stay in ordinary document/folder buckets.

## Safe first run

```bash
npm run organize:downloads
```

That is a dry run. It only shows what would move.

## Move files for real

```bash
npm run organize:downloads -- --apply
```

## Include folders too

By default, only top-level files are moved. If you also want top-level folders moved:

```bash
npm run organize:downloads -- --apply --include-directories
```

## Use a different target

```bash
node organize_downloads.mjs --target ~/Developer/patient-downloads
```

## Notes

- The script scans only the top level of the source folder, which keeps it safer for a busy Downloads folder.
- Hidden files and symlinks are skipped.
- If a destination filename already exists, the script adds ` (2)`, ` (3)`, and so on.

## Test the organizer rules

```bash
npm run test:organize-downloads
```
