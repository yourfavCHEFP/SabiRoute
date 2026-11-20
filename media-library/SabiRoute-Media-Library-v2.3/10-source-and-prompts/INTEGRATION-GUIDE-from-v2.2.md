# Integration Guide — SabiRoute Media Library v2.2

## Start here

1. Open `09-chatgpt-generated-boards/03-index/full-library-contact-sheet.jpg` for the full visual inventory.
2. Use `08-index-and-contact-sheet/media-manifest.csv` or `.json` to find each item by ID.
3. Read the relevant notes before using a file. The manifest distinguishes the 26 Nano Banana originals, 38 ChatGPT-generated composite boards, and 9 previously shared reference outputs.

## New: inspect composite board panels separately

Open `09-chatgpt-generated-boards/03-index/cg029-separated-panel-reference-contact-sheet.jpg` or browse `09-chatgpt-generated-boards/04-separated-panel-reference-crops/`. These 12 crops separate the numbered sections of CG-029 for easier review; they do not turn the designs inside each section into standalone exports. Use them to pick a design, then extract/rebuild the selected underlying asset cleanly.

## Recommended safe workflow

1. **Select, do not publish everything.** Keep one canonical logo lockup, one standalone mark, one website hero, one GitHub preview, and only the relevant social variants after human review.
2. **Use boards as art direction.** All ChatGPT-generated images in `09-chatgpt-generated-boards/` are composite boards/infographics. Panels are not separately generated source files; do not crop indiscriminately and claim those crops are original exported assets.
3. **Do not trust embedded claims.** Generated boards may show provider names, features, dashboards, GitHub statistics, issue/fork counts, success-rate percentages, prices, release status, or ML features that have not been verified. Do not publish those claims without confirming them in source/repo evidence.
4. **Architecture:** use the images as visual companions only. Produce actual editable Mermaid/SVG diagrams from the code for definitive documentation.
5. **Logo exports:** the checkerboard background visible in some source images is baked into the pixels. It is not transparency. A canonical vector reconstruction and real transparent exports remain outstanding.
6. **Website hero:** use a selected wide banner as a concept candidate, then verify dimensions, contrast, text-safe space, crop, and mobile behavior. A standalone mobile hero was not delivered in this session.
7. **Motion:** frame panels inside a board are not individual frames. No GIF/MP4 was assembled during this packaging pass.
8. **Milestone infographics:** keep in `09-chatgpt-generated-boards/02-engineering-milestone-infographics/` as draft illustrations. Validate each milestone claim against actual commits/test reports before posting.

## Individual files currently delivered

- 26 original Nano Banana JPEGs plus categorized copies.
- 9 previously shared separate logo/banner reference outputs.
- 38 ChatGPT-generated composite PNG boards.
- Contact sheets, expanded manifest, prompt/provenance notes, and this guide.

## Still outstanding

- Owner selection/approval of canonical brand identity.
- Clean, genuine transparent PNG logo exports and validated editable SVG logo family.
- Standalone mobile hero export.
- Exact source-derived editable architecture/lifecycle/fallback diagrams.
- Engineering validation of architecture and status/metric claims in illustrations.
- Separately generated individual visual assets from composite boards where needed.
- Individually generated animation frames and actual assembled GIF/WebP/MP4 if wanted.

No asset is marked `APPROVED` or `INTEGRATED` just because it is included here. No SabiRoute repository files have been modified.


## v2.2: section-level panels for the full media-board set

Start with `12-separated-reference-panels/README.md`, then browse `12-separated-reference-panels/01-section-level-panels/` (105 reference crops across 14 source boards). The CSV/JSON manifest records available coordinates, output dimensions, hashes, and status. The 290 fine-grained candidates are retained in `12-separated-reference-panels/02-auto-detail-crop-candidates/` as a secondary layer. These are navigation/reference crops, not generated standalone exports. Preserve and compare against originals before using any cropped design.
