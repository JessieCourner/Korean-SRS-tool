# Mochi Hangul

A responsive Bunpro-style Korean grammar review tool with a pastel chibi study-room theme, based on the lesson structure of How to Study Korean.

## Current scope

- English interface and explanations
- Starts at Unit 2; Units 0–1 are treated as completed
- Lessons 26–208 in sequential lesson packs; HTSK source guides are published for 26–202, while 203–208 are clearly marked as not yet published by HTSK
- 885 verified SRS cards: exactly five separate HTSK example cards for each published lesson 26–202; lessons 203–208 intentionally have no cards until HTSK publishes them
- Two new lessons per day, rotating card reviews, SRS scheduling, progress page, crystals and shop
- Correct / Almost / Wrong SRS grading
- Per-card progress stored in SQLite
- Rotation: cards reviewed today are moved behind other due cards from the same lesson
- Newly added cards with no first rating are included in Review, even if there are no scheduled reviews
- Enter submits an answer; after checking, Enter activates Correct
- The answer field is focused automatically when each new Review card opens
- Four review grades: Again, Hard, Good and Easy. Hotkeys: 1, 2, 3/Enter/Space and 4.
- Study lessons and Review open as large internal app dialogs, so they stay inside the same page on desktop and mobile
- The selected progress mascot sits inside the progress bar and moves with it; the selected card frame decorates the whole Review card
- Consecutive study-day streaks with a daily crystal bonus
- A daily original chibi encouragement: two full-body human chibis appear in different dashboard positions with separate speech bubbles; one bubble gives a Korean message and the other shows its English translation; names and language labels are intentionally omitted, and difficulty follows the furthest lesson started
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

The first run creates `korean_bunpro.db` and imports the seed data. Do not delete that database if you want to keep progress.

The cards are compact practice prompts. Each `unit*.json` lesson record contains its verified HTSK-derived guide, so the explanation shown by **Study** travels with the lesson itself. Guide examples come from the corresponding official HTSK lesson pages; they are separate from the SRS card examples. The app does not invent guide or card content for unpublished lessons.

## Deploy on Streamlit Community Cloud (beginner checklist)

1. Download `korean_grammar_srs_complete.zip` and unzip it. Do not upload only the Python file.
2. Open your existing GitHub repository and upload all files from the unzipped folder into its root. Replace the old files when GitHub asks. The important files are `korean_bunpro_app.py`, all `unit*.json` files, `requirements.txt` and the complete `bts_chibi/` folder.
3. Do not delete `korean_bunpro.db` if it is already in the repository. It contains progress. Do not create a new Streamlit app for this update.
4. In Streamlit Cloud open the existing app and choose **Manage app → Settings** (or **Edit app**). Set **Main file path** to `korean_bunpro_app.py`, then save/redeploy.
5. Wait for the app to finish restarting and open its existing URL. If lesson explanations are missing, check that all `unit*.json` files were uploaded next to the Python file.
6. On the first screen choose **Lessons** to inspect a topic. Press **Study**, read the HTSK guide and source examples, then press **Add to deck**. Only then do its cards enter Review.
7. On **Dashboard**, press the visible **Review · N cards** button. It includes both scheduled reviews and newly added cards that still need their first answer/rating. If you see `Active cards: 10`, those cards are available from this Review button even when the scheduled-review number is zero.

The app is one responsive interface: the same URL works in a computer browser and on a phone. Study and Review are internal full-screen-style windows, not new browser tabs. Lessons 203–208 remain visible in the roadmap but are marked unavailable because HTSK has not published those lesson pages yet.

The chibi messages are original in-app encouragements; they are not presented as official quotations.
