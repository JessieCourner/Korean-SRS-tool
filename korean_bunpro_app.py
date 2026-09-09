import json
import re
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


DB_PATH = Path("korean_bunpro.db")
SEED_PATH = Path("unit2_lessons_26_33.json")
EXTENDED_SEED_PATHS = [Path("unit2_lessons_34_50.json"), Path("unit3_lessons_51_75.json"), Path("unit4_lessons_76_100.json"), Path("unit5_lessons_101_116.json"), Path("unit5_lessons_117_125.json"), Path("unit6_lessons_126_133.json"), Path("unit6_lessons_134_150.json"), Path("unit7_lessons_151_175.json"), Path("unit8_lessons_176_200.json"), Path("unit9_lessons_201_208.json")]
SRS_DAYS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 14, 5: 30, 6: 60, 7: 120, 8: 3650}
UNIT_INFO = {
    0: ("Learn How to Read Korean", "Lessons 1–3", "completed"),
    1: ("Basic Korean Grammar", "Lessons 1–25", "completed"),
    2: ("Lower-Intermediate Korean Grammar", "Lessons 26–50", "current"),
    3: ("Intermediate Korean Grammar", "Lessons 51–75", "locked"),
    4: ("Upper-Intermediate Korean Grammar", "Lessons 76–100", "locked"),
    5: ("Lower-Advanced Korean Grammar", "Lessons 101–125", "locked"),
    6: ("Advanced Korean Grammar", "Lessons 126–150", "locked"),
    7: ("Upper-Advanced Korean Grammar", "Lessons 151–175", "locked"),
    8: ("Near-Expert Korean Grammar", "Lessons 176–200", "locked"),
    9: ("Expert Korean Grammar", "Lessons 201–208", "locked"),
}
HTSK_GROUPS = {
    3: [("Lessons 51–58", "https://www.howtostudykorean.com/unit-3-intermediate-korean-grammar/unit-3-lessons-51-58/"), ("Lessons 59–66", "https://www.howtostudykorean.com/unit-3-intermediate-korean-grammar/unit-3-lessons-59-66/"), ("Lessons 67–75", "https://www.howtostudykorean.com/unit-3-intermediate-korean-grammar/unit-3-lessons-67-75/")],
    4: [("Lessons 76–83", "https://www.howtostudykorean.com/upper-intermediate-korean-grammar/unit-4-lessons-76-83/"), ("Lessons 84–91", "https://www.howtostudykorean.com/upper-intermediate-korean-grammar/unit-4-lessons-84-91/"), ("Lessons 92–100", "https://www.howtostudykorean.com/upper-intermediate-korean-grammar/unit-4-lessons-92-100/")],
    5: [("Lessons 101–108", "https://www.howtostudykorean.com/unit-5/lessons-101-108/"), ("Lessons 109–116", "https://www.howtostudykorean.com/unit-5/lessons-109-116/"), ("Lessons 117–125", "https://www.howtostudykorean.com/unit-5/lessons-117-125/")],
    6: [("Lessons 126–133", "https://www.howtostudykorean.com/unit-6/lessons-126-133/"), ("Lessons 134–141", "https://www.howtostudykorean.com/unit-6/lessons-134-141/"), ("Lessons 142–150", "https://www.howtostudykorean.com/unit-6/lessons-142-150/")],
    7: [("Lessons 151–158", "https://www.howtostudykorean.com/unit-7/lessons-151-158/"), ("Lessons 159–166", "https://www.howtostudykorean.com/unit-7/lessons-159-166/"), ("Lessons 167–175", "https://www.howtostudykorean.com/unit-7/lessons-167-175/")],
    8: [("Lessons 176–183", "https://www.howtostudykorean.com/unit-8/lessons-176-183/"), ("Lessons 184–191", "https://www.howtostudykorean.com/unit-8/lessons-184-191/"), ("Lessons 192–200", "https://www.howtostudykorean.com/unit-8/lessons-192-200/")],
    9: [("Lessons 201–208", "https://www.howtostudykorean.com/unit-9/lessons-201-208/")],
}
SHOP_ITEMS = [
    ("face_bunny", "Sleepy Bunny", "face", 0, "૮ ˶ᵔ ᵕ ᵔ˶ ა", "Your starter study buddy"),
    ("face_cat", "Happy Cat", "face", 80, "ฅ^•ﻌ•^ฅ", "Smiles when you finish a review"),
    ("face_bear", "Tiny Bear", "face", 120, "ʕ•ᴥ•ʔ", "A calm little learning bear"),
    ("character_rabbit", "Bunny Scholar", "character", 220, "🐰", "Cheerful character for your dashboard"),
    ("character_penguin", "Study Penguin", "character", 300, "🐧", "A brave penguin who loves review days"),
    ("design_sakura", "Sakura Dream", "design", 150, "🌸", "Pink sakura study room"),
    ("design_lavender", "Lavender Cloud", "design", 180, "☁️", "Soft purple cloud theme"),
    ("design_peach", "Peach Soda", "design", 240, "🍑", "Warm peachy study theme"),
]

