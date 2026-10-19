# Change Log

## 2026-10-19 — full first draft complete
- All 25 chapters drafted (104,212 words measured); scene breaks, Mature/18+ content per creative contract.
- Canon YAMLs filled: rules, characters, relationships, story_engine, timeline, chapter_toc, foreshadowing, reader_promises, character_arcs, plotlines, pacing_ledger, pov_voices.
- rolling.md continuity entries completed through Ch.25.
- PDF deliverable built with build/build_pdf.py: 471 pages, embedded DejaVu Serif faces incl. renamed synthetic obliques, running heads, body-relative folios, auto TOC, drop caps.
- Style sweep: zero banned phrases; em-dash rule (max one per paragraph) enforced across all chapters.

## 2026-10-19 — illuminated-manuscript redesign
- Rebuilt the PDF as an illuminated manuscript: parchment ground, gold hairline frames with corner diamonds, gilded chapter initials on alternating crimson/ultramarine grounds, vine corner borders (title + part dividers), floral fleuron scene breaks, floral rules, gilt char-spaced display type, and a FINIS mark.
- Added a period frontispiece miniature (build/assets/frontispiece.jpg) in a double-rule gilt frame on its own unframed page.
- Three part dividers added (Part the First/Second/Third) with large gilt Roman numerals and two-line titles.
- Running heads now suppressed on chapter opener pages via a dedicated body_opener page template; folios restart at 1 at Chapter 1 and are flanked by diamonds.
- ReportLab 5 compatibility: char spacing via PDF text objects; multiBuild template-cycle leak cleared in handle_documentBegin; display type auto-fits long chapter titles to the measure.
- Builder (build/build_pdf.py) and synthetic-oblique font generator (build/make_oblique_fonts.py) made reproducible; oblique fonts renamed internally so all four serif faces embed.
- Removed one duplicated adjacent scene break in chapter 21; builder now defensively collapses any consecutive break blocks.
- Verified: 446 physical pages, 439 body folios, all 25 titles and chapter endings intact, 140 scene markers mapped to fleurons, no blank pages, no margin overflows, oblique faces drawn.

## 2026-10-19 — illustration program begun
- 25-plate program defined (build/illustrations/manifest.yaml): one painterly romantic-academic oil plate per chapter, shared style anchor and verbatim character descriptors for consistency, strict 1480s historical accuracy, no text in art.
- Plates ch01-ch10 generated (1376x768 landscape); builder integrates existing plates into chapter openers under gilt double-rule frames and gracefully skips missing ones.
- PDF rebuilt: 448 pages, openers with plates verified visually; no-plate fallback verified.
- Pending: ch07 regen for canon gown color (steel-grey gown + red velvet mantle), then ch11-ch25 generation across subsequent turns (10-image per-turn limit).

## 2026-10-19 — illustration program complete
- All 25 chapter plates generated (build/illustrations/ch01-ch25.jpg), uniform 1376x768 landscape, romantic academic 19th-century salon oil style matching the reference set, no in-art text.
- Consistency controls: verbatim recurring descriptors for Jeanne (dark braided hair, linen veil, grey eyes) and Thiébaut (lean, sandy hair, trimmed beard); Vauréal red-and-silver and Lorraine blue-and-white heraldry; strict 1480s arms, costume, and architecture.
- Canon correction: ch07 regenerated to the steel-grey silver-embroidered gown with red velvet miniver-lined mantle; ch11 softened to a reverent burial procession after an initial moderation block.
- Every chapter opener now carries its gilt-framed plate between the floral title rule and the illuminated initial; builder skips missing plates gracefully.
- Final PDF: 453 physical pages, 446 body folios, 26 embedded images (frontispiece + 25 plates); full verification passed (all titles/endings, no blank pages, no margin overflow, folios restart at 1, three serif faces embedded).
