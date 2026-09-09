# Korean Grammar SRS

A responsive Bunpro-style Korean grammar review tool based on the lesson structure of How to Study Korean.

## Current scope

- English interface and explanations
- Starts at Unit 2; Units 0–1 are treated as completed
- Unit 2 Lessons 26–33
- 5 sentence cards per lesson
- Correct / Almost / Wrong SRS grading
- Per-card progress stored in SQLite
- Rotation: cards reviewed today are moved behind other due cards from the same lesson
- One responsive interface for desktop and mobile browsers

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run korean_bunpro_app.py
```

The first run creates `korean_bunpro.db` and imports the seed data. Do not delete that database if you want to keep progress.
