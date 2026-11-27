# Mochi Hangul — implementation report v6

## Scope

Implemented the seven requested vocabulary and grammar review changes in the app code. The source archive was based on `Mochi_Hangul_Examples_Reviewed_All_6366_v5.zip`. Existing review records, intervals, review dates, and the configured Supabase service are not modified by this code change. The new daily vocabulary selection/settings tables are created by the app when it initializes.

## Results by request

| # | Request | Result |
|---|---|---|
| 1 | Vocabulary review on the dashboard | Added due vocabulary and today’s selected-new-word counts, plus a button that opens Vocabulary Review. |
| 2 | Search and add words from the full vocabulary database | Search covers the complete vocabulary-card table (6,366 seeded cards), matching Korean headwords and English meanings. Results show the sense, part of speech, and pack so the learner can select the intended sense. If a word/sense is absent, the manual-card form accepts a Korean prompt with exactly one blank, the answer, meaning, and English example translation. New manual cards enter the study queue. |
| 2a | Daily amount and overflow | The learner can set today’s new-word amount from 1 to 20. Words added after today’s quota is filled are assigned to the next open day, 20 per day by default. Unstudied selections from earlier days remain available in the mixed review queue. |
| 3 | Mix new and due vocabulary | Selected new cards and due SRS cards are combined, de-duplicated, and shuffled into one queue. The existing vocabulary SRS level and dates are updated only when an answer is submitted. |
| 4 | Shuffle due grammar reviews | The due grammar-card snapshot is shuffled at the start of a review session, so lesson/topic order no longer exposes the next grammar point. |
| 5 | Explain required grammar speech level | Audited the 1,017 seeded grammar cards: all 1,017 have an `answer_form`; none are blank. Every answer ending found by the speech-level audit has a corresponding explicit level label. The review card now explains 해요체, 해체/plain, and formal polite endings in direct learner-facing wording. |
| 6 | Similar but incorrect grammar form | Before grading, the app checks a curated set of 12 common overlapping grammar groups (including reason/cause, permission, conjecture, ability, attempt, and concession forms). When a listed alternative is detected, the card explains which related form was entered, identifies the requested form, clears the field, and asks for another answer without advancing or changing SRS. |
| 7 | Wrong speech level | If the same answer stem is entered with a recognized different speech ending, the app explains the required level, clears the field, and asks for re-entry without grading or advancing. |

## Validation performed

- Python syntax compilation passed for `korean_bunpro_app_v2.py` and `korean_bunpro_v2_features.py`.
- Source-data count check: 6,366 vocabulary cards; 1,017 grammar cards; 0 grammar cards missing `answer_form`.
- No live Supabase writes or import were performed. This report does not claim runtime verification against the production database.

## Implementation note

Similar-grammar feedback is currently based on the explicit curated overlap list in the app code. It catches those listed related forms; it is not a general semantic classifier for every possible wrong Korean grammar construction.
