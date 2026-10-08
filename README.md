# Mochi Hangul

## v41

- Continued the card-by-card answer-span audit. Ten remaining split answers now require the complete semantic phrase plus the lesson grammar, including `보존하지 않으면`, `해고하지 않았으면 좋겠다`, `좋아하지 않을까 봐`, `원활하지 않은 경우`, `위조된 돈이 아닐까 싶어요`, `자청하지 않기 마련이에요`, and the full `-단다` predicates.
- The visible sentence now keeps the unrelated subject, object and context outside the blank; only the lexical predicate/noun phrase that carries the lesson target is required.
- The source sentence, translation, base-form hint and speech-level labels remain unchanged except where the blank boundary changed. UI and SRS logic were not changed.

## v40

- Audited 91 card answer spans. The blank now contains the lexical word/phrase that carries the lesson grammar, while unrelated subjects, time adverbs, discourse words and surrounding context remain visible in the sentence. For example, Lesson 27 now asks for `먹었던` in `우리가 지난 번에 ___ 곳에서 먹고 싶어요`; it no longer asks for `저는 애기가 썼던`.
- Replaced the cards that could not be repaired by moving the blank with distinct official HTSK examples from the same lesson (Lessons 27, 49, 80, 85, 86 and 87). The card's sentence, translation, answer, base-form hint and speech-level label were updated together.
- Rechecked speech-level labels for sentence-final `다`: these are marked `Formal/written plain form`, not informal conversational form. Embedded phrases have no invented speech-level label.
- The content validator now rejects duplicate HTSK source sentences, while allowing the same target word to appear in different source contexts when a lesson teaches one fixed expression or vocabulary item. UI, SRS and stored progress logic were not changed.

## v39

- Removed grammar names, endings and lexical answer hints from the Required answer form labels. The labels retain only useful speech-level/context information; card prompts, complete answers, base-form hints, explanations, design and SRS are unchanged.

## v38

- Replaced every within-lesson duplicate English translation whose Korean source sentence differed with a different official HTSK sentence from the same lesson grammar. The complete answer, base-form hint and required answer form were updated together; the other cards and SRS logic were left unchanged.

## v37

- Rechecked and made answer-form labels explicit for non-polite, polite, honorific, formal/literary, command, question, proposal, and embedded grammar answers.

## v36

- Positions the entire transparent inline answer widget 10px lower so typed text sits on the same baseline as the Korean sentence after Streamlit reruns.
- Replaces lesson-card explanation placeholders with the lesson's actual grammar explanation, and keeps the required answer form visible on both the active card and the graded result.

A responsive Bunpro-style Korean grammar review tool with a pastel chibi study-room theme, based on the lesson structure of How to Study Korean.

## Current scope

