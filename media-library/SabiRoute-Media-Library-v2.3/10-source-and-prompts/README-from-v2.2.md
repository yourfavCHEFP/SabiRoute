# SabiRoute Media Library v2.2

A reviewable media package that preserves the uploaded Nano Banana source archive and adds the actual ChatGPT-generated image outputs from this conversation. It separates original artwork, organized copies, composite concept boards, milestone infographics, and previously shared reference outputs.

## Package contents

- `09-chatgpt-generated-boards/04-separated-panel-reference-crops/`: 12 panel crops from the CG-029 board, for easier inspection; these are reference crops, not final standalone assets.


- `00-originals/`: the 26 original JPEGs from the uploaded Nano Banana archive, unchanged.
- `01-brand-and-identity/` through `07-documentation-covers/`: curated/categorized copies of selected Nano Banana originals.
- `08-index-and-contact-sheet/`: combined machine-readable manifest (JSON/CSV) and original 26-image contact sheet.
- `09-chatgpt-generated-boards/01-media-concept-boards/`: 13 ChatGPT-generated composite boards about the brand/media system.
- `09-chatgpt-generated-boards/02-engineering-milestone-infographics/`: 25 ChatGPT-generated engineering/milestone infographics. These are illustrations, not a source of truth.
- `09-chatgpt-generated-boards/03-index/`: contact sheets of ChatGPT boards, prior reference outputs, and the full inventory.
- `10-source-and-prompts/`: prompt/provenance notes and a request-intent log. It explicitly records that verbatim prompt payloads were not available as files.
- `11-previously-shared-reference-outputs/`: 9 separately attached SabiRoute logo/banner images previously supplied in conversation, preserved with provenance limitations.

## Inventory totals

- 26 original Nano Banana JPEGs.
- 38 actual ChatGPT-generated PNG composite boards.
- 9 previously shared SabiRoute reference images.
- 73 catalogued source visuals overall, plus 12 derived reference-panel crops (85 asset records; categorized copies/contact sheets/index files are additional package files).

## New in v2.1: numbered panels are separated for easier review

The 12 numbered sections in `CG-029-wide_cinematic_tech_brand_asset_presentation_portf.png` are now available as separate panel-crop PNGs. See `09-chatgpt-generated-boards/03-index/cg029-separated-panel-reference-contact-sheet.jpg`. This answers “how do I look at the sections separately?” without asking you to crop them by hand. These panel crops are still concept/reference images; for example, the website hero panel includes a mockup and text rather than a clean background, and the app-icon panel does not provide independently validated favicon files.

## Important distinction: boards are not individual assets

Many ChatGPT image-generation responses in this session returned multi-panel concept boards, even when a standalone asset was requested. The files are included for visual review and provenance, but no arbitrary panel cropping was used to falsely create “original” logo, icon, hero, or diagram exports. The standalone mobile hero was not successfully delivered.

## What is and is not production-ready

The library is organized and the archive is integrity-checked, but this does **not** mean all artwork is approved for publication. Logo concepts need canonical selection; JPEG/checkerboard images are not transparent logos; exact architecture diagrams must be source-verified; generated GitHub stats, provider support, dashboards, metrics, features, releases, and live-status claims must not be published without verification. No asset has been integrated into the SabiRoute repository.

## Browse the library

1. Start with `09-chatgpt-generated-boards/03-index/full-library-contact-sheet.jpg` for a quick inventory of all source visuals.
2. Use `08-index-and-contact-sheet/media-manifest.csv` or `.json` to find IDs, filenames, dimensions, checksums, provenance, and review status.
3. Review `INTEGRATION-GUIDE.md` before using anything publicly.
4. Use `10-source-and-prompts/chatgpt-generation-and-provenance.md` for the exact limitations of the generated boards and prompt records.

## No repository integration performed

This ZIP is a handoff package only. No production website, README, application code, or repository paths were changed by packaging these assets.


## v2.2 — section-level extraction for the full media-board set

`12-separated-reference-panels/01-section-level-panels/` provides 105 broad reference crops across 14 source boards. Use this layer first for browsing the compound boards. The previous 290 fine-grained candidates remain preserved under `12-separated-reference-panels/02-auto-detail-crop-candidates/` as a secondary layer because some can be fragmented. Original images and boards remain unchanged; crops are reference-only, not clean standalone exports.
