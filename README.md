# Mochi Hangul

A responsive Bunpro-style Korean grammar review tool with a pastel chibi study-room theme, based on the lesson structure of How to Study Korean.

## Current scope

- English interface and explanations
- Starts at Unit 2; Units 0–1 are treated as completed
- Lessons 26–208 in sequential lesson packs
- Two new lessons per day, rotating card reviews, SRS scheduling, progress page, crystals and shop
- Correct / Almost / Wrong SRS grading
- Per-card progress stored in SQLite
- Rotation: cards reviewed today are moved behind other due cards from the same lesson
- Enter submits an answer; after checking, Enter activates Correct
- Four review grades: Again, Hard, Good and Easy. Hotkeys: 1, 2, 3/Enter/Space and 4.
- Crystal Shop categories: Faces, Characters, Room designs, Card frames and Progress trackers
- The Dashboard Study button opens a lesson preview; cards are added only after Add to deck
- Shop prices are migrated automatically in an existing database without deleting progress
- One responsive interface for desktop and mobile browsers

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run korean_bunpro_app.py
```

The first run creates `korean_bunpro.db` and imports the seed data. Do not delete that database if you want to keep progress.

The cards are compact practice prompts; each card links to the corresponding official HTSK lesson for the full explanation and examples.
