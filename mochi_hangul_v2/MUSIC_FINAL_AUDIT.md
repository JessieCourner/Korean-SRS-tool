# Music library audit — 2026-10-13

- 39 songs, 1,748 retained lines, all with English translation fields.
- 389 vocabulary entries (DNA has 9; other songs have 10).
- All vocabulary surfaces match their referenced retained Korean lines.
- All entries have a gloss, independent Korean example, and English example translation.
- Back Door repaired: translated its remaining 21 lines; removed an unrelated song heading and 38 lines belonging to CASE 143, which had been accidentally appended to Back Door. Preserved the original 39-song scope.
- Python app syntax compiled successfully.

**Limitations:** This is a structural and targeted editorial audit, NOT an independent second manual reading of all 1,748 lines and 389 example sentences. The library retains Korean-containing lyric lines only, so purely English lyrics are not shown. Real Streamlit/PostgreSQL deployment was not tested.
