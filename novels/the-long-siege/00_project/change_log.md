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
