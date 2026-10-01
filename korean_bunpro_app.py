import base64
import json
import re
import sqlite3
import time
from html import escape
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None


APP_DIR = Path(__file__).resolve().parent
# Resolve the database and lesson packs beside this script.  Streamlit Cloud
# can start the script with a working directory different from the repository
# root; relative paths then silently skipped the seed files and left an old
# database's card text on screen.
DB_PATH = APP_DIR / "korean_bunpro.db"
try:
    SUPABASE_DB_URL = st.secrets.get("SUPABASE_DB_URL", "")
except Exception:
    SUPABASE_DB_URL = ""


class CompatRow(dict):
    """A dict row that also supports SQLite-style numeric indexing."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def postgres_sql(sql):
    sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    sql = sql.replace("INSERT OR REPLACE INTO settings", "INSERT INTO settings")
    sql = sql.replace("id INTEGER PRIMARY KEY AUTOINCREMENT", "id BIGSERIAL PRIMARY KEY")
    sql = sql.replace("AUTOINCREMENT", "")
    sql = sql.replace("?", "%s")
    if "INSERT INTO settings" in sql and "ON CONFLICT" not in sql:
        sql = sql.rstrip().rstrip(';') + " ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value"
    elif "INSERT INTO" in sql and "ON CONFLICT" not in sql and "INSERT OR" not in sql:
        # INSERT OR IGNORE was normalized above; this marker is added by the
        # cursor for those statements so ordinary inserts remain unchanged.
        pass
    return sql


class PostgresCursor:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.raw.cursor(cursor_factory=RealDictCursor)
        connection._open_cursors.add(self)
        self.ignore_conflict = False

    def execute(self, sql, params=()):
        self.ignore_conflict = "INSERT OR IGNORE INTO" in sql
        transformed = postgres_sql(sql)
        if self.ignore_conflict and "ON CONFLICT" not in transformed:
            transformed = transformed.rstrip().rstrip(';') + " ON CONFLICT DO NOTHING"
        if transformed.lstrip().upper().startswith("PRAGMA TABLE_INFO"):
            table = re.search(r"PRAGMA TABLE_INFO\(([^)]+)\)", transformed, re.I).group(1).strip()
            transformed = "SELECT ordinal_position AS cid, column_name AS name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position"
            params = (table,)
        try:
            self.cursor.execute(transformed, params)
        except Exception:
            # A failed PostgreSQL statement aborts the whole transaction.  If
            # the same Streamlit session reuses its connection, roll it back
            # immediately so the next button click can still work.
            self.connection.raw.rollback()
            raise
        return self

    def executescript(self, sql):
        self.cursor.execute(postgres_sql(sql))
        return self

    def fetchone(self):
        try:
            row = self.cursor.fetchone()
            return CompatRow(row) if row is not None else None
        finally:
            self.close()

    def fetchall(self):
        try:
            return [CompatRow(row) for row in self.cursor.fetchall()]
        finally:
            self.close()

    @property
    def rowcount(self):
        value = self.cursor.rowcount
        self.close()
        return value

    @property
    def lastrowid(self):
        try:
            self.cursor.execute("SELECT LASTVAL() AS id")
            return self.cursor.fetchone()["id"]
        finally:
            self.close()

    def close(self):
        if not self.cursor.closed:
            self.cursor.close()
        self.connection._open_cursors.discard(self)


class PostgresConnection:
    def __init__(self, url):
        # A short timeout prevents a blocked startup from looking like a blank
        # page in Streamlit Cloud.  The bootstrap lock below serializes the
        # first-run schema/seed work across multiple Streamlit sessions.
        self.url = url
        self._connect()
        self._open_cursors = set()

    def _connect(self):
        # Schema bootstrap can briefly wait for another Streamlit worker that
        # is importing the same seed data.  Ten seconds was too short for a
        # cold Supabase start and surfaced as psycopg2.errors.QueryCanceled.
        connect_options = "-c statement_timeout=60000 -c lock_timeout=60000"
        self.raw = psycopg2.connect(self.url, connect_timeout=15, options=connect_options) if "sslmode=" in self.url else psycopg2.connect(self.url, sslmode="require", connect_timeout=15, options=connect_options)
        self.last_used = time.monotonic()

    def ensure_alive(self):
        # Mobile browsers can suspend the Streamlit websocket while the phone
        # is locked.  Reopen an idle PostgreSQL socket before the next query.
        if getattr(self.raw, "closed", 1) or time.monotonic() - self.last_used > 45:
            try:
                self.raw.close()
            except Exception:
                pass
            self._connect()

    def execute(self, sql, params=()):
        self.ensure_alive()
        return PostgresCursor(self).execute(sql, params)

    def executescript(self, sql):
        self.ensure_alive()
        return PostgresCursor(self).executescript(sql)

    def commit(self):
        self.raw.commit()
        self.last_used = time.monotonic()
        for cursor in list(self._open_cursors):
            cursor.close()

    def close(self):
        # Keep one network connection per Streamlit browser session, but do
        # finish the current PostgreSQL transaction when a helper is done.
        # psycopg2 otherwise leaves a read transaction open after SELECT;
        # that idle transaction holds an AccessShareLock and can make a later
        # one-time ALTER TABLE migration wait until Supabase cancels it.
        if getattr(self.raw, "closed", 1):
            return None
        try:
            self.raw.commit()
        except Exception:
            # A failed statement leaves PostgreSQL in an aborted transaction.
            # Release it before the persistent session is reused.
            self.raw.rollback()
        self.last_used = time.monotonic()


def is_postgres_connection(connection):
    """Recognize cached connections even after Streamlit reloads this module."""
    return hasattr(connection, "raw") and hasattr(connection, "commit")
BTS_ASSET_DIR = APP_DIR / "bts_chibi"
SEED_PATH = APP_DIR / "unit2_lessons_26_33.json"
EXTENDED_SEED_PATHS = [APP_DIR / name for name in (
    "unit0_1_lessons_0_25.json",
    "unit2_lessons_34_50.json",
    "unit3_lessons_51_75.json",
    "unit4_lessons_76_100.json",
    "unit5_lessons_101_116.json",
    "unit5_lessons_117_125.json",
    "unit6_lessons_126_133.json",
    "unit6_lessons_134_150.json",
    "unit7_lessons_151_175.json",
    "unit8_lessons_176_200.json",
    "unit9_lessons_201_208.json",
)]
# Lessons whose main teaching goal is a set of lexical items. Their cards
# must not collapse into one repeated answer; each card must ask for a
# different target word or lexical expression.
VOCABULARY_LESSON_NUMBERS = frozenset({11, 12, 25, 34, 59, 60, 79, 101, 130, 134, 135, 151, 152})
# A complete card answer must include the lexical stem and the grammar. These
# grammar-only tails appeared in older deployed databases when the blank was
# placed too late in the sentence. Keep this guard close to the seed validator
# so a future content edit cannot reintroduce that regression.
INCOMPLETE_GRAMMAR_TAILS = frozenset({
    "것 같아", "것 같아요", "것 같다", "것 같았어", "것 같았어요",
    "것 같을 거야", "거예요", "거야", "수 있도록", "수 없도록",
    "채로", "거라니까", "말이야", "말이지", "라고 했어요",
    "뻔 했어요", "뻔했어요", "만해요", "만한", "리가 없어요",
    "걸까 싶어요", "중이오니",
    "듯하다", "듯해", "듯해요", "요",
})
# Bunpro-style review ladder. The level is the current consecutive-correct
# streak. A wrong answer drops one level; the same card stays for retry.
BUNPRO_INTERVALS = {
    0: timedelta(hours=4), 1: timedelta(hours=8), 2: timedelta(days=1),
    3: timedelta(days=2), 4: timedelta(days=4), 5: timedelta(days=8),
    6: timedelta(days=12), 7: timedelta(days=24), 8: timedelta(days=48),
    9: timedelta(days=96), 10: timedelta(days=176),
}
SRS_MAX_LEVEL = 11
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
    2: [("Lessons 26–33", "https://www.howtostudykorean.com/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-26-33/"), ("Lessons 34–41", "https://www.howtostudykorean.com/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-34-41/"), ("Lessons 42–50", "https://www.howtostudykorean.com/unit-2-lower-intermediate-korean-grammar/unit-2-lessons-42-50/")],
    3: [("Lessons 51–58", "https://www.howtostudykorean.com/unit-3-intermediate-korean-grammar/unit-3-lessons-51-58/"), ("Lessons 59–66", "https://www.howtostudykorean.com/unit-3-intermediate-korean-grammar/unit-3-lessons-59-66/"), ("Lessons 67–75", "https://www.howtostudykorean.com/unit-3-intermediate-korean-grammar/unit-3-lessons-67-75/")],
    4: [("Lessons 76–83", "https://www.howtostudykorean.com/upper-intermediate-korean-grammar/unit-4-lessons-76-83/"), ("Lessons 84–91", "https://www.howtostudykorean.com/upper-intermediate-korean-grammar/unit-4-lessons-84-91/"), ("Lessons 92–100", "https://www.howtostudykorean.com/upper-intermediate-korean-grammar/unit-4-lessons-92-100/")],
    5: [("Lessons 101–108", "https://www.howtostudykorean.com/unit-5/lessons-101-108/"), ("Lessons 109–116", "https://www.howtostudykorean.com/unit-5/lessons-109-116/"), ("Lessons 117–125", "https://www.howtostudykorean.com/unit-5/lessons-117-125/")],
    6: [("Lessons 126–133", "https://www.howtostudykorean.com/unit-6/lessons-126-133/"), ("Lessons 134–141", "https://www.howtostudykorean.com/unit-6/lessons-134-141/"), ("Lessons 142–150", "https://www.howtostudykorean.com/unit-6/lessons-142-150/")],
    7: [("Lessons 151–158", "https://www.howtostudykorean.com/unit-7/lessons-151-158/"), ("Lessons 159–166", "https://www.howtostudykorean.com/unit-7/lessons-159-166/"), ("Lessons 167–175", "https://www.howtostudykorean.com/unit-7/lessons-167-175/")],
    8: [("Lessons 176–183", "https://www.howtostudykorean.com/unit-8/lessons-176-183/"), ("Lessons 184–191", "https://www.howtostudykorean.com/unit-8/lessons-184-191/"), ("Lessons 192–200", "https://www.howtostudykorean.com/unit-8/lessons-192-200/")],
    9: [("Lessons 201–208", "https://www.howtostudykorean.com/unit-9/lessons-201-208/")],
}

# Each lesson's shortened HTSK guide is embedded in its unit JSON record.
FRAME_STYLES = {
    "frame_sakura": {
        "border": "#efb8d6",
        "background": "#fff7fc",
        "accent": "#ef8fbb",
        "decor": "🌸",
        "label": "Sakura petals",
    },
    "frame_cloud": {
        "border": "#b9d9ed",
        "background": "#f5fbff",
        "accent": "#77bdda",
        "decor": "☁️",
        "label": "Cloudy sky",
    },
    "frame_hearts": {
        "border": "#f2a9c4",
        "background": "#fff4f8",
        "accent": "#ed6f9e",
        "decor": "💗",
        "label": "Heart confetti",
    },
    "frame_rainbow": {
        "border": "#c4a8ed",
        "background": "#fff9f2",
        "accent": "#a27be0",
        "decor": "🌈",
        "label": "Rainbow ribbon",
    },
    "frame_blossom": {
        "border": "#e8ae91",
        "background": "#fff8f2",
        "accent": "#dc8d68",
        "decor": "🌺",
        "label": "Peach blossom",
    },
}
TRACKER_COLORS = {
    "tracker_mochi": "#f5a6c8",
    "tracker_stars": "#c1a7f1",
    "tracker_bubbles": "#8dd9e5",
    "tracker_rainbow": "#f0a6a6",
    "tracker_sakura": "#e8a7c5",
}

# These are original in-app encouragements written for the chibi companions.
# The two daily friends rotate through the requested pairs: Jimin with Jung
# Kook, V (Taehyung) with Jin, and all three pairings among RM, SUGA and
# j-hope.  They are not presented as real quotations or official BTS content.
BTS_PAIR_ROTATION = (
    ("Jimin", "🐣", "Jung Kook", "🐰"),
    ("V", "🐯", "Jin", "🐹"),
    ("RM", "🐨", "SUGA", "🐱"),
    ("RM", "🐨", "j-hope", "🐿️"),
    ("SUGA", "🐱", "j-hope", "🐿️"),
)
BTS_MOTIVATION = [
    {"level": 1, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "오늘도 한 문장만 읽어도 충분해요.", "en": "Reading just one sentence today is already enough."},
    {"level": 1, "ko_member": "V", "ko_icon": "🐯", "en_member": "Jin", "en_icon": "🐹", "ko": "천천히 해도 괜찮아요. 매일 조금씩 나아지고 있어요.", "en": "It is okay to go slowly. You are getting better little by little every day."},
    {"level": 1, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "작은 성공도 소중한 성공이에요.", "en": "A small success is still a precious success."},
    {"level": 2, "ko_member": "V", "ko_icon": "🐯", "en_member": "Jin", "en_icon": "🐹", "ko": "틀린 답은 멈춤이 아니라 다음 시도를 위한 힌트예요.", "en": "A wrong answer is not a stop; it is a hint for your next attempt."},
    {"level": 2, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "익숙한 표현을 직접 써 볼 때 실력이 더 단단해져요.", "en": "Your skills become stronger when you use a familiar expression yourself."},
    {"level": 2, "ko_member": "V", "ko_icon": "🐯", "en_member": "Jin", "en_icon": "🐹", "ko": "오늘 배운 문법을 한 문장으로 만들어 보면 기억에 오래 남아요.", "en": "If you make one sentence with today's grammar, it will stay with you longer."},
    {"level": 3, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "꾸준히 복습하면 어제 어렵던 문장도 자연스럽게 읽을 수 있어요.", "en": "With steady review, you can read naturally even the sentences that felt difficult yesterday."},
    {"level": 3, "ko_member": "V", "ko_icon": "🐯", "en_member": "Jin", "en_icon": "🐹", "ko": "새로운 문법을 이해할 때마다 한국어로 표현할 수 있는 생각이 넓어져요.", "en": "Every time you understand new grammar, more of your thoughts become expressible in Korean."},
    {"level": 3, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "실수한 부분을 다시 살펴보는 습관이 실력을 오래 지켜 줘요.", "en": "The habit of revisiting your mistakes protects your progress for the long term."},
    {"level": 4, "ko_member": "V", "ko_icon": "🐯", "en_member": "Jin", "en_icon": "🐹", "ko": "문맥 속에서 표현의 뉘앙스를 비교하면 더 정확하게 선택할 수 있어요.", "en": "Comparing nuances in context helps you choose the most accurate expression."},
    {"level": 4, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "익숙한 문법을 새로운 상황에 옮겨 쓰는 순간, 지식이 진짜 실력이 돼요.", "en": "When you carry familiar grammar into a new situation, knowledge becomes real skill."},
    {"level": 4, "ko_member": "V", "ko_icon": "🐯", "en_member": "Jin", "en_icon": "🐹", "ko": "긴 문장도 관계를 하나씩 나누어 보면 핵심 의미가 선명해져요.", "en": "Even a long sentence becomes clear when you separate its relationships one by one."},
    {"level": 5, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "복잡한 문장일수록 화자의 의도와 문법의 기능을 함께 살펴보면 의미가 정확해져요.", "en": "The more complex a sentence is, the more accurately you understand it by considering the speaker's intent and the grammar's function together."},
    {"level": 5, "ko_member": "V", "ko_icon": "🐯", "en_member": "Jin", "en_icon": "🐹", "ko": "배운 표현을 자기 경험과 연결해 사용할 때 언어가 수동적인 지식에서 능동적인 감각으로 바뀌어요.", "en": "When you connect a learned expression to your own experience, language shifts from passive knowledge to active intuition."},
    {"level": 5, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "한 번에 완벽하려고 하기보다 반복 속에서 의미와 뉘앙스를 정교하게 다듬어 가면 돼요.", "en": "You do not need to be perfect at once; refine meaning and nuance gradually through repetition."},
]
BTS_ASSET_FILES = {
    "RM": "rm.png",
    "Jin": "jin.png",
    "SUGA": "suga.png",
    "j-hope": "jhope.png",
    "Jimin": "jimin.png",
    "V": "v.png",
    "Jung Kook": "jungkook.png",
}
BTS_VECTOR_PALETTE = {
    "RM": ("#9276c9", "#5a477d"),
    "Jin": ("#f2a2ba", "#d27999"),
    "SUGA": ("#556fa9", "#303c69"),
    "j-hope": ("#f3a53c", "#e77925"),
    "Jimin": ("#f4a9b9", "#df7893"),
    "V": ("#4f9d91", "#2f6c68"),
    "Jung Kook": ("#4b86d8", "#28539b"),
}
# The daily pair uses a stable date-based layout, so a Streamlit rerun does
# not make the characters jump around while the learner is reading.  The
# layout changes on the next day and keeps the two friends in different parts
# of the app.
BTS_SCENE_LAYOUTS = [
    ("left:2.5%;top:102px;", "right:2.5%;bottom:10px;"),
    ("left:8%;bottom:12px;", "right:7%;top:94px;"),
    ("left:1%;top:150px;", "right:4%;bottom:20px;"),
    ("left:14%;top:86px;", "right:1%;bottom:4px;"),
    ("left:3%;bottom:4px;", "right:15%;top:116px;"),
    ("left:10%;top:118px;", "right:2%;bottom:34px;"),
]
SHOP_ITEMS = [
    ("face_bunny", "Sleepy Bunny", "face", 0, "૮ ˶ᵔ ᵕ ᵔ˶ ა", "Your starter study buddy"),
    ("face_cat", "Happy Cat", "face", 180, "ฅ^•ﻌ•^ฅ", "Smiles when you finish a review"),
    ("face_bear", "Tiny Bear", "face", 240, "ʕ•ᴥ•ʔ", "A calm little learning bear"),
    ("character_rabbit", "Bunny Scholar", "character", 320, "🐰", "Cheerful character for your dashboard"),
    ("character_penguin", "Study Penguin", "character", 400, "🐧", "A brave penguin who loves review days"),
    ("design_sakura", "Sakura Dream", "design", 220, "🌸", "Pink sakura study room"),
    ("design_lavender", "Lavender Cloud", "design", 260, "☁️", "Soft purple cloud theme"),
    ("design_peach", "Peach Soda", "design", 320, "🍑", "Warm peachy study theme"),
    ("frame_sakura", "Sakura Border", "frame", 180, "🌸", "A delicate blossom frame for review cards"),
    ("frame_cloud", "Cloudy Border", "frame", 220, "☁️", "A soft cloud border for calm study sessions"),
    ("tracker_mochi", "Mochi Tracker", "tracker", 240, "🍡", "A cute mochi progress-bar style"),
    ("tracker_stars", "Starry Tracker", "tracker", 280, "⭐", "A sparkling progress-bar style"),
    ("face_fox", "Shy Fox", "face", 300, "ᵔᴥᵔ", "A bashful fox study buddy"),
    ("face_puppy", "Happy Puppy", "face", 360, "◕ᴥ◕", "A puppy who celebrates every answer"),
    ("face_mochi", "Mochi Smile", "face", 440, "●ᴗ●", "A round little mochi companion"),
    ("character_koala", "Boba Koala", "character", 360, "🐨", "A sleepy koala with a boba treat"),
    ("character_tiger", "Tiger Scholar", "character", 460, "🐯", "A brave tiger for difficult grammar"),
    ("character_dango", "Dango Fairy", "character", 560, "🍡", "A tiny dango fairy for your study room"),
    ("design_mint", "Mint Matcha", "design", 360, "🍵", "Fresh mint and matcha study room"),
    ("design_sky", "Sky Kawaii", "design", 420, "🌤️", "A bright blue afternoon theme"),
    ("design_night", "Moonlit Seoul", "design", 520, "🌙", "A soft evening city theme"),
    ("frame_hearts", "Heart Confetti", "frame", 300, "💗", "A cheerful heart frame for reviews"),
    ("frame_rainbow", "Rainbow Ribbon", "frame", 380, "🌈", "A colorful ribbon around your study space"),
    ("frame_blossom", "Peach Blossom", "frame", 460, "🌺", "A warm floral frame"),
    ("tracker_bubbles", "Bubble Tracker", "tracker", 340, "🫧", "A bubbly progress journey"),
    ("tracker_rainbow", "Rainbow Tracker", "tracker", 420, "🌈", "A colorful progress journey"),
    ("tracker_sakura", "Sakura Petals", "tracker", 500, "🌸", "Petals bloom as your review grows"),
]

st.set_page_config(page_title="Mochi Hangul", page_icon="🍡", layout="wide")
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background: linear-gradient(135deg, #fff8fc 0%, #f6f1ff 52%, #eefaff 100%) !important;}
    header[data-testid="stHeader"] {background: transparent !important;}
    [data-testid="stToolbar"] {visibility: hidden; height: 0;}
    [data-testid="stDecoration"] {display: none;}
    .stApp {background: transparent !important; color: #5b4770 !important;}
    h1, h2, h3, h4, h5, h6, p, label, [data-testid="stMarkdownContainer"], [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] {color: #5b4770 !important;}
    code, .stMarkdown code {background:#fff8fc !important; color:#5a4050 !important; border:2px solid #f2b8d5; border-radius:16px; padding:.35rem .75rem; box-shadow:0 4px 12px rgba(217,143,179,.16); font-size:clamp(1.05rem,2.5vw,1.35rem); font-weight:700; line-height:1.45; overflow-wrap:anywhere;}
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
    .review-progress {position:relative; display:block; clear:both; z-index:2; padding:12px 18px 10px; border:2px solid #f0c5df; border-radius:24px; background:linear-gradient(110deg,#fff7fc,#f4efff); box-shadow:0 8px 20px rgba(134,101,156,.10); margin:0 0 28px; width:100%; box-sizing:border-box;}
    .review-progress-title {display:flex; justify-content:space-between; align-items:center; color:#654b78; font-weight:800; margin-bottom:8px;}
    .review-progress-track {height:20px; position:relative; border-radius:99px; background:#eadff2; overflow:visible; border:1px solid #e2cbe1; margin:8px 10px 14px;}
    .review-progress-fill {height:100%; border-radius:99px; background:linear-gradient(90deg,#f5a6c8,#c1a7f1,#9edbe0); transition:width .35s ease;}
    .progress-mascot {position:absolute; left:0; top:50%; transform:translateY(-50%); z-index:3; display:flex; align-items:center; justify-content:center; width:38px; height:38px; border-radius:50%; background:#fff; border:3px solid #fff; box-shadow:0 4px 12px rgba(104,77,123,.22); font-size:23px; line-height:1; transition:left .35s ease, transform .15s ease;}
    .review-frame {border:3px solid #efb8d6; border-radius:30px; padding:18px 22px 8px; background:rgba(255,255,255,.55); box-shadow:0 10px 25px rgba(134,101,156,.08);}
    .review-card-top {display:flex; align-items:center; justify-content:space-between; gap:12px; padding:5px 2px 14px; color:#654b78; font-weight:800; font-size:15px;}
    .review-card-top span {display:inline-flex; align-items:center; gap:7px;}
    .review-card-bottom {padding:14px 2px 2px; text-align:center; color:#987a9d; font-size:13px;}
    .review-question-paper {padding:13px 0 12px; margin:2px 0 10px; border:0; border-radius:0; background:transparent; box-shadow:none; text-align:center;}
    .review-question-paper .review-prompt {color:#4f3d64; font-size:clamp(1.16rem,2.7vw,1.45rem); font-weight:850; line-height:1.5; overflow-wrap:anywhere; text-align:center;}
    .review-question-paper .review-translation {margin-top:8px; color:#654b78; font-family:"Aptos","Segoe UI",sans-serif; font-size:clamp(.98rem,2.2vw,1.08rem); font-weight:500; line-height:1.5; overflow-wrap:anywhere; text-align:center;}
    .answer-form-note {margin-top:7px; color:#886d91; font-size:.9rem; line-height:1.4; text-align:center;}
    .inline-answer-slot {display:inline-flex; align-items:baseline; vertical-align:baseline; min-width:1.25em; min-height:1.15em; text-align:left;}
    .inline-answer-slot > .inline-answer-element {display:inline-flex !important; align-items:baseline; width:auto !important; min-width:0 !important; margin:0 !important; padding:0 !important; vertical-align:baseline;}
    .inline-answer-element [data-testid="stTextInput"] {display:inline-flex !important; align-items:baseline; width:auto !important; min-width:0 !important; margin:0 !important; padding:0 !important;}
    .inline-answer-element [data-testid="stTextInput"] > div {display:inline-flex !important; width:auto !important; min-width:0 !important; margin:0 !important; padding:0 !important;}
    .inline-answer-element label, .inline-answer-element [data-testid="InputInstructions"] {display:none !important;}
    .inline-answer-element, .inline-answer-element *, .inline-answer-element [data-testid="stTextInput"], .inline-answer-element [data-baseweb="input"], .inline-answer-element [data-baseweb="base-input"], .inline-answer-element input, input.inline-answer-input, input[aria-label^="Answer for card "] {border:0 !important; border-width:0 !important; border-color:transparent !important; border-radius:0 !important; outline:0 !important; background:transparent !important; background-color:transparent !important; background-image:none !important; box-shadow:none !important; color:inherit !important; -webkit-text-fill-color:inherit !important;}
    .inline-answer-element input, input.inline-answer-input, input[aria-label^="Answer for card "] {display:inline-block !important; width:1.35em; min-width:1.35em; max-width:none !important; height:1.45em; margin:0 !important; padding:0 .06em .04em !important; font:inherit !important; line-height:1.3 !important; text-align:left; appearance:none !important; -webkit-appearance:none !important;}
    .inline-answer-element:focus-within, .inline-answer-element input:focus, input.inline-answer-input:focus, input[aria-label^="Answer for card "]:focus, .inline-answer-element input:hover, input.inline-answer-input:hover, input[aria-label^="Answer for card "]:hover {border:0 !important; border-width:0 !important; border-color:transparent !important; outline:0 !important; box-shadow:none !important; background:transparent !important; background-color:transparent !important; background-image:none !important; color:inherit !important; -webkit-text-fill-color:inherit !important;}
    .inline-answer-element input::placeholder, input.inline-answer-input::placeholder, input[aria-label^="Answer for card "]::placeholder {color:inherit !important; -webkit-text-fill-color:inherit !important; opacity:1 !important;}
    .answer-widget-marker {display:none !important;}
    .answer-results {padding:8px 0; color:#514064; text-align:center; font-size:1.05rem; line-height:1.8;}
    .answer-results .answer-result-value {color:#4f3d64; font-weight:800;}
    @media (max-width: 700px) { .review-progress {padding:10px 12px 9px;} .review-progress-track {margin-left:4px; margin-right:4px;} }
    .frame-sparkles {letter-spacing:4px; color:#d98eb8; font-size:16px;}
    .streak-card {display:flex; align-items:center; justify-content:space-between; gap:16px; padding:13px 18px; margin:14px 0 18px; border:2px solid #f0c5df; border-radius:22px; background:linear-gradient(110deg,#fff7df,#fff3f8 55%,#f2edff); box-shadow:0 7px 18px rgba(134,101,156,.08);}
    .streak-main {display:flex; align-items:center; gap:10px; color:#654b78; font-weight:900; font-size:18px;}
    .streak-fire {font-size:28px; line-height:1;}
    .streak-meta {color:#987a9d; font-size:13px; text-align:right;}
    /* The daily chibi companions are real bundled transparent PNG cut-outs.
       They float above the page; the only outlined elements are the speech
       bubbles themselves, not character cards or frames. */
    /* This is only a DOM anchor. The characters themselves are fixed above
       the whole app, so no empty panel or daily chibi field is shown. */
    .bts-surface {position:relative; width:0; height:0; min-height:0; margin:0; padding:0; overflow:visible; background:transparent;}
    .bts-dialog-surface {position:fixed; inset:0; width:100vw; height:100vh; z-index:2147483002; pointer-events:none; overflow:visible;}
    .bts-dialog-surface .bts-scene {z-index:2147483003;}
    .bts-scene {position:fixed; z-index:2147483646 !important; display:flex; align-items:flex-end; gap:10px; width:max-content; max-width:calc(100vw - 20px); pointer-events:auto !important; cursor:grab; touch-action:none; user-select:none; -webkit-user-select:none; will-change:left,top;}
    .bts-scene.bts-dragging {cursor:grabbing; z-index:2147483646 !important;}
    .bts-scene-right {flex-direction:row-reverse;}
    .bts-character {width:128px; height:205px; flex:0 0 auto; object-fit:contain; pointer-events:auto !important; user-select:none; -webkit-user-select:none; -webkit-user-drag:none; filter:drop-shadow(0 9px 8px rgba(91,71,112,.18)); animation:bts-float 3.8s ease-in-out infinite;}
    .bts-scene-right .bts-character {animation-delay:-1.3s;}
    @keyframes bts-float {0%,100%{transform:translateY(0) rotate(-1deg)}50%{transform:translateY(-7px) rotate(1deg)}}
    .bts-character-fallback {display:flex; align-items:center; justify-content:center; width:92px; height:150px; flex:0 0 auto; font-size:54px;}
    .bts-vector-fallback {width:128px; height:205px; flex:0 0 auto; display:flex; align-items:flex-end; justify-content:center; pointer-events:auto; filter:drop-shadow(0 9px 8px rgba(91,71,112,.18)); animation:bts-float 3.8s ease-in-out infinite;}
    .bts-scene-right .bts-vector-fallback {animation-delay:-1.3s;}
    .bts-vector {width:100%; height:100%; overflow:visible;}
    .bts-speech {position:relative; width:max-content; max-width:250px; min-width:168px; padding:11px 14px 12px; border:2px solid #e9b9d7; border-radius:22px; background:rgba(255,255,255,.96); box-shadow:0 7px 16px rgba(134,101,156,.13); color:#5b4770; pointer-events:auto !important; cursor:grab;}
    .bts-scene-right .bts-speech {border-color:#cdb9ec;}
    .bts-scene-left .bts-speech::after, .bts-scene-right .bts-speech::after {content:""; position:absolute; top:54%; width:0; height:0; border-style:solid;}
    .bts-scene-left .bts-speech::after {left:-12px; border-width:9px 12px 9px 0; border-color:transparent #e9b9d7 transparent transparent;}
    .bts-scene-right .bts-speech::after {right:-12px; border-width:9px 0 9px 12px; border-color:transparent transparent transparent #cdb9ec;}
    .bts-speaker {display:none;}
    .bts-label {display:none;}
    .bts-quote {color:#5b4770; font-size:16px; line-height:1.55; overflow-wrap:anywhere;}
    .bts-character-alt {display:none;}
    .lesson-modal-heading {padding:8px 0 12px; border-bottom:2px dashed #efbdd8; color:#654b78;}
    .lesson-modal-heading h2 {margin:0; color:#654b78;}
    .lesson-modal-heading p {margin:5px 0 0; color:#987a9d; font-size:13px;}
    .lesson-guide-copy {padding:14px 16px; margin:12px 0 8px; border:1px solid #efd8e8; border-radius:20px; background:#fffaff; color:#514064; box-shadow:0 5px 14px rgba(134,101,156,.08); line-height:1.65; overflow-wrap:anywhere;}
    .lesson-guide-copy > div:last-child {color:#514064 !important;}
    .lesson-section-title {margin-top:18px; color:#654b78; font-size:18px; font-weight:900;}
    .lesson-example {padding:13px 15px; margin:10px 0; border:1px solid #efd8e8; border-left:5px solid #efb8d6; border-radius:0 17px 17px 0; background:#ffffff; color:#514064; box-shadow:0 5px 14px rgba(134,101,156,.08); overflow-wrap:anywhere;}
    .lesson-example > div:first-child {color:#514064 !important; font-size:16px; line-height:1.6;}
    [class*="st-key-review_card_shell"] {border:0 !important; border-radius:32px !important; background:#fffaff !important; box-shadow:0 12px 28px rgba(134,101,156,.14) !important; padding:9px 16px 12px !important;}
    [class*="st-key-review_card_shell"] [data-testid="stVerticalBlockBorderWrapper"] {border:3px solid #efb8d6 !important; border-radius:25px !important; background:#fffaff !important;}
    [class*="st-key-review_card_shell"] [data-testid="stMarkdownContainer"] {color:#514064 !important;}
    [class*="st-key-lesson_actions_"] {position:sticky; bottom:0; z-index:8; margin-top:12px; padding:10px 0 3px; background:linear-gradient(180deg,rgba(246,241,255,.25),rgba(246,241,255,.98) 28%); border-top:2px solid #efc8df;}
    .modal-kicker {display:flex; align-items:center; justify-content:space-between; gap:12px; padding:4px 0 12px; color:#987a9d; font-size:13px;}
    .modal-kicker strong {color:#654b78; font-size:18px;}
    /* Streamlit renders the modal as a full-screen .stDialog overlay, a panel,
       and a role=dialog content wrapper.  The overlay owns scrolling for long
       HTSK lessons; only the panel gets the visible border, so there is one
       frame and no dashboard/sidebar text can show through. */
    [data-testid="stDialog"], .stDialog {position:fixed !important; inset:0 !important; z-index:1000000 !important; display:flex !important; align-items:flex-start !important; justify-content:center !important; padding:4vh 0 !important; background:rgba(73,48,93,.28) !important; overflow-y:auto !important; overflow-x:hidden !important; opacity:1 !important;}
    [data-testid="stDialog"] > div, .stDialog > div {position:relative !important; isolation:isolate !important; width:96vw !important; max-width:96vw !important; min-width:0 !important; min-height:92vh !important; height:auto !important; max-height:none !important; margin:0 !important; padding:0 !important; border:3px solid #efb8d6 !important; border-radius:30px !important; background:transparent !important; box-shadow:0 22px 65px rgba(73,48,93,.28) !important; overflow:visible !important; display:flex !important; flex-direction:column !important;}
    [data-testid="stDialog"] > div::before, .stDialog > div::before {content:""; position:absolute; inset:3px; z-index:0; border-radius:27px; background:#fffaff; pointer-events:none;}
    [data-testid="stDialog"] [role="dialog"], .stDialog [role="dialog"] {position:relative !important; z-index:1 !important; width:100% !important; max-width:none !important; min-width:0 !important; min-height:100% !important; height:auto !important; max-height:none !important; margin:0 !important; padding:0 !important; border:0 !important; border-radius:0 !important; background:transparent !important; box-shadow:none !important; overflow:visible !important; display:flex !important; flex-direction:column !important;}
    [data-testid="stDialog"] [role="dialog"] > div, .stDialog [role="dialog"] > div {background:transparent !important;}
    [data-testid="stDialog"] [role="dialog"] > div:last-of-type, .stDialog [role="dialog"] > div:last-of-type {flex:1 1 auto !important; min-height:0 !important; overflow-y:auto !important; overflow-x:hidden !important; background:transparent !important; color:#514064 !important;}
    [data-testid="stDialog"] .block-container, .stDialog .block-container {position:relative !important; z-index:1 !important; width:100% !important; max-width:1180px !important; padding:1.4rem 2rem 2rem !important; background:transparent !important; border-radius:24px !important;}
    [data-testid="stDialog"] [data-testid="stMarkdownContainer"], .stDialog [data-testid="stMarkdownContainer"] {overflow-wrap:anywhere; word-break:normal; line-height:1.55;}
    .quest-card {padding:14px 18px 16px; margin:14px 0 20px; border:2px solid #f0c5df; border-radius:24px; background:linear-gradient(110deg,#fff1f7,#f4efff 65%,#effcff); box-shadow:0 8px 20px rgba(134,101,156,.10);}
    .quest-title {display:flex; justify-content:space-between; gap:12px; color:#654b78; font-weight:800; margin-bottom:9px;}
    .quest-track {height:18px; position:relative; border-radius:99px; background:#eadff2; overflow:visible; border:1px solid #e3cde1; margin:8px 10px 14px;}
    .quest-fill {height:100%; border-radius:99px; background:linear-gradient(90deg,#f5a6c8,#c1a7f1,#9edbe0);}
    .quest-caption {margin-top:7px; color:#886d91; font-size:13px;}
    .brand-logo {display:flex; align-items:center; gap:10px; padding:10px 12px 16px; margin-bottom:12px; border-bottom:2px dashed #efbdd8; color:#654b78;}
    .brand-mark {width:42px; height:42px; display:flex; align-items:center; justify-content:center; border-radius:15px; background:linear-gradient(135deg,#ffb7d4,#c5b2f5); font-size:25px; box-shadow:0 5px 12px rgba(140,105,150,.15);}
    .brand-name {font-weight:900; font-size:20px; line-height:1.05;}
    .brand-subtitle {font-size:11px; color:#987a9d; margin-top:3px;}
    [data-testid="stExpander"] {border:2px solid #efc4de !important; border-radius:22px !important; background:#fffaff !important; color:#654b78 !important; overflow:visible !important; margin:10px 0 !important;}
    [data-testid="stExpander"] details {background:#fffaff !important; color:#654b78 !important; border-radius:20px !important;}
    [data-testid="stExpander"] details > summary,
    [data-testid="stExpander"] summary[data-testid="stExpanderToggle"] {background:#fffaff !important; color:#654b78 !important; border-radius:20px !important; font-weight:800 !important;}
    [data-testid="stExpander"] details[open] > summary,
    [data-testid="stExpander"] details[open] summary[data-testid="stExpanderToggle"] {background:linear-gradient(110deg,#fbe7f3,#eee7ff) !important; color:#5b4770 !important;}
    [data-testid="stExpander"] summary:hover {background:#f8edf8 !important; color:#5b4770 !important;}
    [data-testid="stExpander"] summary > div,
    [data-testid="stExpander"] summary * {background:transparent !important; color:#654b78 !important;}
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p {color:#654b78 !important;}
    [data-testid="stExpander"] summary svg {color:#684d7b !important; fill:#684d7b !important;}
    .stTextInput input:not(.inline-answer-input):not([aria-label^="Answer for card "]) {font-size: 1.1rem; border-radius: 16px; border: 2px solid #e8cfe1; background: #ffffff !important; color: #5b4770 !important; -webkit-text-fill-color: #5b4770 !important;}
    .stTextInput input:not(.inline-answer-input):not([aria-label^="Answer for card "])::placeholder {color: #9b82a5 !important; -webkit-text-fill-color: #9b82a5 !important; opacity: 1 !important;}
    .chibi-table-wrap {overflow-x:auto; border:2px solid #f0cfe0; border-radius:20px; background:rgba(255,255,255,.82); box-shadow:0 8px 20px rgba(134,101,156,.08);}
    .chibi-table {width:100%; border-collapse:collapse; color:#5b4770; min-width:680px;}
    .chibi-table th {background:#f7dbea; color:#684d7b; text-align:left; padding:12px 14px; font-weight:800;}
    .chibi-table td {padding:11px 14px; border-top:1px solid #f1dce8; color:#5b4770;}
    .chibi-table tr:nth-child(even) td {background:#fffafd;}
    .chibi-hero {display:flex; align-items:center; gap:20px; padding:22px 26px; margin:8px 0 24px; border-radius:28px; background:linear-gradient(110deg,#ffdceb,#e9e0ff 58%,#dff7ff); border:2px solid #f2c8df; box-shadow:0 10px 24px rgba(134,101,156,.10);}
    .chibi-face {font-size:42px; line-height:1; white-space:nowrap;}
    .shop-item-icon {display:flex; align-items:center; justify-content:center; min-width:0; min-height:48px; font-size:30px; line-height:1.1; white-space:nowrap; overflow:visible;}
    .chibi-title {font-size:24px; font-weight:800; color:#654b78; margin-bottom:4px;}
    .chibi-subtitle {color:#886d91; font-size:15px;}
    .cute-note {padding:12px 16px; border-radius:18px; background:#fff7fc; border:2px dashed #e8b9d3; color:#765777; margin:10px 0 18px;}
    /* The phone launcher is a regular Streamlit button with a small
       server-backed panel.  It does not depend on popover/expander DOM
       details, so the tap target stays reliable across Streamlit versions. */
    .st-key-mobile_nav_button {position:fixed !important; top:8px; left:8px; z-index:2147483647 !important; width:48px; pointer-events:auto !important;}
    .st-key-mobile_nav_button button,
    .st-key-mobile_nav_button button:hover,
    .st-key-mobile_nav_button button:focus,
    .st-key-mobile_nav_button button:focus-visible,
    .st-key-mobile_nav_button button:active {border:0 !important; outline:none !important; box-shadow:none !important; background:transparent !important; color:#684d7b !important; font-size:27px; padding:2px 6px; min-height:42px; -webkit-tap-highlight-color:transparent;}
    .st-key-mobile_nav_button button p,
    .st-key-mobile_nav_button button span {font-size:27px !important; line-height:1 !important; margin:0 !important; color:#684d7b !important;}
    .st-key-mobile_nav_panel {position:fixed !important; top:55px; left:8px; z-index:2147483647 !important; width:min(280px,calc(100vw - 16px)); max-height:calc(100vh - 65px); overflow-y:auto; padding:10px 12px 12px; border:2px solid #efb8d6; border-radius:20px; background:rgba(255,250,255,.98); box-shadow:0 12px 28px rgba(91,71,112,.2); pointer-events:auto !important;}
    .st-key-mobile_nav_panel .stButton > button {width:100%; min-height:2.6rem; margin:3px 0; touch-action:manipulation;}
    @media (min-width: 701px) {
        .st-key-mobile_nav_button, .st-key-mobile_nav_panel {display:none !important;}
        /* Hide Streamlit's own collapsed-control wrapper.  Some Streamlit
           versions make that wrapper a full-page hit layer; the small custom
           launcher below is the only desktop toggle we expose. */
        [data-testid="stSidebarCollapsedControl"] {
            display:none !important;
            pointer-events:none !important;
        }
        [data-testid="stSidebarCollapsedControl"] button {
            display:flex !important;
            align-items:center !important;
            justify-content:center !important;
            width:44px !important;
            height:44px !important;
            min-width:44px !important;
            min-height:44px !important;
            padding:0 !important;
            border:2px solid #efb8d6 !important;
            border-radius:14px !important;
            background:#fffaff !important;
            color:#684d7b !important;
            box-shadow:0 8px 18px rgba(91,71,112,.18) !important;
            pointer-events:auto !important;
        }
        [data-testid="stSidebarCollapsedControl"] button:hover,
        [data-testid="stSidebarCollapsedControl"] button:focus,
        [data-testid="stSidebarCollapsedControl"] button:focus-visible {
            border-color:#d99ac0 !important;
            background:#fff1f8 !important;
            color:#5b4770 !important;
            outline:none !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg {
            width:22px !important;
            height:22px !important;
            color:#684d7b !important;
            fill:#684d7b !important;
        }
    }
    @media (max-width: 700px) {
        .block-container {padding: 4rem .75rem 2rem;}
        /* Streamlit's desktop sidebar is hidden on a phone; the fixed
           launcher above is the single, tappable mobile navigation control. */
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display:none !important;}
        .st-key-mobile_nav_button {display:block !important; visibility:visible !important; opacity:1 !important;}
        h1 {font-size: 1.8rem;}
        h2 {font-size: 1.35rem;}
        .chibi-hero {padding:18px; gap:12px;}
        .chibi-face {font-size:30px;}
        .shop-item-icon {font-size:24px; min-height:42px;}
        .chibi-title {font-size:19px;}
        .stButton button {min-height: 2.8rem; width: 100%;}
        [data-testid="stDialog"], .stDialog {padding:2vh 0 !important;}
        [data-testid="stDialog"] > div, .stDialog > div {width:98vw !important; max-width:98vw !important; min-height:96vh !important; border-radius:24px !important;}
        [data-testid="stDialog"] .block-container, .stDialog .block-container {padding:1rem .85rem 1.5rem !important;}
        .bts-surface {width:0; height:0; min-height:0; margin:0; padding:0; overflow:visible;}
        .bts-scene, .bts-scene-left, .bts-scene-right {position:fixed !important; width:max-content; max-width:calc(100vw - 12px); margin:0;}
        .bts-scene-right {flex-direction:row-reverse;}
        .bts-character, .bts-vector-fallback {width:82px; height:132px;}
        .bts-speech {min-width:0; max-width:calc(100vw - 96px); flex:1 1 auto; padding:10px 12px;}
        .bts-quote {font-size:14px;}
        .streak-card {align-items:flex-start; flex-direction:column; gap:6px;}
        .streak-meta {text-align:left;}
    }
</style>
""", unsafe_allow_html=True)


