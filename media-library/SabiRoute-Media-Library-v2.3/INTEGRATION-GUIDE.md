# SabiRoute Media Library v2.3 — Integration Guide

## What changed
This version preserves every file from v2.2 and adds a deterministic, independently exported production-assets pack under `13-production-assets/`. Most new assets have editable SVG masters and PNG derivatives.

## Start with these
- `13-production-assets/01-logo-family/`: reconstructed editable logo variants and raster derivatives. These are proposed identity exports, not owner-approved canonical trademarks.
- `13-production-assets/02-app-icons/`: icon size variants. Review visual mark before adoption; small favicons should be tested at their actual display sizes.
- `13-production-assets/03-website/`: separate wide desktop and portrait mobile hero backgrounds with no embedded marketing copy, plus six standalone feature cards.
- `13-production-assets/04-github-readme/`: GitHub share preview, README hero, and quickstart companion visual.
- `13-production-assets/05-technical-diagrams/`: diagrams clearly labelled reference/source-derived. The supplied `SabiRoute-main.zip` snapshot is not guaranteed to equal the current working tree; re-verify before claiming exact current runtime behavior.
- `13-production-assets/06-documentation-covers/`: eight reusable editorial covers.
- `13-production-assets/07-social-media/`: eight standalone announcement cards, LinkedIn banner, and seven carousel slides. Claims must be checked before publication.
- `13-production-assets/08-motion-and-gifs/`: twelve stable-composition frames and an assembled GIF; deterministic processing was used, not video generation.
- `13-production-assets/09-video-production/`: ten individual 1920×1080 stills and a lower-third overlay.

## Technical truth and limitations
The diagrams are intentionally labeled as references where the archive does not establish the current runtime state. The supplied source archive includes a README that frames architecture as a target design and a router snapshot that selects the first available, non-attempted healthy candidate; its `intelligence/scorer.py` file was empty in that archive. Therefore this media package does not claim the scoring formula is implemented in that source snapshot. Confirm any later implementation against the current repo before replacing diagram labels or publishing exact architecture diagrams.

The new logo family was reconstructed as original editable vector artwork following the existing SabiRoute visual direction; it was not pixel-traced from the JPG boards. Its apparent transparency comes from the SVG/PNG canvas and should be tested in target applications. A generated image or reference crop does not establish alpha transparency by itself.

## Status semantics
- `EXPORTED`: a real file exists in this package.
- `VALIDATED`: structural/package checks passed; this does not mean the owner approved the design or the technical claims.
- `APPROVED` and `INTEGRATED`: not automatically granted by this pipeline.

## Suggested usage
Use standalone logo/icon exports only after owner selection. Place hero background behind live HTML text and controls, not in place of accessible DOM text. Embed exact architecture diagrams as editable SVG only after engineering review. Use social/video templates after fact-checking all statements. Preserve v2.2 reference boards as original visual direction.
