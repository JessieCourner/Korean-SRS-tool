"""V2 additions for the V41 Mochi Hangul app.

This module is installed by the separate V2 entry point. It leaves V41's
grammar seed, grammar-review code, and SRS tables intact and adds isolated
tables for vocabulary cards and manual mastery markers.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote_plus


DESIGN_THEMES = {
    "design_lavender": ("#fff8fc", "#f6f1ff", "#eefaff", "#ffe9f2", "#eee7ff"),
    "design_sakura": ("#fff7fb", "#ffe7f0", "#fff2df", "#ffe5ee", "#f7e8ff"),
    "design_peach": ("#fff8f3", "#ffe8dc", "#fff1e7", "#ffe7db", "#fff1e8"),
    "design_mint": ("#f4fffb", "#e1f8ef", "#effbff", "#e5f8ef", "#e9f7ff"),
    "design_sky": ("#f5fbff", "#e2f3ff", "#eff5ff", "#e4f4ff", "#ebecff"),
    "design_night": ("#f8f6ff", "#e9e4f7", "#eaf0fa", "#ece6fa", "#e8effa"),
    "design_moonlight": ("#f6f7ff", "#e5eaff", "#f2eaff", "#e5eaff", "#f1e7ff"),
    "design_ocean": ("#f2fcff", "#dff7ff", "#e7f2ff", "#dff7ff", "#e5edff"),
}

EXTRA_SHOP_ITEMS = [
    ("design_moonlight", "Moonlight Library", "design", 620, "🌙", "A cool blue-violet room theme that changes the page and sidebar backgrounds."),
    ("design_ocean", "Seoul Aquarium", "design", 680, "🐠", "A sea-glass palette that changes the page and sidebar backgrounds."),
    ("frame_starlight", "Starlight Frame", "frame", 540, "✨", "A violet star frame for Review cards."),
    ("tracker_leaf", "Growing Leaf Tracker", "tracker", 560, "🍃", "A green progress fill for the Review tracker."),
]

EXTRA_FRAME_STYLES = {
    "frame_starlight": {"border": "#c6b8ef", "background": "#f8f6ff", "accent": "#8e79cb", "decor": "✨", "label": "Starlight"},
}
EXTRA_TRACKER_COLORS = {"tracker_leaf": "#8bc79c"}


def install_v2(namespace):
    """Patch the V41 namespace before its bootstrap and page dispatch run."""
    st = namespace["st"]
    original_init_db = namespace["init_db"]
    original_page_lessons = namespace["page_lessons"]
    original_page_progress = namespace["page_progress"]
    namespace["NAV_PAGES"] = tuple(namespace["NAV_PAGES"]) + ("Vocabulary Packs", "Vocabulary Review")
    namespace["SHOP_ITEMS"] = list(namespace["SHOP_ITEMS"]) + EXTRA_SHOP_ITEMS
    namespace["FRAME_STYLES"].update(EXTRA_FRAME_STYLES)
    namespace["TRACKER_COLORS"].update(EXTRA_TRACKER_COLORS)
    namespace["CONTENT_SYNC_VERSION"] = "2026-10-12-v2-topik-music-packs"

    def v2_rows(sql, params=()):
        conn = namespace["db"]()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def v2_one(sql, params=()):
        conn = namespace["db"]()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()

    def init_db_v2():
        original_init_db()
        seed_path = Path(__file__).with_name("vocabulary_packs_v2.json")
        if not seed_path.exists():
            raise RuntimeError("Missing vocabulary_packs_v2.json beside the V2 app files.")
        data = json.loads(seed_path.read_text(encoding="utf-8"))
        conn = namespace["db"]()
        for statement in (
            """CREATE TABLE IF NOT EXISTS v2_vocab_packs (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, level TEXT NOT NULL,
                topic TEXT NOT NULL, pack_type TEXT NOT NULL, description TEXT NOT NULL,
                source_label TEXT NOT NULL, source_url TEXT NOT NULL,
                artist TEXT NOT NULL DEFAULT '', song TEXT NOT NULL DEFAULT '', catalog_url TEXT NOT NULL DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS v2_vocab_cards (
                id TEXT PRIMARY KEY, pack_id TEXT NOT NULL, card_type TEXT NOT NULL,
                target TEXT NOT NULL, part_of_speech TEXT NOT NULL, target_translation TEXT NOT NULL,
                prompt TEXT NOT NULL, source_sentence TEXT NOT NULL, translation TEXT NOT NULL,
                answer TEXT NOT NULL, base_form TEXT NOT NULL, answer_form TEXT NOT NULL,
                explanation TEXT NOT NULL DEFAULT '', source_label TEXT NOT NULL,
                source_url TEXT NOT NULL, artist TEXT NOT NULL DEFAULT '', song TEXT NOT NULL DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS v2_vocab_progress (
                card_id TEXT PRIMARY KEY, level INTEGER NOT NULL DEFAULT 0,
                next_review TEXT NOT NULL DEFAULT '1900-01-01T00:00:00',
                last_review TEXT, reviews INTEGER NOT NULL DEFAULT 0,
                mastered INTEGER NOT NULL DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS manual_mastery (
                item_kind TEXT NOT NULL, item_id TEXT NOT NULL,
                mastered INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
                PRIMARY KEY(item_kind, item_id)
            )""",
        ):
            conn.execute(statement)
        # The V2 seed is authoritative for vocabulary content. Remove old V2
        # starter packs/cards that are no longer in the seed while leaving all
        # V41 grammar tables and SRS history untouched.
        valid_pack_ids = [pack["id"] for pack in data["packs"]]
        placeholders = ",".join("?" for _ in valid_pack_ids)
        conn.execute(f"DELETE FROM v2_vocab_cards WHERE pack_id NOT IN ({placeholders})", tuple(valid_pack_ids))
        conn.execute(f"DELETE FROM v2_vocab_packs WHERE id NOT IN ({placeholders})", tuple(valid_pack_ids))
        conn.execute("DELETE FROM v2_vocab_progress WHERE card_id NOT IN (SELECT id FROM v2_vocab_cards)")
        for pack in data["packs"]:
            found = conn.execute("SELECT id FROM v2_vocab_packs WHERE id=?", (pack["id"],)).fetchone()
            values = (pack["title"], pack["level"], pack["topic"], pack["pack_type"], pack["description"],
                      pack["source_label"], pack["source_url"], pack.get("artist", ""), pack.get("song", ""), pack.get("catalog_url", ""))
            if found:
                conn.execute("UPDATE v2_vocab_packs SET title=?,level=?,topic=?,pack_type=?,description=?,source_label=?,source_url=?,artist=?,song=?,catalog_url=? WHERE id=?", (*values, pack["id"]))
            else:
                conn.execute("INSERT OR IGNORE INTO v2_vocab_packs(id,title,level,topic,pack_type,description,source_label,source_url,artist,song,catalog_url) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (pack["id"], *values))
        for card in data["cards"]:
            found = conn.execute("SELECT id FROM v2_vocab_cards WHERE id=?", (card["id"],)).fetchone()
            values = (card["pack_id"], card["card_type"], card["target"], card["part_of_speech"], card["target_translation"],
                      card["prompt"], card["source_sentence"], card["translation"], card["answer"], card["base_form"],
                      card["answer_form"], card.get("explanation", ""), card["source_label"], card["source_url"],
                      card.get("artist", ""), card.get("song", ""))
            if found:
                conn.execute("""UPDATE v2_vocab_cards SET pack_id=?,card_type=?,target=?,part_of_speech=?,target_translation=?,
                    prompt=?,source_sentence=?,translation=?,answer=?,base_form=?,answer_form=?,explanation=?,source_label=?,
                    source_url=?,artist=?,song=? WHERE id=?""", (*values, card["id"]))
            else:
                conn.execute("""INSERT OR IGNORE INTO v2_vocab_cards
                    (id,pack_id,card_type,target,part_of_speech,target_translation,prompt,source_sentence,translation,answer,
                     base_form,answer_form,explanation,source_label,source_url,artist,song)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (card["id"], *values))
            conn.execute("INSERT OR IGNORE INTO v2_vocab_progress(card_id) VALUES(?)", (card["id"],))
        conn.commit()
        conn.close()

    namespace["init_db"] = init_db_v2

    def set_mastery(kind, item_id, value):
        conn = namespace["db"]()
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute("INSERT OR IGNORE INTO manual_mastery(item_kind,item_id,mastered,updated_at) VALUES(?,?,?,?)", (kind, str(item_id), int(value), now))
        conn.execute("UPDATE manual_mastery SET mastered=?,updated_at=? WHERE item_kind=? AND item_id=?", (int(value), now, kind, str(item_id)))
        conn.commit()
        conn.close()
        st.session_state.pop("_content_query_cache", None)

    def is_mastered(kind, item_id):
        row = v2_one("SELECT mastered FROM manual_mastery WHERE item_kind=? AND item_id=?", (kind, str(item_id)))
        return bool(row and row["mastered"])

    def render_room_theme():
        chosen = namespace["setting"]("active_design", "design_lavender")
        colors = DESIGN_THEMES.get(chosen, DESIGN_THEMES["design_lavender"])
        c1, c2, c3, s1, s2 = colors
        st.markdown(f"""<style>
          html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background:linear-gradient(135deg,{c1} 0%,{c2} 52%,{c3} 100%) !important;
          }}
          [data-testid="stSidebar"] {{background:linear-gradient(180deg,{s1} 0%,{s2} 100%) !important;}}
          .vocab-target {{color:#d45491;font-weight:850;background:rgba(255,222,239,.72);border-radius:6px;padding:0 .12em;}}
          .v2-pack-card {{border:1px solid #efd8e8;border-left:5px solid #efb8d6;border-radius:0 16px 16px 0;background:rgba(255,255,255,.84);padding:12px 16px;margin:10px 0;color:#514064;}}
          .v2-source-note {{color:#8a6f95;font-size:.88rem;text-align:center;margin:4px 0 14px;}}
        </style>""", unsafe_allow_html=True)

    namespace["render_room_theme"] = render_room_theme

    def page_vocabulary_packs():
        st.title("Vocabulary Packs")
        st.caption("Context cloze cards from beginner and intermediate topic vocabulary, plus one short song excerpt and a second original sentence per track.")
        packs = v2_rows("SELECT * FROM v2_vocab_packs ORDER BY CASE WHEN pack_type='topik' THEN 0 ELSE 1 END, level, topic, artist, title")
        levels = ["All levels"] + sorted({p["level"] for p in packs})
        selected_level = st.selectbox("Level", levels, key="v2_pack_level")
        topics = ["All topics"] + sorted({p["topic"] for p in packs if selected_level == "All levels" or p["level"] == selected_level})
        selected_topic = st.selectbox("Topic / artist", topics, key="v2_pack_topic")
        visible = [p for p in packs if (selected_level == "All levels" or p["level"] == selected_level)
                   and (selected_topic == "All topics" or p["topic"] == selected_topic)]
        pack_counts = {row["pack_id"]: row["n"] for row in v2_rows(
            "SELECT pack_id,COUNT(*) AS n FROM v2_vocab_cards GROUP BY pack_id")}
        mastered_packs = {row["item_id"] for row in v2_rows(
            "SELECT item_id FROM manual_mastery WHERE item_kind='vocab_pack' AND mastered=1")}
        for pack in visible:
            count = pack_counts.get(pack["id"], 0)
            mastered = pack["id"] in mastered_packs
            with st.container(border=True):
                left, action, words, review = st.columns([5, 1.35, 1.0, 1.4])
                with left:
                    st.markdown(f"### {pack['title']}")
                    st.caption(f"{pack['level']} · {pack['topic']} · {count} cards · {'Mastered' if mastered else 'In progress'}")
                    st.write(pack["description"])
                    st.markdown(f"[Vocabulary source ↗]({pack['source_url']})")
                    if pack["pack_type"] == "music":
                        st.markdown(f"[Artist's official catalog ↗]({pack['catalog_url']})")
                with action:
                    label = "Undo mastered" if mastered else "Mark mastered"
                    if st.button(label, key=f"v2_master_{pack['id']}", use_container_width=True):
                        set_mastery("vocab_pack", pack["id"], not mastered)
                        st.rerun()
                with words:
                    if st.button("Words", key=f"v2_words_{pack['id']}", use_container_width=True):
                        st.session_state["v2_word_pack"] = pack["id"]
                        st.rerun()
                with review:
                    if st.button("Review pack", key=f"v2_review_pack_{pack['id']}", type="primary", use_container_width=True):
                        st.session_state["vocab_review_pack"] = pack["id"]
                        st.session_state["nav"] = "Vocabulary Review"
                        st.session_state["v2_review_select"] = pack["id"]
                        st.session_state.pop("vocab_queue_ids", None)
                        st.rerun()

        word_pack_id = st.session_state.get("v2_word_pack")
        selected_pack = next((pack for pack in visible if pack["id"] == word_pack_id), None)
        if selected_pack:
            st.subheader(f"Words · {selected_pack['title']}")
            word_rows = v2_rows("""SELECT target,part_of_speech,target_translation,base_form
                FROM v2_vocab_cards WHERE pack_id=? GROUP BY target,part_of_speech,target_translation,base_form
                ORDER BY target""", (word_pack_id,))
            mastered_words = {row["item_id"] for row in v2_rows(
                "SELECT item_id FROM manual_mastery WHERE item_kind='vocab_word' AND mastered=1")}
            for word in word_rows:
                word_id = f"{word_pack_id}:{word['target']}"
                mastered = word_id in mastered_words
                label_col, action_col = st.columns([5, 1.5])
                with label_col:
                    st.markdown(f"**{word['target']}** · {word['target_translation']} · {word['base_form']}")
                with action_col:
                    if st.button("Undo mastered" if mastered else "Mark mastered",
                                  key=f"v2_word_master_{word_pack_id}_{word['target']}",
                                  use_container_width=True):
                        set_mastery("vocab_word", word_id, not mastered)
                        st.rerun()

    namespace["page_vocabulary_packs"] = page_vocabulary_packs

    def highlight_translation(translation, target):
        safe = escape(str(translation or ""))
        if not target:
            return safe
        pattern = re.compile(re.escape(str(target)), re.IGNORECASE)
        return pattern.sub(lambda match: f'<span class="vocab-target">{match.group(0)}</span>', safe, count=1)

    def current_vocab_card(card_id):
        return v2_one("""SELECT c.*,p.title AS pack_title,p.level,p.topic,p.catalog_url
            FROM v2_vocab_cards c JOIN v2_vocab_packs p ON p.id=c.pack_id WHERE c.id=?""", (card_id,))

    def grade_vocab(card_id, input_key):
        conn = namespace["db"]()
        try:
            card = conn.execute("""SELECT c.*,p.title AS pack_title,p.level,p.topic,p.catalog_url
                FROM v2_vocab_cards c JOIN v2_vocab_packs p ON p.id=c.pack_id WHERE c.id=?""", (card_id,)).fetchone()
            if not card:
                return
            user_answer = namespace["normalize"](st.session_state.get(input_key, ""))
            correct_answer = namespace["normalize"](card["answer"])
            correct = user_answer.casefold() == correct_answer.casefold()
            previous = conn.execute("SELECT * FROM v2_vocab_progress WHERE card_id=?", (card_id,)).fetchone()
            old_level = max(0, int(previous["level"] or 0)) if previous else 0
            new_level = min(namespace["SRS_MAX_LEVEL"], old_level + 1) if correct else max(0, old_level - 1)
            now_dt = datetime.now()
            interval = namespace["BUNPRO_INTERVALS"].get(old_level if correct else new_level)
            due = now_dt + interval if interval else datetime(2999, 1, 1)
            now = now_dt.isoformat(timespec="seconds")
            conn.execute("""UPDATE v2_vocab_progress SET level=?,next_review=?,last_review=?,
                reviews=reviews+1,mastered=? WHERE card_id=?""", (new_level, due.isoformat(timespec="seconds"), now, int(new_level >= namespace["SRS_MAX_LEVEL"]), card_id))
            conn.commit()
        finally:
            conn.close()
        st.session_state["vocab_result"] = {"card_id": card_id, "user_answer": user_answer,
                                             "correct": correct, "correct_answer": card["answer"]}

    namespace["grade_vocab"] = grade_vocab

    def start_vocab_queue(pack_id):
        now = datetime.now().isoformat(timespec="seconds")
        params = [now, pack_id, pack_id, pack_id]
        filters = [
            "v.next_review<=?",
            "(?='__all__' OR c.pack_id=?)",
            "(?<>'__all__' OR NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_pack' AND m.item_id=c.pack_id AND m.mastered=1))",
            "NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_word' AND m.item_id=(c.pack_id || ':' || c.target) AND m.mastered=1)",
        ]
        where = "WHERE " + " AND ".join(filters)
        rows_due = v2_rows(f"""SELECT c.id FROM v2_vocab_cards c JOIN v2_vocab_progress v ON v.card_id=c.id
            {where} ORDER BY v.next_review,c.pack_id,c.id""", tuple(params))
        ids = [row["id"] for row in rows_due]
        st.session_state["vocab_queue_ids"] = ids
        st.session_state["vocab_queue_index"] = 0
        st.session_state["vocab_queue_pack"] = pack_id
        st.session_state.pop("vocab_result", None)

    namespace["start_vocab_queue"] = start_vocab_queue

    def page_vocabulary_review():
        st.title("Vocabulary Review")
        packs = v2_rows("SELECT id,title,pack_type,level,artist,song FROM v2_vocab_packs ORDER BY CASE WHEN pack_type='topik' THEN 0 ELSE 1 END,level,topic,artist,title")
        options = [("__all__", "All vocabulary packs")] + [(p["id"], p["title"]) for p in packs]
        default_pack = st.session_state.get("vocab_review_pack", "__all__")
        default_index = next((i for i, item in enumerate(options) if item[0] == default_pack), 0)
        selected_id = st.selectbox("Choose a pack", [item[0] for item in options], index=default_index,
                                   format_func=lambda item_id: next((name for key, name in options if key == item_id), item_id),
                                   key="v2_review_select")
        if "vocab_queue_ids" not in st.session_state or st.session_state.get("vocab_queue_pack") != selected_id:
            if st.button("Start vocabulary review", key="v2_start_vocab_review", type="primary"):
                start_vocab_queue(selected_id)
                st.rerun()
            st.caption("Choose a pack, then start. New cards are included; each answer is scheduled using the same Bunpro-style interval ladder as grammar review.")
            return
        queue = st.session_state.get("vocab_queue_ids", [])
        index = int(st.session_state.get("vocab_queue_index", 0))
        result = st.session_state.get("vocab_result")
        if result:
            card = current_vocab_card(result["card_id"])
            if not card:
                st.session_state.pop("vocab_result", None)
                st.rerun()
            answered = escape(str(card["prompt"])).replace("___", f'<span class="answer-result-value">{escape(result["user_answer"])}</span>', 1)
            st.markdown(f'<div class="review-question-paper"><div class="review-prompt">{answered}</div><div class="review-translation">{highlight_translation(card["translation"], card["target_translation"])}</div></div>', unsafe_allow_html=True)
            if result["correct"]:
                st.success("Correct — this word is scheduled for its next review.")
            else:
                st.info("The card is complete. Review the full answer before continuing.")
            st.markdown(f'<div class="answer-results">Your answer: <b>{escape(result["user_answer"])}</b><br>Correct answer: <b>{escape(result["correct_answer"])}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="v2-source-note">Base form: {escape(card["base_form"])} · Required form: {escape(card["answer_form"])}</div>', unsafe_allow_html=True)
            st.markdown(f'[Open source ↗]({card["source_url"]})')
            if card["catalog_url"]:
                st.markdown(f"[Artist's official catalog ↗]({card['catalog_url']})")
            word_id = f"{card['pack_id']}:{card['target']}"
            mastered = is_mastered("vocab_word", word_id)
            if st.button("Undo word mastered" if mastered else "Mark this word mastered",
                          key=f"v2_result_master_{card['pack_id']}_{card['target']}"):
                set_mastery("vocab_word", word_id, not mastered)
                st.rerun()
            if st.button("Continue →", key="v2_vocab_continue", type="primary", use_container_width=True):
                st.session_state["vocab_queue_index"] = index + 1
                st.session_state.pop("vocab_result", None)
                st.rerun()
            return
        if not queue or index >= len(queue):
            st.success("This vocabulary review is complete.")
            st.progress(1.0)
            if st.button("Choose another pack", key="v2_vocab_restart"):
                st.session_state.pop("vocab_queue_ids", None)
                st.session_state.pop("vocab_review_pack", None)
                st.rerun()
            return
        card_id = queue[index]
        card = current_vocab_card(card_id)
        if not card:
            st.session_state["vocab_queue_index"] = index + 1
            st.rerun()
        st.progress(index / max(1, len(queue)), text=f"{index} / {len(queue)} cards")
        slot_id = f"v2_vocab_slot_{card_id}"
        marker_id = f"v2_vocab_marker_{card_id}"
        label = f"Answer for card {card_id}"
        key = f"v2_vocab_answer_{card_id}"
        korean = escape(str(card["prompt"])).replace("___", f'<span class="inline-answer-slot" id="{slot_id}"></span>', 1)
        translation = highlight_translation(card["translation"], card["target_translation"])
        st.markdown(f'<div class="review-question-paper"><div class="review-prompt">{korean}</div><div class="review-translation">{translation}</div><div class="answer-form-note">Required answer form: {escape(card["answer_form"])}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="v2-source-note">{escape(card["pack_title"])} · {escape(card["card_type"].title())} card</div>', unsafe_allow_html=True)
        with st.expander("Show the word in its base form"):
            st.write(card["base_form"])
        with st.form(key=f"v2_vocab_form_{card_id}", clear_on_submit=False):
            st.markdown(f'<span id="{marker_id}" class="answer-widget-marker"></span>', unsafe_allow_html=True)
            st.text_input(label, key=key, placeholder="...", label_visibility="collapsed")
            st.form_submit_button("Check answer", on_click=grade_vocab, args=(card_id, key))
        namespace["mount_inline_answer"](slot_id, marker_id, label)
        namespace["focus_answer_field"]()
        if st.button("Restart this queue", key="v2_restart_queue"):
            st.session_state.pop("vocab_queue_ids", None)
            st.session_state.pop("vocab_result", None)
            st.rerun()

    namespace["page_vocabulary_review"] = page_vocabulary_review

    def page_lessons_v2():
        st.title("Lessons")
        st.caption("Browse by HTSK level/unit, lesson topic, and grammar point. Manual mastery badges do not alter SRS scheduling.")
        start = int(namespace["setting"]("start_unit", "2"))
        lessons = namespace["rows"]("SELECT * FROM lessons ORDER BY unit,lesson_number")
        stats = namespace["rows"]("""SELECT cards.lesson_id,
            SUM(CASE WHEN reviews.retired=0 THEN 1 ELSE 0 END) AS cards,
            SUM(CASE WHEN reviews.active=1 AND reviews.retired=0 THEN 1 ELSE 0 END) AS active
            FROM cards JOIN reviews ON reviews.card_id=cards.id GROUP BY cards.lesson_id""")
        by_stats = {row["lesson_id"]: row for row in stats}
        mastered_lesson_nums = {int(row["item_id"]) for row in v2_rows(
            "SELECT item_id FROM manual_mastery WHERE item_kind='grammar_lesson' AND mastered=1")}
        units = sorted({int(row["unit"]) for row in lessons})
        unit_options = ["All levels"] + units
        unit_pick = st.selectbox("HTSK level / unit", unit_options, key="v2_lesson_unit")
        topic_options = ["All topics"] + sorted({row["title"] for row in lessons if unit_pick == "All levels" or int(row["unit"]) == unit_pick})
        topic_pick = st.selectbox("Topic", topic_options, key="v2_lesson_topic")
        filtered = [row for row in lessons if (unit_pick == "All levels" or int(row["unit"]) == unit_pick)
                    and (topic_pick == "All topics" or row["title"] == topic_pick)]
        patterns = ["All grammar points"] + sorted({row["pattern"] for row in filtered})
        pattern_pick = st.selectbox("Grammar point", patterns, key="v2_lesson_pattern")
        filtered = [row for row in filtered if pattern_pick == "All grammar points" or row["pattern"] == pattern_pick]
        grouped = {}
        for lesson in filtered:
            grouped.setdefault(int(lesson["unit"]), []).append(lesson)
        requests = []
        for unit in sorted(grouped):
            title, lesson_range, status = namespace["UNIT_INFO"].get(unit, ("HTSK Korean", "", "locked"))
            badge = {"completed": "✅ Completed", "current": "🌸 Current unit"}.get(status, "📘 Unit")
            with st.expander(f"Level {unit} · Unit {unit}: {title} · {lesson_range} · {badge}", expanded=(unit == start and unit_pick == "All levels")):
                if unit < start:
                    st.caption("Completed before your starting point; lessons remain available to study manually.")
                for lesson in grouped[unit]:
                    lesson_id = int(lesson["id"])
                    lesson_num = int(lesson["lesson_number"])
                    row_stats = by_stats.get(lesson_id, {})
                    active = row_stats.get("active", 0) or 0
                    count = row_stats.get("cards", 0) or 0
                    mastered = lesson_num in mastered_lesson_nums
                    guide = namespace["lesson_guide"](lesson)
                    with st.container(border=True):
                        info, master_col, study_col = st.columns([5, 1.6, 1.1])
                        with info:
                            st.markdown(f"**Lesson {lesson_num}: {lesson['title']}**")
                            st.caption(f"{lesson['pattern']} · {active}/{count} cards active")
                            st.markdown(f"[Open the HTSK lesson ↗]({guide['source_url']})")
                            if not guide.get("available"):
                                st.caption("HTSK has not published this lesson yet.")
                        with master_col:
                            if st.button("✓ Mastered" if mastered else "Mark mastered", key=f"v2_grammar_master_{lesson_num}", use_container_width=True):
                                set_mastery("grammar_lesson", lesson_num, not mastered)
                                st.rerun()
                        with study_col:
                            if guide.get("available") and st.button("Study", key=f"v2_study_{lesson_id}", use_container_width=True):
                                requests.append((lesson_id, False))
        for request in requests:
            namespace["render_lesson_dialog"](*request)

    namespace["page_lessons"] = page_lessons_v2

    def page_progress_v2():
        counts = v2_one("""SELECT
            (SELECT COUNT(*) FROM manual_mastery WHERE item_kind='grammar_lesson' AND mastered=1) AS grammar_count,
            (SELECT COUNT(*) FROM manual_mastery WHERE item_kind='vocab_pack' AND mastered=1) AS vocab_count,
            (SELECT COUNT(*) FROM manual_mastery WHERE item_kind='vocab_word' AND mastered=1) AS word_count,
            (SELECT COUNT(*) FROM manual_mastery m JOIN v2_vocab_packs p ON p.id=m.item_id
                WHERE m.item_kind='vocab_pack' AND m.mastered=1 AND p.pack_type='topik') AS topik_count,
            (SELECT COUNT(*) FROM manual_mastery m JOIN v2_vocab_packs p ON p.id=m.item_id
                WHERE m.item_kind='vocab_pack' AND m.mastered=1 AND p.pack_type='music') AS music_count""")
        grammar_count = counts["grammar_count"]
        vocab_count = counts["vocab_count"]
        word_count = counts["word_count"]
        topik_count = counts["topik_count"]
        music_count = counts["music_count"]
        st.title("Study achievements")
        cols = st.columns(5)
        cols[0].metric("Grammar lessons mastered", grammar_count)
        cols[1].metric("Vocabulary packs mastered", vocab_count)
        cols[2].metric("TOPIK packs mastered", topik_count)
        cols[3].metric("Music packs mastered", music_count)
        cols[4].metric("Words mastered", word_count)
        badges = [
            (grammar_count >= 1, "🌱 First grammar lesson", "Mark one HTSK lesson mastered."),
            (topik_count >= 1, "📚 Topic collector", "Master one TOPIK vocabulary pack."),
            (music_count >= 1, "🎧 First encore", "Master one song vocabulary pack."),
            (music_count >= 10, "🎼 Set-list star", "Master ten music packs."),
            (vocab_count >= 20, "🍡 Word garden", "Master twenty vocabulary packs."),
            (word_count >= 25, "🌼 Word by word", "Mark twenty-five vocabulary items mastered."),
        ]
        st.subheader("Badges")
        for earned, title, requirement in badges:
            st.markdown(f"{'🏅' if earned else '🔒'} **{title}** — {requirement}")
        original_page_progress()

    namespace["page_progress"] = page_progress_v2

    # Add real theme and shop styling before each page is rendered.
    namespace["_render_room_theme_v2"] = render_room_theme

