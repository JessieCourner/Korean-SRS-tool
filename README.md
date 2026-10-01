# Mochi Hangul

A responsive Bunpro-style Korean grammar review tool with a pastel chibi study-room theme, based on the lesson structure of How to Study Korean.

## Current scope

- English interface and explanations
- Starts at Unit 2; Units 0–1 are treated as completed by default, but remain available in Lessons for reading and optional manual deck activation
- Includes HTSK foundation material for Unit 0 and Lessons 1–25 of Unit 1; these lessons never enter the daily queue automatically
- Lessons 26–208 in sequential lesson packs; HTSK source guides are published for 26–202, while 203–208 are clearly marked as not yet published by HTSK
- 1027 manually reviewed SRS cards across foundation lessons 0–25 and published lessons 26–202; lessons 203–208 intentionally have no cards because HTSK has not published those lesson pages
- Two new lessons per day, rotating card reviews, SRS scheduling, progress page, crystals and shop
- Correct / Almost / Wrong SRS grading
- Per-card progress stored in SQLite
- Rotation: cards reviewed today are moved behind other due cards from the same lesson
- Newly added cards with no first rating are included in Review, even if there are no scheduled reviews
- Enter submits an answer; the app grades automatically from the number of attempts and repeats a wrong card immediately
- The answer field is focused automatically when each new Review card opens
- Each card has a separate optional hint that shows the word in its base form, without revealing the completed grammar answer
- Automatic review grading: first correct attempt = Good, second = Hard, third or later = Again; a wrong answer does not leave the card until it is answered correctly
- Study lessons and Review open as large internal app dialogs, so they stay inside the same page on desktop and mobile
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

The cards are manually curated practice prompts: the answer contains the lexical base or phrase that the lesson is actually practicing together with its grammar ending, and vocabulary lessons use distinct target words where the lesson teaches more than one. Each `unit*.json` lesson record contains its HTSK-derived guide and examples, so the explanation shown by **Study** travels with the lesson itself. The app does not invent guide or card content for unpublished lessons. The content sync version is bumped for this pack so an existing database imports the edited prompt, translation, answer, hint and explanation once on startup without resetting review progress.

## Deploy on Streamlit Community Cloud (beginner checklist)

1. Download `korean_bunpro_content_full_20261001.zip` and unzip it. Do not upload only the Python file.
2. Open your existing GitHub repository and upload all files from the unzipped folder into its root. Replace the old files when GitHub asks. The important files are `korean_bunpro_app.py`, all `unit*.json` files, `requirements.txt` and the complete `bts_chibi/` folder.
3. Do not delete `korean_bunpro.db` if it is already in the repository. It contains progress. Do not create a new Streamlit app for this update.
4. In Streamlit Cloud open the existing app and choose **Manage app → Settings** (or **Edit app**). Set **Main file path** to `korean_bunpro_app.py`, then save/redeploy.
5. Wait for the app to finish restarting and open its existing URL. If lesson explanations are missing, check that all `unit*.json` files were uploaded next to the Python file.
6. On the first screen choose **Lessons** to inspect a topic. Press **Study**, read the HTSK guide and source examples, then press **Add to deck**. Only then do its cards enter Review.
7. On **Dashboard**, press the visible **Review · N cards** button. It includes both scheduled reviews and newly added cards that still need their first answer/rating. If you see `Active cards: 10`, those cards are available from this Review button even when the scheduled-review number is zero.

The app is one responsive interface: the same URL works in a computer browser and on a phone. Study and Review are internal full-screen-style windows, not new browser tabs. Lessons 203–208 remain visible in the roadmap but are marked unavailable because HTSK has not published those lesson pages yet.

The chibi messages are original in-app encouragements; they are not presented as official quotations.