NAV_PAGES = ("Dashboard", "Review", "Lessons", "Progress", "Crystal Shop")


def render_mobile_navigation():
    """Render a reliable tappable mobile menu before the sidebar radio."""
    def toggle_mobile_menu():
        st.session_state["mobile_menu_open"] = not st.session_state.get("mobile_menu_open", False)

    def select_mobile_page(page_name):
        st.session_state["nav"] = page_name
        st.session_state["mobile_menu_open"] = False

    with st.container(key="mobile_nav_button"):
        st.button(
            "☰",
            key="mobile_nav_toggle",
            help="Open navigation",
            on_click=toggle_mobile_menu,
        )
    if not st.session_state.get("mobile_menu_open", False):
        return
    with st.container(key="mobile_nav_panel"):
        st.markdown("### Navigate")
        current = st.session_state.get("nav", "Dashboard")
        for page_name in NAV_PAGES:
            label = ("● " if page_name == current else "○ ") + page_name
            st.button(
                label,
                key=f"mobile_nav_{page_name}",
                use_container_width=True,
                on_click=select_mobile_page,
                args=(page_name,),
            )


def db():
    if SUPABASE_DB_URL:
        if psycopg2 is None:
            raise RuntimeError("SUPABASE_DB_URL is set, but psycopg2-binary is missing from requirements.txt")
        cached_connection = st.session_state.get("_supabase_connection")
        if cached_connection is not None and hasattr(cached_connection, "ensure_alive") and getattr(cached_connection.raw, "closed", 1) == 0:
            return cached_connection
        if cached_connection is not None:
            try:
                cached_connection.raw.close()
            except Exception:
                pass
        cached_connection = PostgresConnection(SUPABASE_DB_URL)
        st.session_state["_supabase_connection"] = cached_connection
        return cached_connection
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def today():
    return date.today().isoformat()


