"""V2 additions for the V41 Mochi Hangul app.

This module is installed by the separate V2 entry point. It leaves V41's
grammar seed, grammar-review code, and SRS tables intact and adds isolated
tables for vocabulary cards and manual mastery markers.
"""
from __future__ import annotations

import json
import hashlib
import re
import random
import uuid
from datetime import datetime, timedelta
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
    namespace["NAV_PAGES"] = tuple(namespace["NAV_PAGES"]) + ("Vocabulary Packs", "Vocabulary Review", "Themed Packs", "Music Packs", "Import Anki Progress")
    # Review queues open from Dashboard; themed vocabulary lives inside Vocabulary Packs.
    namespace["NAV_MENU_PAGES"] = tuple(p for p in namespace["NAV_PAGES"] if p not in {"Review", "Vocabulary Review", "Themed Packs"})
    namespace["SHOP_ITEMS"] = list(namespace["SHOP_ITEMS"]) + EXTRA_SHOP_ITEMS
    namespace["FRAME_STYLES"].update(EXTRA_FRAME_STYLES)
    namespace["TRACKER_COLORS"].update(EXTRA_TRACKER_COLORS)
    namespace["CONTENT_SYNC_VERSION"] = "2026-10-13-v2-topik-user-music"

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
        seed_hash = hashlib.sha256(seed_path.read_bytes()).hexdigest()
        conn = namespace["db"]()
        # V2 vocabulary seeding runs after the legacy schema bootstrap, on its
        # own connection/transaction. The legacy lock has been released by then,
        # so concurrent Streamlit sessions can otherwise update the same pack
        # rows and PostgreSQL may cancel a waiting UPDATE. Reuse the transaction
        # advisory lock to serialize the complete V2 content sync.
        namespace["lock_bootstrap"](conn)
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
            """CREATE TABLE IF NOT EXISTS v2_vocab_daily_selection (
                study_date TEXT NOT NULL, card_id TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(study_date, card_id)
            )""",
            """CREATE TABLE IF NOT EXISTS v2_vocab_daily_settings (
                study_date TEXT PRIMARY KEY, daily_limit INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS manual_mastery (
                item_kind TEXT NOT NULL, item_id TEXT NOT NULL,
                mastered INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
                PRIMARY KEY(item_kind, item_id)
            )""",
            """CREATE TABLE IF NOT EXISTS v2_content_meta (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            )""",
        ):
            conn.execute(statement)
        synced = conn.execute("SELECT value FROM v2_content_meta WHERE key='seed_hash'").fetchone()
        if synced and synced["value"] == seed_hash:
            conn.commit()
            conn.close()
            return
        # A previous version could have completed all row writes and then
        # stalled only on its cleanup DELETE before recording this marker.
        # Recognize that already-complete state with two indexed counts and
        # avoid rewriting thousands of unchanged cards.
        built_pack_count = conn.execute(
            "SELECT COUNT(*) AS n FROM v2_vocab_packs WHERE pack_type <> 'music_custom'"
        ).fetchone()["n"]
        built_card_count = conn.execute(
            """SELECT COUNT(*) AS n FROM v2_vocab_cards c
               JOIN v2_vocab_packs p ON p.id=c.pack_id
               WHERE p.pack_type <> 'music_custom'"""
        ).fetchone()["n"]
        if int(built_pack_count or 0) == len(data["packs"]) and int(built_card_count or 0) == len(data["cards"]):
            conn.execute("INSERT INTO v2_content_meta(key,value) VALUES('seed_hash',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (seed_hash,))
            conn.commit()
            conn.close()
            return
        # Only built-in content is synchronized here. User-created music packs
        # are stored with pack_type=music_custom and must survive every update.
        # Do not delete rows during startup.  On Postgres, a cleanup query
        # over a large vocabulary table can wait on another browser session
        # and make Streamlit show a blank page with QueryCanceled.  Seed rows
        # below are upserted by id; user-created music packs and existing
        # progress remain safe, and obsolete rows are harmless until an
        # explicit maintenance action is added.
        # Existing seed packs and cards are insert-only at startup. Rewriting
        # content rows can block on another active Supabase session and cause
        # QueryCanceled before Streamlit renders. Existing user progress is
        # stored separately and remains untouched.
        is_postgres = namespace["is_postgres_connection"](conn)

        def insert_ignore_many(sqlite_sql, postgres_sql, rows):
            if not rows:
                return
            if is_postgres:
                # One batched INSERT per table avoids thousands of network
                # round-trips before Streamlit can render its first page.
                from psycopg2.extras import execute_values
                cursor = conn.raw.cursor()
                try:
                    execute_values(cursor, postgres_sql, rows, page_size=500)
                finally:
                    cursor.close()
                conn.last_used = __import__("time").monotonic()
            else:
                conn.executemany(sqlite_sql, rows)

        pack_rows = [
            (pack["id"], pack["title"], pack["level"], pack["topic"], pack["pack_type"], pack["description"],
             pack["source_label"], pack["source_url"], pack.get("artist", ""), pack.get("song", ""), pack.get("catalog_url", ""))
            for pack in data["packs"]
        ]
        insert_ignore_many(
            "INSERT OR IGNORE INTO v2_vocab_packs(id,title,level,topic,pack_type,description,source_label,source_url,artist,song,catalog_url) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            "INSERT INTO v2_vocab_packs(id,title,level,topic,pack_type,description,source_label,source_url,artist,song,catalog_url) VALUES %s ON CONFLICT DO NOTHING",
            pack_rows,
        )

        card_rows = [
            (card["id"], card["pack_id"], card["card_type"], card["target"], card["part_of_speech"], card["target_translation"],
             card["prompt"], card["source_sentence"], card["translation"], card["answer"], card["base_form"],
             card["answer_form"], card.get("explanation", ""), card["source_label"], card["source_url"],
             card.get("artist", ""), card.get("song", ""))
            for card in data["cards"]
        ]
        insert_ignore_many(
            "INSERT OR IGNORE INTO v2_vocab_cards(id,pack_id,card_type,target,part_of_speech,target_translation,prompt,source_sentence,translation,answer,base_form,answer_form,explanation,source_label,source_url,artist,song) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            "INSERT INTO v2_vocab_cards(id,pack_id,card_type,target,part_of_speech,target_translation,prompt,source_sentence,translation,answer,base_form,answer_form,explanation,source_label,source_url,artist,song) VALUES %s ON CONFLICT DO NOTHING",
            card_rows,
        )
        progress_rows = [(card["id"],) for card in data["cards"]]
        insert_ignore_many(
            "INSERT OR IGNORE INTO v2_vocab_progress(card_id) VALUES(?)",
            "INSERT INTO v2_vocab_progress(card_id) VALUES %s ON CONFLICT DO NOTHING",
            progress_rows,
        )
        conn.execute("INSERT INTO v2_content_meta(key,value) VALUES('seed_hash',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (seed_hash,))
        conn.commit()
        conn.close()

    namespace["init_db"] = init_db_v2

    def set_mastery(kind, item_id, value):
        conn = namespace["db"]()
        now = datetime.now().isoformat(timespec="seconds")
        # One atomic write instead of INSERT + UPDATE for every click.
        conn.execute("""INSERT INTO manual_mastery(item_kind,item_id,mastered,updated_at)
            VALUES(?,?,?,?) ON CONFLICT(item_kind,item_id)
            DO UPDATE SET mastered=excluded.mastered,updated_at=excluded.updated_at""",
            (kind, str(item_id), int(value), now))
        conn.commit()
        conn.close()
        st.session_state.pop("_content_query_cache", None)

    def is_mastered(kind, item_id):
        row = v2_one("SELECT mastered FROM manual_mastery WHERE item_kind=? AND item_id=?", (kind, str(item_id)))
        return bool(row and row["mastered"])

    def _mastery_click(kind, item_id, legacy_id=None):
        """Persist the clicked value before the fragment renders again."""
        current = is_mastered(kind, item_id)
        if legacy_id and is_mastered(kind, legacy_id):
            current = True
        set_mastery(kind, item_id, not current)
        if legacy_id and is_mastered(kind, legacy_id):
            set_mastery(kind, legacy_id, False)
        # Display the committed result even if a read replica/cache is delayed.
        st.session_state[f"_mastery_value:{kind}:{item_id}"] = not current

    @st.fragment
    def mastery_button_fragment(kind, item_id, widget_key, legacy_id=None):
        """Only rerender this button; do not rerun the parent word list."""
        current = is_mastered(kind, item_id)
        if legacy_id and is_mastered(kind, legacy_id):
            current = True
        state_key = f"_mastery_value:{kind}:{item_id}"
        if state_key in st.session_state:
            current = st.session_state[state_key]
        st.button("Undo mastered" if current else "Mark mastered",
                  key=widget_key, use_container_width=True,
                  on_click=_mastery_click, args=(kind, item_id, legacy_id))

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

    def page_anki_import():
        from anki_import import render as render_anki_import
        render_anki_import(st, namespace["db"])

    namespace["page_anki_import"] = page_anki_import

    def page_vocabulary_packs(title="Vocabulary Packs", pack_type_filter="topik"):
        st.title(title)
        if title == "Vocabulary Packs" and pack_type_filter == "topik":
            pack_choice = st.selectbox("Pack type", ["TOPIK vocabulary", "Themed vocabulary"], key="v2_pack_type")
            pack_type_filter = "topik" if pack_choice == "TOPIK vocabulary" else "theme"
        caption = "TOPIK vocabulary packs." if pack_type_filter == "topik" else "Themed vocabulary packs, separate from TOPIK vocabulary."
        st.caption(caption)
        packs = v2_rows("SELECT * FROM v2_vocab_packs WHERE pack_type=? ORDER BY level, topic, artist, title", (pack_type_filter,))
        levels = ["All levels"] + sorted({p["level"] for p in packs})
        selected_level = st.selectbox("Level", levels, key=f"v2_pack_level_{pack_type_filter}")
        topics = ["All topics"] + sorted({p["topic"] for p in packs if selected_level == "All levels" or p["level"] == selected_level})
        selected_topic = st.selectbox("Topic / artist", topics, key=f"v2_pack_topic_{pack_type_filter}")
        visible = [p for p in packs if (selected_level == "All levels" or p["level"] == selected_level)
                   and (selected_topic == "All topics" or p["topic"] == selected_topic)]
        pack_counts = {row["pack_id"]: row["n"] for row in v2_rows(
            "SELECT pack_id,COUNT(*) AS n FROM v2_vocab_cards GROUP BY pack_id")}
        mastered_packs = {row["item_id"] for row in v2_rows(
            "SELECT item_id FROM manual_mastery WHERE item_kind='vocab_pack' AND mastered=1")}
        import hashlib
        word_pack_id = st.session_state.get("v2_word_pack")
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
                with action:
                    mastery_button_fragment("vocab_pack", pack["id"], f"v2_master_{pack['id']}")
                with words:
                    is_open = word_pack_id == pack["id"]
                    if st.button("Hide words" if is_open else "Words", key=f"v2_words_{pack['id']}", use_container_width=True):
                        st.session_state["v2_word_pack"] = None if is_open else pack["id"]
                        st.rerun()
                with review:
                    if st.button("Review pack", key=f"v2_review_pack_{pack['id']}", type="primary", use_container_width=True):
                        st.session_state["vocab_review_pack"] = pack["id"]
                        st.session_state["nav"] = "Vocabulary Review"
                        st.session_state["v2_review_select"] = pack["id"]
                        st.session_state.pop("vocab_queue_ids", None)
                        st.session_state.pop("vocab_queue_mode", None)
                        st.rerun()

                # Keep the expanded word list inside its own pack card, not at page bottom.
                def render_words_fragment_topik(active_pack_id, expanded):
                    if expanded:
                        st.markdown("#### Words")
                        word_rows = v2_rows("""SELECT target,part_of_speech,target_translation,base_form
                            FROM v2_vocab_cards WHERE pack_id=?
                            GROUP BY target,part_of_speech,target_translation,base_form
                            ORDER BY target,part_of_speech,target_translation,base_form""", (active_pack_id,))
                        mastered_words = {row["item_id"] for row in v2_rows(
                            "SELECT item_id FROM manual_mastery WHERE item_kind='vocab_word' AND mastered=1")}
                        page_size = 40
                        total_pages = max(1, (len(word_rows) + page_size - 1) // page_size)
                        current_page = st.number_input(
                            "Word page", min_value=1, max_value=total_pages, value=1,
                            step=1, key=f"v2_word_page_{active_pack_id}",
                        ) if total_pages > 1 else 1
                        st.caption(f"{len(word_rows)} words · Page {current_page} of {total_pages}")
                        start = (current_page - 1) * page_size
                        for index, word in enumerate(word_rows[start:start + page_size], start=start):
                            # Disambiguate homographs: identical Korean targets can have different meanings.
                            word_id = f"{active_pack_id}:{word['target']}:{word['part_of_speech']}:{word['target_translation']}:{word['base_form']}"
                            legacy_id = f"{active_pack_id}:{word['target']}"
                            mastered_word = word_id in mastered_words or legacy_id in mastered_words
                            unique_key = hashlib.sha256(f"{active_pack_id}:{index}:{word_id}".encode("utf-8")).hexdigest()[:20]
                            label_col, action_col = st.columns([5, 1.5])
                            with label_col:
                                st.markdown(f"**{word['target']}** · {word['target_translation']} · {word['base_form']}")
                            with action_col:
                                mastery_button_fragment("vocab_word", word_id,
                                                        f"v2_word_master_{unique_key}", legacy_id)
                render_words_fragment_topik(pack["id"], is_open)

    namespace["page_vocabulary_packs"] = page_vocabulary_packs

    def page_themed_packs():
        page_vocabulary_packs("Themed Packs", "theme")

    namespace["page_themed_packs"] = page_themed_packs

    def _music_payload(raw):
        """Validate one uploaded user music-pack JSON payload."""
        payload = json.loads(raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw)
        packs = payload.get("packs") if isinstance(payload, dict) else None
        cards = payload.get("cards") if isinstance(payload, dict) else None
        if packs is None and isinstance(payload, dict) and payload.get("pack"):
            packs, cards = [payload["pack"]], payload.get("cards", [])
        if not isinstance(packs, list) or not isinstance(cards, list) or not packs:
            raise ValueError("The file must contain 'packs' and 'cards' arrays (or one 'pack' and 'cards').")
        pack_ids = set()
        clean_packs = []
        for pack in packs:
            if not isinstance(pack, dict):
                raise ValueError("Each pack must be an object.")
            pack_id = str(pack.get("id", "")).strip()
            if not pack_id:
                raise ValueError("Every music pack needs a unique id.")
            pack_id = pack_id if pack_id.startswith("custom_music_") else f"custom_music_{pack_id}"
            if pack_id in pack_ids:
                raise ValueError(f"Duplicate pack id: {pack_id}")
            pack_ids.add(pack_id)
            clean_packs.append({
                "id": pack_id,
                "title": str(pack.get("title", "")).strip(),
                "level": str(pack.get("level", "Themed")).strip(),
                "topic": str(pack.get("topic", "Music")).strip(),
                "description": str(pack.get("description", "User-added music vocabulary")).strip(),
                "source_label": str(pack.get("source_label", "User-added music pack")).strip(),
                "source_url": str(pack.get("source_url", "")).strip(),
                "artist": str(pack.get("artist", "")).strip(),
                "song": str(pack.get("song", "")).strip(),
                "catalog_url": str(pack.get("catalog_url", "")).strip(),
            })
            if not clean_packs[-1]["title"]:
                raise ValueError(f"Pack {pack_id} needs a title.")
        clean_cards = []
        card_ids = set()
        for card in cards:
            if not isinstance(card, dict):
                raise ValueError("Each card must be an object.")
            card_id = str(card.get("id", "")).strip()
            pack_id = str(card.get("pack_id", "")).strip()
            required = ("target", "target_translation", "prompt", "translation", "answer", "base_form", "answer_form")
            if not card_id or not pack_id or any(not str(card.get(key, "")).strip() for key in required):
                raise ValueError(f"Card {card_id or '<missing id>'} is missing a required field.")
            pack_id = pack_id if pack_id.startswith("custom_music_") else f"custom_music_{pack_id}"
            if pack_id not in pack_ids:
                raise ValueError(f"Card {card_id} refers to unknown pack {pack_id}.")
            if card_id in card_ids:
                raise ValueError(f"Duplicate card id: {card_id}")
            card_ids.add(card_id)
            clean_cards.append({
                "id": card_id if card_id.startswith("custom_music_") else f"custom_music_{card_id}",
                "pack_id": pack_id,
                "card_type": str(card.get("card_type", "lyric")).strip(),
                "target": str(card["target"]).strip(),
                "part_of_speech": str(card.get("part_of_speech", "word")).strip(),
                "target_translation": str(card["target_translation"]).strip(),
                "prompt": str(card["prompt"]).strip(),
                "source_sentence": str(card.get("source_sentence", card["prompt"])).strip(),
                "translation": str(card["translation"]).strip(),
                "answer": str(card["answer"]).strip(),
                "base_form": str(card["base_form"]).strip(),
                "answer_form": str(card["answer_form"]).strip(),
                "explanation": str(card.get("explanation", "")).strip(),
                "source_label": str(card.get("source_label", "User-added music pack")).strip(),
                "source_url": str(card.get("source_url", "")).strip(),
                "artist": str(card.get("artist", "")).strip(),
                "song": str(card.get("song", "")).strip(),
            })
        if not clean_cards:
            raise ValueError("At least one card is required.")
        return clean_packs, clean_cards

    def import_music_payload(raw):
        packs, cards = _music_payload(raw)
        conn = namespace["db"]()
        try:
            for pack in packs:
                conn.execute("""INSERT INTO v2_vocab_packs
                    (id,title,level,topic,pack_type,description,source_label,source_url,artist,song,catalog_url)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET title=excluded.title,level=excluded.level,topic=excluded.topic,
                    pack_type='music_custom',description=excluded.description,source_label=excluded.source_label,
                    source_url=excluded.source_url,artist=excluded.artist,song=excluded.song,catalog_url=excluded.catalog_url""",
                    (pack["id"], pack["title"], pack["level"], pack["topic"], "music_custom", pack["description"],
                     pack["source_label"], pack["source_url"], pack["artist"], pack["song"], pack["catalog_url"]))
            for card in cards:
                conn.execute("""INSERT INTO v2_vocab_cards
                    (id,pack_id,card_type,target,part_of_speech,target_translation,prompt,source_sentence,translation,answer,
                     base_form,answer_form,explanation,source_label,source_url,artist,song)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET pack_id=excluded.pack_id,card_type=excluded.card_type,target=excluded.target,
                    part_of_speech=excluded.part_of_speech,target_translation=excluded.target_translation,prompt=excluded.prompt,
                    source_sentence=excluded.source_sentence,translation=excluded.translation,answer=excluded.answer,
                    base_form=excluded.base_form,answer_form=excluded.answer_form,explanation=excluded.explanation,
                    source_label=excluded.source_label,source_url=excluded.source_url,artist=excluded.artist,song=excluded.song""",
                    tuple(card[key] for key in ("id","pack_id","card_type","target","part_of_speech","target_translation","prompt",
                                                "source_sentence","translation","answer","base_form","answer_form","explanation",
                                                "source_label","source_url","artist","song")))
                conn.execute("INSERT OR IGNORE INTO v2_vocab_progress(card_id) VALUES(?)", (card["id"],))
            conn.commit()
        finally:
            conn.close()

    def open_vocabulary_pack_review(pack_id, set_selector=False):
        # Streamlit forbids modifying a widget key after its radio was rendered.
        # Button callbacks run before the next script pass, so navigation is safe.
        st.session_state["vocab_review_pack"] = pack_id
        if set_selector:
            st.session_state["v2_review_select"] = pack_id
        st.session_state.pop("vocab_queue_ids", None)
        st.session_state["nav"] = "Vocabulary Review"

    def add_song_word(song, word):
        """Enroll exactly two cards for one selected word; never reset progress."""
        pack_id = song["id"]
        lemma = word["lemma"]
        idx = word["line"]
        source = song["lines"][idx]["ko"]
        surface = word["surface"]
        if surface not in source:
            raise ValueError("Selected word is not present in its lyric line")
        prompt_lyric = source.replace(surface, "___", 1)
        example = word["example"]
        # The independent sentence uses a natural inflected form, not the dictionary form.
        independent_surface = next((token for token in re.findall(r"[가-힣]+", example)
            if token.startswith(lemma[:-1]) and len(lemma) > 2), None)
        if not independent_surface:
            # For nouns the example can have an attached particle.
            independent_surface = next((token for token in re.findall(r"[가-힣]+", example)
                if token.startswith(lemma)), None)
        if not independent_surface:
            independent_surface = re.findall(r"[가-힣]+", example)[0]
        independent_prompt = example.replace(independent_surface, "___", 1)
        conn = namespace["db"]()
        try:
            conn.execute("""INSERT OR IGNORE INTO v2_vocab_packs
                (id,title,level,topic,pack_type,description,source_label,source_url,artist,song,catalog_url)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(pack_id,song["title"],"Music","Songs","music_custom",
                "Vocabulary selected from your supplied lyrics","User-supplied lyrics","",song["artist"],song["title"],""))
            for kind,prompt,full,translation,answer in (
                ("lyric",prompt_lyric,source,song["lines"][idx].get("en") or word["gloss"],surface),
                ("independent",independent_prompt,example,word["example_en"],independent_surface)):
                cid = pack_id + ":" + hashlib.sha1((lemma+"|"+kind).encode()).hexdigest()[:16]
                conn.execute("""INSERT OR IGNORE INTO v2_vocab_cards
                    (id,pack_id,card_type,target,part_of_speech,target_translation,prompt,source_sentence,translation,
                    answer,base_form,answer_form,explanation,source_label,source_url,artist,song)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (cid,pack_id,kind,lemma,word["pos"],word["gloss"],prompt,full,translation,
                     answer,lemma,"form used in sentence","","User-supplied lyrics","",song["artist"],song["title"]))
                conn.execute("INSERT OR IGNORE INTO v2_vocab_progress(card_id) VALUES(?)",(cid,))
            conn.commit()
        finally:
            conn.close()

    def page_song_library():
        library_file = Path(__file__).with_name("music_lyrics_library.json")
        if not library_file.exists():
            return
        songs = json.loads(library_file.read_text(encoding="utf-8"))
        st.subheader("Song lyrics & vocabulary")
        st.caption("39 songs with line-by-line English translations. Select a word to inspect it and add two cards to the shared review.")
        requested_song = st.query_params.get("music_song")
        requested_word = st.query_params.get("music_word")
        if requested_song is not None and requested_word is not None:
            try:
                st.session_state["music_selected_word"] = (str(requested_song), int(requested_word))
                requested_artist = next((x["artist"] for x in songs if x["id"] == requested_song), None)
                if requested_artist and st.session_state.get("song_artist_filter") not in ("All artists", requested_artist):
                    st.session_state["song_artist_filter"] = requested_artist
            except (ValueError, TypeError):
                st.session_state["music_selected_word"] = None
        else:
            st.session_state["music_selected_word"] = None
        artist = st.selectbox("Artist", ["All artists"] + sorted({x["artist"] for x in songs}), key="song_artist_filter")
        visible_songs = [x for x in songs if artist == "All artists" or x["artist"] == artist]
        chosen = st.selectbox("Song", range(len(visible_songs)),
            format_func=lambda i: visible_songs[i]["artist"] + " · " + visible_songs[i]["title"],
            key="music_song_choice")
        if requested_song and any(x["id"] == requested_song for x in visible_songs):
            chosen = next(i for i,x in enumerate(visible_songs) if x["id"] == requested_song)
        for song in [visible_songs[chosen]]:
            with st.container(border=True):
                if not song["words"]:
                    st.info("This song needs additional manual vocabulary curation.")
                st.markdown("**Lyrics · select a highlighted word to see its meaning and add it to study**")
                # No separate dark vocabulary buttons: vocabulary is linked in the lyrics.
                selected_word = st.session_state.get("music_selected_word")
                for li, line in enumerate(song["lines"]):
                    matches = [(wi, w) for wi, w in enumerate(song["words"]) if w["line"] == li]
                    if matches:
                        # Build an inline text run with actual clickable words using HTML anchors.
                        # Query params preserve the song and identify the selected word.
                        from urllib.parse import quote
                        from html import escape as html_escape
                        raw = line["ko"]
                        hits = []
                        for wi, w in matches:
                            token = w.get("surface", "")
                            pos = raw.find(token)
                            if token and pos >= 0:
                                hits.append((pos, pos + len(token), wi, w))
                        hits.sort(key=lambda x: (x[0], -(x[1]-x[0])))
                        chunks = []; last = 0
                        for start, end, wi, w in hits:
                            if start < last: continue
                            chunks.append(html_escape(raw[last:start]))
                            link = "?music_song=" + quote(song["id"],safe="") + "&music_word=" + str(wi)
                            chunks.append('<a class="mochi-lyric-link" href="' + html_escape(link,quote=True) + '" title="' + html_escape(w["gloss"],quote=True) + '">' + html_escape(raw[start:end]) + '</a>')
                            last = end
                        chunks.append(html_escape(raw[last:]))
                        st.markdown('<div class="mochi-lyric-line">' + ''.join(chunks) + '</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="mochi-lyric-line">' + html_escape(line["ko"]) + '</div>', unsafe_allow_html=True)
                    st.caption(line.get("en") or "Translation unavailable")
                    for wi, w in matches:
                        if selected_word == (song["id"], wi):
                            with st.container(border=True):
                                st.markdown(f"**{w['lemma']}** — {w['gloss']} ({w['pos']})")
                                st.write("Independent example:", w["example"])
                                st.caption(w["example_en"])
                                if st.button("Add to study · 2 cards",key=f"lyric_enroll_{song['id']}_{li}_{wi}"):
                                    add_song_word(song,w)
                                    st.success("Added to shared Vocabulary Review (or already enrolled).")
        st.caption("All enrolled music cards share the same SRS and Vocabulary Review as TOPIK and themed packs.")

    def page_music_packs():
        st.title("Music Packs")
        page_song_library()
        st.caption("Your own music vocabulary lives here, separately from TOPIK vocabulary.")
        template_path = Path(__file__).with_name("music_pack_template.json")
        if template_path.exists():
            st.download_button("Download music-pack template", template_path.read_bytes(), file_name="music_pack_template.json", mime="application/json", key="v2_music_template")
        uploaded = st.file_uploader("Add your music pack (.json)", type=["json"], key="v2_music_upload")
        if uploaded is not None and st.button("Import music pack", type="primary", key="v2_music_import"):
            try:
                import_music_payload(uploaded.getvalue())
                st.success("Music pack imported. It will not be removed by future app updates.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not import this pack: {exc}")
        packs = v2_rows("SELECT * FROM v2_vocab_packs WHERE pack_type IN ('music','music_custom') ORDER BY artist,title,level,topic")
        if not packs:
            st.info("No user music packs yet. Download the template, fill it in, and import it here.")
            return
        counts = {row["pack_id"]: row["n"] for row in v2_rows("SELECT pack_id,COUNT(*) AS n FROM v2_vocab_cards GROUP BY pack_id")}
        mastered = {row["item_id"] for row in v2_rows("SELECT item_id FROM manual_mastery WHERE item_kind='vocab_pack' AND mastered=1")}
        for pack in packs:
            with st.container(border=True):
                left, action, words, review = st.columns([5, 1.6, 1.2, 1.7])
                with left:
                    st.markdown(f"### {pack['title']}")
                    st.caption(f"{pack['artist'] or 'Music'} · {pack['level']} · {counts.get(pack['id'], 0)} cards · {'Mastered' if pack['id'] in mastered else 'In progress'}")
                    st.write(pack["description"])
                    if pack["source_url"]:
                        st.markdown(f"[Source ↗]({pack['source_url']})")
                with action:
                    done = pack["id"] in mastered
                    mastery_button_fragment("vocab_pack", pack["id"], f"v2_music_master_{pack['id']}")
                with words:
                    is_open = st.session_state.get("v2_music_words_pack") == pack["id"]
                    if st.button("Hide words" if is_open else "Words", key=f"v2_music_words_{pack['id']}", use_container_width=True):
                        st.session_state["v2_music_words_pack"] = None if is_open else pack["id"]
                        st.rerun()
                with review:
                    st.button("Review pack", key=f"v2_music_review_{pack['id']}", type="primary", use_container_width=True,
                              on_click=open_vocabulary_pack_review, args=(pack["id"],))
                def render_words_fragment_music(active_pack_id, expanded):
                    if expanded:
                        st.markdown("#### Words in this music pack")
                        music_words = v2_rows("""SELECT target,part_of_speech,target_translation,base_form,
                            COUNT(*) AS card_count FROM v2_vocab_cards WHERE pack_id=?
                            GROUP BY target,part_of_speech,target_translation,base_form
                            ORDER BY target,part_of_speech,target_translation,base_form""", (active_pack_id,))
                        mastered_words = {r["item_id"] for r in v2_rows(
                            "SELECT item_id FROM manual_mastery WHERE item_kind='vocab_word' AND mastered=1")}
                        import hashlib
                        for index, word in enumerate(music_words):
                            word_id = f"{active_pack_id}:{word['target']}:{word['part_of_speech']}:{word['target_translation']}:{word['base_form']}"
                            legacy_id = f"{active_pack_id}:{word['target']}"
                            done_word = word_id in mastered_words or legacy_id in mastered_words
                            label_col, master_col = st.columns([5, 1.5])
                            with label_col:
                                st.markdown(f"**{word['target']}** · {word['target_translation']} · {word['base_form']} ({word['part_of_speech']})")
                            with master_col:
                                word_key = hashlib.sha256(f"music:{active_pack_id}:{index}:{word_id}".encode()).hexdigest()[:20]
                                mastery_button_fragment("vocab_word", word_id,
                                                        f"v2_music_word_{word_key}", legacy_id)
                render_words_fragment_music(pack["id"], is_open)

    namespace["page_music_packs"] = page_music_packs

    def highlight_translation(translation, target):
        safe = escape(str(translation or "")).replace("\n", "<br>")
        if not target:
            return safe
        pattern = re.compile(re.escape(str(target)), re.IGNORECASE)
        return pattern.sub(lambda match: f'<span class="vocab-target">{match.group(0)}</span>', safe, count=1)

    def current_vocab_card(card_id):
        cached = st.session_state.get("_vocab_review_card_cache", {}).get(str(card_id))
        if cached:
            return cached
        card = v2_one("""SELECT c.*,p.title AS pack_title,p.level,p.topic,p.catalog_url
            FROM v2_vocab_cards c JOIN v2_vocab_packs p ON p.id=c.pack_id WHERE c.id=?""", (card_id,))
        if card:
            st.session_state.setdefault("_vocab_review_card_cache", {})[str(card_id)] = dict(card)
        return card

    def grade_vocab(card_id, input_key):
        conn = namespace["db"]()
        try:
            card = conn.execute("""SELECT c.*,p.title AS pack_title,p.level,p.topic,p.catalog_url,
                    v.level AS progress_level
                FROM v2_vocab_cards c
                JOIN v2_vocab_packs p ON p.id=c.pack_id
                LEFT JOIN v2_vocab_progress v ON v.card_id=c.id
                WHERE c.id=?""", (card_id,)).fetchone()
            if not card:
                return
            user_answer = namespace["normalize"](st.session_state.get(input_key, ""))
            correct_answer = namespace["normalize"](card["answer"])
            correct = user_answer.casefold() == correct_answer.casefold()
            old_level = max(0, int(card["progress_level"] or 0))
            new_level = min(namespace["SRS_MAX_LEVEL"], old_level + 1) if correct else max(0, old_level - 1)
            now_dt = datetime.now()
            interval = namespace["BUNPRO_INTERVALS"].get(old_level if correct else new_level)
            due = now_dt + interval if interval else datetime(2999, 1, 1)
            now = now_dt.isoformat(timespec="seconds")
            conn.execute("""UPDATE v2_vocab_progress SET level=?,next_review=?,last_review=?,
                reviews=reviews+1,mastered=? WHERE card_id=?""", (new_level, due.isoformat(timespec="seconds"), now, int(new_level >= namespace["SRS_MAX_LEVEL"]), card_id))
            conn.commit()
            st.session_state.setdefault("_vocab_review_card_cache", {})[str(card_id)] = dict(card)
        finally:
            conn.close()
        st.session_state["vocab_result"] = {"card_id": card_id, "user_answer": user_answer,
                                             "correct": correct, "correct_answer": card["answer"]}

    namespace["grade_vocab"] = grade_vocab

    def assign_vocab_study_day(conn, card_id):
        """Place each selected new word in the earliest day with room under its daily cap."""
        first_day = datetime.now().date()
        existing = conn.execute("SELECT study_date FROM v2_vocab_daily_selection WHERE card_id=? ORDER BY study_date LIMIT 1", (card_id,)).fetchone()
        if existing:
            return existing["study_date"]
        for offset in range(3660):
            day = (first_day + timedelta(days=offset)).isoformat()
            setting = conn.execute("SELECT daily_limit FROM v2_vocab_daily_settings WHERE study_date=?", (day,)).fetchone()
            cap = int(setting["daily_limit"]) if setting else 20
            count = conn.execute("SELECT COUNT(*) AS n FROM v2_vocab_daily_selection WHERE study_date=?", (day,)).fetchone()["n"]
            if int(count) < cap:
                conn.execute("INSERT INTO v2_vocab_daily_selection(study_date,card_id,created_at) VALUES(?,?,?)", (day,card_id,datetime.now().isoformat(timespec="seconds")))
                return day
        raise RuntimeError("Could not find an open study day for this vocabulary card.")

    def start_vocab_queue(pack_id="__all__", pack_type_filter=None, mode="mixed", new_limit=20):
        now = datetime.now().isoformat(timespec="seconds")
        day = datetime.now().date().isoformat()
        # Query the full overdue backlog; missed days remain due until reviewed.
        new_limit = max(1, min(20, int(new_limit)))
        due = v2_rows("""SELECT c.id FROM v2_vocab_cards c JOIN v2_vocab_progress v ON v.card_id=c.id
            WHERE COALESCE(v.reviews,0)>0 AND v.next_review<=?
            AND NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_pack' AND m.item_id=c.pack_id AND m.mastered=1)
            AND NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_word' AND m.item_id=(c.pack_id || ':' || c.target) AND m.mastered=1)
            ORDER BY v.next_review, c.id""", (now,))
        selected = v2_rows("""SELECT c.id FROM v2_vocab_daily_selection d
            JOIN v2_vocab_cards c ON c.id=d.card_id JOIN v2_vocab_progress v ON v.card_id=c.id
            WHERE d.study_date<=? AND COALESCE(v.reviews,0)=0
            AND NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_pack' AND m.item_id=c.pack_id AND m.mastered=1)
            AND NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_word' AND m.item_id=(c.pack_id || ':' || c.target) AND m.mastered=1)
            ORDER BY d.study_date, c.id LIMIT ?""", (day, new_limit))
        ids = list(dict.fromkeys([r["id"] for r in due] + [r["id"] for r in selected]))
        random.shuffle(ids)
        st.session_state["vocab_queue_ids"] = ids
        st.session_state["vocab_queue_index"] = 0
        st.session_state["vocab_queue_pack"] = "__all__"
        st.session_state["vocab_queue_mode"] = "mixed"
        st.session_state["vocab_queue_version"] = 6
        st.session_state.pop("vocab_result", None)
        st.session_state["_vocab_review_card_cache"] = {}

    namespace["start_vocab_queue"] = start_vocab_queue

    def hide_manual_vocab_form():
        st.session_state["v2_manual_card_open"] = False

    def render_vocab_progress(current, total):
        total = max(0, int(total))
        current = max(0, min(int(current), total))
        ratio = 1.0 if total == 0 else current / total
        label = "No cards" if total == 0 else f"{current} / {total} cards"
        st.markdown(f'''<div class="review-progress vocab-progress">
            <div class="review-progress-title"><span>🌸 Vocabulary journey</span><span>{label}</span></div>
            <div class="review-progress-track"><div class="review-progress-fill" style="width:{ratio * 100:.2f}%"></div>
                <div class="progress-mascot" style="left:clamp(0px,calc({ratio * 100:.2f}% - 19px),calc(100% - 38px))">🍡</div></div>
        </div>''', unsafe_allow_html=True)

    def install_vocab_continue_enter():
        namespace["components"].html('''
        <script>
        (function() {
            const win = window.parent;
            if (win.__mochiVocabContinueHandler) {
                win.document.removeEventListener('keydown', win.__mochiVocabContinueHandler, true);
            }
            win.__mochiVocabContinueHandler = function(event) {
                if (event.key !== 'Enter' && event.key !== ' ') return;
                const button = Array.from(win.document.querySelectorAll('button')).find((item) =>
                    item.getClientRects().length && (item.innerText || item.textContent || '').trim().startsWith('Continue')
                );
                if (!button) return;
                event.preventDefault();
                event.stopImmediatePropagation();
                button.click();
            };
            win.document.addEventListener('keydown', win.__mochiVocabContinueHandler, true);
        })();
        </script>
        ''', height=1)

    def close_vocab_review():
        st.session_state["nav"] = "Dashboard"
        st.session_state["nav_menu"] = "Dashboard"
        for key in ("vocab_queue_ids", "vocab_queue_index", "vocab_queue_mode", "vocab_queue_pack", "vocab_result"):
            st.session_state.pop(key, None)
        st.rerun(scope="app")

    def render_vocab_review_session():
        st.markdown('<div class="review-page-heading">🌸 Vocabulary Review</div>', unsafe_allow_html=True)
        close_col, _ = st.columns([1, 8])
        if close_col.button("← Dashboard", key="v2_vocab_close_session"):
            close_vocab_review()
        queue = st.session_state.get("vocab_queue_ids", [])
        index = int(st.session_state.get("vocab_queue_index", 0))
        result = st.session_state.get("vocab_result")
        if result:
            card = current_vocab_card(result["card_id"])
            if not card:
                st.session_state.pop("vocab_result", None)
                st.rerun(scope="fragment")
            answered = escape(str(card["prompt"])).replace("___", f'<span class="answer-result-value">{escape(result["user_answer"])}</span>', 1)
            st.markdown(f'<div class="review-question-paper"><div class="review-prompt">{answered}</div><div class="review-translation">{highlight_translation(card["translation"], card["target_translation"])}</div></div>', unsafe_allow_html=True)
            if result["correct"]:
                st.markdown('<div class="review-result-chip is-correct">✓ Correct</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="review-result-chip is-retry">Correct answer: <b>{escape(result["correct_answer"])}</b></div>', unsafe_allow_html=True)
            if st.button("Continue →", key="v2_vocab_continue", type="primary", use_container_width=True):
                st.session_state["vocab_queue_index"] = index + 1
                st.session_state.pop("vocab_result", None)
                st.rerun(scope="fragment")
            install_vocab_continue_enter()
            return
        if "vocab_queue_ids" not in st.session_state:
            st.info("Start the mixed deck when you are ready.")
            return
        if not queue or index >= len(queue):
            render_vocab_progress(len(queue), len(queue))
            st.markdown('<div class="review-result-chip is-correct">✨ Vocabulary review complete</div>', unsafe_allow_html=True)
            if st.button("← Dashboard", key="v2_vocab_done_dashboard", type="primary", use_container_width=True):
                close_vocab_review()
            return
        card_id = queue[index]
        card = current_vocab_card(card_id)
        if not card:
            st.session_state["vocab_queue_index"] = index + 1
            st.rerun()
        render_vocab_progress(index + 1, len(queue))
        slot_id = f"v2_vocab_slot_{card_id}"
        marker_id = f"v2_vocab_marker_{card_id}"
        label = f"Answer for card {card_id}"
        key = f"v2_vocab_answer_{card_id}"
        korean = escape(str(card["prompt"])).replace("___", f'<span class="inline-answer-slot" id="{slot_id}"></span>', 1)
        translation = highlight_translation(card["translation"], card["target_translation"])
        answer_form = card["answer_form"]
        if "해요체" in answer_form:
            answer_form = "Use polite conversational speech (해요체; typically -아요/-어요)."
        elif "해체" in answer_form:
            answer_form = "Use casual/plain speech (해체; omit 요 and use the requested plain ending)."
        elif "합니다체" in answer_form or "하십시오체" in answer_form:
            answer_form = "Use formal polite speech (하십시오체; typically -습니다/-ㅂ니다)."
        st.markdown(f'<div class="review-question-paper"><div class="review-prompt">{korean}</div><div class="review-translation">{translation}</div><div class="answer-form-note">Required answer form: {escape(answer_form)}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="v2-source-note">{escape(card["pack_title"])} · {escape(card["card_type"].title())} card</div>', unsafe_allow_html=True)
        with st.expander("Show the word in its base form"):
            st.write(card["base_form"])
        with st.form(key=f"v2_vocab_form_{card_id}", clear_on_submit=False):
            st.markdown(f'<span id="{marker_id}" class="answer-widget-marker"></span>', unsafe_allow_html=True)
            st.text_input(label, key=key, placeholder="...", label_visibility="collapsed")
            st.form_submit_button("Check answer", on_click=grade_vocab, args=(card_id, key))
        namespace["mount_inline_answer"](slot_id, marker_id, label)
        namespace["focus_answer_field"]()



    def page_vocabulary_review(title="Vocabulary Review", pack_type_filter=None):
        if st.session_state.get("vocab_queue_version") != 6:
            st.session_state.pop("vocab_queue_ids", None)
            st.session_state.pop("vocab_queue_index", None)
            st.session_state.pop("vocab_queue_pack", None)
            st.session_state.pop("vocab_queue_mode", None)
            st.session_state["vocab_queue_version"] = 6
        if "vocab_queue_ids" in st.session_state:
            render_vocab_review_session()
            return
        st.markdown(f'<div class="review-page-heading">🌸 {escape(title)}</div>', unsafe_allow_html=True)
        close_col, _ = st.columns([1, 8])
        if close_col.button("← Dashboard", key="v2_vocab_close_setup"):
            close_vocab_review()
        st.caption("The deck combines due reviews with your selected new words.")
        today_key = datetime.now().date().isoformat()
        selected_today = v2_one("SELECT COUNT(*) AS n FROM v2_vocab_daily_selection WHERE study_date=?", (today_key,))["n"]
        selected_tomorrow = v2_one("SELECT COUNT(*) AS n FROM v2_vocab_daily_selection WHERE study_date=?", ((datetime.now().date()+timedelta(days=1)).isoformat(),))["n"]
        saved_limit = v2_one("SELECT daily_limit FROM v2_vocab_daily_settings WHERE study_date=?", (today_key,))
        today_limit = int(saved_limit["daily_limit"]) if saved_limit else 20
        today_limit = int(st.number_input("New words to study today", min_value=1, max_value=20, value=today_limit, step=1, key="v2_vocab_daily_limit_number"))
        if not saved_limit or int(saved_limit["daily_limit"]) != today_limit:
            conn=namespace["db"]()
            try:
                conn.execute("INSERT INTO v2_vocab_daily_settings(study_date,daily_limit) VALUES(?,?) ON CONFLICT(study_date) DO UPDATE SET daily_limit=excluded.daily_limit", (today_key,today_limit))
                conn.commit()
            finally: conn.close()
        st.write(f"Scheduled: **{selected_today}/{today_limit} today** · **{selected_tomorrow}/20 tomorrow**")
        if "v2_vocab_search_query" not in st.session_state:
            st.session_state["v2_vocab_search_query"] = st.session_state.get("v2_vocab_search", "")
        with st.form("v2_vocab_search_form", clear_on_submit=False):
            st.text_input("Find a word in your vocabulary", key="v2_vocab_search_input", placeholder="Type Korean or English")
            search_submitted = st.form_submit_button("Search")
        if search_submitted:
            st.session_state["v2_vocab_search_query"] = st.session_state.get("v2_vocab_search_input", "").strip()
        query = st.session_state.get("v2_vocab_search_query", "")
        if query.strip():
            st.caption("Search results from your vocabulary cards")
            matches = v2_rows("""SELECT c.id,c.target,c.target_translation,c.part_of_speech,p.title,v.reviews,d.study_date
                FROM v2_vocab_cards c JOIN v2_vocab_packs p ON p.id=c.pack_id
                JOIN v2_vocab_progress v ON v.card_id=c.id
                LEFT JOIN v2_vocab_daily_selection d ON d.card_id=c.id
                WHERE lower(c.target) LIKE lower(?) OR lower(c.target_translation) LIKE lower(?)
                ORDER BY CASE WHEN lower(c.target)=lower(?) THEN 0 WHEN lower(c.target_translation)=lower(?) THEN 1 ELSE 2 END, c.target LIMIT 100""", ("%"+query.strip()+"%", "%"+query.strip()+"%", query.strip(), query.strip()))
            if matches:
                st.caption("Choose the matching meaning/sense:")
                for m in matches:
                    cols = st.columns([5,1])
                    cols[0].write(f"**{m['target']}** — {m['target_translation']} · {m['part_of_speech']} · {m['title']}")
                    if m["study_date"]:
                        cols[1].caption("Scheduled " + m["study_date"])
                    elif int(m["reviews"] or 0)>0:
                        cols[1].caption("Already in SRS")
                    elif cols[1].button("Add", key="v2_add_existing_"+str(m["id"])):
                        conn=namespace["db"]()
                        try:
                            day=assign_vocab_study_day(conn,m["id"])
                            conn.commit()
                        finally: conn.close()
                        st.session_state["v2_vocab_added_flash"] = day
                        st.rerun()
            else:
                st.info("No matching vocabulary found. Create a new card below.")
        if not st.session_state.get("v2_manual_card_open", False):
            manual_label = "Create a new card manually" if query.strip() else "Add a word that is not in the database"
            if st.button(manual_label, key="v2_open_manual_vocab_form", use_container_width=True):
                st.session_state["v2_manual_card_open"] = True
                st.rerun()
        else:
            with st.container(key="v2_manual_vocab_card", border=True):
                title_col, close_col = st.columns([4,1])
                with title_col:
                    st.markdown("#### Create a vocabulary card")
                    st.caption("Changed your mind? Close this form; nothing will be saved.")
                with close_col:
                    st.button("Hide form", key="v2_hide_manual_vocab_form", on_click=hide_manual_vocab_form, use_container_width=True)
                with st.form("v2_manual_vocab_form"):
                    target=st.text_input("Korean word or expression", value=query.strip())
                    meaning=st.text_input("Meaning")
                    pos=st.text_input("Part of speech (optional)", value="word")
                    prompt=st.text_input("Korean example with exactly one ___ blank")
                    answer=st.text_input("Answer to fill the blank")
                    translation=st.text_input("English translation of the example")
                    submitted=st.form_submit_button("Create card and add to study queue")
                if submitted:
                    if not all(x.strip() for x in (target,meaning,prompt,answer,translation)) or prompt.count("___")!=1:
                        st.error("Complete the required fields and use exactly one ___ in the Korean example.")
                    else:
                        conn=namespace["db"]()
                        try:
                            conn.execute("INSERT OR IGNORE INTO v2_vocab_packs(id,title,level,topic,pack_type,description,source_label,source_url) VALUES(?,?,?,?,?,?,?,?)",("user_manual","My vocabulary","Custom","User added","manual","Vocabulary you add yourself","User-created card",""))
                            cid="manual_"+hashlib.sha256((target.strip()+"|"+meaning.strip()+"|"+uuid.uuid4().hex).encode()).hexdigest()[:20]
                            conn.execute("""INSERT INTO v2_vocab_cards(id,pack_id,card_type,target,part_of_speech,target_translation,prompt,source_sentence,translation,answer,base_form,answer_form,explanation,source_label,source_url)
                                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(cid,"user_manual","manual",target.strip(),pos.strip() or "word",meaning.strip(),prompt.strip(),prompt.replace("___",answer.strip(),1),translation.strip(),answer.strip(),target.strip(),"As used in the example","User-created vocabulary card","User-created card",""))
                            conn.execute("INSERT INTO v2_vocab_progress(card_id) VALUES(?)",(cid,))
                            assigned_day=assign_vocab_study_day(conn,cid)
                            conn.commit()
                        finally: conn.close()
                        st.session_state["v2_manual_card_open"] = False
                        st.session_state["v2_vocab_added_flash"] = assigned_day
                        st.rerun()
        added_flash=st.session_state.pop("v2_vocab_added_flash",None)
        if added_flash:
            st.caption("Added to today’s study queue." if added_flash==today_key else f"Added to your study queue for {added_flash}.")
        if st.button("Start today’s mixed vocabulary deck", key="v2_start_vocab_mixed", type="primary", use_container_width=True):
            start_vocab_queue(new_limit=today_limit)
            st.rerun()

    namespace["page_vocabulary_review"] = page_vocabulary_review

    if hasattr(st, "dialog"):
        @st.dialog("🌸 Vocabulary Review", width="large")
        def vocabulary_review_dialog():
            page_vocabulary_review()
    else:
        vocabulary_review_dialog = None

    def render_vocabulary_review_dialog():
        if vocabulary_review_dialog is not None:
            vocabulary_review_dialog()
        else:
            page_vocabulary_review()

    namespace["render_vocabulary_review_dialog"] = render_vocabulary_review_dialog



    def go_vocab_review():
        st.session_state["nav"] = "Vocabulary Review"
        st.session_state.pop("vocab_queue_ids", None)

    namespace["go_vocab_review"] = go_vocab_review

    def page_lessons_v2():
        st.title("Lessons")
        st.caption("Browse grammar lessons by HTSK unit. Manual mastery badges do not alter SRS scheduling.")
        start = int(namespace["setting"]("start_unit", "2"))
        lessons = namespace["rows"]("SELECT * FROM lessons ORDER BY unit,lesson_number")
        grouped = {}
        for lesson in lessons:
            grouped.setdefault(int(lesson["unit"]), []).append(lesson)

        selected_unit = st.session_state.get("v2_lessons_selected_unit")
        if selected_unit is None or int(selected_unit) not in grouped:
            st.session_state["v2_lessons_selected_unit"] = None
            st.markdown("### Choose a unit")
            units = sorted(grouped)
            for offset in range(0, len(units), 2):
                columns = st.columns(2)
                for column, unit in zip(columns, units[offset:offset + 2]):
                    title, lesson_range, status = namespace["UNIT_INFO"].get(unit, ("HTSK Korean", "", "locked"))
                    unit_lessons = grouped[unit]
                    badge = {"completed": "✅ Completed", "current": "🌸 Current unit", "locked": "📘 Unit"}.get(status, "📘 Unit")
                    with column:
                        with st.container(border=True):
                            st.markdown(f"### Unit {unit}: {title}")
                            st.caption(f"{lesson_range} · {len(unit_lessons)} lessons · {badge}")
                            if unit < start:
                                st.caption("Completed before your starting point; lessons remain available to study manually.")
                            if st.button("Open unit", key=f"v2_open_lesson_unit_{unit}", use_container_width=True):
                                st.session_state["v2_lessons_selected_unit"] = unit
                                st.rerun()
            return

        selected_unit = int(selected_unit)
        if st.button("← All units", key="v2_back_to_lesson_units"):
            st.session_state["v2_lessons_selected_unit"] = None
            st.rerun()
        title, lesson_range, status = namespace["UNIT_INFO"].get(selected_unit, ("HTSK Korean", "", "locked"))
        st.subheader(f"Unit {selected_unit}: {title}")
        st.caption(f"{lesson_range} · {len(grouped[selected_unit])} lessons")

        lesson_ids = [int(lesson["id"]) for lesson in grouped[selected_unit]]
        lesson_numbers = [int(lesson["lesson_number"]) for lesson in grouped[selected_unit]]
        stats = namespace["rows"]("""SELECT cards.lesson_id,
            SUM(CASE WHEN reviews.retired=0 THEN 1 ELSE 0 END) AS cards,
            SUM(CASE WHEN reviews.active=1 AND reviews.retired=0 THEN 1 ELSE 0 END) AS active
            FROM cards JOIN reviews ON reviews.card_id=cards.id
            WHERE cards.lesson_id IN (""" + ",".join("?" for _ in lesson_ids) + ") GROUP BY cards.lesson_id", tuple(lesson_ids)) if lesson_ids else []
        by_stats = {row["lesson_id"]: row for row in stats}
        placeholders = ",".join("?" for _ in lesson_numbers)
        mastered_lesson_nums = {int(row["item_id"]) for row in v2_rows(
            f"SELECT item_id FROM manual_mastery WHERE item_kind='grammar_lesson' AND mastered=1 AND item_id IN ({placeholders})",
            tuple(str(number) for number in lesson_numbers),
        )} if lesson_numbers else set()

        requests = []
        for lesson in grouped[selected_unit]:
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
        st.title("Progress")
        grammar_tab, vocab_tab = st.tabs(["📖 Grammar", "🌸 Vocabulary"])
        with grammar_tab:
            grammar_count = v2_one("SELECT COUNT(*) AS n FROM manual_mastery WHERE item_kind='grammar_lesson' AND mastered=1")["n"]
            st.metric("Grammar lessons mastered", grammar_count)
            original_page_progress()
        with vocab_tab:
            counts = v2_one("""SELECT
                (SELECT COUNT(*) FROM manual_mastery WHERE item_kind='vocab_pack' AND mastered=1) AS vocab_count,
                (SELECT COUNT(*) FROM manual_mastery WHERE item_kind='vocab_word' AND mastered=1) AS word_count,
                (SELECT COUNT(*) FROM manual_mastery m JOIN v2_vocab_packs p ON p.id=m.item_id
                    WHERE m.item_kind='vocab_pack' AND m.mastered=1 AND p.pack_type='topik') AS topik_count,
                (SELECT COUNT(*) FROM manual_mastery m JOIN v2_vocab_packs p ON p.id=m.item_id
                    WHERE m.item_kind='vocab_pack' AND m.mastered=1 AND p.pack_type='music') AS music_count""")
            cols = st.columns(4)
            cols[0].metric("Vocabulary packs mastered", counts["vocab_count"])
            cols[1].metric("TOPIK packs mastered", counts["topik_count"])
            cols[2].metric("Music packs mastered", counts["music_count"])
            cols[3].metric("Words mastered", counts["word_count"])
            st.subheader("Vocabulary achievements")
            for earned, title, requirement in [
                (counts["topik_count"] >= 1, "📚 Topic collector", "Master one TOPIK pack."),
                (counts["music_count"] >= 1, "🎧 First encore", "Master one song pack."),
                (counts["music_count"] >= 10, "🎼 Set-list star", "Master ten music packs."),
                (counts["vocab_count"] >= 20, "🍡 Word garden", "Master twenty vocabulary packs."),
                (counts["word_count"] >= 25, "🌼 Word by word", "Master twenty-five vocabulary items."),
            ]:
                st.markdown(f"{'🏅' if earned else '🔒'} **{title}** — {requirement}")

    namespace["page_progress"] = page_progress_v2

    # Add real theme and shop styling before each page is rendered.
    namespace["_render_room_theme_v2"] = render_room_theme

