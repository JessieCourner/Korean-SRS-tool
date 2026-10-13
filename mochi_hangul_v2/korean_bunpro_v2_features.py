"""V2 additions for the V41 Mochi Hangul app.

This module is installed by the separate V2 entry point. It leaves V41's
grammar seed, grammar-review code, and SRS tables intact and adds isolated
tables for vocabulary cards and manual mastery markers.
"""
from __future__ import annotations

import json
import hashlib
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
    namespace["NAV_PAGES"] = tuple(namespace["NAV_PAGES"]) + ("Vocabulary Packs", "Vocabulary Review", "Themed Packs", "Music Packs")
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
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET
                        target=excluded.target,part_of_speech=excluded.part_of_speech,
                        target_translation=excluded.target_translation,prompt=excluded.prompt,
                        source_sentence=excluded.source_sentence,translation=excluded.translation,
                        answer=excluded.answer,base_form=excluded.base_form,
                        answer_form=excluded.answer_form,explanation=excluded.explanation""", (card["id"], *values))
            conn.execute("INSERT OR IGNORE INTO v2_vocab_progress(card_id) VALUES(?)", (card["id"],))
        conn.execute("INSERT INTO v2_content_meta(key,value) VALUES('seed_hash',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (seed_hash,))
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

    def page_vocabulary_packs(title="Vocabulary Packs", pack_type_filter="topik"):
        st.title(title)
        caption = "TOPIK vocabulary packs." if pack_type_filter == "topik" else "Themed vocabulary packs, separate from TOPIK vocabulary."
        st.caption(caption)
        packs = v2_rows("SELECT * FROM v2_vocab_packs WHERE pack_type=? ORDER BY level, topic, artist, title", (pack_type_filter,))
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
                    label = "Undo mastered" if mastered else "Mark mastered"
                    if st.button(label, key=f"v2_master_{pack['id']}", use_container_width=True):
                        set_mastery("vocab_pack", pack["id"], not mastered)
                        st.rerun()
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
                        st.rerun()

                # Keep the expanded word list inside its own pack card, not at page bottom.
                if is_open:
                    st.markdown("#### Words")
                    word_rows = v2_rows("""SELECT target,part_of_speech,target_translation,base_form
                        FROM v2_vocab_cards WHERE pack_id=?
                        GROUP BY target,part_of_speech,target_translation,base_form
                        ORDER BY target,part_of_speech,target_translation,base_form""", (pack["id"],))
                    mastered_words = {row["item_id"] for row in v2_rows(
                        "SELECT item_id FROM manual_mastery WHERE item_kind='vocab_word' AND mastered=1")}
                    for index, word in enumerate(word_rows):
                        # Disambiguate homographs: identical Korean targets can have different meanings.
                        word_id = f"{pack['id']}:{word['target']}:{word['part_of_speech']}:{word['target_translation']}:{word['base_form']}"
                        legacy_id = f"{pack['id']}:{word['target']}"
                        mastered_word = word_id in mastered_words or legacy_id in mastered_words
                        unique_key = hashlib.sha256(f"{pack['id']}:{index}:{word_id}".encode("utf-8")).hexdigest()[:20]
                        label_col, action_col = st.columns([5, 1.5])
                        with label_col:
                            st.markdown(f"**{word['target']}** · {word['target_translation']} · {word['base_form']}")
                        with action_col:
                            if st.button("Undo mastered" if mastered_word else "Mark mastered",
                                         key=f"v2_word_master_{unique_key}", use_container_width=True):
                                set_mastery("vocab_word", word_id, not mastered_word)
                                if legacy_id in mastered_words:
                                    set_mastery("vocab_word", legacy_id, False)
                                st.rerun()

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
                    if st.button("Undo mastered" if done else "Mark mastered", key=f"v2_music_master_{pack['id']}", use_container_width=True):
                        set_mastery("vocab_pack", pack["id"], not done)
                        st.rerun()
                with words:
                    is_open = st.session_state.get("v2_music_words_pack") == pack["id"]
                    if st.button("Hide words" if is_open else "Words", key=f"v2_music_words_{pack['id']}", use_container_width=True):
                        st.session_state["v2_music_words_pack"] = None if is_open else pack["id"]
                        st.rerun()
                with review:
                    st.button("Review pack", key=f"v2_music_review_{pack['id']}", type="primary", use_container_width=True,
                              on_click=open_vocabulary_pack_review, args=(pack["id"],))
                if is_open:
                    st.markdown("#### Words in this music pack")
                    music_words = v2_rows("""SELECT target,part_of_speech,target_translation,base_form,
                        COUNT(*) AS card_count FROM v2_vocab_cards WHERE pack_id=?
                        GROUP BY target,part_of_speech,target_translation,base_form
                        ORDER BY target,part_of_speech,target_translation,base_form""", (pack["id"],))
                    mastered_words = {r["item_id"] for r in v2_rows(
                        "SELECT item_id FROM manual_mastery WHERE item_kind='vocab_word' AND mastered=1")}
                    import hashlib
                    for index, word in enumerate(music_words):
                        word_id = f"{pack['id']}:{word['target']}:{word['part_of_speech']}:{word['target_translation']}:{word['base_form']}"
                        legacy_id = f"{pack['id']}:{word['target']}"
                        done_word = word_id in mastered_words or legacy_id in mastered_words
                        label_col, master_col = st.columns([5, 1.5])
                        with label_col:
                            st.markdown(f"**{word['target']}** · {word['target_translation']} · {word['base_form']} ({word['part_of_speech']})")
                        with master_col:
                            word_key = hashlib.sha256(f"music:{pack['id']}:{index}:{word_id}".encode()).hexdigest()[:20]
                            if st.button("Undo mastered" if done_word else "Mark mastered", key=f"v2_music_word_{word_key}", use_container_width=True):
                                set_mastery("vocab_word", word_id, not done_word)
                                if legacy_id in mastered_words:
                                    set_mastery("vocab_word", legacy_id, False)
                                st.rerun()

    namespace["page_music_packs"] = page_music_packs

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

    def start_vocab_queue(pack_id, pack_type_filter=None):
        now = datetime.now().isoformat(timespec="seconds")
        params = [now]
        filters = ["v.next_review<=?"]
        if pack_id != "__all__":
            filters.append("c.pack_id=?")
            params.append(pack_id)
        elif pack_type_filter:
            filters.append("p.pack_type=?")
            params.append(pack_type_filter)
        filters.extend([
            "NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_pack' AND m.item_id=c.pack_id AND m.mastered=1)",
            "NOT EXISTS (SELECT 1 FROM manual_mastery m WHERE m.item_kind='vocab_word' AND m.item_id=(c.pack_id || ':' || c.target) AND m.mastered=1)",
        ])
        where = "WHERE " + " AND ".join(filters)
        rows_due = v2_rows(f"""SELECT c.id FROM v2_vocab_cards c JOIN v2_vocab_progress v ON v.card_id=c.id
            JOIN v2_vocab_packs p ON p.id=c.pack_id
            {where} ORDER BY v.next_review,c.pack_id,c.id""", tuple(params))
        ids = [row["id"] for row in rows_due]
        st.session_state["vocab_queue_ids"] = ids
        st.session_state["vocab_queue_index"] = 0
        st.session_state["vocab_queue_pack"] = pack_id
        st.session_state.pop("vocab_result", None)

    namespace["start_vocab_queue"] = start_vocab_queue

    def page_vocabulary_review(title="Vocabulary Review", pack_type_filter=None):
        st.title(title)
        if isinstance(pack_type_filter, (tuple, list)):
            pack_where = " WHERE pack_type IN (" + ",".join("?" for _ in pack_type_filter) + ")"
            pack_params = tuple(pack_type_filter)
        elif pack_type_filter is None:
            pack_where = ""
            pack_params = ()
        else:
            pack_where = " WHERE pack_type=?"
            pack_params = (pack_type_filter,) if pack_type_filter else ()
        packs = v2_rows("SELECT id,title,pack_type,level,artist,song FROM v2_vocab_packs" + pack_where + " ORDER BY level,topic,artist,title", pack_params)
        options = [("__all__", "All vocabulary packs")] + [(p["id"], p["title"]) for p in packs]
        default_pack = st.session_state.get("vocab_review_pack", "__all__")
        default_index = next((i for i, item in enumerate(options) if item[0] == default_pack), 0)
        selected_id = st.selectbox("Choose a pack", [item[0] for item in options], index=default_index,
                                   format_func=lambda item_id: next((name for key, name in options if key == item_id), item_id),
                                   key="v2_review_select")
        if "vocab_queue_ids" not in st.session_state or st.session_state.get("vocab_queue_pack") != selected_id:
            if st.button("Start vocabulary review", key="v2_start_vocab_review", type="primary"):
                start_vocab_queue(selected_id, pack_type_filter)
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

