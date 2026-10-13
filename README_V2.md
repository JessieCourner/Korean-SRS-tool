# Mochi Hangul V2 update

This is a separate V2 entry point built on the supplied V41 project. The V41 app, lesson seed files, review screen, and grammar SRS code are included unchanged. Start V2 with `korean_bunpro_app_v2.py`.

## Run locally

1. Extract the complete ZIP into the existing project folder, beside its existing `korean_bunpro.db` if you use the local database. Do not replace or delete that database.
2. Install the dependencies from `requirements.txt` in your Python environment.
3. Run `streamlit run korean_bunpro_app_v2.py`.

V2 uses the same database path and the same `SUPABASE_DB_URL` secret as V41. It adds isolated tables for vocabulary packs and mastery markers; the database file and grammar review history are not included in this ZIP.

## Run on Streamlit Community Cloud

1. Add these files to the same repository as the current app, preserving the existing `.streamlit/secrets.toml` configuration or Cloud secrets.
2. In the app settings, change **Main file path** to `korean_bunpro_app_v2.py`.
3. Keep the existing `SUPABASE_DB_URL` secret. Do not create a new database if you want to keep the current grammar SRS history.

The first V2 launch creates and seeds only `v2_vocab_packs`, `v2_vocab_cards`, `v2_vocab_progress`, and `manual_mastery`. The normal V41 bootstrap continues to synchronize the existing grammar content.

## V2 contents

- Six TOPIK vocabulary packs built from the supplied TOPIK 1–6 PDFs: 5,665 review cards for 5,665 usable Korean headwords. Each word has its own card, individual Mastered marker, base form and answer-form label. One level-4 source row had no Korean headword and is recorded in `skipped_source_records`.
- Cards use examples from the supplied supplemental dictionary only when the English sense matches. Other cards use short controlled present or past contexts designed to test the vocabulary word. The English target is highlighted in the review translation.
- The source extraction and build scripts are `import_topik_sources.py` and `build_topik_full.py`; `CONTENT_AUDIT_V2.md` records the counts and checks.
- Four themed packs (40 cards): K-pop fandom, K-drama, everyday slang, and Korean sound/motion words. Slang cards identify informal and vulgar usage.
- Music is a separate area in the Vocabulary menu. The archive contains a Music Packs list and a JSON template for importing your own lyric/context cards; its cards are reviewed through the common Vocabulary Review and are not placed into the daily TOPIK queue automatically. User music packs are stored as `music_custom` and are never removed by a later built-in content sync.
- Vocabulary review, per-pack review, per-word and per-pack Mastered markers, answer-form/base-form details, source links, and additional room themes/shop items.

`build_vocab_seed.py` regenerates `vocabulary_packs_v2.json` and checks the blank, answer reconstruction, target translation, and excerpt length for every card. `CONTENT_AUDIT_V2.md` records the package counts and checks.

## Vocabulary source and coverage

The 5,665 TOPIK cards in this build come from the six supplied lists. They are a broad study library, not an official word-by-word TOPIK syllabus. I checked a more complete, source-backed route for a later vocabulary expansion:

- NIKL's [2017 International Standard Curriculum vocabulary and grammar grade spreadsheet](https://www.korean.go.kr/front/reportData/reportDataView.do?mn_id=45&pageIndex=5&report_seq=932) supplies curriculum grades 1–6. These are curriculum grades, not official TOPIK word-by-word labels.
- NIKL's [Basic Korean Dictionary](https://krdict.korean.go.kr/eng/openApi/openApiInfo) supplies headwords, parts of speech, definitions, usage examples, and semantic categories. Its API documentation lists searchable semantic categories and requires an API key. The dictionary's simple learner-grade filter is elementary/intermediate/advanced.
- A [public dictionary-data mirror](https://github.com/basickorean/basickorean-vocab) says it combines the Basic Korean Dictionary with the NIKL curriculum grades 1–6 and is distributed under CC BY-SA 2.0 KR. Any redistributed derivative must retain attribution and the share-alike terms.
- For a six-band TOPIK-labelled study index, [kfluent's 10,890-word list](https://kfluent.com/vocabulary/) is searchable by TOPIK 1–6 and seven topics, and is curated by a certified Korean teacher. Its TOPIK labels are a teacher-curated mapping, not an official exhaustive TOPIK syllabus.

The current archive contains the six supplied PDF lists as the TOPIK vocabulary source. It does not contain the 10,890-word index or a full dictionary export. The official NIKL source remains the better foundation for a broad curriculum-grade library; TOPIK-specific labels should be stored separately and treated as estimates.