- English interface and explanations
- Starts at Unit 2; Units 0–1 are treated as completed by default, but remain available in Lessons for reading and optional manual deck activation
- Includes HTSK foundation material for Unit 0 and Lessons 1–25 of Unit 1; these lessons never enter the daily queue automatically
- Lessons 26–208 in sequential lesson packs; HTSK source guides are published for 26–202, while 203–208 are clearly marked as not yet published by HTSK
- 1,017 cards total: 130 foundation cards for Units 0–1 plus HTSK-derived practice cards for each published lesson 26–202 (887 cards); Lesson 59 has seven cards because its official vocabulary list has seven target words, and lessons 203–208 intentionally have no cards until HTSK publishes them
- Two new lessons per day, rotating card reviews, SRS scheduling, progress page, crystals and shop
- Bunpro-style level and interval SRS grading
- Per-card progress stored in SQLite
- Rotation: cards reviewed today are moved behind other due cards from the same lesson
- Newly added cards with no first rating are included in Review, even if there are no scheduled reviews
- Enter submits one answer; the app grades it once from its correctness and moves to the next card
- The answer field is focused automatically when each new Review card opens
- Each card has a separate optional hint with the lexical base form appropriate to the part of speech (for example, a noun stays a noun and passive practice points back to the active verb), without revealing the completed grammar answer
- The Korean prompt and translation stay centered together; the real answer input sits in the blank, starts narrow, expands locally while typing, has no box or alternate fill color, and submits on Enter without a rerun for every keystroke
- Automatic review grading: correct answers advance the Bunpro level and incorrect answers lower it; the result is recorded once and the card leaves the current queue
- Study lessons and Review open as internal app dialogs; Review snapshots its due-card queue for the visit so the progress count and visible cards stay synchronized during SRS updates
- On phones, the borderless ☰ button opens a real in-app navigation panel; its page buttons work for Dashboard, Review, Lessons, Progress and Crystal Shop
- The selected progress mascot starts flush at the beginning of the progress bar and moves with its fill; the selected card frame decorates the whole Review card
- Consecutive study-day streaks with a daily crystal bonus
- A daily original chibi encouragement: two full-body human chibis appear in different random positions over every app page with separate speech bubbles; they float above all app content and can be dragged aside with a mouse or finger, including while a Study or Review window is open, and remain available after a dialog is closed; one bubble gives a Korean message and the other shows its English translation; names and language labels are intentionally omitted, and difficulty follows the furthest lesson started. The daily pair is always Jimin–Jung Kook or V (Taehyung)–Jin. The floating control at the lower right hides or restores all chibis. There is no separate chibi panel behind them.
- Lessons are grouped into expandable Unit sections, with that unit's lesson rows and Study buttons inside each section. Completed Units 0–1 remain visible and can be added manually to Review.
- The seven transparent chibi character assets live in the bundled `bts_chibi/` folder; keep that folder next to `korean_bunpro_app.py`. If only the Python file is uploaded, it still draws a self-contained full-body chibi instead of showing an animal emoji.
- Crystal Shop categories: Faces, Characters, Room designs, Card frames and Progress trackers
- The Dashboard Study button opens a lesson preview; cards are added only after Add to deck
- Each lesson record contains its shortened HTSK guide directly: Meaning, When to use it, How to build it and separate source examples; guide examples are never generated from SRS cards
- Shop prices are migrated automatically in an existing database without deleting progress
- One responsive interface for desktop and mobile browsers

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run korean_bunpro_app.py
```

## Supabase progress storage

To keep one progress record across devices, add this to the app's Streamlit Cloud Secrets after creating a Supabase project:

```toml
SUPABASE_DB_URL = "postgresql://postgres:<YOUR_PASSWORD>@<YOUR_HOST>:5432/postgres?sslmode=require"
```

When `SUPABASE_DB_URL` is present, the app uses Supabase PostgreSQL. Without it, the app falls back to the local `korean_bunpro.db` file.

The first run creates `korean_bunpro.db` and imports the seed data. Do not delete that database if you want to keep progress.

The cards are compact practice prompts and require the complete missing word or phrase, including the lexical stem and grammar ending, whenever the stem is shown before the blank. Each prompt has exactly one `___`; where a source sentence is recorded, filling that blank reconstructs the full sentence. Vocabulary lessons are checked so their cards require different target words or lexical expressions rather than repeating one answer. Each `unit*.json` lesson record contains its HTSK-derived guide and examples, so the explanation shown by **Study** travels with the lesson itself. The app does not invent guide or card content for unpublished lessons. The seed paths are resolved beside `korean_bunpro_app.py`, not from the process working directory. If any lesson pack is missing, startup stops with a clear error instead of silently showing stale card text from the old database. The startup resource cache runs the idempotent content sync once per app process, so a corrected seed file repairs stale database card text without resetting SRS progress.

## Deploy on Streamlit Community Cloud (beginner checklist)

1. Download the complete archive and unzip it. Do not upload only the Python file.
2. Open your existing GitHub repository and upload all files from the unzipped folder into its root. Replace the old files when GitHub asks. The important files are `korean_bunpro_app.py`, all `unit*.json` files, `requirements.txt` and the complete `bts_chibi/` folder.
3. Do not delete `korean_bunpro.db` if it is already in the repository. It contains progress. Do not create a new Streamlit app for this update.
4. In Streamlit Cloud open the existing app and choose **Manage app → Settings** (or **Edit app**). Set **Main file path** to `korean_bunpro_app.py`, then save/redeploy.
5. Wait for the app to finish restarting and open its existing URL. If lesson explanations are missing, check that all `unit*.json` files were uploaded next to the Python file.
6. On the first screen choose **Lessons** to inspect a topic. Press **Study**, read the HTSK guide and source examples, then press **Add to deck**. Only then do its cards enter Review.
7. On **Dashboard**, press the visible **Review · N cards** button. It includes both scheduled reviews and newly added cards that still need their first answer/rating. If you see `Active cards: 10`, those cards are available from this Review button even when the scheduled-review number is zero.

The app is one responsive interface: the same URL works in a computer browser and on a phone. Study and Review are internal app windows, not new browser tabs. Lessons 203–208 remain visible in the roadmap but are marked unavailable because HTSK has not published those lesson pages yet.

The chibi messages are original in-app encouragements; they are not presented as official quotations.

## Final card-content pass

This archive contains the full-answer-span and speech-form pass through 2026-10-07 (`2026-10-07-full-answer-spans-and-speech-forms-v41`). Lessons 26–202 retain their HTSK source sentences and were checked so the answer span contains the lexical base plus the lesson grammar, while unrelated sentence context stays outside the blank. Where the previous example could only be repaired by changing the source, it was replaced with another official HTSK example from the same lesson. Base-form hints continue to follow the word's part of speech (noun, adjective, verb, adverb or fixed construction), and sentence-final `다` forms are labeled as written/plain rather than informal conversation. Repeated fixed targets are allowed only when their HTSK source sentences are distinct.

On startup, the v33 content sync refreshes every card's prompt, complete answer, hint, explanation and answer-form in an existing local or Supabase database while preserving review levels, dates and history. It also fills in missing foundation lessons 0–25 when an older database already contains later lessons; existing lesson rows are never duplicated or reset. The migration records a permanent `seed_index` for each card inside its lesson and uses that position first on already-migrated databases, so later updates do not guess from visible text. The first migration still uses the old translation only to attach an existing SRS row to the correct new content; missing review rows are restored without changing existing progress. Obsolete rows are retired, and a strict post-sync verification checks the repaired content before the app renders. Verification includes retired/unpublished seed cards too, because retirement controls availability rather than whether their stored content is valid. The sync version is part of Streamlit's cache key and the old static card-query cache is cleared. This specifically replaces older records where a grammar tail was left outside the blank, even if an earlier deployment had already written a content marker. The dashboard welcome panel is removed; the single global chibi pair remains draggable above every page, and the hide/show control stays above the app controls.

The PostgreSQL connection updates its liveness timestamp after every successful
statement. This is required because the complete seed sync can last longer than
the socket idle threshold; without it, a reconnect could roll back the first
lesson's card inserts/updates in the middle of bootstrap and produce
`card_missing` during the final verification.

The PostgreSQL startup migration is serialized and checks `information_schema` before changing the schema. It only runs `ALTER TABLE` when a column is genuinely missing; already-migrated Supabase databases no longer repeat a locking no-op migration on every Streamlit start. Short-lived read helpers commit when finished, so idle PostgreSQL read transactions cannot keep a table lock forever. The local SQLite fallback keeps its `PRAGMA` checks.

## Fixes in this build

- Dashboard due-card SQL binds both date values it uses (`due_at` timestamp and `next_review` date), preventing the PostgreSQL `IndexError` on startup.
- Inline Review answer fields are transparent and borderless, including focus and hover states; the typed text inherits the sentence color. Ordinary text inputs elsewhere keep their normal styling.
- The inline mount applies the transparent/borderless styles directly to the Streamlit input and its BaseWeb wrappers, then positions the existing widget over the blank without reparenting it. This preserves the centered sentence while keeping Streamlit's widget tree valid across answer reruns.
- The inline mount copies the Korean prompt's font, weight, line height and color to the real answer input. The blank width is recalculated on each input event, so the sentence re-centers and grows with the typed answer.
- Review opens as one native `st.dialog` window. The old DOM-reparenting approach is gone, and the dialog reruns cleanly after Continue so accepting an answer cannot leave a blank screen or stack cards.
- Review uses one Bunpro-style SRS update per submitted answer; there is no `attempts_1/2/3` grading path or immediate retry loop.
- Continue clears the result view before selecting the next card with a fragment-scoped rerun, so the previous result and the next prompt cannot stack vertically.
- The answer widget is inside a batched Streamlit form, so opening the grammar explanation or base-form hint cannot submit an answer by causing the field to lose focus; only Enter/form submission grades it.
- Continuing a card uses a fragment-scoped rerun inside the Review dialog, so the dialog does not close and reopen between cards.
- Review snapshots the due-card IDs at the start of each visit and removes an ID only after its answer is graded; the progress count therefore cannot say `35 / 41` while the remaining cards have disappeared from the window.
- The final cleanup also covers every descendant of the answer widget and disables native input appearance, preventing a dark theme or browser default from drawing a colored rectangle.
- The content validator rejects a card with anything other than one blank, rejects an empty or grammar-tail-only answer, requires a real base-form hint, requires a source sentence for every published lesson 26–202 card, and rejects duplicate HTSK source sentences before the app starts.
- Repaired split answers now keep the lexical stem and the grammar chunk together (for example, `할 것 같아요`, `수 있도록`, `끈 채로`, `날 거라니까`), so the learner supplies the complete target phrase.
- The archive must be deployed as a complete folder: replacing only `korean_bunpro_app.py` cannot change card content because the corrected cards live in the `unit*.json` packs.
