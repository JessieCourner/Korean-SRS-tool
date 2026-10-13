# Vocabulary source review for Mochi Hangul V2

## Recommendation

Use the National Institute of Korean Language (NIKL) Basic Korean Dictionary as the source for the broad vocabulary library, and use NIKL's 2017 International Standard Curriculum vocabulary grades 1–6 as the primary study-level field. Keep any TOPIK exam band as a separate, explicitly approximate field.

There is no published official TOPIK dictionary that assigns every Korean word to one of TOPIK levels 1–6. A website that groups words by TOPIK level is useful for exam preparation, but its mapping should not be represented as an official exhaustive TOPIK syllabus.

## Sources checked

| Source | What it provides | How to use it |
|---|---|---|
| [NIKL 2017 International Standard Curriculum report and grade spreadsheet](https://www.korean.go.kr/front/reportData/reportDataView.do?mn_id=45&pageIndex=5&report_seq=932) | Official curriculum vocabulary/grammar grade list, levels 1–6 | Primary level ordering; label as curriculum level |
| [NIKL Basic Korean Dictionary Open API](https://krdict.korean.go.kr/eng/openApi/openApiInfo) | Headwords, definitions, parts of speech, examples, and semantic category filters | Dictionary and context source; API access requires an issued key |
| [NIKL Basic Korean Dictionary search page](https://krdict.korean.go.kr/eng/dicSearchDetail/searchDetailWords?nation=eng&nationCode=6) | Browse by part of speech, learner grade, and topic/situation | Manual verification and reference; topic/situation options are available in the UI |
| [basickorean-vocab public mirror](https://github.com/basickorean/basickorean-vocab) | Static JSON derived from NIKL dictionary data, with curriculum grade 1–6 and dictionary elementary/intermediate/advanced tags | Potential import route; states CC BY-SA 2.0 KR, so keep attribution and share-alike terms |
| [kfluent vocabulary index](https://kfluent.com/vocabulary/) | 10,890 words mapped to TOPIK 1–6 and seven topics; maintained by a certified Korean language teacher | Helpful exam-oriented index, but not an official TOPIK word syllabus |
| [NIKL 5,965-word learner vocabulary list](https://www.korean.go.kr/front_eng/down/down_02V.do?etc_seq=71) | Official list in three NIKL bands: 982, 2,111, and 2,872 words | A smaller official core list; its three bands are not the six TOPIK levels |

## What is in the current V2 archive

The archive has 240 curated TOPIK-topic cards, 40 cards across four theme packs, and 80 music cards across 40 tracks. It does not yet bundle the full NIKL dictionary or the 10,890-word kfluent index. Therefore these cards are a starter library, not full lexical coverage.

The NIKL report page and Basic Dictionary documentation were verified, but the environment blocked downloading the public JSON mirror (HTTP 403). No unseen word list was fabricated or counted as imported. To add the full source data to the local app, obtain the dataset export/mirror files and import those records with their attribution and CC BY-SA 2.0 KR notice. Each word can then become a separate contextual cloze using the dictionary's attested example sentence where suitable, retaining the word's part of speech, semantic topic, curriculum grade, and source link.

## Source notes

- NIKL's official 2003 learner word list describes grades A/B/C and 5,965 entries; it is distinct from the 2017 curriculum's six-grade vocabulary list.
- The Basic Korean Dictionary API describes three learner grades (elementary, intermediate, advanced) and semantic-category filters. Do not collapse these three grades into the six curriculum grades.
- Add TOPIK 1–6 labels only when the source provides them, and identify third-party mappings as estimates.