def lock_bootstrap(c):
    """Serialize schema and seed migrations when several sessions start together."""
    if is_postgres_connection(c):
        # Fetch the result so the cursor is completed/closed while the
        # transaction-level advisory lock remains held until commit.
        c.execute("SELECT pg_advisory_xact_lock(81620417)").fetchone()


def init_db():
    c = db()
    lock_bootstrap(c)
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
        explanation TEXT NOT NULL,
        answer_form TEXT DEFAULT '',
        seed_index INTEGER
    );
    CREATE TABLE IF NOT EXISTS reviews (
        card_id INTEGER PRIMARY KEY,
        level INTEGER DEFAULT 0,
        next_review TEXT DEFAULT '2999-01-01',
        due_at TEXT DEFAULT '2999-01-01T00:00:00',
        last_review TEXT,
        last_result TEXT,
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
    CREATE TABLE IF NOT EXISTS study_activity (
        day TEXT PRIMARY KEY,
        lessons INTEGER NOT NULL DEFAULT 0,
        reviews INTEGER NOT NULL DEFAULT 0,
        last_activity TEXT NOT NULL
    );
    """)
    # A retired review row belongs to an old card that was removed from the
    # checked-in lesson pack.  Keep the row and its history for progress
    # safety, but never put it back into a deck when its lesson is activated.
    # ALTER TABLE is needed because deployed databases predate this column.
    review_migrations = {
        "due_at": "TEXT DEFAULT '2999-01-01T00:00:00'",
        "last_result": "TEXT",
        "retired": "INTEGER NOT NULL DEFAULT 0",
    }
    if is_postgres_connection(c):
        # Do not issue a no-op ALTER TABLE on every Streamlit startup.  Even
        # ``ADD COLUMN IF NOT EXISTS`` takes an ACCESS EXCLUSIVE lock on the
        # table in PostgreSQL.  A review query from another browser can then
        # hold that lock long enough for Supabase to cancel startup with
        # psycopg2.errors.QueryCanceled.  The advisory lock above serializes
        # the one real migration, so an explicit schema check is both safer
        # and faster for already-migrated databases.
        postgres_columns = lambda table: {
            row["name"]
            for row in c.execute(
                """
                SELECT column_name AS name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name=?
                """,
                (table,),
            ).fetchall()
        }
        card_columns = postgres_columns("cards")
        if "answer_form" not in card_columns:
            c.execute("ALTER TABLE cards ADD COLUMN answer_form TEXT DEFAULT ''")
        if "seed_index" not in card_columns:
            c.execute("ALTER TABLE cards ADD COLUMN seed_index INTEGER")
        review_columns = postgres_columns("reviews")
        for column, definition in review_migrations.items():
            if column not in review_columns:
                c.execute(f"ALTER TABLE reviews ADD COLUMN {column} {definition}")
    else:
        review_columns = {row[1] for row in c.execute("PRAGMA table_info(reviews)").fetchall()}
        card_columns = {row[1] for row in c.execute("PRAGMA table_info(cards)").fetchall()}
        if "answer_form" not in card_columns:
            c.execute("ALTER TABLE cards ADD COLUMN answer_form TEXT DEFAULT ''")
        if "seed_index" not in card_columns:
            c.execute("ALTER TABLE cards ADD COLUMN seed_index INTEGER")
        for column, definition in review_migrations.items():
            if column not in review_columns:
                c.execute(f"ALTER TABLE reviews ADD COLUMN {column} {definition}")
    c.execute("UPDATE reviews SET due_at=next_review || 'T00:00:00' WHERE due_at IS NULL")
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('start_unit','2')")
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('new_lessons_per_day','2')")
    # The current course plan is two new lessons per day. Keep this migration
    # explicit so an older database that used three is corrected as well.
    c.execute("UPDATE settings SET value='2' WHERE key='new_lessons_per_day'")
    c.execute("INSERT OR IGNORE INTO wallet(id,crystals) VALUES(1,0)")
    for item in SHOP_ITEMS:
        c.execute("INSERT OR IGNORE INTO shop_items(id,name,kind,price,icon,description) VALUES(?,?,?,?,?,?)", item)
        c.execute("UPDATE shop_items SET name=?, kind=?, price=?, icon=?, description=? WHERE id=?", (item[1], item[2], item[3], item[4], item[5], item[0]))
    c.execute("INSERT OR IGNORE INTO inventory(item_id,purchased_at) VALUES('face_bunny',?)", (datetime.now().isoformat(timespec='seconds'),))
    c.execute("INSERT OR IGNORE INTO inventory(item_id,purchased_at) VALUES('design_lavender',?)", (datetime.now().isoformat(timespec='seconds'),))
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('active_face','face_bunny')")
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('active_design','design_lavender')")
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('active_frame','frame_sakura')")
    c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('active_tracker','tracker_mochi')")
    c.commit()
    c.close()


def import_seed_once():
    if not SEED_PATH.exists():
        return
    c = db()
    lock_bootstrap(c)
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
        for seed_index, card in enumerate(lesson["cards"], start=1):
            card_id = c.execute("""
                INSERT INTO cards(lesson_id,prompt,translation,answer,hint,explanation,answer_form,seed_index)
                VALUES(?,?,?,?,?,?,?,?)
            """, (lesson_id, card["prompt"], card["translation"], card["answer"],
                  card["hint"], card["explanation"], card.get("answer_form", ""), seed_index)).lastrowid
            c.execute("INSERT INTO reviews(card_id) VALUES(?)", (card_id,))
    c.commit()
    c.close()


def import_extended_seeds():
    """Add later lesson packs without rebuilding or overwriting the database."""
    c = db()
    lock_bootstrap(c)
    for seed_path in EXTENDED_SEED_PATHS:
        if not seed_path.exists():
            continue
        data = json.loads(seed_path.read_text(encoding="utf-8"))
        for lesson in data.get("lessons", []):
            # The app can have several browser sessions on first deployment.
            # Insert-or-ignore at the database level avoids the check-then-
            # insert race that previously blocked lessons_lesson_number_key.
            if is_postgres_connection(c):
                inserted = c.execute("""
                    INSERT INTO lessons(unit,lesson_number,title,pattern,explanation,source_url,status)
                    VALUES(?,?,?,?,?,?,?)
                    ON CONFLICT (lesson_number) DO NOTHING
                    RETURNING id
                """, (lesson["unit"], lesson["lesson_number"], lesson["title"], lesson["pattern"],
                      lesson["explanation"], lesson["source_url"], "available")).fetchone()
                if not inserted:
                    # Another session already owns this lesson.  Its cards
                    # are handled by sync_seed_card_content later in startup.
                    continue
                lesson_id = inserted["id"]
            else:
                existing = c.execute("SELECT id FROM lessons WHERE lesson_number=?", (lesson["lesson_number"],)).fetchone()
                if existing:
                    continue
                lesson_id = c.execute("""
                    INSERT INTO lessons(unit,lesson_number,title,pattern,explanation,source_url,status)
                    VALUES(?,?,?,?,?,?,?)
                """, (lesson["unit"], lesson["lesson_number"], lesson["title"], lesson["pattern"],
                      lesson["explanation"], lesson["source_url"], "available")).lastrowid
            for seed_index, card in enumerate(lesson.get("cards", []), start=1):
                card_id = c.execute("""
                    INSERT INTO cards(lesson_id,prompt,translation,answer,hint,explanation,answer_form,seed_index)
                    VALUES(?,?,?,?,?,?,?,?)
                """, (lesson_id, card["prompt"], card["translation"], card["answer"],
                      card["hint"], card["explanation"], card.get("answer_form", ""), seed_index)).lastrowid
                c.execute("INSERT INTO reviews(card_id) VALUES(?)", (card_id,))
            # Keep each lesson's write short so a cancelled browser request
            # cannot hold the unique lesson index for the entire course.
            if is_postgres_connection(c):
                c.commit()
    c.commit()
    c.close()


def _card_content_key(value):
    """Normalize a stable human-readable card key without changing content."""
    return re.sub(r"\s+", " ", str(value or "").strip())


def _match_seed_cards(existing_rows, seed_cards):
    """Match seed cards to old rows before changing any card text.

    Card IDs are database history, not content identity: old deployments could
    insert a repaired card later or use a different order.  The translation is
    stable across the content repair and is unique within these lesson packs;
    position is used only as a controlled fallback for a genuinely new or
    translated card.
    """
    by_translation = {}
    for row in existing_rows:
        by_translation.setdefault(_card_content_key(row["translation"]), []).append(row)
    unused_ids = {row["id"] for row in existing_rows}
    matches = []
    for index, seed_card in enumerate(seed_cards):
        translation_key = _card_content_key(seed_card.get("translation", ""))
        candidate = next(
            (row for row in by_translation.get(translation_key, []) if row["id"] in unused_ids),
            None,
        )
        if candidate is None:
            candidate = next(
                (row for row in existing_rows if row["id"] in unused_ids),
                None,
            )
        if candidate is not None:
            unused_ids.remove(candidate["id"])
        matches.append((seed_card, candidate))
    obsolete = [row for row in existing_rows if row["id"] in unused_ids]
    return matches, obsolete


def sync_seed_card_content():
    """Refresh checked-in card text while preserving every review record.

    The first version of the deployed app imported a card only once.  That
    meant a corrected HTSK example stayed wrong in an existing database.  We
    now assign every seed card a stable position inside its lesson and update
    only the card content.  The first assignment uses the old translation
    mapping so an already-reviewed card keeps its meaning; after that, the
    durable ``seed_index`` makes every later migration deterministic.  Level,
    dates, mistakes, active state, and answer history are intentionally
    untouched.
    """
    c = db()
    lock_bootstrap(c)
    for seed_path in [SEED_PATH, *EXTENDED_SEED_PATHS]:
        if not seed_path.exists():
            continue
        data = json.loads(seed_path.read_text(encoding="utf-8"))
        for lesson_data in data.get("lessons", []):
            lesson = c.execute(
                "SELECT id FROM lessons WHERE lesson_number=?",
                (lesson_data["lesson_number"],),
            ).fetchone()
            if not lesson:
                continue
            existing = c.execute(
                "SELECT id, translation, seed_index FROM cards WHERE lesson_id=? ORDER BY id",
                (lesson["id"],),
            ).fetchall()
            matches, obsolete = _match_seed_cards(existing, lesson_data.get("cards", []))
            for seed_index, (card, old_row) in enumerate(matches, start=1):
                values = (
                    card["prompt"],
                    card["translation"],
                    card["answer"],
                    card["hint"],
                    card["explanation"],
                    card.get("answer_form", ""),
                )
                if old_row is not None:
                    c.execute(
                        "UPDATE reviews SET retired=0 WHERE card_id=?",
                        (old_row["id"],),
                    )
                    # A very old database can contain a card without its
                    # review row.  Recreate only that missing row with the
                    # default SRS state; existing progress is not touched.
                    c.execute(
                        "INSERT OR IGNORE INTO reviews(card_id) VALUES(?)",
                        (old_row["id"],),
                    )
                    c.execute(
                        """UPDATE cards
                           SET seed_index=?, prompt=?, translation=?, answer=?, hint=?, explanation=?, answer_form=?
                           WHERE id=?""",
                        (seed_index, *values, old_row["id"]),
                    )
                else:
                    card_id = c.execute(
                        """INSERT INTO cards
                           (lesson_id,prompt,translation,answer,hint,explanation,answer_form,seed_index)
                           VALUES(?,?,?,?,?,?,?,?)""",
                        (lesson["id"], *values, seed_index),
                    ).lastrowid
                    c.execute(
                        "INSERT OR IGNORE INTO reviews(card_id) VALUES(?)",
                        (card_id,),
                    )
            # A repaired seed can intentionally contain fewer cards than an
            # older deployed database.  Keep the old review/history rows for
            # progress safety, but take obsolete cards out of the active deck
            # so stale examples cannot reappear after an app update.
            if obsolete:
                obsolete_ids = [row["id"] for row in obsolete]
                placeholders = ",".join("?" for _ in obsolete_ids)
                c.execute(
                    f"UPDATE cards SET seed_index=NULL WHERE id IN ({placeholders})",
                    obsolete_ids,
                )
                c.execute(
                    f"UPDATE reviews SET active=0, retired=1 WHERE card_id IN ({placeholders})",
                    obsolete_ids,
                )
    c.commit()
    c.close()


def sync_htsk_metadata():
    """Keep lesson labels, links and availability aligned with the HTSK manifest."""
    c = db()
    lock_bootstrap(c)
    for number, guide in HTSK_GUIDES.items():
        lesson = c.execute(
            "SELECT id, status FROM lessons WHERE lesson_number=?", (int(number),)
        ).fetchone()
        if not lesson:
            continue
        if guide.get("source_status") == "published":
            # Older databases used ``locked`` for lessons that were already
            # present in the course pack.  The current app unlocks the whole
            # published HTSK queue and lets the daily queue reveal it in
            # order, so those stale flags must not hide new lessons forever.
            status = "available" if lesson["status"] in {"unavailable", "locked"} else lesson["status"]
            c.execute(
                "UPDATE lessons SET title=?, pattern=?, source_url=?, status=? WHERE id=?",
                (
                    guide["source_title"],
                    guide["source_pattern"],
                    guide["source_url"],
                    status,
                    lesson["id"],
                ),
            )
        else:
            c.execute(
                "UPDATE lessons SET title=?, pattern=?, source_url=?, status='unavailable' WHERE id=?",
                (
                    guide["source_title"],
                    guide.get("source_pattern") or "—",
                    guide["source_url"],
                    lesson["id"],
                ),
            )
            c.execute(
                "UPDATE reviews SET active=0, retired=1 WHERE card_id IN (SELECT id FROM cards WHERE lesson_id=?)",
                (lesson["id"],),
            )
            c.execute(
                "DELETE FROM daily_lessons WHERE lesson_id=? AND status='new'",
                (lesson["id"],),
            )
    c.commit()
    c.close()


def verify_live_card_content():
    """Verify that the live database contains the checked-in card content.

    A stale Streamlit resource cache used to make an old prompt look valid
    after a deployment.  The sync now runs with an explicit version key, and
    this second pass proves that every seeded card actually reached the live
    database before the app renders a page.
    """
    c = db()
    mismatches = []
    fields = ("prompt", "translation", "answer", "hint", "explanation", "answer_form")
    for seed_path in [SEED_PATH, *EXTENDED_SEED_PATHS]:
        if not seed_path.exists():
            continue
        data = json.loads(seed_path.read_text(encoding="utf-8"))
        for lesson_data in data.get("lessons", []):
            lesson_number = lesson_data["lesson_number"]
            lesson = c.execute(
                "SELECT id FROM lessons WHERE lesson_number=?",
                (lesson_number,),
            ).fetchone()
            if not lesson:
                mismatches.append((lesson_number, 0, "lesson_missing"))
                continue
            live_rows = c.execute(
                """
                SELECT cards.id, cards.seed_index, cards.prompt, cards.translation,
                       cards.answer, cards.hint, cards.explanation, cards.answer_form
                FROM cards
                LEFT JOIN reviews ON reviews.card_id=cards.id
                WHERE cards.lesson_id=?
                  AND COALESCE(reviews.retired, 0)=0
                  AND cards.seed_index IS NOT NULL
                ORDER BY cards.seed_index, cards.id
                """,
                (lesson["id"],),
            ).fetchall()
            live_by_index = {}
            for row in live_rows:
                live_by_index.setdefault(int(row["seed_index"]), row)
            seed_cards = lesson_data.get("cards", [])
            for index, seed_card in enumerate(seed_cards, start=1):
                live = live_by_index.get(index)
                if live is None:
                    mismatches.append((lesson_number, index, "card_missing"))
                    continue
                for field in fields:
                    live_value = "" if live[field] is None else live[field]
                    seed_value = seed_card.get(field, "")
                    seed_value = "" if seed_value is None else seed_value
                    if live_value != seed_value:
                        mismatches.append((lesson_number, index, field))
                        break
            if len(live_by_index) != len(seed_cards):
                mismatches.append((lesson_number, 0, "card_count"))
    c.close()
    if mismatches:
        # Keep the diagnostic safe (lesson/card/field only): Streamlit redacts
        # exception messages that contain Korean card text, which used to hide
        # the actual location of a real migration failure.
        lesson_number, card_index, field = mismatches[0]
        raise RuntimeError(
            f"Card content sync failed at lesson {lesson_number}, "
            f"card {card_index}, field {field}"
        )


# Bump this whenever card prompts/answers change. Existing databases keep
# their SRS levels and history, but every card is re-synced from the checked-in
# lesson JSON on the next startup. This prevents an old split-answer record
# from surviving after the seed content has been corrected.
CONTENT_SYNC_VERSION = "2026-10-01-cards-content-ui-content-v17"


def ensure_seed_bundle():
    """Fail loudly instead of showing stale card text from an old database."""
    missing = [path.name for path in [SEED_PATH, *EXTENDED_SEED_PATHS] if not path.exists()]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            "The complete lesson bundle is required next to korean_bunpro_app.py; "
            f"missing: {names}"
        )


@st.cache_resource(show_spinner="Preparing your Korean course…")
def bootstrap_app_data(sync_version):
    """Run database setup and content synchronization once per app process.

    The resource cache makes this startup-only. Do not use the database's
    content marker as an early return: an earlier deployment could write the
    marker before the corrected seed files arrived, leaving old split answers
    in an otherwise valid database. Running the idempotent sync at startup
    repairs those records while preserving SRS levels and answer history.
    """
    ensure_seed_bundle()
    init_db()
    import_seed_once()
    import_extended_seeds()
    sync_seed_card_content()
    sync_htsk_metadata()
    verify_live_card_content()
    # Static lesson/card query results can survive a Streamlit rerun in the
    # same browser session.  Do not let those pre-sync rows remain visible.
    st.session_state.pop("_content_query_cache", None)
    c = db()
    c.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
        ("content_sync_version", sync_version),
    )
    c.commit()
    c.close()


def setting(key, default):
    cache = st.session_state.setdefault("_settings_cache", {})
    if key in cache:
        return cache[key]
    c = db()
    row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    c.close()
    value = row["value"] if row else default
    cache[key] = value
    return value


def crystals():
    row = one("SELECT crystals FROM wallet WHERE id=1")
    return row["crystals"] if row else 0


def award_crystals(event_key, amount):
    if amount <= 0:
        return
    c = db()
    params = (event_key, amount, datetime.now().isoformat(timespec="seconds"))
    if is_postgres_connection(c):
        # RETURNING is reliable for PostgreSQL and avoids relying on the
        # SQLite-only cursor.rowcount convention for a duplicate-safe insert.
        inserted = c.execute(
            "INSERT INTO reward_events(event_key,amount,created_at) VALUES(?,?,?) "
            "ON CONFLICT (event_key) DO NOTHING RETURNING event_key",
            params,
        ).fetchone()
        was_inserted = inserted is not None
    else:
        cur = c.execute(
            "INSERT OR IGNORE INTO reward_events(event_key,amount,created_at) VALUES(?,?,?)",
            params,
        )
        was_inserted = bool(getattr(cur, "rowcount", 0))
    if was_inserted:
        c.execute("UPDATE wallet SET crystals=crystals+? WHERE id=1", (amount,))
    c.commit()
    c.close()


def streak_info():
    """Return the current and best consecutive study-day streaks."""
    activity = rows("SELECT day FROM study_activity WHERE lessons>0 OR reviews>0")
    days = set()
    for row in activity:
        try:
            days.add(date.fromisoformat(row["day"]))
        except (TypeError, ValueError):
            continue

    today_value = date.today()
    active_today = today_value in days
    cursor = today_value if active_today else today_value - timedelta(days=1)
    current = 0
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)

    best = 0
    ordered = sorted(days)
    run = 0
    previous = None
    for day_value in ordered:
        if previous is not None and day_value == previous + timedelta(days=1):
            run += 1
        else:
            run = 1
        best = max(best, run)
        previous = day_value
    return {"current": current, "best": max(best, current), "active_today": active_today}


def record_activity(kind):
    """Count a lesson or review as study activity and award one daily bonus."""
    if kind not in {"lesson", "review"}:
        return streak_info()
    column = "lessons" if kind == "lesson" else "reviews"
    now = datetime.now().isoformat(timespec="seconds")
    day = today()
    c = db()
    c.execute(
        "INSERT OR IGNORE INTO study_activity(day,lessons,reviews,last_activity) VALUES(?,?,?,?)",
        (day, 0, 0, now),
    )
    c.execute(
        f"UPDATE study_activity SET {column}={column}+1, last_activity=? WHERE day=?",
        (now, day),
    )
    c.commit()
    c.close()
    current = streak_info()
    # The event key makes this idempotent: reviewing ten cards today does not
    # multiply the streak bonus ten times.
    award_crystals(f"streak_bonus:{day}", 5)
    return current


def learner_level():
    """Map the furthest started lesson to the difficulty of the daily message."""
    started = one("SELECT MAX(lesson_number) AS n FROM lessons WHERE status='studying'")
    active = one("""
        SELECT MAX(lessons.lesson_number) AS n
        FROM lessons JOIN cards ON cards.lesson_id=lessons.id
        JOIN reviews ON reviews.card_id=cards.id
        WHERE reviews.active=1 AND reviews.retired=0
    """)
    highest = max(int(started["n"] or 0), int(active["n"] or 0))
    if highest < 51:
        level = 1
    elif highest < 101:
        level = 2
    elif highest < 151:
        level = 3
    elif highest < 176:
        level = 4
    else:
        level = 5
    return level, highest


def daily_bts_message():
    """Select a deterministic daily two-member encouragement at the user level."""
    level, highest = learner_level()
    choices = [item for item in BTS_MOTIVATION if item["level"] == level]
    if not choices:
        choices = [item for item in BTS_MOTIVATION if item["level"] <= level]
    # Choose the pair independently from the wording.  The previous code
    # selected from a list containing only Jimin/Jung Kook and V/Jin, so the
    # remaining three members could never appear.
    day_number = date.today().toordinal()
    choice = dict(choices[day_number % len(choices)])
    ko_member, ko_icon, en_member, en_icon = BTS_PAIR_ROTATION[day_number % len(BTS_PAIR_ROTATION)]
    choice.update(
        ko_member=ko_member,
        ko_icon=ko_icon,
        en_member=en_member,
        en_icon=en_icon,
    )
    return choice, level, highest


def bts_character_image(member, fallback_icon):
    """Return a bundled chibi or a self-contained human fallback.

    The PNGs are included in the full project archive.  The vector fallback
    is intentional: if somebody uploads only the Python file through GitHub,
    the dashboard still shows a full-body chibi instead of silently falling
    back to a small animal emoji.
    """
    filename = BTS_ASSET_FILES.get(member)
    asset_path = BTS_ASSET_DIR / filename if filename else None
    if asset_path and asset_path.is_file():
        encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
        return f'<img class="bts-character" src="data:image/png;base64,{encoded}" alt="Daily chibi character">'
    hair, outfit = BTS_VECTOR_PALETTE.get(member, ("#9276c9", "#5a477d"))
    skin = "#f4c7ad"
    return f'''<div class="bts-vector-fallback" role="img" aria-label="Daily chibi character">
        <svg class="bts-vector" viewBox="0 0 120 180" aria-hidden="true">
            <ellipse cx="60" cy="171" rx="28" ry="6" fill="rgba(91,71,112,.18)"/>
            <path d="M45 125 L43 158 Q43 164 49 164 L55 164 L59 132 Z" fill="#f7f2f7" stroke="#5b4770" stroke-width="2"/>
            <path d="M61 132 L65 164 L72 164 Q77 164 76 158 L74 125 Z" fill="#f7f2f7" stroke="#5b4770" stroke-width="2"/>
            <path d="M43 158 Q49 154 56 162 L57 168 L38 168 Q37 162 43 158 Z" fill="#ffffff" stroke="#5b4770" stroke-width="2"/>
            <path d="M64 162 Q71 154 77 158 Q82 162 81 168 L62 168 Z" fill="#ffffff" stroke="#5b4770" stroke-width="2"/>
            <rect x="40" y="83" width="40" height="49" rx="16" fill="{outfit}" stroke="#5b4770" stroke-width="2"/>
            <path d="M43 91 Q31 95 32 111" fill="none" stroke="{skin}" stroke-width="10" stroke-linecap="round"/>
            <path d="M77 91 Q89 95 88 111" fill="none" stroke="{skin}" stroke-width="10" stroke-linecap="round"/>
            <circle cx="32" cy="112" r="5" fill="{skin}"/>
            <circle cx="88" cy="112" r="5" fill="{skin}"/>
            <circle cx="60" cy="55" r="29" fill="{skin}" stroke="#5b4770" stroke-width="2"/>
            <path d="M32 55 Q30 22 61 23 Q91 22 89 54 Q80 40 67 42 Q51 45 42 60 Z" fill="{hair}" stroke="#5b4770" stroke-width="2"/>
            <path d="M39 62 Q43 72 50 75" fill="none" stroke="{hair}" stroke-width="5" stroke-linecap="round"/>
            <circle cx="50" cy="57" r="3" fill="#463953"/>
            <circle cx="70" cy="57" r="3" fill="#463953"/>
            <path d="M54 69 Q60 74 66 69" fill="none" stroke="#b75f7f" stroke-width="2" stroke-linecap="round"/>
            <circle cx="41" cy="66" r="4" fill="#f3a2ac" opacity=".65"/>
            <circle cx="79" cy="66" r="4" fill="#f3a2ac" opacity=".65"/>
            <path d="M53 88 L60 100 L67 88" fill="#ffffff" opacity=".9"/>
            <circle cx="60" cy="102" r="3" fill="#ffe49b"/>
        </svg>
    </div>'''


def render_bts_motivation(in_dialog=False):
    """Render two draggable full-body chibis on the page or inside a dialog."""
    message, _, _ = daily_bts_message()
    ko_icon = escape(message["ko_icon"])
    en_icon = escape(message["en_icon"])
    ko_quote = escape(message["ko"])
    en_quote = escape(message["en"])
    ko_style, en_style = BTS_SCENE_LAYOUTS[date.today().toordinal() % len(BTS_SCENE_LAYOUTS)]
    ko_image = bts_character_image(message["ko_member"], message["ko_icon"])
    en_image = bts_character_image(message["en_member"], message["en_icon"])
    surface_class = "bts-surface bts-dialog-surface" if in_dialog else "bts-surface bts-global-surface"
    host_name = "dialog" if in_dialog else "global"
    st.markdown(
        f'''<div class="{surface_class}" data-bts-host="{host_name}" data-bts-day="{date.today().isoformat()}">
            <div class="bts-scene bts-scene-left" data-chibi-slot="ko" style="{ko_style}">
                {ko_image}
                <div class="bts-speech">
                    <div class="bts-quote">{ko_quote}</div>
                </div>
            </div>
            <div class="bts-scene bts-scene-right" data-chibi-slot="en" style="{en_style}">
                {en_image}
                <div class="bts-speech">
                    <div class="bts-quote">{en_quote}</div>
                </div>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )
    components.html(
        """
        <script>
        (() => {
            const win = window.parent;
            const storagePrefix = "mochi-hangul-chibi-position-v3";
            const hiddenStorageKey = "mochi-hangul-chibis-hidden-v1";

            function chibisAreHidden() {
                try {
                    return win.localStorage.getItem(hiddenStorageKey) === "1";
                } catch (error) {
                    return false;
                }
            }

            function applyChibiVisibility() {
                const hidden = chibisAreHidden();
                win.document.querySelectorAll(".bts-scene").forEach((scene) => {
                    scene.style.visibility = hidden ? "hidden" : "";
                    scene.style.pointerEvents = hidden ? "none" : "";
                });
                const toggle = win.document.getElementById("mochi-chibi-toggle");
                if (toggle) {
                    toggle.textContent = hidden ? "👀" : "🙈";
                    toggle.title = hidden ? "Show chibis" : "Hide chibis";
                    toggle.setAttribute("aria-label", hidden ? "Show chibis" : "Hide chibis");
                }
            }

            function activeDialogSurface() {
                return Array.from(win.document.querySelectorAll(".bts-dialog-surface"))
                    .find((surface) => isVisible(surface)) || null;
            }

            function moveToggleToTopHost(modal) {
                const toggle = win.document.getElementById("mochi-chibi-toggle");
                if (!toggle) return;
                const host = modal || win.document.body;
                if (toggle.parentElement !== host) host.appendChild(toggle);
                toggle.style.setProperty("position", "fixed", "important");
                toggle.style.setProperty("right", "14px", "important");
                toggle.style.setProperty("top", modal ? "14px" : "auto", "important");
                toggle.style.setProperty("bottom", modal ? "auto" : "68px", "important");
                toggle.style.setProperty("z-index", "2147483647", "important");
                toggle.style.setProperty("pointer-events", "auto", "important");
            }

            function clamp(value, minimum, maximum) {
                return Math.min(Math.max(value, minimum), maximum);
            }

            function setPosition(scene, left, top) {
                scene.style.left = `${left}px`;
                scene.style.top = `${top}px`;
                scene.style.right = "auto";
                scene.style.bottom = "auto";
            }

            function sceneKey(day, slot) {
                return `${storagePrefix}-${day}-${slot}`;
            }

            function seededNumber(value) {
                let hash = 0;
                for (let index = 0; index < value.length; index += 1) {
                    hash = ((hash << 5) - hash) + value.charCodeAt(index);
                    hash |= 0;
                }
                const random = Math.sin(hash) * 10000;
                return random - Math.floor(random);
            }

            function placeRandomly(scene, day, slot) {
                const rect = scene.getBoundingClientRect();
                const maxLeft = Math.max(6, win.innerWidth - rect.width - 6);
                const maxTop = Math.max(6, win.innerHeight - rect.height - 6);
                const leftRange = Math.max(0, maxLeft - 12);
                const topRange = Math.max(0, maxTop - 72);
                const left = 6 + seededNumber(`${day}-${slot}-left`) * leftRange;
                const top = 72 + seededNumber(`${day}-${slot}-top`) * topRange;
                setPosition(scene, clamp(left, 6, maxLeft), clamp(top, 6, maxTop));
            }

            function savePosition(scene, key) {
                const rect = scene.getBoundingClientRect();
                try {
                    win.localStorage.setItem(key, JSON.stringify({left: rect.left, top: rect.top}));
                } catch (error) {}
            }

            function keepOnScreen(scene) {
                const rect = scene.getBoundingClientRect();
                const maxLeft = Math.max(6, win.innerWidth - rect.width - 6);
                const maxTop = Math.max(6, win.innerHeight - rect.height - 6);
                if (rect.left < 6 || rect.top < 6 || rect.right > win.innerWidth - 6 || rect.bottom > win.innerHeight - 6) {
                    setPosition(scene, clamp(rect.left, 6, maxLeft), clamp(rect.top, 6, maxTop));
                }
            }

            function isVisible(element) {
                if (!element) return false;
                const style = win.getComputedStyle ? win.getComputedStyle(element) : null;
                if (style && (style.display === "none" || style.visibility === "hidden" || style.opacity === "0")) return false;
                const rect = element.getBoundingClientRect ? element.getBoundingClientRect() : null;
                if (rect && rect.width === 0 && rect.height === 0) return false;
                return true;
            }

            function syncHosts() {
                const modal = activeDialogSurface();
                const modalOpen = Boolean(modal && isVisible(modal));
                // A dialog rerun can remove the old top-layer host together
                // with its children. Recreate the toggle before trying to
                // move it, otherwise the hide/show control disappears after
                // closing a Study or Review window.
                if (!win.document.getElementById("mochi-chibi-toggle")) {
                    installDesktopSidebarLauncher();
                }
                win.document.querySelectorAll(".bts-global-surface .bts-scene").forEach((scene) => {
                    scene.style.display = "";
                });
                win.document.querySelectorAll(".bts-dialog-surface .bts-scene").forEach((scene) => {
                    scene.style.display = modalOpen ? "" : "none";
                });
                moveToggleToTopHost(modalOpen ? modal : null);
                applyChibiVisibility();
                return modalOpen;
            }

            function installDesktopSidebarLauncher() {
                const doc = win.document;
                const sidebarLauncherVersion = "launcher-v3";
                if (win.__mochiSidebarLauncherObserverVersion !== sidebarLauncherVersion) {
                    if (win.__mochiSidebarLauncherObserver) win.__mochiSidebarLauncherObserver.disconnect();
                    if (win.__mochiSidebarLauncherResize) win.removeEventListener("resize", win.__mochiSidebarLauncherResize);
                    if (win.__mochiSidebarLauncherInterval) win.clearInterval(win.__mochiSidebarLauncherInterval);
                    win.__mochiSidebarLauncherObserver = null;
                    win.__mochiSidebarLauncherResize = null;
                    win.__mochiSidebarLauncherInterval = null;
                    win.__mochiSidebarLauncherObserverVersion = sidebarLauncherVersion;
                }
                let launcher = doc.getElementById("mochi-desktop-sidebar-launcher");
                if (!launcher) {
                    launcher = doc.createElement("button");
                    launcher.id = "mochi-desktop-sidebar-launcher";
                    launcher.type = "button";
                    launcher.textContent = "☰";
                    launcher.setAttribute("aria-label", "Open navigation menu");
                    launcher.title = "Open navigation menu";
                    Object.assign(launcher.style, {
                        position: "fixed",
                        top: "10px",
                        left: "10px",
                        zIndex: "2147483647",
                        display: "none",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "44px",
                        height: "44px",
                        minWidth: "44px",
                        minHeight: "44px",
                        padding: "0",
                        border: "2px solid #efb8d6",
                        borderRadius: "14px",
                        background: "#fffaff",
                        color: "#684d7b",
                        boxShadow: "0 8px 18px rgba(91,71,112,.18)",
                        fontFamily: "inherit",
                        fontSize: "25px",
                        lineHeight: "1",
                        cursor: "pointer",
                        pointerEvents: "auto",
                        touchAction: "manipulation",
                    });
                    launcher.addEventListener("mouseenter", () => {
                        launcher.style.background = "#fff1f8";
                        launcher.style.borderColor = "#d99ac0";
                    });
                    launcher.addEventListener("mouseleave", () => {
                        launcher.style.background = "#fffaff";
                        launcher.style.borderColor = "#efb8d6";
                    });
                    launcher.addEventListener("click", () => {
                        const open = sidebarIsOpen();
                        const selectors = open ? [
                            '[data-testid="stSidebarCollapseButton"]',
                            'button[aria-label*="Close sidebar" i]',
                            'button[title*="Close sidebar" i]',
                        ] : [
                            '[data-testid="stExpandSidebarButton"]',
                            '[data-testid="stSidebarCollapsedControl"] button',
                            'button[aria-label*="Expand sidebar" i]',
                            'button[title*="Expand sidebar" i]',
                        ];
                        for (const selector of selectors) {
                            const sidebarButton = doc.querySelector(selector);
                            if (sidebarButton && (open ? isVisible(sidebarButton) : true) && typeof sidebarButton.click === "function") {
                                sidebarButton.click();
                                win.setTimeout(update, 80);
                                return;
                            }
                        }
                    });
                    doc.body.appendChild(launcher);
                }

                let toggle = doc.getElementById("mochi-chibi-toggle");
                if (!toggle) {
                    toggle = doc.createElement("button");
                    toggle.id = "mochi-chibi-toggle";
                    toggle.type = "button";
                    Object.assign(toggle.style, {
                        position: "fixed",
                        right: "14px",
                        bottom: "68px",
                        zIndex: "2147483647",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: "46px",
                        height: "46px",
                        minWidth: "46px",
                        minHeight: "46px",
                        padding: "0",
                        border: "2px solid #efb8d6",
                        borderRadius: "16px",
                        background: "#fffaff",
                        color: "#684d7b",
                        boxShadow: "0 8px 18px rgba(91,71,112,.18)",
                        fontFamily: "inherit",
                        fontSize: "23px",
                        lineHeight: "1",
                        cursor: "pointer",
                        pointerEvents: "auto",
                        touchAction: "manipulation",
                    });
                    toggle.style.setProperty("z-index", "2147483647", "important");
                    toggle.style.setProperty("pointer-events", "auto", "important");
                    toggle.addEventListener("click", () => {
                        const hidden = !chibisAreHidden();
                        try {
                            win.localStorage.setItem(hiddenStorageKey, hidden ? "1" : "0");
                        } catch (error) {}
                        applyChibiVisibility();
                    });
                    toggle.addEventListener("mouseenter", () => {
                        toggle.style.background = "#fff1f8";
                        toggle.style.borderColor = "#d99ac0";
                    });
                    toggle.addEventListener("mouseleave", () => {
                        toggle.style.background = "#fffaff";
                        toggle.style.borderColor = "#efb8d6";
                    });
                    doc.body.appendChild(toggle);
                }
                toggle.style.setProperty("z-index", "2147483647", "important");
                toggle.style.setProperty("pointer-events", "auto", "important");
                moveToggleToTopHost(activeDialogSurface());
                applyChibiVisibility();

                function sidebarIsOpen() {
                    if (win.innerWidth <= 700) return true;
                    const collapsedControl = doc.querySelector(
                        '[data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"]'
                    );
                    if (collapsedControl && isVisible(collapsedControl)) return false;
                    const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                    if (!sidebar) return false;
                    const expanded = sidebar.getAttribute("aria-expanded");
                    if (expanded === "true") return true;
                    if (expanded === "false") return false;
                    const style = win.getComputedStyle ? win.getComputedStyle(sidebar) : null;
                    if (style && (style.display === "none" || style.visibility === "hidden")) return false;
                    const rect = sidebar.getBoundingClientRect();
                    return rect.width > 120 && rect.right > 1 && rect.left > -20;
                }

                function update() {
                    const open = sidebarIsOpen();
                    const display = win.innerWidth > 700 ? "flex" : "none";
                    const title = open ? "Close navigation menu" : "Open navigation menu";
                    if (launcher.style.display !== display) launcher.style.display = display;
                    if (launcher.title !== title) launcher.title = title;
                    if (launcher.getAttribute("aria-label") !== title) launcher.setAttribute("aria-label", title);
                }

                update();
                if (!win.__mochiSidebarLauncherInterval) {
                    win.__mochiSidebarLauncherResize = update;
                    win.addEventListener("resize", win.__mochiSidebarLauncherResize);
                    win.__mochiSidebarLauncherInterval = win.setInterval(update, 500);
                }
            }

            function bindChibis() {
                const modalOpen = syncHosts();
                const stage = win.document.querySelector(".bts-surface[data-bts-host]");
                if (!stage) return false;
                const day = stage.dataset.btsDay || "today";
                win.document.querySelectorAll(".bts-scene").forEach((scene, index) => {
                    scene.querySelectorAll("img").forEach((image) => {
                        image.draggable = false;
                        image.setAttribute("draggable", "false");
                        image.style.userSelect = "none";
                        image.style.webkitUserDrag = "none";
                    });
                    const slot = scene.dataset.chibiSlot || String(index);
                    scene.style.position = "fixed";
                    scene.style.zIndex = "2147483646";
                    const key = sceneKey(day, slot);
                    scene.dataset.chibiStorageKey = key;
                    scene.style.setProperty("pointer-events", "auto", "important");
                    if (scene.dataset.chibiPositionBound === "1") {
                        keepOnScreen(scene);
                        return;
                    }
                    scene.dataset.chibiPositionBound = "1";
                    scene.addEventListener("pointerdown", beginDrag, eventOptions);
                    scene.addEventListener("mousedown", beginDrag, eventOptions);
                    scene.addEventListener("touchstart", beginDrag, eventOptions);
                    scene.addEventListener("dragstart", preventNativeDrag, eventOptions);
                    controller.sceneBindings.push({scene, events: [
                        ["pointerdown", beginDrag],
                        ["mousedown", beginDrag],
                        ["touchstart", beginDrag],
                        ["dragstart", preventNativeDrag],
                    ]});
                    let hasSavedPosition = false;
                    try {
                        const saved = JSON.parse(win.localStorage.getItem(key) || "null");
                        if (saved && Number.isFinite(saved.left) && Number.isFinite(saved.top)) {
                            setPosition(scene, saved.left, saved.top);
                            hasSavedPosition = true;
                        }
                    } catch (error) {}
                    if (!hasSavedPosition) {
                        placeRandomly(scene, day, slot);
                        savePosition(scene, key);
                    }
                    keepOnScreen(scene);
                });
                return true;
            }

            // Keep one controller for the whole app. A Study/Review dialog
            // creates another HTML host, but must not destroy the controller
            // that owns the global chibis. Otherwise closing the dialog can
            // leave the global characters hidden and no longer draggable.
            const dragControllerVersion = "drag-v6";
            if (win.__mochiBtsDragController && win.__mochiBtsDragController.version === dragControllerVersion && win.__mochiBtsDragController.refresh) {
                installDesktopSidebarLauncher();
                win.__mochiBtsDragController.refresh();
                return;
            }
            if (win.__mochiBtsDragController && win.__mochiBtsDragController.destroy) {
                win.__mochiBtsDragController.destroy();
            }
            if (win.__mochiBtsDragObserver) win.__mochiBtsDragObserver.disconnect();
            win.__mochiBtsDragObserver = null;
            if (win.__mochiBtsDragResize) win.removeEventListener("resize", win.__mochiBtsDragResize);

            const controller = {drag: null, sceneBindings: [], version: dragControllerVersion};
            const eventOptions = {capture: true, passive: false};

            function sceneFromTarget(target) {
                if (!target) return null;
                if (target.closest) {
                    const scene = target.closest(".bts-scene");
                    if (scene) return scene;
                }
                return target.matches && target.matches(".bts-scene") ? target : null;
            }

            function pointFromEvent(event) {
                if (event.touches && event.touches.length) return event.touches[0];
                if (event.changedTouches && event.changedTouches.length) return event.changedTouches[0];
                return event;
            }

            function preventNativeDrag(event) {
                event.preventDefault();
                event.stopPropagation();
            }

            function beginDrag(event) {
                if (controller.drag) return;
                const scene = sceneFromTarget(event.target) || sceneFromTarget(event.currentTarget);
                if (!scene) return;
                if (event.type === "mousedown" && event.button !== 0) return;
                const point = pointFromEvent(event);
                if (!point || !Number.isFinite(point.clientX) || !Number.isFinite(point.clientY)) return;
                const rect = scene.getBoundingClientRect();
                setPosition(scene, rect.left, rect.top);
                controller.drag = {
                    scene,
                    key: scene.dataset.chibiStorageKey,
                    pointerId: event.pointerId,
                    source: event.type.startsWith("touch") ? "touch" : event.type.startsWith("pointer") ? "pointer" : "mouse",
                    dx: point.clientX - rect.left,
                    dy: point.clientY - rect.top,
                };
                scene.classList.add("bts-dragging");
                if (event.pointerId !== undefined && scene.setPointerCapture) {
                    try { scene.setPointerCapture(event.pointerId); } catch (error) {}
                }
                event.preventDefault();
                event.stopPropagation();
            }

            function moveDrag(event) {
                const drag = controller.drag;
                if (!drag) return;
                if (drag.source === "pointer" && (event.type !== "pointermove" || event.pointerId !== drag.pointerId)) return;
                if (drag.source === "mouse" && event.type !== "mousemove") return;
                if (drag.source === "touch" && event.type !== "touchmove") return;
                const point = pointFromEvent(event);
                if (!point) return;
                const rect = drag.scene.getBoundingClientRect();
                const maxLeft = Math.max(6, win.innerWidth - rect.width - 6);
                const maxTop = Math.max(6, win.innerHeight - rect.height - 6);
                setPosition(drag.scene, clamp(point.clientX - drag.dx, 6, maxLeft), clamp(point.clientY - drag.dy, 6, maxTop));
                event.preventDefault();
                event.stopPropagation();
            }

            function endDrag(event) {
                const drag = controller.drag;
                if (!drag) return;
                if (drag.source === "pointer" && ((event.type !== "pointerup" && event.type !== "pointercancel") || event.pointerId !== drag.pointerId)) return;
                if (drag.source === "mouse" && event.type !== "mouseup") return;
                if (drag.source === "touch" && event.type !== "touchend" && event.type !== "touchcancel") return;
                if (drag.key) savePosition(drag.scene, drag.key);
                drag.scene.classList.remove("bts-dragging");
                controller.drag = null;
                event.preventDefault();
                event.stopPropagation();
            }

            const listeners = {
                pointerdown: beginDrag,
                pointermove: moveDrag,
                pointerup: endDrag,
                pointercancel: endDrag,
                mousedown: beginDrag,
                mousemove: moveDrag,
                mouseup: endDrag,
                touchstart: beginDrag,
                touchmove: moveDrag,
                touchend: endDrag,
                touchcancel: endDrag,
            };
            Object.entries(listeners).forEach(([name, handler]) => {
                const target = ["pointermove", "pointerup", "pointercancel", "mousemove", "mouseup", "touchmove", "touchend", "touchcancel"].includes(name) ? win : win.document;
                target.addEventListener(name, handler, eventOptions);
            });
            controller.refresh = bindChibis;
            controller.destroy = () => {
                Object.entries(listeners).forEach(([name, handler]) => {
                    const target = ["pointermove", "pointerup", "pointercancel", "mousemove", "mouseup", "touchmove", "touchend", "touchcancel"].includes(name) ? win : win.document;
                    target.removeEventListener(name, handler, eventOptions);
                });
                controller.sceneBindings.forEach(({scene, events}) => {
                    events.forEach(([name, handler]) => scene.removeEventListener(name, handler, eventOptions));
                    delete scene.dataset.chibiPositionBound;
                });
                controller.sceneBindings = [];
                if (controller.drag) controller.drag.scene.classList.remove("bts-dragging");
                controller.drag = null;
                if (win.__mochiBtsDragObserver) win.__mochiBtsDragObserver.disconnect();
                if (win.__mochiBtsDragInterval) win.clearInterval(win.__mochiBtsDragInterval);
            };
            win.__mochiBtsDragController = controller;
            const stage = win.document.querySelector(".bts-surface[data-bts-host]");
            if (stage) {
                win.document.querySelectorAll(".bts-scene").forEach((scene, index) => {
                    scene.dataset.chibiStorageKey = sceneKey(stage.dataset.btsDay || "today", scene.dataset.chibiSlot || String(index));
                });
            }
            bindChibis();
            [0, 80, 250, 700].forEach((delay) => win.setTimeout(bindChibis, delay));
            // Polling is deliberately used instead of MutationObserver here.
            // It also handles dialogs that Streamlit hides by changing style
            // rather than removing them, without risking a DOM observer loop.
            if (win.setInterval) win.__mochiBtsDragInterval = win.setInterval(bindChibis, 500);
            win.__mochiBtsDragResize = () => win.document.querySelectorAll(".bts-scene").forEach(keepOnScreen);
            win.addEventListener("resize", win.__mochiBtsDragResize);
            installDesktopSidebarLauncher();
        })();
        </script>
        """,
        height=1,
    )


def active_item(kind):
    key = f"active_{kind}"
    defaults = {"face": "face_bunny", "design": "design_lavender", "frame": "frame_sakura", "tracker": "tracker_mochi"}
    item_id = setting(key, defaults.get(kind, ""))
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
    set_key = f"active_{item['kind']}"
    set_value = item_id
    c = db(); c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (set_key, set_value)); c.commit(); c.close()
    st.session_state.setdefault("_settings_cache", {})[set_key] = set_value
    return True


def is_static_content_query(sql):
    """Identify read-only lesson/card catalog queries safe to cache per session."""
    normalized = " ".join(sql.lower().split())
    if not normalized.startswith("select"):
        return False
    if any(name in normalized for name in ("reviews", "daily_lessons", "study_activity", "answer_history", "settings", "wallet", "inventory", "reward_events")):
        return False
    return "lessons" in normalized or "cards" in normalized or "shop_items" in normalized


def rows(sql, params=()):
    if is_static_content_query(sql):
        cache = st.session_state.setdefault("_content_query_cache", {})
        key = (sql, tuple(params))
        if key in cache:
            return cache[key]
    c = db()
    result = c.execute(sql, params).fetchall()
    c.close()
    if is_static_content_query(sql):
        cache[key] = result
    return result


def one(sql, params=()):
    if is_static_content_query(sql):
        cache = st.session_state.setdefault("_content_query_cache", {})
        key = (sql, tuple(params))
        if key in cache:
            return cache[key]
    c = db()
    result = c.execute(sql, params).fetchone()
    c.close()
    if is_static_content_query(sql):
        cache[key] = result
    return result


def normalize(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def inferred_answer_form(card):
    """Return a safe speech-level hint when a legacy card omitted one.

    The seed's explicit label always wins. For older cards, only endings
    whose speech level is unambiguous are inferred; grammar-only endings such
    as -고 or -는지 remain unlabeled instead of guessing.
    """
    explicit = normalize(card["answer_form"] if "answer_form" in card.keys() else "")
    if explicit:
        return explicit
    answer = normalize(card["answer"] if "answer" in card.keys() else "")
    answer = re.sub(r"[.!?。！？]+$", "", answer).strip()
    if re.search(r"(?:거든요|기는요|네요|군요|구요)$", answer):
        return "Polite conversational form (-요)"
    if re.search(r"(?:습니다|ㅂ니다|습니까|ㅂ니까|십시오|시오|오니)$", answer):
        return "Formal polite/literary form"
    if re.search(r"(?:어요|아요|여요|이에요|예요|세요|요)$", answer):
        return "Polite conversational form (-요)"
    if re.search(r"(?:거야|잖아|거든|구나|군|네|자|라|까|어|아|야)$", answer):
        return "Informal/plain conversational form"
    return ""


# The lesson guide is stored directly on each lesson record in the unit seed
# files.  It is not reconstructed from SRS cards or lesson titles, and the
# guide examples remain separate from the cards array in the same lesson.


def load_htsk_guides():
    """Load and validate HTSK guide fields embedded in the lesson seeds."""
    guides = {}
    for seed_path in [SEED_PATH, *EXTENDED_SEED_PATHS]:
        if not seed_path.exists():
            raise FileNotFoundError(
                f"{seed_path.name} is missing. Deploy all unit lesson files next to korean_bunpro_app.py."
            )
        payload = json.loads(seed_path.read_text(encoding="utf-8"))
        for lesson in payload.get("lessons", []):
            number = str(int(lesson["lesson_number"]))
            if number in guides:
                raise ValueError(f"Lesson {number} appears in more than one seed file.")
            cards = lesson.get("cards", [])
            lesson_number = int(number)
            for card_index, card in enumerate(cards, start=1):
                prompt = str(card.get("prompt", ""))
                answer = str(card.get("answer", ""))
                if prompt.count("___") != 1 or not answer.strip():
                    raise ValueError(
                        f"Lesson {number} card {card_index} must have one blank and a complete answer."
                    )
                if normalize(answer) in INCOMPLETE_GRAMMAR_TAILS:
                    raise ValueError(
                        f"Lesson {number} card {card_index} contains only a grammar tail; "
                        "the answer must include the lexical word or stem too."
                    )
                hint = normalize(card.get("hint", ""))
                if not re.match(r"^Base forms?:\s+\S", hint):
                    raise ValueError(
                        f"Lesson {number} card {card_index} must show a non-empty base-form hint."
                    )
                if hint in {
                    "Base form: The base word is already shown",
                    "Base forms: The base word is already shown",
                    "Base form: TBD",
                    "Base forms: TBD",
                }:
                    raise ValueError(
                        f"Lesson {number} card {card_index} contains a placeholder base-form hint."
                    )
                source_sentence = card.get("source_sentence")
                if (
                    26 <= lesson_number <= 202
                    and lesson.get("source_status") == "published"
                    and not source_sentence
                ):
                    raise ValueError(
                        f"Lesson {number} card {card_index} is missing its published HTSK source sentence."
                    )
                if source_sentence:
                    built = normalize(prompt.replace("___", answer, 1))
                    expected_sentence = normalize(str(source_sentence))
                    built = re.sub(r"[.!?。！？]+$", "", built)
                    expected_sentence = re.sub(r"[.!?。！？]+$", "", expected_sentence)
                    if built != expected_sentence:
                        raise ValueError(
                            f"Lesson {number} card {card_index} does not reconstruct its source sentence."
                        )
            answers = [normalize(card.get("answer", "")) for card in cards]
            if len(answers) != len(set(answers)):
                raise ValueError(
                    f"Lesson {number} contains duplicate target answers; each card must use "
                    "a distinct lexical context or target expression."
                )
            if lesson_number in VOCABULARY_LESSON_NUMBERS and not cards:
                raise ValueError(f"Vocabulary lesson {number} must contain target-word cards.")
            guides[number] = {
                "source_status": lesson.get("source_status"),
                "source_title": lesson.get("source_title", lesson.get("title", "")),
                "source_pattern": lesson.get("source_pattern", lesson.get("pattern", "")),
                "source_url": lesson.get("source_url", ""),
                "meaning": lesson.get("meaning", ""),
                "when_to_use": lesson.get("when_to_use", ""),
                "how_to_build": lesson.get("how_to_build", ""),
                "examples": lesson.get("examples", []),
                "examples_source": lesson.get("examples_source", ""),
                "source_note": lesson.get("source_note", ""),
            }
    expected = {str(number) for number in range(0, 209)}
    if set(guides) != expected:
        raise ValueError("The unit lesson seed files must contain exactly lessons 26–208.")
    for number, guide in guides.items():
        if guide.get("source_status") == "published":
            required = ("source_url", "meaning", "when_to_use", "how_to_build", "examples")
            if any(not guide.get(field) for field in required):
                raise ValueError(f"HTSK guide for lesson {number} is incomplete.")
    return guides


HTSK_GUIDES = load_htsk_guides()


def lesson_guide(lesson):
    """Return only the explicit HTSK guide for this lesson."""
    raw = HTSK_GUIDES.get(str(int(lesson["lesson_number"])))
    if not raw or raw.get("source_status") != "published":
        return {
            "available": False,
            "source_url": (raw or {}).get(
                "source_url",
                "https://www.howtostudykorean.com/unit-9/lessons-201-208/",
            ),
            "source_title": (raw or {}).get("source_title", "Not published by HTSK"),
            "source_note": (raw or {}).get(
                "source_note", "HTSK has not published this lesson yet."
            ),
            "examples": [],
        }
    return {
        "available": True,
        "source_url": raw["source_url"],
        "source_title": raw["source_title"],
        "meaning": raw["meaning"],
        "usage": raw["when_to_use"],
        "building": raw["how_to_build"],
        "examples": raw["examples"],
        "examples_source": raw.get("examples_source", "HTSK lesson page"),
        "source_note": raw.get("source_note", ""),
    }

def answer_is_correct(user, answer):
    return normalize(user) == normalize(answer)


def check_answer(card_id, answer_key):
    """Automatically grade a card from the number of attempts.

    A wrong answer lowers the Bunpro streak once and keeps the same card on
    screen. The next correct answer confirms the retry and keeps that level.
    """
    # The current card was already loaded for rendering.  Reusing its answer
    # removes one network round-trip on every Enter press against Supabase.
    answer_cache = st.session_state.setdefault("_review_answer_cache", {})
    answer = answer_cache.get(card_id)
    card = {"answer": answer} if answer is not None else one(
        "SELECT answer FROM cards WHERE id=?", (card_id,)
    )
    user_answer = st.session_state.get(answer_key, "")
    if not card or not normalize(user_answer):
        return
    attempt_key = f"attempts_{card_id}"
    attempts = st.session_state.get(attempt_key, 0) + 1
    st.session_state[attempt_key] = attempts
    if answer_is_correct(user_answer, card["answer"]):
        had_wrong_attempt = st.session_state.pop(f"wrong_graded_{card_id}", False)
        st.session_state.pop("retry_card_id", None)
        result = "incorrect → correct" if had_wrong_attempt else "correct"
        st.session_state["result_card_id"] = card_id
        st.session_state["result_user_answer"] = user_answer
        st.session_state["result_correct_answer"] = card["answer"]
        st.session_state["result_grade"] = result
        if not had_wrong_attempt:
            grade(card_id, "correct")
        else:
            # The first wrong attempt already moved the card down, but the
            # card is counted as completed only after the retry is correct.
            st.session_state["review_completed"] = st.session_state.get("review_completed", 0) + 1
            st.session_state.pop(attempt_key, None)
            st.session_state.pop("wrong_feedback", None)
        st.rerun()
    else:
        if not st.session_state.get(f"wrong_graded_{card_id}"):
            grade(card_id, "incorrect")
            st.session_state[f"wrong_graded_{card_id}"] = True
        st.session_state["retry_card_id"] = card_id
        st.session_state["wrong_feedback"] = card_id
        # The callback runs before the widget is rendered again, so this is
        # safe and gives the learner a clean field for the next attempt.
        st.session_state[answer_key] = ""
        st.rerun()


def focus_answer_field():
    """Put the cursor in the Review answer box after a card is rendered."""
    components.html("""
    <script>
    (function() {
        const parentWindow = window.parent;
        function focusAnswer() {
            const input = parentWindow.document.querySelector('input[aria-label^="Answer for card "]');
            if (!input) return false;
            input.focus();
            const end = input.value.length;
            try { input.setSelectionRange(end, end); } catch (error) {}
            return true;
        }
        let attempts = 0;
        const timer = parentWindow.setInterval(function() {
            attempts += 1;
            if (focusAnswer() || attempts >= 20) {
                parentWindow.clearInterval(timer);
            }
        }, 100);
        parentWindow.setTimeout(focusAnswer, 0);
    })();
    </script>
    """, height=1)


def mount_inline_answer(slot_id, marker_id, input_label):
    """Move the real Streamlit widget into the sentence blank.

    Streamlit still owns the input and its ``on_change`` callback, so Enter
    grades the answer normally.  The small DOM bridge only changes its visual
    position and resizes it locally while typing; it never causes a rerun per
    character.
    """
    components.html(f"""
    <script>
    (function() {{
        const parentWindow = window.parent;
        const slotId = {json.dumps(slot_id)};
        const markerId = {json.dumps(marker_id)};
        const inputLabel = {json.dumps(input_label)};
        function resize(input) {{
            const measure = parentWindow.document.createElement('span');
            const style = parentWindow.getComputedStyle(input);
            measure.style.position = 'absolute';
            measure.style.visibility = 'hidden';
            measure.style.whiteSpace = 'pre';
            measure.style.font = style.font;
            measure.textContent = input.value || '...';
            parentWindow.document.body.appendChild(measure);
            const width = Math.max(parseFloat(style.fontSize) * 1.25, measure.getBoundingClientRect().width + 5);
            input.style.width = Math.ceil(width) + 'px';
            measure.remove();
        }}
        function mount() {{
            const slot = parentWindow.document.getElementById(slotId);
            const marker = parentWindow.document.getElementById(markerId);
            const input = parentWindow.document.querySelector('input[aria-label="' + inputLabel + '"]');
            if (!slot || !marker || !input) return false;
            const inputElement = input.closest('[data-testid="stElementContainer"]') || input.closest('[data-testid="stTextInput"]') || input;
            const markerElement = marker.closest('[data-testid="stElementContainer"]');
            if (markerElement) markerElement.style.display = 'none';
            inputElement.classList.add('inline-answer-element');
            input.classList.add('inline-answer-input');
            function clearAnswerChrome(node) {{
                if (!node) return;
                node.style.setProperty('border', '0', 'important');
                node.style.setProperty('border-width', '0', 'important');
                node.style.setProperty('border-color', 'transparent', 'important');
                node.style.setProperty('border-radius', '0', 'important');
                node.style.setProperty('outline', '0', 'important');
                node.style.setProperty('background', 'transparent', 'important');
                node.style.setProperty('background-color', 'transparent', 'important');
                node.style.setProperty('background-image', 'none', 'important');
                node.style.setProperty('box-shadow', 'none', 'important');
                node.style.setProperty('appearance', 'none', 'important');
                node.style.setProperty('-webkit-appearance', 'none', 'important');
                node.style.setProperty('color', 'inherit', 'important');
                node.style.setProperty('-webkit-text-fill-color', 'inherit', 'important');
            }}
            [input, inputElement, input.closest('[data-baseweb="input"]'), input.closest('[data-baseweb="base-input"]'), input.closest('[data-testid="stTextInput"]')].forEach(clearAnswerChrome);
            inputElement.querySelectorAll('*').forEach(clearAnswerChrome);
            if (slot.firstElementChild !== inputElement) {{
                slot.replaceChildren(inputElement);
            }}
            if (!input.dataset.inlineResizeBound) {{
                input.dataset.inlineResizeBound = '1';
                input.addEventListener('input', function() {{ resize(input); }});
            }}
            resize(input);
            return true;
        }}
        let attempts = 0;
        const timer = parentWindow.setInterval(function() {{
            attempts += 1;
            if (mount() || attempts >= 30) parentWindow.clearInterval(timer);
        }}, 80);
        parentWindow.setTimeout(mount, 0);
    }})();
    </script>
    """, height=1)


def enable_review_hotkeys(card_id, nonce):
    """Kept for compatibility with older saved sessions."""
    components.html(f"""
    <script>
    (function() {{
        const win = window.parent;
        const marker = 'korean_srs_review_keys_{card_id}_{nonce}';
        if (win[marker]) return;
        win[marker] = true;
        function reviewRoot() {{
            return win.document.querySelector('[role="dialog"]') || win.document;
        }}
        function findButton(label) {{
            return Array.from(reviewRoot().querySelectorAll('button')).find(function(button) {{
                return (button.innerText || button.textContent || '').trim() === label;
            }});
        }}
        function handler(event) {{
            const key = event.key;
            const label = (key === '1') ? 'Again' : (key === '2') ? 'Hard' : (key === '4') ? 'Easy' : ((key === '3' || key === 'Enter' || key === ' ') ? 'Good' : null);
            if (!label) return;
            const button = findButton(label);
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
    lesson = one("SELECT lesson_number FROM lessons WHERE id=?", (lesson_id,))
    if not lesson:
        return False
    source_guide = HTSK_GUIDES.get(str(lesson["lesson_number"]))
    if not source_guide or source_guide.get("source_status") != "published":
        return False
    c = db()
    c.execute("""
        UPDATE reviews SET active=1, level=0, next_review=?, due_at=?,
                           last_review=NULL, last_result=NULL, mistakes=0
        WHERE card_id IN (SELECT id FROM cards WHERE lesson_id=?)
          AND active=0 AND retired=0
    """, (today(), datetime.now().isoformat(timespec="seconds"), lesson_id))
    c.execute("UPDATE lessons SET status='studying' WHERE id=?", (lesson_id,))
    c.commit()
    c.close()
    award_crystals(f"lesson_started:{lesson_id}", 10)
    record_activity("lesson")
    # If Review was opened earlier in the same browser session, discard its
    # old denominator so newly added cards appear immediately in the queue.
    for key in ("review_total", "review_completed", "checked"):
        st.session_state.pop(key, None)
    return True


def ensure_daily_lessons():
    """Assign the first unlocked pair of lessons for today.

    New lessons are released in sequential pairs.  A later pair must never
    appear while an earlier lesson is still only ``available``.  ``studying``
    is the app's durable marker that the learner opened the lesson and added
    its cards to the deck, so it counts as completed for unlocking the next
    pair.  The reconciliation also repairs a stale today's assignment left
    by the old non-gated scheduler.
    """
    day = today()
    start = int(setting("start_unit", "2"))
    limit = int(setting("new_lessons_per_day", "2"))
    if limit != 2:
        # The product rule is two lessons per day, even if an old database
        # contains another value in settings.
        limit = 2

    lessons = rows("""
        SELECT * FROM lessons
        WHERE unit>=?
        ORDER BY unit, lesson_number
    """, (start,))
    if not lessons:
        return

    completed_statuses = {"studying", "completed"}
    unlocked_pair = None
    # Start at the first unfinished lesson, then take the next lesson too.
    # This keeps the natural sequence intact even when the learner began at
    # an odd lesson number (for example 31–32, then 33–34).
    first_unfinished = next(
        (index for index, lesson in enumerate(lessons)
         if lesson["status"] not in completed_statuses),
        None,
    )
    if first_unfinished is not None:
        previous_complete = all(
            lesson["status"] in completed_statuses
            for lesson in lessons[:first_unfinished]
        )
        pair = lessons[first_unfinished:first_unfinished + limit]
        if previous_complete and len(pair) == limit:
            unlocked_pair = pair
    if not unlocked_pair:
        return

    current_rows = rows("""
        SELECT lessons.id, lessons.lesson_number, daily_lessons.status AS daily_status
        FROM daily_lessons JOIN lessons ON lessons.id=daily_lessons.lesson_id
        WHERE daily_lessons.day=?
        ORDER BY lessons.lesson_number
    """, (day,))
    current_ids = {row["id"] for row in current_rows}
    target_ids = {lesson["id"] for lesson in unlocked_pair}
    if current_ids == target_ids:
        return

    # Never erase a lesson the learner already completed today.  Otherwise
    # remove only the stale/new assignment and replace it with the gated pair.
    c = db()
    if current_rows and all(row["daily_status"] == "new" for row in current_rows):
        c.execute("DELETE FROM daily_lessons WHERE day=?", (day,))
    elif current_rows:
        c.close()
        return
    for lesson in unlocked_pair:
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


def _reward_once_in_transaction(connection, event_key, amount, created_at):
    """Add one idempotent reward without opening another database transaction."""
    if amount <= 0:
        return
    params = (event_key, amount, created_at)
    if is_postgres_connection(connection):
        inserted = connection.execute(
            "INSERT INTO reward_events(event_key,amount,created_at) VALUES(?,?,?) "
            "ON CONFLICT (event_key) DO NOTHING RETURNING event_key",
            params,
        ).fetchone()
        was_inserted = inserted is not None
    else:
        cursor = connection.execute(
            "INSERT OR IGNORE INTO reward_events(event_key,amount,created_at) VALUES(?,?,?)",
            params,
        )
        was_inserted = bool(getattr(cursor, "rowcount", 0))
    if was_inserted:
        connection.execute("UPDATE wallet SET crystals=crystals+? WHERE id=1", (amount,))


def grade(card_id, result):
    current = one("SELECT * FROM reviews WHERE card_id=?", (card_id,))
    if not current:
        return
    old_level = max(0, int(current["level"] or 0))
    mistakes = int(current["mistakes"] or 0)
    now_dt = datetime.now()
    if result == "correct":
        new_level = min(SRS_MAX_LEVEL, old_level + 1)
        interval = BUNPRO_INTERVALS.get(old_level)
        due_at = now_dt + interval if interval else datetime(2999, 1, 1)
        active = 0 if new_level >= SRS_MAX_LEVEL else 1
    elif result == "incorrect":
        new_level = max(0, old_level - 1)
        due_at = now_dt + BUNPRO_INTERVALS[new_level]
        mistakes += 1
        active = 1
    else:
        raise ValueError(f"Unknown SRS result: {result}")
    due_text = due_at.isoformat(timespec="seconds")
    next_date = due_at.date().isoformat()
    now = now_dt.isoformat(timespec="seconds")
    c = db()
    c.execute("""
        UPDATE reviews SET level=?, next_review=?, due_at=?, last_review=?,
                           last_result=?, mistakes=?, active=?
        WHERE card_id=?
    """, (new_level, next_date, due_text, now, result, mistakes, active, card_id))
    c.execute("INSERT INTO answer_history(card_id,result,created_at) VALUES(?,?,?)", (card_id, result, now))
    # Keep the review write, activity counter and both idempotent rewards in
    # one database transaction.  The old path committed the review, opened a
    # second reward transaction, then opened a third activity transaction and
    # a fourth streak query; that made every Enter feel like a freeze on a
    # remote PostgreSQL database.
    day = today()
    c.execute(
        "INSERT OR IGNORE INTO study_activity(day,lessons,reviews,last_activity) VALUES(?,?,?,?)",
        (day, 0, 0, now),
    )
    c.execute(
        "UPDATE study_activity SET reviews=reviews+1, last_activity=? WHERE day=?",
        (now, day),
    )
    _reward_once_in_transaction(c, f"card_review:{card_id}:{due_text}:{result}", {"correct": 3, "incorrect": 0}[result], now)
    _reward_once_in_transaction(c, f"streak_bonus:{day}", 5, now)
    c.commit()
    c.close()
    if result == "correct":
        st.session_state["review_completed"] = st.session_state.get("review_completed", 0) + 1
    st.session_state.pop("checked", None)
    st.session_state.pop(f"attempts_{card_id}", None)
    st.session_state.pop("wrong_feedback", None)
    st.session_state.pop(f"revealed_answer_{card_id}", None)
    # A widget key cannot be changed after the widget is created in the
    # current Streamlit run. A nonce gives the next card a fresh input field.
    st.session_state["review_nonce"] = st.session_state.get("review_nonce", 0) + 1


def next_new_lesson():
    start = int(setting("start_unit", "2"))
    return one("""
        SELECT * FROM lessons
        WHERE status IN ('available','studying') AND unit>=?
        AND id NOT IN (
            SELECT lesson_id
            FROM cards
            JOIN reviews ON reviews.card_id=cards.id
            WHERE reviews.active=1 AND reviews.retired=0
        )
        ORDER BY unit, lesson_number LIMIT 1
    """, (start,))


def next_due_card():
    # Rotation rule: cards reviewed today go last; NULL/old last_review go first.
    # This matters when all cards in a grammar point share the same due date.
    # A newly added card has no last_review yet, so it belongs in Review even
    # if an older database left its placeholder next_review in the future.
    return one("""
        SELECT cards.*, lessons.title AS lesson_title, lessons.pattern,
               reviews.level, reviews.next_review, reviews.due_at, reviews.last_review
        FROM cards
        JOIN lessons ON lessons.id=cards.lesson_id
        JOIN reviews ON reviews.card_id=cards.id
        WHERE reviews.active=1
          AND reviews.retired=0
          AND (reviews.due_at<=? OR (reviews.due_at IS NULL AND (reviews.next_review<=? OR reviews.last_review IS NULL)))
          AND lessons.status IN ('available','studying')
        ORDER BY
            CASE WHEN substr(reviews.last_review,1,10)=? THEN 1 ELSE 0 END,
            COALESCE(reviews.last_review,'0000-01-01T00:00:00'),
            reviews.next_review, cards.id
        LIMIT 1
    """, (datetime.now().isoformat(timespec="seconds"), today(), today()))


def open_review():
    """Start a fresh Review visit from a dashboard or lesson action."""
    for key in ("review_total", "review_completed", "checked"):
        st.session_state.pop(key, None)
    st.session_state["go_review"] = True
    st.session_state.pop("retry_card_id", None)
    st.rerun()


def render_card(card):
    st.session_state.setdefault("_review_answer_cache", {})[card["id"]] = card["answer"]
    nonce = st.session_state.get("review_nonce", 0)
    answer_key = f"answer_{card['id']}_{nonce}"
    slot_id = f"inline_answer_slot_{card['id']}_{nonce}"
    marker_id = f"inline_answer_marker_{card['id']}_{nonce}"
    input_label = f"Answer for card {card['id']}"
    blank = f'<span class="inline-answer-slot" id="{slot_id}">...</span>'
    prompt_html = escape(str(card["prompt"])).replace("___", blank, 1).replace("\n", "<br>")
    translation_html = escape(str(card["translation"])).replace("\n", "<br>")
    answer_form = inferred_answer_form(card)
    st.markdown(
        f'''<div class="review-question-paper"><div class="review-prompt">{prompt_html}</div><div class="review-translation">{translation_html}</div>{f"<div class='answer-form-note'>Required answer form: {escape(answer_form)}</div>" if answer_form else ""}</div>''',
        unsafe_allow_html=True,
    )
    with st.expander("Show the word in its base form"):
        st.write(card["hint"])
    with st.expander("Show the grammar explanation"):
        st.write(card["explanation"])
    with st.container():
        st.markdown(f'<span id="{marker_id}" class="answer-widget-marker"></span>', unsafe_allow_html=True)
        answer = st.text_input(
            input_label,
            key=answer_key,
            on_change=check_answer,
            args=(card["id"], answer_key),
            placeholder="...",
            label_visibility="collapsed",
        )
    mount_inline_answer(slot_id, marker_id, input_label)
    attempts = st.session_state.get(f"attempts_{card['id']}", 0)
    if st.session_state.get("wrong_feedback") == card["id"]:
        st.warning(f"Not quite yet. Try again — attempt {attempts + 1}.")
    elif attempts:
        st.caption(f"Attempts: {attempts}. Enter your answer again.")
    focus_answer_field()


def lesson_preview(lesson_id, daily=False):
    """Render the lesson contents inside the native in-app Study dialog."""
    lesson = one("SELECT * FROM lessons WHERE id=?", (lesson_id,))
    if not lesson:
        return
    guide = lesson_guide(lesson)
    st.markdown(
        f'''<div class="lesson-modal-heading"><h2>📖 Lesson {lesson['lesson_number']}: {escape(lesson['title'])}</h2><p>Study room · read the HTSK guide first, then add this lesson to your SRS deck.</p></div>''',
        unsafe_allow_html=True,
    )
    if lesson["pattern"] and lesson["pattern"] != "—":
        st.markdown(f"### Grammar point: `{lesson['pattern']}`")
    st.markdown(f"[Open the full HTSK lesson ↗]({guide['source_url']})")
    if not guide.get("available"):
        st.warning(guide["source_note"])
        st.caption("The app will not create SRS cards for this lesson until HTSK publishes its content.")
        if st.button("← Back", key=f"close_unpublished_{lesson_id}", use_container_width=True):
            st.rerun()
        return

    def guide_text(value):
        return escape(str(value or "")).replace("\n", "<br>")

    st.markdown(
        f'''<div class="lesson-guide-copy" style="background:#fffaff;border:1px solid #efd8e8;color:#514064"><div class="lesson-section-title">Meaning</div><div>{guide_text(guide['meaning'])}</div></div>''',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''<div class="lesson-guide-copy" style="background:#fffaff;border:1px solid #efd8e8;color:#514064"><div class="lesson-section-title">When to use it</div><div>{guide_text(guide['usage'])}</div></div>''',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''<div class="lesson-guide-copy" style="background:#fffaff;border:1px solid #efd8e8;color:#514064"><div class="lesson-section-title">How to build it</div><div>{guide_text(guide['building'])}</div></div>''',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="lesson-section-title">Examples from HTSK</div>', unsafe_allow_html=True)
    guide_examples = guide.get("examples", [])
    if guide_examples:
        for index, (example, translation) in enumerate(guide_examples, 1):
            # A few HTSK examples are short conversational exchanges.  Keep
            # the context and the ~다니 reaction on separate visible lines.
            display_example = guide_text(example)
            display_translation = guide_text(translation)
            st.markdown(
                f'''<div class="lesson-example" style="background:#ffffff;border:1px solid #efd8e8;border-left:5px solid #efb8d6;color:#514064"><div><b>{index}.</b> {display_example}</div><div style="margin-top:7px;color:#7d668d;font-size:14px">Translation: {display_translation}</div></div>''',
                unsafe_allow_html=True,
            )
    st.caption(f"{guide.get('examples_source', 'HTSK lesson page')} · examples are separate from SRS cards")
    with st.container(key=f"lesson_actions_{lesson_id}"):
        st.divider()
        cancel, add = st.columns(2)
        with cancel:
            if st.button("← Back", key=f"close_preview_{lesson_id}", use_container_width=True):
                st.rerun()
        with add:
            if st.button("Add to deck ✨", key=f"add_preview_{lesson_id}", type="primary", use_container_width=True):
                activated = activate_lesson(lesson_id)
                if activated and daily:
                    c = db()
                    c.execute("UPDATE daily_lessons SET status='studied' WHERE day=? AND lesson_id=?", (today(), lesson_id))
                    c.commit()
                    c.close()
                if activated:
                    st.rerun()
                st.error("This lesson cannot be added until HTSK publishes its material.")


def render_lesson_dialog(lesson_id, daily=False):
    """Open a Study lesson as a large internal modal, with an inline fallback."""
    if hasattr(st, "dialog"):
        lesson_dialog(lesson_id, daily)
    else:
        lesson_preview(lesson_id, daily)


def render_review_dialog():
    """Open Review as a large internal modal, with an inline fallback."""
    if hasattr(st, "dialog"):
        review_dialog()
    else:
        render_review_contents()


def page_dashboard():
    st.markdown('<div class="brand-logo"><div class="brand-mark">🍡</div><div><div class="brand-name">Mochi Hangul</div><div class="brand-subtitle">cute Korean grammar garden</div></div></div>', unsafe_allow_html=True)
    st.title("Mochi Hangul")
    summary = one("""
        SELECT
          (SELECT COUNT(*) FROM reviews JOIN cards ON cards.id=reviews.card_id
             JOIN lessons ON lessons.id=cards.lesson_id
             WHERE reviews.active=1 AND reviews.retired=0
               AND (reviews.due_at<=? OR (reviews.due_at IS NULL AND (reviews.next_review<=? OR reviews.last_review IS NULL)))
               AND lessons.status IN ('available','studying')) AS due,
          (SELECT COUNT(*) FROM reviews WHERE active=1 AND retired=0) AS active,
          (SELECT COUNT(*) FROM reviews WHERE active=1 AND retired=0 AND level>=8) AS mastered
    """, (datetime.now().isoformat(timespec="seconds"), today()))
    due = summary["due"]
    active = summary["active"]
    mastered = summary["mastered"]
    a, b, c = st.columns(3)
    a.metric("Due reviews", due)
    b.metric("Active cards", active)
    c.metric("Mastered cards", mastered)
    st.markdown(f"<div class='cute-note'>💎 <b>{crystals()}</b> crystals · collect more in reviews and daily lessons</div>", unsafe_allow_html=True)
    current_streak = streak_info()
    streak_status = "Your flame is lit today — keep it glowing!" if current_streak["active_today"] else "Study today to keep the flame glowing."
    st.markdown(
        f'''<div class="streak-card"><div class="streak-main"><span class="streak-fire">🔥</span><span>{current_streak['current']} day streak</span></div><div class="streak-meta"><b>Best: {current_streak['best']} days</b><br>{streak_status}</div></div>''',
        unsafe_allow_html=True,
    )
    if due:
        st.markdown(
            f"<div class='cute-note'>📝 <b>{due} cards are waiting in Review.</b> "
            "Newly added cards are included here even before their first rating.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("No cards are waiting in Review right now.")
    if st.button(
        f"Review · {due} cards" if due else "Review",
        key="dashboard_review_top",
        type="primary",
        use_container_width=True,
    ):
        open_review()

    st.header("Today's new lessons")
    todays = daily_lessons()
    lesson_request = None
    completed = sum(lesson["daily_status"] == "studied" for lesson in todays)
    if todays:
        st.caption(f"{completed} of {len(todays)} new lessons completed today")
        quest_tracker = active_item("tracker")
        quest_icon = quest_tracker["icon"] if quest_tracker else "🍡"
        quest_ratio = completed / len(todays)
        st.markdown(f'''<div class="quest-card">
            <div class="quest-title"><span>Today's learning quest</span><span>{completed} / {len(todays)}</span></div>
            <div class="quest-track"><div class="quest-fill" style="width:{quest_ratio * 100:.1f}%"></div><div class="progress-mascot" style="left:clamp(0px,calc({quest_ratio * 100:.1f}% - 19px),calc(100% - 38px))">{quest_icon}</div></div>
            <div class="quest-caption">Complete your tiny lesson quest and collect crystals ✨</div>
        </div>''', unsafe_allow_html=True)
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
                            lesson_request = (lesson["id"], True)
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
    if st.button(
        f"Review · {due} cards" if due else "Review",
        key="dashboard_review_bottom",
        type="primary",
        use_container_width=True,
    ):
        open_review()
    if lesson_request:
        render_lesson_dialog(*lesson_request)


def render_review_contents():
    """Render the Review experience inside the app's full-screen dialog."""
    if "review_total" not in st.session_state:
        remaining = one("SELECT COUNT(*) AS n FROM reviews JOIN cards ON cards.id=reviews.card_id JOIN lessons ON lessons.id=cards.lesson_id WHERE reviews.active=1 AND reviews.retired=0 AND (reviews.due_at<=? OR (reviews.due_at IS NULL AND (reviews.next_review<=? OR reviews.last_review IS NULL))) AND lessons.status IN ('available','studying')", (datetime.now().isoformat(timespec='seconds'), today()))["n"]
        st.session_state["review_total"] = remaining
        st.session_state["review_completed"] = 0
    total = st.session_state.get("review_total", 0)
    completed = min(st.session_state.get("review_completed", 0), total) if total else 0
    progress = 1.0 if total == 0 else completed / total
    frame = active_item("frame")
    tracker = active_item("tracker")
    frame_icon = escape(frame["icon"] if frame else "🌸")
    tracker_icon = escape(tracker["icon"] if tracker else "🍡")
    character = active_item("character")
    character_icon = escape(character["icon"] if character else "🐰")
    frame_style = FRAME_STYLES.get(frame["id"] if frame else "frame_sakura", FRAME_STYLES["frame_sakura"])
    frame_border = frame_style["border"]
    frame_bg = frame_style["background"]
    frame_decor = escape(frame_style["decor"])
    frame_label = escape(frame_style["label"])
    tracker_color = TRACKER_COLORS.get(tracker["id"] if tracker else "tracker_mochi", "#f5a6c8")
    st.markdown(f'''<div class="review-progress" style="border-color:{frame_border};background:linear-gradient(110deg,{frame_bg},#f4efff)">
        <div class="review-progress-title"><span>{frame_icon} Today's progress</span><span>{completed} / {total} cards</span></div>
        <div class="review-progress-track">
            <div class="review-progress-fill" style="width:{progress * 100:.1f}%;background:{tracker_color}"></div>
            <div class="progress-mascot" style="left:clamp(0px,calc({progress * 100:.1f}% - 19px),calc(100% - 38px));border-color:{tracker_color}">{tracker_icon}</div>
        </div>
    </div>''', unsafe_allow_html=True)
    result_card_id = st.session_state.get("result_card_id")
    if result_card_id:
        result_card = one("""
            SELECT cards.*, lessons.title AS lesson_title
            FROM cards JOIN lessons ON lessons.id=cards.lesson_id
            WHERE cards.id=?
        """, (result_card_id,))
        if result_card:
            user_answer = escape(str(st.session_state.get("result_user_answer", "")))
            answered_prompt = escape(str(result_card["prompt"])).replace(
                "___",
                f'''<span class="answer-result-value">{user_answer}</span>''',
                1,
            )
            st.markdown(
                f'''<div class="review-question-paper"><div class="review-prompt">{answered_prompt.replace(chr(10), "<br>")}</div><div class="review-translation">{escape(str(result_card["translation"])).replace(chr(10), "<br>")}</div></div>''',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'''<div class="answer-results"><div>Your answer: <span class="answer-result-value">{user_answer}</span></div><div>Correct answer: <span class="answer-result-value">{escape(str(st.session_state.get("result_correct_answer", "")))}</span></div></div>''',
                unsafe_allow_html=True,
            )
            if st.button("Continue →", key="continue_after_grade", type="primary", use_container_width=True):
                for key in ("result_card_id", "result_user_answer", "result_correct_answer", "result_grade"):
                    st.session_state.pop(key, None)
                st.rerun()
            components.html("""
                <script>
                (function() {
                    const win = window.parent;
                    if (win.__mochiContinueHandler) {
                        win.document.removeEventListener('keydown', win.__mochiContinueHandler, true);
                    }
                    win.__mochiContinueHandler = function(event) {
                        if (event.key !== 'Enter' && event.key !== ' ') return;
                        const buttons = Array.from(win.document.querySelectorAll('button'));
                        const button = buttons.find((item) =>
                            (item.innerText || item.textContent || '').trim().startsWith('Continue')
                        );
                        if (!button) return;
                        event.preventDefault();
                        event.stopPropagation();
                        button.click();
                    };
                    win.document.addEventListener('keydown', win.__mochiContinueHandler, true);
                })();
                </script>
            """, height=1)
            return

    retry_id = st.session_state.get("retry_card_id")
    due = None
    if retry_id:
        due = one("""
            SELECT cards.*, lessons.title AS lesson_title, lessons.pattern,
                   reviews.level, reviews.next_review, reviews.due_at, reviews.last_review
            FROM cards
            JOIN lessons ON lessons.id=cards.lesson_id
            JOIN reviews ON reviews.card_id=cards.id
            WHERE cards.id=? AND reviews.active=1 AND reviews.retired=0
        """, (retry_id,))
        if not due:
            st.session_state.pop("retry_card_id", None)
    if not due:
        due = next_due_card()
    if not due:
        st.success("No reviews due today. Your review quest is complete! ✨")
        if st.button("← Close Review", key="close_review_modal_empty", use_container_width=True):
            st.session_state["nav"] = "Dashboard"
            st.session_state.pop("review_total", None)
            st.session_state.pop("review_completed", None)
            st.rerun()
        return
    st.markdown(
        f'''<style>
        .st-key-review_card_shell {{border:0 !important; border-radius:32px !important; background:{frame_bg} !important; box-shadow:0 12px 28px rgba(134,101,156,.14) !important; padding:9px 16px 12px !important;}}
        .st-key-review_card_shell [data-testid="stVerticalBlockBorderWrapper"] {{border:3px solid {frame_border} !important; border-radius:25px !important; background:{frame_bg} !important;}}
        </style>''',
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="review_card_shell"):
        st.markdown(
            f'''<div class="review-card-top" style="color:{frame_style['accent']}"><span class="frame-sparkles">{frame_decor} {frame_decor}</span><span>{frame_decor} {frame_label} · today's card {completed + 1}</span><span class="frame-sparkles">{frame_decor} {frame_decor}</span></div>''',
            unsafe_allow_html=True,
        )
        render_card(due)
        st.markdown(
            f'''<div class="review-card-bottom">{frame_decor} Your answer is one tiny step forward {frame_decor}</div>''',
            unsafe_allow_html=True,
        )
    if st.button("← Close Review", key="close_review_modal", use_container_width=True):
        st.session_state["nav"] = "Dashboard"
        for key in ("review_total", "review_completed", "checked"):
            st.session_state.pop(key, None)
        st.rerun()


if hasattr(st, "dialog"):
    @st.dialog("📖 Study lesson", width="large")
    def lesson_dialog(lesson_id, daily=False):
        render_bts_motivation(in_dialog=True)
        lesson_preview(lesson_id, daily)

    @st.dialog("✨ Review", width="large")
    def review_dialog():
        render_bts_motivation(in_dialog=True)
        render_review_contents()
else:
    lesson_dialog = None
    review_dialog = None


def page_lessons():
    st.title("Lessons")
    start = int(setting("start_unit", "2"))
    # Units 0–1 are completed by default, but remain visible for reference
    # and can be added manually to the SRS deck from their Study dialogs.
    lessons = rows("SELECT * FROM lessons ORDER BY unit, lesson_number")
    # Do not issue two PostgreSQL queries for every lesson.  With 209 lessons
    # that made opening the Lessons page wait for hundreds of network round
    # trips, and the Study dialog could not appear until all of them finished.
    card_stats = rows("""
        SELECT cards.lesson_id,
               SUM(CASE WHEN reviews.retired=0 THEN 1 ELSE 0 END) AS cards,
               SUM(CASE WHEN reviews.active=1 AND reviews.retired=0 THEN 1 ELSE 0 END) AS active
        FROM cards JOIN reviews ON reviews.card_id=cards.id
        GROUP BY cards.lesson_id
    """)
    stats_by_lesson = {row["lesson_id"]: row for row in card_stats}
    lessons_by_unit = {unit: [] for unit in UNIT_INFO}
    for lesson in lessons:
        lessons_by_unit.setdefault(lesson["unit"], []).append(lesson)
    st.caption("Open a unit to see its lessons. Study shows the HTSK explanation and separate examples; cards appear only after Add to deck.")
    lesson_request = None
    for unit, (title, lesson_range, status) in UNIT_INFO.items():
        if status == "completed":
            badge = "✅ Completed"
        elif status == "current":
            badge = "🌸 Current unit"
        else:
            badge = "🔒 Locked"
        with st.expander(
            f"Unit {unit}: {title} · {lesson_range} · {badge}",
            expanded=(unit == start),
        ):
            if unit < start:
                st.success("This unit is marked as completed before your starting point.")
                st.caption("It is not included in the daily queue, but you can open any lesson and add its cards manually.")
            if unit in HTSK_GROUPS:
                links = " · ".join(f"[{name}]({url})" for name, url in HTSK_GROUPS[unit])
                st.markdown(f"Official HTSK lesson pages: {links}")
            unit_lessons = lessons_by_unit.get(unit, [])
            if not unit_lessons:
                st.caption("No lessons are available in this unit yet.")
                continue
            for lesson in unit_lessons:
                stats = stats_by_lesson.get(lesson["id"], {})
                cards = stats.get("cards", 0) or 0
                active = stats.get("active", 0) or 0
                guide = lesson_guide(lesson)
                with st.container(border=True):
                    left, right = st.columns([5, 1.3])
                    with left:
                        st.markdown(f"**Lesson {lesson['lesson_number']}: {lesson['title']}**")
                        if guide.get("available"):
                            st.caption(f"{lesson['pattern']} · {active}/{cards} cards active · HTSK guide inside Study")
                            st.markdown(f"[Open the full HTSK lesson ↗]({guide['source_url']})")
                        else:
                            st.caption("🔒 HTSK has not published this lesson yet")
                            st.markdown(f"[Open the official HTSK page ↗]({guide['source_url']})")
                    with right:
                        if guide.get("available"):
                            if st.button("Study", key=f"study_{lesson['id']}", use_container_width=True):
                                lesson_request = (lesson["id"], False)
    if lesson_request:
        render_lesson_dialog(*lesson_request)


def page_progress():
    st.title("Progress")
    data = rows("""
        SELECT lessons.unit, lessons.lesson_number, lessons.title,
               SUM(CASE WHEN reviews.retired=0 THEN 1 ELSE 0 END) AS cards,
               SUM(CASE WHEN reviews.retired=0 AND reviews.active=1 THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN reviews.retired=0 AND reviews.level>=8 THEN 1 ELSE 0 END) AS mastered
        FROM lessons JOIN cards ON cards.lesson_id=lessons.id
        JOIN reviews ON reviews.card_id=cards.id
        GROUP BY lessons.id ORDER BY lessons.unit, lessons.lesson_number
    """)
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
    categories = [("Faces", "face", "Choose your study buddy"), ("Characters", "character", "A little friend for your dashboard"), ("Room designs", "design", "Change the mood of your study room"), ("Card frames", "frame", "Decorate your Review screen"), ("Progress trackers", "tracker", "Choose how your progress grows")]
    tabs = st.tabs([f"{name}  ✨" for name, _, _ in categories])
    for tab, (name, kind, subtitle) in zip(tabs, categories):
        with tab:
            st.subheader(name)
            st.caption(subtitle)
            items = rows("SELECT * FROM shop_items WHERE kind=? ORDER BY price, id", (kind,))
            for item in items:
                owned = one("SELECT 1 FROM inventory WHERE item_id=?", (item["id"],))
                active_key = f"active_{item['kind']}"
                is_active = setting(active_key, "") == item["id"]
                with st.container(border=True):
                    left, middle, right = st.columns([1, 4, 1.5])
                    with left:
                        st.markdown(f"<div class='shop-item-icon'>{item['icon']}</div>", unsafe_allow_html=True)
                    with middle:
                        st.markdown(f"### {item['name']}")
                        st.caption(item["description"])
                        if kind == "frame":
                            style = FRAME_STYLES.get(item["id"], FRAME_STYLES["frame_sakura"])
                            st.markdown(
                                f'''<div style="border:3px solid {style['border']};border-radius:18px;padding:9px 12px;background:{style['background']};color:#684d7b;text-align:center;font-weight:800">{style['decor']} Review card preview · {style['decor']}</div>''',
                                unsafe_allow_html=True,
                            )
                        elif kind == "tracker":
                            st.markdown(
                                f'''<div class="quest-track" style="margin:7px 0 4px"><div class="quest-fill" style="width:55%;background:{TRACKER_COLORS.get(item['id'], '#f5a6c8')}"></div><div class="progress-mascot" style="left:clamp(0px,calc(55% - 19px),calc(100% - 38px))">{item['icon']}</div></div>''',
                                unsafe_allow_html=True,
                            )
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


bootstrap_app_data(CONTENT_SYNC_VERSION)
if st.session_state.pop("go_review", False):
    st.session_state["nav"] = "Review"
pending_mobile_page = st.session_state.pop("mobile_nav_target", None)
if pending_mobile_page in NAV_PAGES:
    st.session_state["nav"] = pending_mobile_page
render_mobile_navigation()
render_bts_motivation()
st.sidebar.markdown('<div class="brand-logo"><div class="brand-mark">🍡</div><div><div class="brand-name">Mochi Hangul</div><div class="brand-subtitle">Korean grammar SRS</div></div></div>', unsafe_allow_html=True)
page = st.sidebar.radio("Navigate", list(NAV_PAGES), key="nav")
st.sidebar.markdown(f"💎 **{crystals()} crystals**")
if page == "Dashboard": page_dashboard()
elif page == "Review": render_review_dialog()
elif page == "Lessons": page_lessons()
elif page == "Progress": page_progress()
else: page_shop()