st.set_page_config(page_title="Korean Grammar SRS", page_icon="🇰🇷", layout="wide")
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background: linear-gradient(135deg, #fff8fc 0%, #f6f1ff 52%, #eefaff 100%) !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    [data-testid="stToolbar"] {visibility: hidden; height: 0;}
    [data-testid="stDecoration"] {display: none;}
    .stApp {background: transparent !important; color: #5b4770 !important;}
    h1, h2, h3, h4, h5, h6, p, label, [data-testid="stMarkdownContainer"], [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] {color: #5b4770 !important;}
    .block-container {max-width: 1100px; padding-top: 2rem;}
    [data-testid="stSidebar"] {background: linear-gradient(180deg, #ffe9f2 0%, #eee7ff 100%);}
    [data-testid="stSidebar"] * {color: #5b4770 !important;}
    [data-testid="stMetric"] {background: rgba(255,255,255,.78); border: 2px solid #f4d8e7; border-radius: 22px; padding: 14px 18px; box-shadow: 0 6px 18px rgba(140,105,150,.08);}
    [data-testid="stMetricLabel"] {color: #9b7090 !important;}
    [data-testid="stMetricValue"] {color: #654b78 !important;}
    .stButton > button {border-radius: 18px; border: 2px solid #e9c8dd; background: #fff !important; color: #684d7b !important; font-weight: 700; transition: .15s ease;}
    .stButton > button:hover {border-color: #d99ac0; background: #fff3fa; transform: translateY(-1px);}
    [data-testid="stProgressBar"] > div {background: #eadff2 !important; border-radius: 12px;}
    [data-testid="stProgressBar"] > div > div {background: linear-gradient(90deg, #f4a8c9, #b9a7ee) !important; border-radius: 12px;}
    .stTextInput input {font-size: 1.1rem; border-radius: 16px; border: 2px solid #e8cfe1; background: #ffffff !important; color: #5b4770 !important; -webkit-text-fill-color: #5b4770 !important;}
    .stTextInput input::placeholder {color: #9b82a5 !important; -webkit-text-fill-color: #9b82a5 !important; opacity: 1 !important;}
    .chibi-table-wrap {overflow-x:auto; border:2px solid #f0cfe0; border-radius:20px; background:rgba(255,255,255,.82); box-shadow:0 8px 20px rgba(134,101,156,.08);}
    .chibi-table {width:100%; border-collapse:collapse; color:#5b4770; min-width:680px;}
    .chibi-table th {background:#f7dbea; color:#684d7b; text-align:left; padding:12px 14px; font-weight:800;}
    .chibi-table td {padding:11px 14px; border-top:1px solid #f1dce8; color:#5b4770;}
    .chibi-table tr:nth-child(even) td {background:#fffafd;}
    .chibi-hero {display:flex; align-items:center; gap:20px; padding:22px 26px; margin:8px 0 24px; border-radius:28px; background:linear-gradient(110deg,#ffdceb,#e9e0ff 58%,#dff7ff); border:2px solid #f2c8df; box-shadow:0 10px 24px rgba(134,101,156,.10);}
    .chibi-face {font-size:42px; line-height:1; white-space:nowrap;}
    .chibi-title {font-size:24px; font-weight:800; color:#654b78; margin-bottom:4px;}
    .chibi-subtitle {color:#886d91; font-size:15px;}
    .cute-note {padding:12px 16px; border-radius:18px; background:#fff7fc; border:2px dashed #e8b9d3; color:#765777; margin:10px 0 18px;}
    @media (max-width: 700px) {
        .block-container {padding: 1rem .75rem 2rem;}
        h1 {font-size: 1.8rem;}
        h2 {font-size: 1.35rem;}
        .chibi-hero {padding:18px; gap:12px;}
        .chibi-face {font-size:30px;}
        .chibi-title {font-size:19px;}
        .stButton button {min-height: 2.8rem; width: 100%;}
    }
</style>
""", unsafe_allow_html=True)


def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def today():
    return date.today().isoformat()


def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit INTEGER NOT NULL,
        lesson_number INTEGER UNIQUE NOT NULL,
        title TEXT NOT NULL,
        pattern TEXT NOT NULL,
        explanation TEXT NOT NULL,
        source_url TEXT NOT NULL,
        status TEXT DEFAULT 'locked'
    );
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        prompt TEXT NOT NULL,
        translation TEXT NOT NULL,
        answer TEXT NOT NULL,
        hint TEXT NOT NULL,
        explanation TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reviews (
        card_id INTEGER PRIMARY KEY,
        level INTEGER DEFAULT 0,
        next_review TEXT DEFAULT '2999-01-01',
        last_review TEXT,
        mistakes INTEGER DEFAULT 0,
        active INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS answer_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        card_id INTEGER NOT NULL,
        result TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY CHECK(id=1), crystals INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS reward_events (event_key TEXT PRIMARY KEY, amount INTEGER NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS shop_items (id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, price INTEGER NOT NULL, icon TEXT NOT NULL, description TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS inventory (item_id TEXT PRIMARY KEY, purchased_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS daily_lessons (
        day TEXT NOT NULL,
        lesson_id INTEGER NOT NULL,
        status TEXT DEFAULT 'new',
        PRIMARY KEY(day, lesson_id)
    );
    """)
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('start_unit','2')")
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('new_lessons_per_day','2')")
    # The current course plan is two new lessons per day. Keep this migration
    # explicit so an older database that used three is corrected as well.
    c.execute("UPDATE settings SET value='2' WHERE key='new_lessons_per_day'")
    c.execute("INSERT OR IGNORE INTO wallet(id,crystals) VALUES(1,0)")
    for item in SHOP_ITEMS:
        c.execute("INSERT OR IGNORE INTO shop_items(id,name,kind,price,icon,description) VALUES(?,?,?,?,?,?)", item)
    c.execute("INSERT OR IGNORE INTO inventory(item_id,purchased_at) VALUES('face_bunny',?)", (datetime.now().isoformat(timespec='seconds'),))
    c.execute("INSERT OR IGNORE INTO inventory(item_id,purchased_at) VALUES('design_lavender',?)", (datetime.now().isoformat(timespec='seconds'),))
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('active_face','face_bunny')")
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('active_design','design_lavender')")
    c.commit()
    c.close()


def import_seed_once():
    if not SEED_PATH.exists():
        return
    c = db()
    if c.execute("SELECT COUNT(*) FROM lessons").fetchone()[0] > 0:
        c.close()
        return
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for lesson in data["lessons"]:
        cur = c.execute("""
            INSERT INTO lessons(unit,lesson_number,title,pattern,explanation,source_url,status)
            VALUES(?,?,?,?,?,?,?)
        """, (lesson["unit"], lesson["lesson_number"], lesson["title"], lesson["pattern"],
              lesson["explanation"], lesson["source_url"],
              "available" if lesson["lesson_number"] >= 26 else "completed"))
        lesson_id = cur.lastrowid
        for card in lesson["cards"]:
            card_id = c.execute("""
                INSERT INTO cards(lesson_id,prompt,translation,answer,hint,explanation)
                VALUES(?,?,?,?,?,?)
            """, (lesson_id, card["prompt"], card["translation"], card["answer"],
                  card["hint"], card["explanation"])).lastrowid
            c.execute("INSERT INTO reviews(card_id) VALUES(?)", (card_id,))
    c.commit()
    c.close()


def import_extended_seeds():
    """Add later lesson packs without rebuilding or overwriting the database."""
    c = db()
    for seed_path in EXTENDED_SEED_PATHS:
        if not seed_path.exists():
            continue
        data = json.loads(seed_path.read_text(encoding="utf-8"))
        for lesson in data.get("lessons", []):
            existing = c.execute("SELECT id FROM lessons WHERE lesson_number=?", (lesson["lesson_number"],)).fetchone()
            if existing:
                continue
            lesson_id = c.execute("""
                INSERT INTO lessons(unit,lesson_number,title,pattern,explanation,source_url,status)
                VALUES(?,?,?,?,?,?,?)
            """, (lesson["unit"], lesson["lesson_number"], lesson["title"], lesson["pattern"],
                  lesson["explanation"], lesson["source_url"], "available")).lastrowid
            for card in lesson.get("cards", []):
                card_id = c.execute("""
                    INSERT INTO cards(lesson_id,prompt,translation,answer,hint,explanation)
                    VALUES(?,?,?,?,?,?)
                """, (lesson_id, card["prompt"], card["translation"], card["answer"],
                      card["hint"], card["explanation"])).lastrowid
                c.execute("INSERT INTO reviews(card_id) VALUES(?)", (card_id,))
    c.commit()
    c.close()


def setting(key, default):
    c = db()
    row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    c.close()
    return row["value"] if row else default


def crystals():
    row = one("SELECT crystals FROM wallet WHERE id=1")
    return row["crystals"] if row else 0


def award_crystals(event_key, amount):
    if amount <= 0:
        return
    c = db()
    cur = c.execute("INSERT OR IGNORE INTO reward_events(event_key,amount,created_at) VALUES(?,?,?)", (event_key, amount, datetime.now().isoformat(timespec="seconds")))
    if cur.rowcount:
        c.execute("UPDATE wallet SET crystals=crystals+? WHERE id=1", (amount,))
    c.commit()
    c.close()


def active_item(kind):
    key = "active_face" if kind == "face" else "active_design"
    item_id = setting(key, "face_bunny" if kind == "face" else "design_lavender")
    return one("SELECT * FROM shop_items WHERE id=?", (item_id,))


def buy_or_activate(item_id):
    item = one("SELECT * FROM shop_items WHERE id=?", (item_id,))
    owned = one("SELECT 1 FROM inventory WHERE item_id=?", (item_id,))
    if not owned:
        if crystals() < item["price"]:
            return False
        c = db()
        c.execute("UPDATE wallet SET crystals=crystals-? WHERE id=1", (item["price"],))
        c.execute("INSERT INTO inventory(item_id,purchased_at) VALUES(?,?)", (item_id, datetime.now().isoformat(timespec="seconds")))
        c.commit()
        c.close()
    if item["kind"] == "face":
        set_key = "active_face"
    elif item["kind"] == "design":
        set_key = "active_design"
    else:
        set_key = "active_character"
    set_value = item_id
    c = db(); c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (set_key, set_value)); c.commit(); c.close()
    return True


def rows(sql, params=()):
    c = db()
    result = c.execute(sql, params).fetchall()
    c.close()
    return result


def one(sql, params=()):
    c = db()
    result = c.execute(sql, params).fetchone()
    c.close()
    return result


def normalize(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def answer_is_correct(user, answer):
    return normalize(user) == normalize(answer)


def check_answer(card_id, answer_key):
    """Check the answer when the user presses Enter in the text field."""
    card = one("SELECT answer FROM cards WHERE id=?", (card_id,))
    user_answer = st.session_state.get(answer_key, "")
    st.session_state["checked"] = answer_is_correct(user_answer, card["answer"])


def enable_enter_to_correct(card_id, nonce):
    """When a correct answer is already displayed, Enter clicks Correct."""
    components.html(f"""
    <script>
    (function() {{
        const win = window.parent;
        const marker = 'korean_srs_enter_correct_{card_id}_{nonce}';
        if (win[marker]) return;
        win[marker] = true;
        function findCorrect() {{
            return Array.from(win.document.querySelectorAll('button')).find(function(button) {{
                return (button.innerText || button.textContent || '').trim() === 'Correct';
            }});
        }}
        function handler(event) {{
            if (event.key !== 'Enter') return;
            const button = findCorrect();
            if (!button) return;
            event.preventDefault();
            event.stopPropagation();
            button.click();
        }}
        win.document.addEventListener('keydown', handler, true);
    }})();
    </script>
    """, height=1)


def activate_lesson(lesson_id):
    c = db()
    c.execute("""
        UPDATE reviews SET active=1, level=0, next_review=?, last_review=NULL
        WHERE card_id IN (SELECT id FROM cards WHERE lesson_id=?) AND active=0
    """, (today(), lesson_id))
    c.execute("UPDATE lessons SET status='studying' WHERE id=?", (lesson_id,))
    c.commit()
    c.close()
    award_crystals(f"lesson_started:{lesson_id}", 10)


def ensure_daily_lessons():
    """Assign two stable new lessons for today and keep them until completed."""
    day = today()
    start = int(setting("start_unit", "2"))
    limit = int(setting("new_lessons_per_day", "2"))
    current = one("SELECT COUNT(*) AS n FROM daily_lessons WHERE day=?", (day,))["n"]
    if current >= limit:
        return
    candidates = rows("""
        SELECT * FROM lessons
        WHERE unit>=? AND status='available'
          AND id NOT IN (SELECT lesson_id FROM daily_lessons)
        ORDER BY unit, lesson_number
        LIMIT ?
    """, (start, limit - current))
    if not candidates:
        return
    c = db()
    for lesson in candidates:
        c.execute("INSERT OR IGNORE INTO daily_lessons(day,lesson_id,status) VALUES(?,?,?)", (day, lesson["id"], "new"))
    c.commit()
    c.close()


def daily_lessons():
    ensure_daily_lessons()
    return rows("""
        SELECT lessons.*, daily_lessons.status AS daily_status
        FROM daily_lessons JOIN lessons ON lessons.id=daily_lessons.lesson_id
        WHERE daily_lessons.day=? ORDER BY lessons.lesson_number
    """, (today(),))


def grade(card_id, result):
    current = one("SELECT * FROM reviews WHERE card_id=?", (card_id,))
    level = current["level"]
    mistakes = current["mistakes"]
    if result == "correct":
        level = min(8, level + 1)
    elif result == "wrong":
        level = max(0, level - 2)
        mistakes += 1
    next_date = (date.today() + timedelta(days=SRS_DAYS[level])).isoformat()
    now = datetime.now().isoformat(timespec="seconds")
    c = db()
    c.execute("""
        UPDATE reviews SET level=?, next_review=?, last_review=?, mistakes=?, active=1
        WHERE card_id=?
    """, (level, next_date, now, mistakes, card_id))
    c.execute("INSERT INTO answer_history(card_id,result,created_at) VALUES(?,?,?)", (card_id, result, now))
    c.commit()
    c.close()
    award_crystals(f"card_review:{card_id}:{now}", {"correct": 3, "almost": 1, "wrong": 0}[result])
    st.session_state.pop("checked", None)
    # A widget key cannot be changed after the widget is created in the
    # current Streamlit run. A nonce gives the next card a fresh input field.
    st.session_state["review_nonce"] = st.session_state.get("review_nonce", 0) + 1


def next_new_lesson():
    start = int(setting("start_unit", "2"))
    return one("""
        SELECT * FROM lessons
        WHERE status IN ('available','studying') AND unit>=?
        AND id NOT IN (SELECT lesson_id FROM cards JOIN reviews ON reviews.card_id=cards.id WHERE reviews.active=1)
        ORDER BY unit, lesson_number LIMIT 1
    """, (start,))


def next_due_card():
    # Rotation rule: cards reviewed today go last; NULL/old last_review go first.
    # This matters when all cards in a grammar point share the same due date.
    return one("""
        SELECT cards.*, lessons.title AS lesson_title, lessons.pattern,
               reviews.level, reviews.next_review, reviews.last_review
        FROM cards
        JOIN lessons ON lessons.id=cards.lesson_id
        JOIN reviews ON reviews.card_id=cards.id
        WHERE reviews.active=1 AND reviews.next_review<=? AND lessons.unit>=?
        ORDER BY
            CASE WHEN substr(reviews.last_review,1,10)=? THEN 1 ELSE 0 END,
            COALESCE(reviews.last_review,'0000-01-01T00:00:00'),
            reviews.next_review, cards.id
        LIMIT 1
    """, (today(), int(setting("start_unit", "2")), today()))


def render_card(card):
    st.markdown(f"### {card['prompt']}")
    st.write(f"**Translation:** {card['translation']}")
    with st.expander("Show hint"):
        st.write(card["hint"])
    answer_key = f"answer_{card['id']}_{st.session_state.get('review_nonce', 0)}"
    answer = st.text_input(
        "Your answer",
        key=answer_key,
        on_change=check_answer,
        args=(card["id"], answer_key),
        placeholder="Type the missing Korean form and press Enter",
    )
    if st.button("Check answer", use_container_width=True):
        st.session_state["checked"] = answer_is_correct(answer, card["answer"])
    if "checked" in st.session_state:
        if st.session_state["checked"]:
            st.success("Correct!")
            st.caption("Choose how well you remembered it:")
            a, b, c = st.columns(3)
            if a.button("Correct", key=f"correct_{card['id']}", use_container_width=True):
                grade(card["id"], "correct"); st.rerun()
            if b.button("Almost", key=f"almost_{card['id']}", use_container_width=True):
                grade(card["id"], "almost"); st.rerun()
            if c.button("Wrong", key=f"wrong_{card['id']}", use_container_width=True):
                grade(card["id"], "wrong"); st.rerun()
            enable_enter_to_correct(card["id"], st.session_state.get("review_nonce", 0))
        else:
            st.error("Not quite.")
            if st.button("Show correct answer", use_container_width=True):
                st.info(f"Correct answer: {card['answer']}")
                st.write(card["explanation"])
                if st.button("Mark as wrong", key=f"show_wrong_{card['id']}", use_container_width=True):
                    grade(card["id"], "wrong"); st.rerun()


def page_dashboard():
    st.title("Korean Grammar SRS")
    face = active_item("face")
    design = active_item("design")
    character_id = setting("active_character", "")
    character = one("SELECT * FROM shop_items WHERE id=?", (character_id,)) if character_id else None
    mascot = character["icon"] if character else face["icon"]
    design_colors = {
        "design_sakura": ("#ffdceb", "#ffeef7", "#fff8fc"),
        "design_lavender": ("#e9e0ff", "#f2edff", "#f8f5ff"),
        "design_peach": ("#ffe0c2", "#fff0df", "#fff8ef"),
    }
    color_a, color_b, color_c = design_colors.get(design["id"], ("#ffdceb", "#e9e0ff", "#dff7ff"))
    st.markdown("""
    <div class="chibi-hero" style="background:linear-gradient(110deg, COLOR_A, COLOR_B 58%, COLOR_C);">
        <div class="chibi-face">MASCOT</div>
        <div>
            <div class="chibi-title">Welcome back, little learner!</div>
            <div class="chibi-subtitle">A tiny step today = a big Korean win tomorrow ✨</div>
        </div>
    </div>
    """.replace("COLOR_A", color_a).replace("COLOR_B", color_b).replace("COLOR_C", color_c).replace("MASCOT", mascot), unsafe_allow_html=True)
    st.write("A Bunpro-style review tool based on the How to Study Korean curriculum.")
    due = one("SELECT COUNT(*) AS n FROM reviews JOIN cards ON cards.id=reviews.card_id JOIN lessons ON lessons.id=cards.lesson_id WHERE active=1 AND next_review<=? AND lessons.unit>=?", (today(), int(setting("start_unit", "2"))))["n"]
    active = one("SELECT COUNT(*) AS n FROM reviews WHERE active=1")["n"]
    mastered = one("SELECT COUNT(*) AS n FROM reviews WHERE active=1 AND level>=8")["n"]
    a, b, c = st.columns(3)
    a.metric("Due reviews", due)
    b.metric("Active cards", active)
    c.metric("Mastered cards", mastered)
    st.markdown(f"<div class='cute-note'>💎 <b>{crystals()}</b> crystals · collect more in reviews and daily lessons</div>", unsafe_allow_html=True)
    st.info("Your starting point is Unit 2. Units 0–1 are treated as completed.")

    st.header("Today's new lessons")
    todays = daily_lessons()
    completed = sum(lesson["daily_status"] == "studied" for lesson in todays)
    if todays:
        st.caption(f"{completed} of {len(todays)} new lessons completed today")
        st.progress(completed / len(todays), text="Today's learning quest")
        for lesson in todays:
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    if lesson["daily_status"] == "studied":
                        st.markdown(f"✅ **Lesson {lesson['lesson_number']}: {lesson['title']}**")
                        st.caption("Studied today · cards added to SRS")
                    else:
                        st.markdown(f"**Lesson {lesson['lesson_number']}: {lesson['title']}**")
                        st.caption(lesson["pattern"])
                with right:
                    if lesson["daily_status"] != "studied":
                        if st.button("Study", key=f"daily_study_{lesson['id']}", use_container_width=True):
                            activate_lesson(lesson["id"])
                            c = db()
                            c.execute("UPDATE daily_lessons SET status='studied' WHERE day=? AND lesson_id=?", (today(), lesson["id"]))
                            c.commit()
                            c.close()
                            st.rerun()
                    else:
                        st.success("Done")
    else:
        st.success("No new topics for today.")

    if todays and completed == len(todays):
        award_crystals(f"daily_goal:{today()}", 30)
        st.markdown('<div class="cute-note">૮₍ ˶ᵔ ᵕ ᵔ˶ ₎ა No new topics for today. Great job!</div>', unsafe_allow_html=True)
    elif todays:
        st.markdown('<div class="cute-note">(ง •̀ᴗ•́)ง You can do it! Finish today\'s tiny quest.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="cute-note">(｡•́‿•̀｡) Your lesson shelf is waiting for the next study day.</div>', unsafe_allow_html=True)

    st.divider()
    if st.button("Review", type="primary", use_container_width=True):
        st.session_state["nav"] = "Review"
        st.rerun()


def page_review():
    st.title("Review")
    due = next_due_card()
    if not due:
        st.success("No reviews due today.")
        return
    render_card(due)


def page_lessons():
    st.title("Lessons")
    st.header("Course roadmap")
    for unit, (title, lesson_range, status) in UNIT_INFO.items():
        with st.container(border=True):
            if status == "completed":
                badge = "✅ Completed"
            elif status == "current":
                badge = "🌸 Current unit"
            else:
                badge = "🔒 Locked"
            st.markdown(f"### Unit {unit}: {title}")
            st.caption(f"{lesson_range} · {badge}")
            if unit in HTSK_GROUPS:
                links = " · ".join(f"[{name}]({url})" for name, url in HTSK_GROUPS[unit])
                st.markdown(f"Official lesson pages: {links}")
    st.divider()
    st.header("Available lessons")
    lessons = rows("SELECT * FROM lessons WHERE unit>=? ORDER BY unit, lesson_number", (int(setting("start_unit", "2")),))
    for lesson in lessons:
        cards = one("SELECT COUNT(*) AS n FROM cards WHERE lesson_id=?", (lesson["id"],))["n"]
        active = one("SELECT COUNT(*) AS n FROM cards JOIN reviews ON reviews.card_id=cards.id WHERE lesson_id=? AND active=1", (lesson["id"],))["n"]
        with st.expander(f"Lesson {lesson['lesson_number']}: {lesson['title']} · {active}/{cards} cards active"):
            st.markdown(f"### Lesson {lesson['lesson_number']} guide")
            st.markdown(f"**Grammar point:** `{lesson['pattern']}`")
            st.write(lesson["explanation"])
            st.markdown("**Practice examples**")
            lesson_cards = rows("SELECT prompt, translation, answer, hint, explanation FROM cards WHERE lesson_id=? ORDER BY id", (lesson["id"],))
            for index, card in enumerate(lesson_cards, 1):
                st.markdown(f"**Example {index}:** {card['prompt']}")
                st.caption(f"Translation: {card['translation']} · Target: {card['answer']}")
            st.markdown(f"[Read the full official HTSK explanation ↗]({lesson['source_url']})")
            if st.button("Study this lesson", key=f"study_{lesson['id']}", use_container_width=True):
                activate_lesson(lesson["id"])
                st.success("Lesson added to your SRS.")
                st.rerun()


def page_progress():
    st.title("Progress")
    data = rows("""
        SELECT lessons.unit, lessons.lesson_number, lessons.title,
               COUNT(cards.id) AS cards,
               SUM(CASE WHEN reviews.active=1 THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN reviews.level>=8 THEN 1 ELSE 0 END) AS mastered
        FROM lessons JOIN cards ON cards.lesson_id=lessons.id
        JOIN reviews ON reviews.card_id=cards.id
        WHERE lessons.unit>=? GROUP BY lessons.id ORDER BY lessons.lesson_number
    """, (int(setting("start_unit", "2")),))
    headers = ["Unit", "Lesson", "Title", "Cards", "Active", "Mastered"]
    body = []
    for row in data:
        body.append("<tr>" + "".join([
            f"<td>{row['unit']}</td>",
            f"<td>{row['lesson_number']}</td>",
            f"<td>{row['title']}</td>",
            f"<td>{row['cards'] or 0}</td>",
            f"<td>{row['active'] or 0}</td>",
            f"<td>{row['mastered'] or 0}</td>",
        ]) + "</tr>")
    table = "<div class='chibi-table-wrap'><table class='chibi-table'><thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"
    st.markdown(table, unsafe_allow_html=True)


def page_shop():
    st.title("Crystal Shop ✨")
    st.markdown(f"<div class='cute-note'>💎 You have <b>{crystals()} crystals</b></div>", unsafe_allow_html=True)
    st.write("Earn crystals by studying and reviewing. Buy a cute companion or a new study-room design.")
    items = rows("SELECT * FROM shop_items ORDER BY price, id")
    for item in items:
        owned = one("SELECT 1 FROM inventory WHERE item_id=?", (item["id"],))
        active_key = "active_face" if item["kind"] == "face" else ("active_design" if item["kind"] == "design" else "active_character")
        is_active = setting(active_key, "") == item["id"]
        with st.container(border=True):
            left, middle, right = st.columns([1, 4, 1.5])
            with left:
                st.markdown(f"<div style='font-size:38px;text-align:center'>{item['icon']}</div>", unsafe_allow_html=True)
            with middle:
                st.markdown(f"### {item['name']}")
                st.caption(f"{item['kind'].title()} · {item['description']}")
            with right:
                if is_active:
                    st.success("Active")
                elif owned:
                    if st.button("Use", key=f"use_{item['id']}", use_container_width=True):
                        buy_or_activate(item["id"]); st.rerun()
                elif st.button(f"Buy · {item['price']} 💎", key=f"buy_{item['id']}", use_container_width=True):
                    if buy_or_activate(item["id"]):
                        st.success("Purchased!")
                        st.rerun()
                    else:
                        st.error("Not enough crystals yet.")


init_db()
import_seed_once()
import_extended_seeds()
page = st.sidebar.radio("Navigate", ["Dashboard", "Review", "Lessons", "Progress", "Crystal Shop"], key="nav")
st.sidebar.markdown(f"💎 **{crystals()} crystals**")
st.sidebar.caption("Starting point: Unit 2")
if page == "Dashboard": page_dashboard()
elif page == "Review": page_review()
elif page == "Lessons": page_lessons()
elif page == "Progress": page_progress()
else: page_shop()
