# Separated Reference Panels — SabiRoute Media Library v2.2

This package has two crop levels for the composite media boards.

## Recommended first stop: section-level panels
- `01-section-level-panels/by-board/<BOARD-ID>/`: 105 broad section-level reference crops across 14 boards.
- `01-section-level-panels/index/section-panel-manifest.csv` and `.json`: crop inventory, known coordinates, file dimensions, hashes, and review status.
- `01-section-level-panels/index/contact-sheets/`: paginated master previews.
- Every board folder contains a contact sheet.

## Secondary detail candidates
- `02-auto-detail-crop-candidates/by-board/<BOARD-ID>/`: 290 finer crop candidates from the earlier segmentation pass.
- `02-auto-detail-crop-candidates/index/detail-crop-candidate-manifest.csv` and `.json`: detailed crop metadata.
- `02-auto-detail-crop-candidates/index/contact-sheets/`: existing fine-crop contact sheets.

The section-level layer is intended to make boards easier to browse; it can still contain multiple designs in one crop. The fine-crop layer is secondary because some regions are fragments. Neither layer should be represented as independently generated, approved, or integrated assets.

## Preservation and limitations
- All 13 ChatGPT media concept boards and Nano Banana board NB-013 are covered.
- CG-029 uses 12 previously curated numbered-section crops.
- All original source images and boards remain unchanged.
- The 25 ChatGPT engineering/milestone infographics remain whole, as do coherent technical diagrams/flowboards such as NB-014, NB-015, and NB-018.
- Logo panels are not clean transparent logo exports. Website mockups are not clean hero backgrounds. Architecture illustrations require source-code verification. Embedded GitHub counts, metrics, provider lists, release, live-status and ML claims are not facts without independent verification.
