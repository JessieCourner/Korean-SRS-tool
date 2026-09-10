import base64
import json
import re
import sqlite3
from html import escape
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path("korean_bunpro.db")
BTS_ASSET_DIR = APP_DIR / "bts_chibi"
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

# These are original in-app encouragements written for the chibi companion
# panel.  They use the BTS member names as character labels; they are not
# presented as real quotations or official BTS content.
BTS_MOTIVATION = [
    {"level": 1, "ko_member": "RM", "ko_icon": "🐨", "en_member": "Jin", "en_icon": "🐹", "ko": "오늘도 한 문장만 읽어도 충분해요.", "en": "Reading just one sentence today is already enough."},
    {"level": 1, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "V", "en_icon": "🐯", "ko": "천천히 해도 괜찮아요. 매일 조금씩 나아지고 있어요.", "en": "It is okay to go slowly. You are getting better little by little every day."},
    {"level": 1, "ko_member": "Jin", "ko_icon": "🐹", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "작은 성공도 소중한 성공이에요.", "en": "A small success is still a precious success."},
    {"level": 2, "ko_member": "SUGA", "ko_icon": "🐱", "en_member": "Jimin", "en_icon": "🐣", "ko": "틀린 답은 멈춤이 아니라 다음 시도를 위한 힌트예요.", "en": "A wrong answer is not a stop; it is a hint for your next attempt."},
    {"level": 2, "ko_member": "V", "ko_icon": "🐯", "en_member": "RM", "en_icon": "🐨", "ko": "익숙한 표현을 직접 써 볼 때 실력이 더 단단해져요.", "en": "Your skills become stronger when you use a familiar expression yourself."},
    {"level": 2, "ko_member": "j-hope", "ko_icon": "🐿️", "en_member": "Jin", "en_icon": "🐹", "ko": "오늘 배운 문법을 한 문장으로 만들어 보면 기억에 오래 남아요.", "en": "If you make one sentence with today's grammar, it will stay with you longer."},
    {"level": 3, "ko_member": "Jung Kook", "ko_icon": "🐰", "en_member": "SUGA", "en_icon": "🐱", "ko": "꾸준히 복습하면 어제 어렵던 문장도 자연스럽게 읽을 수 있어요.", "en": "With steady review, you can read naturally even the sentences that felt difficult yesterday."},
    {"level": 3, "ko_member": "j-hope", "ko_icon": "🐿️", "en_member": "Jimin", "en_icon": "🐣", "ko": "새로운 문법을 이해할 때마다 한국어로 표현할 수 있는 생각이 넓어져요.", "en": "Every time you understand new grammar, more of your thoughts become expressible in Korean."},
    {"level": 3, "ko_member": "RM", "ko_icon": "🐨", "en_member": "V", "en_icon": "🐯", "ko": "실수한 부분을 다시 살펴보는 습관이 실력을 오래 지켜 줘요.", "en": "The habit of revisiting your mistakes protects your progress for the long term."},
    {"level": 4, "ko_member": "SUGA", "ko_icon": "🐱", "en_member": "Jung Kook", "en_icon": "🐰", "ko": "문맥 속에서 표현의 뉘앙스를 비교하면 더 정확하게 선택할 수 있어요.", "en": "Comparing nuances in context helps you choose the most accurate expression."},
    {"level": 4, "ko_member": "Jimin", "ko_icon": "🐣", "en_member": "RM", "en_icon": "🐨", "ko": "익숙한 문법을 새로운 상황에 옮겨 쓰는 순간, 지식이 진짜 실력이 돼요.", "en": "When you carry familiar grammar into a new situation, knowledge becomes real skill."},
    {"level": 4, "ko_member": "V", "ko_icon": "🐯", "en_member": "j-hope", "en_icon": "🐿️", "ko": "긴 문장도 관계를 하나씩 나누어 보면 핵심 의미가 선명해져요.", "en": "Even a long sentence becomes clear when you separate its relationships one by one."},
    {"level": 5, "ko_member": "RM", "ko_icon": "🐨", "en_member": "Jimin", "en_icon": "🐣", "ko": "복잡한 문장일수록 화자의 의도와 문법의 기능을 함께 살펴보면 의미가 정확해져요.", "en": "The more complex a sentence is, the more accurately you understand it by considering the speaker's intent and the grammar's function together."},
    {"level": 5, "ko_member": "SUGA", "ko_icon": "🐱", "en_member": "V", "en_icon": "🐯", "ko": "배운 표현을 자기 경험과 연결해 사용할 때 언어가 수동적인 지식에서 능동적인 감각으로 바뀌어요.", "en": "When you connect a learned expression to your own experience, language shifts from passive knowledge to active intuition."},
    {"level": 5, "ko_member": "Jung Kook", "ko_icon": "🐰", "en_member": "j-hope", "en_icon": "🐿️", "ko": "한 번에 완벽하려고 하기보다 반복 속에서 의미와 뉘앙스를 정교하게 다듬어 가면 돼요.", "en": "You do not need to be perfect at once; refine meaning and nuance gradually through repetition."},
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
# The daily pair uses a stable date-based layout, so a Streamlit rerun does
# not make the characters jump around while the learner is reading.  The
# layout changes on the next day and keeps the two friends in different parts
# of the dashboard.
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
    .review-progress {padding:16px 18px 12px; border:2px solid #f0c5df; border-radius:24px; background:linear-gradient(110deg,#fff7fc,#f4efff); box-shadow:0 8px 20px rgba(134,101,156,.10); margin:10px 0 22px;}
    .review-progress-title {display:flex; justify-content:space-between; align-items:center; color:#654b78; font-weight:800; margin-bottom:8px;}
    .review-progress-track {height:20px; position:relative; border-radius:99px; background:#eadff2; overflow:visible; border:1px solid #e2cbe1; margin:8px 10px 14px;}
    .review-progress-fill {height:100%; border-radius:99px; background:linear-gradient(90deg,#f5a6c8,#c1a7f1,#9edbe0); transition:width .35s ease;}
    .progress-mascot {position:absolute; top:50%; transform:translate(-50%,-50%); z-index:3; display:flex; align-items:center; justify-content:center; width:38px; height:38px; border-radius:50%; background:#fff; border:3px solid #fff; box-shadow:0 4px 12px rgba(104,77,123,.22); font-size:23px; line-height:1; transition:left .35s ease;}
    .review-frame {border:3px solid #efb8d6; border-radius:30px; padding:18px 22px 8px; background:rgba(255,255,255,.55); box-shadow:0 10px 25px rgba(134,101,156,.08);}
    .review-card-top {display:flex; align-items:center; justify-content:space-between; gap:12px; padding:5px 2px 14px; color:#654b78; font-weight:800; font-size:15px;}
    .review-card-top span {display:inline-flex; align-items:center; gap:7px;}
    .review-card-bottom {padding:14px 2px 2px; text-align:center; color:#987a9d; font-size:13px;}
    .frame-sparkles {letter-spacing:4px; color:#d98eb8; font-size:16px;}
    .streak-card {display:flex; align-items:center; justify-content:space-between; gap:16px; padding:13px 18px; margin:14px 0 18px; border:2px solid #f0c5df; border-radius:22px; background:linear-gradient(110deg,#fff7df,#fff3f8 55%,#f2edff); box-shadow:0 7px 18px rgba(134,101,156,.08);}
    .streak-main {display:flex; align-items:center; gap:10px; color:#654b78; font-weight:900; font-size:18px;}
    .streak-fire {font-size:28px; line-height:1;}
    .streak-meta {color:#987a9d; font-size:13px; text-align:right;}
    /* The daily BTS companions are real bundled transparent PNG cut-outs.
       They float freely on a small stage; the only outlined elements are the
       speech bubbles themselves, not character cards or frames. */
    .bts-stage {position:relative; min-height:380px; overflow:hidden; margin:14px 0 24px; padding:17px 20px 14px; border-radius:30px; background:radial-gradient(circle at 11% 26%,rgba(255,255,255,.95) 0 8%,transparent 27%),radial-gradient(circle at 91% 78%,rgba(255,255,255,.88) 0 7%,transparent 25%),linear-gradient(125deg,#fff3fa 0%,#f3edff 55%,#e9f9ff 100%); box-shadow:0 10px 24px rgba(134,101,156,.10);}
    .bts-stage::before {content:"✦ ｡˚  ♡  ˚｡ ✦"; position:absolute; right:25px; top:18px; color:#e1acd0; font-size:17px; letter-spacing:5px; opacity:.9;}
    .bts-stage::after {content:"✿"; position:absolute; left:28px; bottom:18px; color:#efb2cf; font-size:24px; opacity:.8;}
    .bts-stage-heading {position:relative; z-index:3; display:flex; align-items:center; justify-content:space-between; gap:12px; color:#654b78; font-weight:900; font-size:18px; margin-bottom:4px;}
    .bts-stage-subtitle {position:relative; z-index:3; color:#987a9d; font-size:13px;}
    .bts-scene {position:absolute; z-index:2; display:flex; align-items:flex-end; gap:10px; max-width:48%;}
    .bts-scene-right {flex-direction:row-reverse;}
    .bts-character {width:128px; height:205px; flex:0 0 auto; object-fit:contain; filter:drop-shadow(0 9px 8px rgba(91,71,112,.18)); animation:bts-float 3.8s ease-in-out infinite;}
    .bts-scene-right .bts-character {animation-delay:-1.3s;}
    @keyframes bts-float {0%,100%{transform:translateY(0) rotate(-1deg)}50%{transform:translateY(-7px) rotate(1deg)}}
    .bts-character-fallback {display:flex; align-items:center; justify-content:center; width:92px; height:150px; flex:0 0 auto; font-size:54px;}
    .bts-speech {position:relative; width:max-content; max-width:250px; min-width:168px; padding:11px 14px 12px; border:2px solid #e9b9d7; border-radius:22px; background:rgba(255,255,255,.96); box-shadow:0 7px 16px rgba(134,101,156,.13); color:#5b4770;}
    .bts-scene-right .bts-speech {border-color:#cdb9ec;}
    .bts-scene-left .bts-speech::after, .bts-scene-right .bts-speech::after {content:""; position:absolute; top:54%; width:0; height:0; border-style:solid;}
    .bts-scene-left .bts-speech::after {left:-12px; border-width:9px 12px 9px 0; border-color:transparent #e9b9d7 transparent transparent;}
    .bts-scene-right .bts-speech::after {right:-12px; border-width:9px 0 9px 12px; border-color:transparent transparent transparent #cdb9ec;}
    .bts-speaker {color:#684d7b; font-weight:900; font-size:14px; margin-bottom:5px;}
    .bts-label {display:block; margin-top:2px; color:#a27fa4; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.08em;}
    .bts-quote {color:#5b4770; font-size:15px; line-height:1.5; overflow-wrap:anywhere;}
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
    /* Native Streamlit dialogs stay inside the current app.  The wide dialog
       is expanded almost to the viewport edges so Study and Review feel like
       full-screen cards on both desktop and phone. */
    /* Only the native dialog gets a border.  Its first child is the scroll
       surface; styling that child too was the source of the second frame and
       also clipped the Study actions below long HTSK examples. */
    div[role="dialog"] {width:96vw !important; max-width:96vw !important; height:92vh !important; max-height:92vh !important; top:4vh !important; border:3px solid #efb8d6 !important; border-radius:30px !important; background:linear-gradient(135deg,#fff8fc 0%,#f4efff 58%,#eefaff 100%) !important; box-shadow:0 22px 65px rgba(73,48,93,.28) !important; overflow:hidden !important; display:flex !important; flex-direction:column !important;}
    /* Streamlit's dialog test-id is an inner content wrapper.  It must stay
       transparent so there is only one visible window border. */
    div[role="dialog"] [data-testid="stDialog"], section[data-testid="stDialog"], [data-testid="stDialog"] {border:0 !important; border-radius:0 !important; background:transparent !important; box-shadow:none !important; width:100% !important; max-width:none !important; min-height:0 !important; max-height:100% !important; overflow-y:auto !important; overflow-x:hidden !important;}
    div[role="dialog"] > div:first-child, div[role="dialog"] [data-testid="stDialog"] > div:first-child, section[data-testid="stDialog"] > div:first-child, [data-testid="stDialog"] > div:first-child {width:100% !important; max-width:none !important; min-height:0 !important; max-height:100% !important; flex:1 1 auto !important; overflow-y:auto !important; overflow-x:hidden !important; border:0 !important; border-radius:0 !important; background:transparent !important; box-shadow:none !important;}
    div[role="dialog"] .block-container, section[data-testid="stDialog"] .block-container, [data-testid="stDialog"] .block-container {width:100% !important; max-width:1180px !important; padding:1.4rem 2rem 2rem !important;}
    div[role="dialog"] [data-testid="stMarkdownContainer"], section[data-testid="stDialog"] [data-testid="stMarkdownContainer"], [data-testid="stDialog"] [data-testid="stMarkdownContainer"] {overflow-wrap:anywhere; word-break:normal; line-height:1.55;}
    .quest-card {padding:14px 18px 16px; margin:14px 0 20px; border:2px solid #f0c5df; border-radius:24px; background:linear-gradient(110deg,#fff1f7,#f4efff 65%,#effcff); box-shadow:0 8px 20px rgba(134,101,156,.10);}
    .quest-title {display:flex; justify-content:space-between; gap:12px; color:#654b78; font-weight:800; margin-bottom:9px;}
    .quest-track {height:18px; position:relative; border-radius:99px; background:#eadff2; overflow:visible; border:1px solid #e3cde1; margin:8px 10px 14px;}
    .quest-fill {height:100%; border-radius:99px; background:linear-gradient(90deg,#f5a6c8,#c1a7f1,#9edbe0);}
    .quest-caption {margin-top:7px; color:#886d91; font-size:13px;}
    .brand-logo {display:flex; align-items:center; gap:10px; padding:10px 12px 16px; margin-bottom:12px; border-bottom:2px dashed #efbdd8; color:#654b78;}
    .brand-mark {width:42px; height:42px; display:flex; align-items:center; justify-content:center; border-radius:15px; background:linear-gradient(135deg,#ffb7d4,#c5b2f5); font-size:25px; box-shadow:0 5px 12px rgba(140,105,150,.15);}
    .brand-name {font-weight:900; font-size:20px; line-height:1.05;}
    .brand-subtitle {font-size:11px; color:#987a9d; margin-top:3px;}
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
    /* The mobile menu is a native Streamlit popover.  It is deliberately
       anchored with a keyed CSS class so the launcher remains tappable even
       when the main content is long.  The tertiary style plus these rules
       removes the default outline/border without removing the button itself. */
    .st-key-mobile_nav_popover {position:fixed !important; top:8px; left:8px; z-index:100000 !important; width:52px; pointer-events:auto !important;}
    .st-key-mobile_nav_popover > button,
    .st-key-mobile_nav_popover > button:hover,
    .st-key-mobile_nav_popover > button:focus,
    .st-key-mobile_nav_popover > button:focus-visible,
    .st-key-mobile_nav_popover > button:active,
    .st-key-mobile_nav_popover > div:first-child > button,
    .st-key-mobile_nav_popover > div:first-child > button:hover,
    .st-key-mobile_nav_popover > div:first-child > button:focus,
    .st-key-mobile_nav_popover > div:first-child > button:focus-visible,
    .st-key-mobile_nav_popover > div:first-child > button:active,
    .st-key-mobile_nav_popover [data-testid="stPopoverButton"] > button,
    .st-key-mobile_nav_popover [data-testid="stPopoverButton"] > button:hover,
    .st-key-mobile_nav_popover [data-testid="stPopoverButton"] > button:focus,
    .st-key-mobile_nav_popover [data-testid="stPopoverButton"] > button:focus-visible,
    .st-key-mobile_nav_popover [data-testid="stPopoverButton"] > button:active {border:0 !important; outline:none !important; box-shadow:none !important; background:transparent !important; color:#684d7b !important; font-size:27px; padding:2px 6px; min-height:42px; -webkit-tap-highlight-color:transparent;}
    .st-key-mobile_nav_popover > button p,
    .st-key-mobile_nav_popover > div:first-child > button p,
    .st-key-mobile_nav_popover [data-testid="stPopoverButton"] > button p {font-size:27px !important; line-height:1 !important; margin:0 !important;}
    @media (min-width: 701px) { .st-key-mobile_nav_popover {display:none !important;} }
    @media (max-width: 700px) {
        .block-container {padding: 4rem .75rem 2rem;}
        /* Streamlit's desktop sidebar is hidden on a phone; the fixed
           launcher above is the single, tappable mobile navigation control. */
        [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display:none !important;}
        .st-key-mobile_nav_popover {display:block !important; visibility:visible !important; opacity:1 !important;}
        .st-key-mobile_nav_popover button {pointer-events:auto !important; touch-action:manipulation;}
        h1 {font-size: 1.8rem;}
        h2 {font-size: 1.35rem;}
        .chibi-hero {padding:18px; gap:12px;}
        .chibi-face {font-size:30px;}
        .chibi-title {font-size:19px;}
        .stButton button {min-height: 2.8rem; width: 100%;}
        div[role="dialog"] {width:98vw !important; max-width:98vw !important; height:96vh !important; max-height:96vh !important; top:2vh !important; border-radius:24px !important;}
        div[role="dialog"] .block-container, section[data-testid="stDialog"] .block-container, [data-testid="stDialog"] .block-container {padding:1rem .85rem 1.5rem !important;}
        .bts-stage {min-height:0; padding:15px 13px 18px; overflow:visible;}
        .bts-stage-heading {font-size:16px;}
        .bts-stage-subtitle {padding-right:22px;}
        .bts-scene, .bts-scene-left, .bts-scene-right {position:relative !important; left:auto !important; right:auto !important; top:auto !important; bottom:auto !important; width:100%; max-width:none; margin:19px 0 0;}
        .bts-scene-right {flex-direction:row-reverse;}
        .bts-character {width:92px; height:150px;}
        .bts-speech {min-width:0; max-width:none; flex:1 1 auto; padding:10px 12px;}
        .bts-quote {font-size:14px;}
        .streak-card {align-items:flex-start; flex-direction:column; gap:6px;}
        .streak-meta {text-align:left;}
    }
</style>
""", unsafe_allow_html=True)


NAV_PAGES = ("Dashboard", "Review", "Lessons", "Progress", "Crystal Shop")


def render_mobile_navigation():
    """Render a working native mobile navigation popover.

    A popover owns the open/close interaction in Streamlit itself, so the
    launcher is not dependent on a CSS click handler or manually maintained
    panel state.  Selecting a page happens before the sidebar radio widget is
    created on the rerun, avoiding the old widget-instantiation failure.
    """
    with st.popover("☰", key="mobile_nav_popover", type="tertiary", help="Open navigation"):
        st.markdown("### Navigate")
        current = st.session_state.get("nav", "Dashboard")
        for page_name in NAV_PAGES:
            label = ("● " if page_name == current else "○ ") + page_name
            if st.button(label, key=f"mobile_nav_{page_name}", use_container_width=True):
                # This function runs before the sidebar radio is instantiated.
                # Setting its value here is safe; the next run opens the
                # selected page on both phone and desktop browsers.
                st.session_state["nav"] = page_name
                st.rerun()


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
    review_columns = {row[1] for row in c.execute("PRAGMA table_info(reviews)").fetchall()}
    if "retired" not in review_columns:
        c.execute("ALTER TABLE reviews ADD COLUMN retired INTEGER NOT NULL DEFAULT 0")
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


def sync_seed_card_content():
    """Refresh checked-in card text while preserving every review record.

    The first version of the deployed app imported a card only once.  That
    meant a corrected HTSK example stayed wrong in an existing database.  We
    now match cards by their stable lesson/order position and update only the
    prompt, translation, answer, hint, and explanation.  Level, dates,
    mistakes, active state, and answer history are intentionally untouched.
    """
    c = db()
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
                "SELECT id FROM cards WHERE lesson_id=? ORDER BY id",
                (lesson["id"],),
            ).fetchall()
            for index, card in enumerate(lesson_data.get("cards", [])):
                values = (
                    card["prompt"],
                    card["translation"],
                    card["answer"],
                    card["hint"],
                    card["explanation"],
                )
                if index < len(existing):
                    c.execute(
                        "UPDATE reviews SET retired=0 WHERE card_id=?",
                        (existing[index]["id"],),
                    )
                    c.execute(
                        """UPDATE cards
                           SET prompt=?, translation=?, answer=?, hint=?, explanation=?
                           WHERE id=?""",
                        (*values, existing[index]["id"]),
                    )
                else:
                    card_id = c.execute(
                        """INSERT INTO cards
                           (lesson_id,prompt,translation,answer,hint,explanation)
                           VALUES(?,?,?,?,?,?)""",
                        (lesson["id"], *values),
                    ).lastrowid
                    c.execute(
                        "INSERT OR IGNORE INTO reviews(card_id) VALUES(?)",
                        (card_id,),
                    )
            # A repaired seed can intentionally contain fewer cards than an
            # older deployed database.  Keep the old review/history rows for
            # progress safety, but take obsolete cards out of the active deck
            # so stale examples cannot reappear after an app update.
            if len(existing) > len(lesson_data.get("cards", [])):
                obsolete_ids = [row["id"] for row in existing[len(lesson_data.get("cards", [])):]]
                placeholders = ",".join("?" for _ in obsolete_ids)
                c.execute(
                    f"UPDATE reviews SET active=0, retired=1 WHERE card_id IN ({placeholders})",
                    obsolete_ids,
                )
    c.commit()
    c.close()


def sync_htsk_metadata():
    """Keep lesson labels, links and availability aligned with the HTSK manifest."""
    c = db()
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
    choice = choices[date.today().toordinal() % len(choices)]
    return choice, level, highest


def bts_character_image(member, fallback_icon):
    """Return an inline image for a bundled chibi, with a safe fallback."""
    filename = BTS_ASSET_FILES.get(member)
    asset_path = BTS_ASSET_DIR / filename if filename else None
    if asset_path and asset_path.is_file():
        encoded = base64.b64encode(asset_path.read_bytes()).decode("ascii")
        return f'<img class="bts-character" src="data:image/png;base64,{encoded}" alt="{escape(member)} chibi">'
    return f'<div class="bts-character-fallback" role="img" aria-label="{escape(member)}">{escape(fallback_icon)}</div>'


def render_bts_motivation():
    """Render two full-body chibis in date-rotated positions with speech bubbles."""
    message, level, highest = daily_bts_message()
    ko_member = escape(message["ko_member"])
    en_member = escape(message["en_member"])
    ko_icon = escape(message["ko_icon"])
    en_icon = escape(message["en_icon"])
    ko_quote = escape(message["ko"])
    en_quote = escape(message["en"])
    progress_label = f"up to Lesson {highest}" if highest else "ready for Lesson 26"
    ko_style, en_style = BTS_SCENE_LAYOUTS[date.today().toordinal() % len(BTS_SCENE_LAYOUTS)]
    ko_image = bts_character_image(message["ko_member"], message["ko_icon"])
    en_image = bts_character_image(message["en_member"], message["en_icon"])
    st.markdown(
        f'''<div class="bts-stage">
            <div class="bts-stage-heading"><span>💜 Daily BTS chibi cheer</span><span>Level {level}</span></div>
            <div class="bts-stage-subtitle">Two friends for today · your Korean level: {progress_label}</div>
            <div class="bts-scene bts-scene-left" style="{ko_style}">
                {ko_image}
                <div class="bts-speech">
                    <div class="bts-speaker">{ko_member}<span class="bts-label">encouragement in Korean</span></div>
                    <div class="bts-quote">{ko_quote}</div>
                </div>
            </div>
            <div class="bts-scene bts-scene-right" style="{en_style}">
                {en_image}
                <div class="bts-speech">
                    <div class="bts-speaker">{en_member}<span class="bts-label">English translation</span></div>
                    <div class="bts-quote">{en_quote}</div>
                </div>
            </div>
        </div>''',
        unsafe_allow_html=True,
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
    expected = {str(number) for number in range(26, 209)}
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
    """Check the answer when the user presses Enter in the text field."""
    card = one("SELECT answer FROM cards WHERE id=?", (card_id,))
    user_answer = st.session_state.get(answer_key, "")
    st.session_state["checked"] = answer_is_correct(user_answer, card["answer"])


def focus_answer_field():
    """Put the cursor in the Review answer box after a card is rendered."""
    components.html("""
    <script>
    (function() {
        const parentWindow = window.parent;
        function focusAnswer() {
            const input = parentWindow.document.querySelector(
                'input[aria-label="Your answer"]'
            );
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


def enable_review_hotkeys(card_id, nonce):
    """Keyboard grading: 1 Again, 2 Hard, 3/Enter/Space Good, 4 Easy."""
    components.html(f"""
    <script>
    (function() {{
        const win = window.parent;
        const marker = 'korean_srs_review_keys_{card_id}_{nonce}';
        if (win[marker]) return;
        win[marker] = true;
        function reviewRoot() {{
            return win.document.querySelector('div[role="dialog"]') || win.document;
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
        UPDATE reviews SET active=1, level=0, next_review=?, last_review=NULL
        WHERE card_id IN (SELECT id FROM cards WHERE lesson_id=?)
          AND active=0 AND retired=0
    """, (today(), lesson_id))
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
    if result == "good":
        level = min(8, level + 1)
    elif result == "easy":
        level = min(8, level + 2)
    elif result == "hard":
        level = max(0, level)
    elif result == "again":
        level = max(0, level - 2)
        mistakes += 1
    interval = SRS_DAYS[level]
    if result == "hard":
        interval = max(1, SRS_DAYS[max(1, level)] // 2)
    if result == "again":
        interval = 0
    next_date = (date.today() + timedelta(days=interval)).isoformat()
    now = datetime.now().isoformat(timespec="seconds")
    c = db()
    c.execute("""
        UPDATE reviews SET level=?, next_review=?, last_review=?, mistakes=?, active=1
        WHERE card_id=?
    """, (level, next_date, now, mistakes, card_id))
    c.execute("INSERT INTO answer_history(card_id,result,created_at) VALUES(?,?,?)", (card_id, result, now))
    c.commit()
    c.close()
    award_crystals(f"card_review:{card_id}:{now}", {"good": 3, "easy": 5, "hard": 1, "again": 0}[result])
    record_activity("review")
    st.session_state["review_completed"] = st.session_state.get("review_completed", 0) + 1
    st.session_state.pop("checked", None)
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
               reviews.level, reviews.next_review, reviews.last_review
        FROM cards
        JOIN lessons ON lessons.id=cards.lesson_id
        JOIN reviews ON reviews.card_id=cards.id
        WHERE reviews.active=1
          AND reviews.retired=0
          AND (reviews.next_review<=? OR reviews.last_review IS NULL)
          AND lessons.unit>=? AND lessons.status IN ('available','studying')
        ORDER BY
            CASE WHEN substr(reviews.last_review,1,10)=? THEN 1 ELSE 0 END,
            COALESCE(reviews.last_review,'0000-01-01T00:00:00'),
            reviews.next_review, cards.id
        LIMIT 1
    """, (today(), int(setting("start_unit", "2")), today()))


def open_review():
    """Start a fresh Review visit from a dashboard or lesson action."""
    for key in ("review_total", "review_completed", "checked"):
        st.session_state.pop(key, None)
    st.session_state["go_review"] = True
    st.rerun()


def render_card(card):
    st.markdown(f"### {card['prompt']}")
    st.write(f"**Translation:** {card['translation']}")
    with st.expander("Show hint"):
        st.write(card["hint"])
    answer_key = f"answer_{card['id']}_{st.session_state.get('review_nonce', 0)}"
    revealed_key = f"revealed_answer_{card['id']}"
    answer = st.text_input(
        "Your answer",
        key=answer_key,
        on_change=check_answer,
        args=(card["id"], answer_key),
        placeholder="Type the missing Korean form and press Enter",
    )
    if "checked" not in st.session_state:
        focus_answer_field()
    if st.button("Check answer", use_container_width=True):
        st.session_state["checked"] = answer_is_correct(answer, card["answer"])
    if "checked" in st.session_state:
        if st.session_state["checked"]:
            st.success("Correct!")
            st.caption("Choose how well you remembered it:")
            a, b, c, d = st.columns(4)
            if a.button("Again", key=f"again_{card['id']}", use_container_width=True):
                grade(card["id"], "again"); st.rerun()
            if b.button("Hard", key=f"hard_{card['id']}", use_container_width=True):
                grade(card["id"], "hard"); st.rerun()
            if c.button("Good", key=f"good_{card['id']}", use_container_width=True):
                grade(card["id"], "good"); st.rerun()
            if d.button("Easy", key=f"easy_{card['id']}", use_container_width=True):
                grade(card["id"], "easy"); st.rerun()
            st.caption("Keyboard: 1 Again · 2 Hard · 3 / Enter / Space Good · 4 Easy")
            enable_review_hotkeys(card["id"], st.session_state.get("review_nonce", 0))
        else:
            st.error("Not quite.")
            if not st.session_state.get(revealed_key):
                if st.button("Show correct answer", key=f"reveal_{card['id']}", use_container_width=True):
                    st.session_state[revealed_key] = True
                    st.rerun()
            if st.session_state.get(revealed_key):
                st.info(f"Correct answer: {card['answer']}")
                st.write(card["explanation"])
                if st.button("Again", key=f"again_wrong_{card['id']}", use_container_width=True):
                    grade(card["id"], "again"); st.rerun()


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
        f'''<div class="lesson-guide-copy"><div class="lesson-section-title">Meaning</div><div>{guide_text(guide['meaning'])}</div></div>''',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''<div class="lesson-guide-copy"><div class="lesson-section-title">When to use it</div><div>{guide_text(guide['usage'])}</div></div>''',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'''<div class="lesson-guide-copy"><div class="lesson-section-title">How to build it</div><div>{guide_text(guide['building'])}</div></div>''',
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
                f'''<div class="lesson-example"><div><b>{index}.</b> {display_example}</div><div style="margin-top:7px;color:#987a9d;font-size:14px">Translation: {display_translation}</div></div>''',
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
    face = active_item("face")
    design = active_item("design")
    character_id = setting("active_character", "")
    character = one("SELECT * FROM shop_items WHERE id=?", (character_id,)) if character_id else None
    mascot = character["icon"] if character else face["icon"]
    design_colors = {
        "design_sakura": ("#ffdceb", "#ffeef7", "#fff8fc"),
        "design_lavender": ("#e9e0ff", "#f2edff", "#f8f5ff"),
        "design_peach": ("#ffe0c2", "#fff0df", "#fff8ef"),
        "design_mint": ("#d6f4e9", "#effff8", "#f8fffc"),
        "design_sky": ("#d7efff", "#effaff", "#f8fdff"),
        "design_night": ("#d9d8f5", "#eeeefe", "#f8f7ff"),
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
    due = one("SELECT COUNT(*) AS n FROM reviews JOIN cards ON cards.id=reviews.card_id JOIN lessons ON lessons.id=cards.lesson_id WHERE reviews.active=1 AND reviews.retired=0 AND (reviews.next_review<=? OR reviews.last_review IS NULL) AND lessons.unit>=? AND lessons.status IN ('available','studying')", (today(), int(setting("start_unit", "2"))))["n"]
    active = one("SELECT COUNT(*) AS n FROM reviews WHERE active=1 AND retired=0")["n"]
    mastered = one("SELECT COUNT(*) AS n FROM reviews WHERE active=1 AND retired=0 AND level>=8")["n"]
    a, b, c = st.columns(3)
    a.metric("Due reviews", due)
    b.metric("Active cards", active)
    c.metric("Mastered cards", mastered)
    st.markdown(f"<div class='cute-note'>💎 <b>{crystals()}</b> crystals · collect more in reviews and daily lessons</div>", unsafe_allow_html=True)
    st.info("Your starting point is Unit 2. Units 0–1 are treated as completed.")
    current_streak = streak_info()
    streak_status = "Your flame is lit today — keep it glowing!" if current_streak["active_today"] else "Study today to keep the flame glowing."
    st.markdown(
        f'''<div class="streak-card"><div class="streak-main"><span class="streak-fire">🔥</span><span>{current_streak['current']} day streak</span></div><div class="streak-meta"><b>Best: {current_streak['best']} days</b><br>{streak_status}</div></div>''',
        unsafe_allow_html=True,
    )
    render_bts_motivation()

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
        # Keep the tracker visually inside the rail even at 0%/100%; it is
        # intentionally inset instead of sitting at the very start of a line.
        quest_position = 7 + (86 * quest_ratio)
        st.markdown(f'''<div class="quest-card">
            <div class="quest-title"><span>Today's learning quest</span><span>{completed} / {len(todays)}</span></div>
            <div class="quest-track"><div class="quest-fill" style="width:{quest_ratio * 100:.1f}%"></div><div class="progress-mascot" style="left:{quest_position:.1f}%">{quest_icon}</div></div>
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
        remaining = one("SELECT COUNT(*) AS n FROM reviews JOIN cards ON cards.id=reviews.card_id JOIN lessons ON lessons.id=cards.lesson_id WHERE reviews.active=1 AND reviews.retired=0 AND (reviews.next_review<=? OR reviews.last_review IS NULL) AND lessons.unit>=? AND lessons.status IN ('available','studying')", (today(), int(setting("start_unit", "2"))))["n"]
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
    tracker_position = 7 + (86 * progress)
    st.markdown(
        f'''<div class="modal-kicker"><strong>✨ Review</strong><span>{character_icon} cozy Korean garden · {completed} / {total} today</span></div>''',
        unsafe_allow_html=True,
    )
    st.markdown(f'''<div class="review-frame" style="border-color:{frame_border};background:{frame_bg}"><div style="font-size:18px;font-weight:800;color:#654b78">{character_icon} Welcome to your cozy review corner!</div><div style="color:#886d91;margin-top:4px">Small steps, pretty progress, big Korean wins ✨</div></div>''', unsafe_allow_html=True)
    st.markdown(f'''<div class="review-progress" style="border-color:{frame_border};background:linear-gradient(110deg,{frame_bg},#f4efff)">
        <div class="review-progress-title"><span>{frame_icon} Today's review quest</span><span>{completed} / {total} cards</span></div>
        <div class="review-progress-track">
            <div class="review-progress-fill" style="width:{progress * 100:.1f}%;background:{tracker_color}"></div>
            <div class="progress-mascot" style="left:{tracker_position:.1f}%;border-color:{tracker_color}">{tracker_icon}</div>
        </div>
        <div style="margin-top:7px;color:#886d91;font-size:14px">Your tracker travels along the bar with you!</div>
    </div>''', unsafe_allow_html=True)
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
        lesson_preview(lesson_id, daily)

    @st.dialog("✨ Review", width="large")
    def review_dialog():
        render_review_contents()
else:
    lesson_dialog = None
    review_dialog = None


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
    lesson_request = None
    for lesson in lessons:
        cards = one("SELECT COUNT(*) AS n FROM cards JOIN reviews ON reviews.card_id=cards.id WHERE cards.lesson_id=? AND reviews.retired=0", (lesson["id"],))["n"]
        active = one("SELECT COUNT(*) AS n FROM cards JOIN reviews ON reviews.card_id=cards.id WHERE cards.lesson_id=? AND reviews.active=1 AND reviews.retired=0", (lesson["id"],))["n"]
        guide = lesson_guide(lesson)
        with st.expander(f"Lesson {lesson['lesson_number']}: {lesson['title']} · {active}/{cards} cards active"):
            if guide.get("available"):
                st.markdown(f"**Grammar point:** `{lesson['pattern']}`")
                st.caption("HTSK guide and separate official examples are inside the Study window · 5 SRS cards")
            else:
                st.warning(guide["source_note"])
                st.caption("This lesson will not enter the new-lesson queue until HTSK publishes its content.")
            st.markdown(f"[Read the full official HTSK explanation ↗]({guide['source_url']})")
            if guide.get("available") and st.button("Study this lesson", key=f"study_{lesson['id']}", use_container_width=True):
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
                        st.markdown(f"<div style='font-size:38px;text-align:center'>{item['icon']}</div>", unsafe_allow_html=True)
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
                            tracker_position = 56
                            st.markdown(
                                f'''<div class="quest-track" style="margin:7px 0 4px"><div class="quest-fill" style="width:55%;background:{TRACKER_COLORS.get(item['id'], '#f5a6c8')}"></div><div class="progress-mascot" style="left:{tracker_position}%">{item['icon']}</div></div>''',
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


init_db()
import_seed_once()
import_extended_seeds()
sync_seed_card_content()
sync_htsk_metadata()
if st.session_state.pop("go_review", False):
    st.session_state["nav"] = "Review"
pending_mobile_page = st.session_state.pop("mobile_nav_target", None)
if pending_mobile_page in NAV_PAGES:
    st.session_state["nav"] = pending_mobile_page
render_mobile_navigation()
st.sidebar.markdown('<div class="brand-logo"><div class="brand-mark">🍡</div><div><div class="brand-name">Mochi Hangul</div><div class="brand-subtitle">Korean grammar SRS</div></div></div>', unsafe_allow_html=True)
page = st.sidebar.radio("Navigate", list(NAV_PAGES), key="nav")
st.sidebar.markdown(f"💎 **{crystals()} crystals**")
st.sidebar.caption("Starting point: Unit 2")
if page == "Dashboard": page_dashboard()
elif page == "Review": render_review_dialog()
elif page == "Lessons": page_lessons()
elif page == "Progress": page_progress()
else: page_shop()
