# Mochi Hangul — implementation report v7

## Updates in this archive

| # | Request | Result |
|---|---|---|
| 1 | Dashboard vocabulary review | The dashboard now places Grammar Review and Vocabulary Review side by side near the top. Both use matching bordered pastel cards. Vocabulary shows due reviews and today’s new words; it also has separate Review and Find or add words actions. |
| 2 | Search and add vocabulary | Search covers all 6,366 seeded vocabulary cards by Korean headword and English meaning. Matching results show sense, part of speech, and pack. If a sense is missing, a manual card can be created with a Korean example, one blank, the expected answer, and English translation. |
| 3 | Daily word amount | Today’s selection amount is adjustable from 1 to 20. Additional selections are queued for the next open study day; future days default to 20. |
| 4 | Mixed vocabulary review | New words selected for today and due vocabulary reviews are shuffled into one deck. Existing SRS dates and levels remain intact until the learner submits an answer. |
| 5 | Grammar review order | Due grammar cards are shuffled across topics at the start of a review session. |
| 6 | Speech-level instructions | Audited 1,017 grammar cards: all have an `answer_form`, with none missing. The review prompt explains common 해요체, 해체/plain, and formal polite requirements in direct learner-facing wording. |
| 7 | Similar grammar responses | Before grading, the app checks a curated set of 12 common overlapping grammar groups. If a listed alternative is detected, it names the related form and requested form, clears the field, and asks the learner to try again without grading or advancing. This list is not a general semantic classifier for every possible Korean grammar error. |
| 8 | Close manual-card form | Replaced the always-visible expander with an explicit open button. Once opened, a “Hide form” button closes it; closing saves nothing. |
| 9 | App colors for controls | Extended the Mochi palette to text/date/number inputs, text areas, select controls and menus, buttons, alerts, tabs, sliders, and checkbox/radio accents. This targets the default Streamlit colors that could show through. |
| 10 | Position and styling | Moved Vocabulary Review up beside Grammar Review. The two dashboard panels share the same layout and card styling; the vocabulary panel has the additional word search/add actions. |

## Validation

- Python syntax compilation passed for the edited app and feature module.
- Seed data check: 6,366 vocabulary cards and 1,017 grammar cards; 0 grammar cards missing `answer_form`.
- No live Supabase write, app deployment, or browser-based visual test was performed. The app code has not been run against the production database.
