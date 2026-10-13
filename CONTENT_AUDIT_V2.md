# Mochi Hangul V2 content audit

## TOPIK vocabulary update

The six supplied vocabulary PDFs contain 5,666 numbered entries for TOPIK levels 1–6. One source row (level 4, source number 3755) contains only the continuation of the previous English definition and has no Korean headword, so it is recorded in `skipped_source_records` and does not create a duplicate or empty card.

| Pack | Source entries | Review cards |
|---|---:|---:|
| TOPIK 1 | 1,000 | 1,000 |
| TOPIK 2 | 1,000 | 1,000 |
| TOPIK 3 | 1,000 | 1,000 |
| TOPIK 4 | 1,000 | 999 |
| TOPIK 5 | 1,000 | 1,000 |
| TOPIK 6 | 666 | 666 |
| **Total** | **5,666** | **5,665** |

The supplemental advanced vocabulary PDF contains 3,887 example records and 3,682 unique headwords. Examples are used when the English sense overlaps the supplied TOPIK gloss. Remaining cards use short controlled Korean contexts in simple present or past forms. The target word is the answer; the English translation contains the target meaning for highlighting in the V2 review screen.

The update retains the V41 grammar lessons, SRS tables, design, and themed packs. Music is now a separate user-managed area; imported music packs use isolated V2 tables and are not removed by the built-in seed sync. Vocabulary packs use per-word or per-pack Mastered markers, so existing grammar progress is preserved.

## Automated checks

- 10 built-in packs and 5,705 total cards are present: 5,665 TOPIK vocabulary cards plus four themed packs. Music packs are added by the user through the separate Music Packs menu.
- Every card has exactly one blank and reconstructs its stored Korean sentence when the answer is inserted.
- No generated vocabulary translation contains Cyrillic text.
- Python syntax compilation passes for the app, feature module, source importer, and TOPIK builder.
- Existing V41 files in the archive remain unchanged.
