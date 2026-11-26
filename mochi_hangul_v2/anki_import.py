"""Meaning-aware, conservative Anki progress migration for Mochi Hangul V2."""
from __future__ import annotations

import csv
import html
import io
import json
import re
import sqlite3
import unicodedata
import zipfile
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Europe/Budapest")
STOP_WORDS = {
    "a", "an", "the", "to", "be", "is", "am", "are", "was", "were", "did",
    "do", "does", "of", "in", "on", "at", "for", "with", "and", "or", "length",
    "your", "one", "someone", "something", "very",
}
SYNONYMS = {
    frozenset(("grey", "gray")), frozenset(("home", "house")),
    frozenset(("gift", "present")), frozenset(("shop", "store")),
    frozenset(("right", "correct")), frozenset(("match", "game")),
    frozenset(("inexpensive", "cheap")), frozenset(("physician", "doctor")),
    frozenset(("journey", "trip")), frozenset(("begin", "start")),
    frozenset(("lovely", "pretty")), frozenset(("enthusiast", "fan")),
    frozenset(("relax", "rest")), frozenset(("recover", "heal")),
    frozenset(("gray", "grey")), frozenset(("street", "road")),
    frozenset(("teacher", "instructor")), frozenset(("wallet", "purse")),
    frozenset(("player", "athlete")), frozenset(("pen", "ballpen")),
    frozenset(("usa", "america")), frozenset(("kimchi", "cabbage")),
    frozenset(("tangerine", "orange")), frozenset(("older", "elder")),
    frozenset(("tall", "high")), frozenset(("wide", "spacious")),
    frozenset(("available", "free")), frozenset(("necessary", "need")),
    frozenset(("weird", "strange")), frozenset(("morning", "forenoon")),
    frozenset(("watch", "timepiece")), frozenset(("sneaker", "shoe")),
    frozenset(("chalkboard", "blackboard")), frozenset(("similar", "resemble")),
    frozenset(("pain", "suffering")), frozenset(("feeling", "feel")),
    frozenset(("turn", "extinguish")), frozenset(("service", "volunteer")),
    frozenset(("be", "exist")), frozenset(("beautiful", "lovely")),
    frozenset(("appointment", "reservation")), frozenset(("morning", "am")),
    frozenset(("somewhere", "exist")), frozenset(("present", "exist")),
    frozenset(("be", "exist")),
}


def clean(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def korean_norm(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "")
    return re.sub(r"[\s·,;/]", "", value).strip()


def _syllable_parts(ch: str):
    n = ord(ch) - 0xAC00
    if not 0 <= n < 11172:
        return None
    return n // 588, (n % 588) // 28, n % 28


def _syllable(initial: int, vowel: int, final: int = 0) -> str:
    return chr(0xAC00 + initial * 588 + vowel * 28 + final)


def conjugations(lemma: str) -> set[str]:
    """Common polite, informal, past, and modifier forms for Korean headwords."""
    if not lemma.endswith("다") or len(lemma) < 2:
        return set()
    stem = lemma[:-1]
    forms = {stem}
    if lemma.endswith("하다"):
        root = lemma[:-2]
        forms.update({
            root + "해", root + "했", root + "해요", root + "했어요",
            root + "해서", root + "하고", root + "하는", root + "한",
            root + "할", root + "합니다", root + "하세요",
        })
        return forms
    parts = _syllable_parts(stem[-1])
    if not parts:
        return forms
    initial, vowel, final = parts
    rest = stem[:-1]
    # Stem vowel joins the common 아/어 ending. Irregular conjugations that
    # cannot be generated safely are deliberately left for manual review.
    if vowel in (0, 8):  # ㅏ, ㅗ
        ending_vowel = 0
        joined_vowel = {0: 0, 8: 9}.get(vowel, vowel)
    elif vowel == 20:  # ㅣ + 어 -> 여
        ending_vowel, joined_vowel = 4, 6
    elif vowel == 13:  # ㅜ + 어 -> 워
        ending_vowel, joined_vowel = 4, 14
    elif vowel == 18:  # ㅡ contracts to ㅓ/ㅏ
        prior = _syllable_parts(rest[-1]) if rest else None
        ending_vowel = 0 if prior and prior[1] in (0, 8) else 4
        joined_vowel = ending_vowel
        rest = stem[:-1]
        if rest:
            p = _syllable_parts(rest[-1])
            rest = rest[:-1] + _syllable(*p[:2], p[2]) if p else rest
    else:
        ending_vowel, joined_vowel = 4, vowel
    joined = rest + _syllable(initial, joined_vowel, final)
    # For vowels that already carry the ending, retain the ordinary stem too.
    if vowel in (0, 8):
        joined = stem
    past = rest + _syllable(initial, joined_vowel, 20)
    forms.update({
        joined, past, joined + "요", past + "어요", joined + "서",
        stem + "고", stem + "는", stem + "은", stem + "ㄴ",
        stem + "을", stem + "ㄹ", stem + "습니다", stem + "세요",
    })
    # A few highly frequent irregulars with reliable surface forms.
    if lemma == "있다":
        forms.update({"있어", "있어요", "있었어요", "있는", "있을", "있습니다"})
    elif lemma == "없다":
        forms.update({"없어", "없어요", "없었어요", "없는", "없을", "없습니다"})
    elif lemma == "가다":
        forms.update({"가", "가요", "갔", "갔어요", "가서", "가는", "갈"})
    elif lemma == "오다":
        forms.update({"와", "와요", "왔", "왔어요", "와서", "오는", "올"})
    elif lemma == "주다":
        forms.update({"줘", "줘요", "줬", "줬어요", "줘서", "주는", "줄"})
    return forms


def _english_tokens(value: str) -> set[str]:
    value = (value or "").lower()
    value = re.sub(r"\b(?:there\s+are|there\s+is|is\s+there|are\s+there|be\s+present)\b", "exist", value)
    value = re.sub(r"\bsomewhere\b", "exist", value)
    value = re.sub(r"\btae\s*kwon\s*do\b", "taekwondo", value)
    value = re.sub(r"\bspicy\s+cabbage\b", "kimchi", value)
    value = re.sub(r"\bbeef[ -]rib\s+soup\b", "galbitang", value)
    value = re.sub(r"\bjeju\s+orange\b", "tangerine", value)
    value = re.sub(r"\bstudent\s+identification\b", "student id", value)
    value = re.sub(r"\b(?:pian|piano)\b", "piano", value)
    words = re.findall(r"[a-z]+", (value or "").lower())
    out = set()
    for word in words:
        if word in STOP_WORDS:
            continue
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("ing") and len(word) > 5:
            word = word[:-3]
        elif word.endswith("ed") and len(word) > 4:
            word = word[:-2]
        elif word.endswith("s") and len(word) > 3:
            word = word[:-1]
        out.add(word)
    if not out and re.fullmatch(r"\s*(?:to\s+)?(?:be|is|am|are|was|were)\s*", value):
        out.add("be")
    return out


def _canonical_tokens(tokens: set[str]) -> tuple[str, ...]:
    def root(word: str) -> str:
        group = {word}
        changed = True
        while changed:
            changed = False
            for pair in SYNONYMS:
                if group & pair and not pair <= group:
                    group.update(pair)
                    changed = True
        return min(group)
    return tuple(sorted({root(word) for word in tokens}))


def _meaning_signature(source: str, destination: str) -> tuple[float, tuple[str, ...]]:
    best = 0.0
    signature: tuple[str, ...] = ()
    for left in _variants(source):
        a = _english_tokens(left)
        if not a:
            continue
        for right in _variants(destination):
            b = _english_tokens(right)
            if not b:
                continue
            overlap = len(a & b)
            alias_overlap = sum(1 for pair in SYNONYMS if pair & a and pair & b)
            matched = overlap + alias_overlap
            if not matched:
                continue
            coverage = matched / max(1, min(len(a), len(b)))
            score = min(1.0, 0.65 + 0.35 * coverage) if coverage >= 1 else 0.45 + 0.45 * coverage
            if score > best:
                best = score
                signature = _canonical_tokens(b)
    return best, signature


def _variants(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;/]", value or "") if part.strip()] or [value]


def meaning_score(source: str, destination: str) -> float:
    return _meaning_signature(source, destination)[0]


def _local_iso(timestamp: int | float) -> str:
    return datetime.fromtimestamp(timestamp, LOCAL_TZ).replace(tzinfo=None).isoformat(timespec="seconds")


def read_deck(blob: bytes) -> list[dict]:
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        name = next((n for n in ("collection.anki21", "collection.anki2") if n in archive.namelist()), None)
        if not name:
            raise ValueError("Export an Anki .apkg that includes scheduling information.")
        if archive.getinfo(name).file_size > 200_000_000:
            raise ValueError("Collection is too large.")
    # Load the SQLite image via a temporary file, with read-only access.
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".db") as temporary:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            temporary.write(archive.read(name))
            temporary.flush()
            db = sqlite3.connect(f"file:{temporary.name}?mode=ro", uri=True)
            try:
                created = db.execute("SELECT crt FROM col").fetchone()[0]
                rows = db.execute("""
                    SELECT c.id,n.flds,c.type,c.queue,c.due,c.ivl,c.reps,c.lapses,
                           c.odue,c.odid,(SELECT max(id) FROM revlog WHERE cid=c.id)
                    FROM cards c JOIN notes n ON n.id=c.nid ORDER BY c.id
                """).fetchall()
            finally:
                db.close()
    result = []
    for cid, fields, typ, queue, due, interval, reps, lapses, odue, odid, last in rows:
        values = fields.split("\x1f")
        english = clean(values[0]) if values else ""
        raw = clean(values[1]) if len(values) > 1 else ""
        korean = re.split(r"\s*\(", raw, 1)[0].strip()
        if queue == 1:
            due_at = _local_iso(due)
        else:
            due_at = (datetime.fromtimestamp(created, LOCAL_TZ).replace(tzinfo=None) + timedelta(days=due)).isoformat(timespec="seconds")
        level = 1 if typ != 2 else min(10, max(1, sum(interval >= n for n in (1, 2, 4, 8, 12, 24, 48, 96, 176)) + 1))
        result.append({
            "cid": cid, "word": korean, "meaning": english, "interval": int(interval),
            "reviews": int(reps), "lapses": int(lapses), "level": level,
            "due": due_at, "last": _local_iso(last / 1000) if last else None,
            "queue": int(queue), "card_type": int(typ),
            "suspended_or_buried": bool(queue < 0 or odid),
        })
    return result


def _destination_lemma(card: dict) -> str:
    base = card.get("base_form", "").split(" (", 1)[0].strip()
    return base or card.get("target", "").strip()


def plan(source: list[dict], destination_cards: list[dict]):
    exact = defaultdict(list)
    surface = defaultdict(list)
    for card in destination_cards:
        lemma = _destination_lemma(card)
        if not lemma:
            continue
        exact[korean_norm(lemma)].append(card)
        for form in conjugations(lemma):
            surface[korean_norm(form)].append(card)
    mappings, report = [], []
    for item in source:
        word = item.get("word", "").strip()
        key = korean_norm(word)
        candidates = exact.get(key, [])
        match_kind = "dictionary form"
        if not candidates:
            candidates = surface.get(key, [])
            match_kind = "inflected form"
        # Only collapse true repeated references to the same destination ID.
        candidates = list({str(c["id"]): c for c in candidates}.values())
        scored = []
        for candidate in candidates:
            score, gloss_signature = _meaning_signature(item.get("meaning", ""), candidate.get("target_translation", ""))
            if score >= 0.70:
                scored.append((score, gloss_signature, candidate))
        best = max((score for score, _, _ in scored), default=0.0)
        best_cards = [c for score, _, c in scored if score == best]
        sense_keys = {
            (korean_norm(_destination_lemma(c)), c.get("part_of_speech", ""), signature)
            for score, signature, c in scored if score == best
        }
        status, reason, chosen = "", "", []
        if item.get("suspended_or_buried"):
            status, reason = "not imported", "Anki card is suspended or buried."
        elif not candidates:
            status, reason = "missing", "No dictionary-form or safely recognized inflected-form match in Mochi vocabulary."
        elif not scored:
            status, reason = "meaning mismatch", "Korean headword exists, but the English senses do not support the same meaning."
        elif len(sense_keys) > 1:
            status, reason = "ambiguous", "More than one Mochi sense has an equally strong English meaning match."
        else:
            status, reason, chosen = "matched", f"Meaning-compatible {match_kind} match.", best_cards
            mappings.extend((item, c) for c in chosen)
        candidate_text = " | ".join(
            f"{c.get('target','')} [{c.get('target_translation','')}; {c.get('part_of_speech','')}]"
            for c in candidates[:8]
        )
        report.append({
            "anki_id": item.get("cid"), "english": item.get("meaning", ""),
            "korean": word, "status": status, "match_basis": match_kind if candidates else "",
            "candidate_count": len(candidates), "matched_destination_ids": ";".join(c["id"] for c in chosen),
            "candidates": candidate_text, "reason": reason, "interval_days": item.get("interval", 0),
            "due_at": item.get("due", ""), "last_review": item.get("last") or "",
            "reviews": item.get("reviews", 0), "lapses": item.get("lapses", 0),
        })
    # Prevent two distinct Anki schedules from competing for one Mochi card.
    owners = defaultdict(list)
    for item, card in mappings:
        owners[str(card["id"])].append(item)
    conflicts = {card_id for card_id, owners_for_card in owners.items() if len({x["cid"] for x in owners_for_card}) > 1}
    if conflicts:
        conflicting_source_ids = {
            item["cid"] for item, card in mappings if str(card["id"]) in conflicts
        }
        mappings = [(item, card) for item, card in mappings if str(card["id"]) not in conflicts]
        for row in report:
            if row["anki_id"] in conflicting_source_ids:
                row["status"] = "ambiguous"
                row["matched_destination_ids"] = ""
                row["reason"] = "Multiple Anki cards map to the same Mochi card with different schedules; none was selected."
    return mappings, report


def import_progress(conn, mappings):
    """Apply only to untouched cards; scheduling fields are retained verbatim."""
    count = 0
    for source, card in mappings:
        result = conn.execute("""
            UPDATE v2_vocab_progress
            SET level=?, next_review=?, last_review=?, reviews=?, interval_days=?, lapses=?
            WHERE card_id=? AND reviews=0 AND level=0 AND mastered=0
              AND last_review IS NULL AND interval_days=0
        """, (
            source["level"], source["due"], source["last"], source["reviews"],
            source["interval"], source["lapses"], card["id"],
        ))
        count += result.rowcount
    return count


def curated_plan(source, cards, bundle):
    """Use the completed user-reviewed migration plan shipped with this app."""
    by_source = {str(a["cid"]): a for a in source}
    by_card = {str(c["id"]): c for c in cards}
    expected = {str(r["anki_id"]) for r in bundle.get("report_rows", [])}
    if len(expected) != bundle.get("checked_cards") or set(by_source) != expected:
        return None
    mappings = []
    for entry in bundle.get("progress_mappings", []):
        original = by_source.get(str(entry["anki_id"]))
        card = by_card.get(str(entry["destination_id"]))
        if not original or not card:
            continue
        scheduled = dict(original)
        scheduled["level"] = int(entry.get("level", original["level"]))
        scheduled["due"] = entry.get("due") or original["due"]
        scheduled["last"] = entry.get("last") or original["last"]
        scheduled["interval"] = int(entry.get("interval", original["interval"]))
        scheduled["reviews"] = int(entry.get("reviews", original["reviews"]))
        scheduled["lapses"] = int(entry.get("lapses", original["lapses"]))
        mappings.append((scheduled, card))
    report = []
    for row in bundle.get("report_rows", []):
        report.append({
            "anki_id": row.get("anki_id", ""),
            "word": row.get("korean", ""),
            "meaning": row.get("english", ""),
            "status": row.get("final_status", ""),
            "destination_ids": row.get("destination_ids", ""),
            "interval_days": row.get("interval_days", ""),
            "next_review": row.get("next_review", ""),
            "last_review": row.get("last_review", ""),
            "action": row.get("action", ""),
            "review_comment": row.get("review_comment", ""),
        })
    return mappings, report


def render(st, db):
    st.subheader("Import Anki Progress")
    st.caption("All Anki cards are checked by Korean headword, common inflection, and English sense. Ambiguous and unsupported matches are left for review; existing Mochi progress is preserved.")
    upload = st.file_uploader("Anki deck with scheduling (.apkg)", type=["apkg"], key="anki_progress_upload")
    if not upload:
        return
    try:
        source = read_deck(upload.getvalue())
    except Exception as exc:
        st.error(str(exc))
        return
    conn = db()
    try:
        cards = conn.execute("SELECT id,target,target_translation,part_of_speech,base_form FROM v2_vocab_cards").fetchall()
        cards = [dict(row) for row in cards]
    finally:
        conn.close()
    bundle_path = Path(__file__).with_name("anki_migration_bundle.json")
    curated = None
    if bundle_path.is_file():
        try:
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            curated = curated_plan(source, cards, bundle)
        except (OSError, ValueError, KeyError, TypeError):
            curated = None
    mappings, report = curated if curated is not None else plan(source, cards)
    counts = defaultdict(int)
    for row in report:
        counts[row["status"]] += 1
    if curated is not None:
        st.write(f"Reviewed plan: {len(source)} cards checked, {counts['matched']} matched, {counts['new card']} separate Anki cards, {counts['unresolved']} left unresolved, {counts['excluded by user']} excluded by your instruction.")
    else:
        st.write(f"{len(source)} Anki cards checked: {counts['matched']} matched, {counts['ambiguous']} ambiguous, {counts['meaning mismatch']} sense mismatches, {counts['missing']} not found, {counts['not imported']} suspended or buried.")
    output = io.StringIO()
    fields = list(report[0]) if report else ["status"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(report)
    st.download_button("Download full matching report", output.getvalue(), "anki_matching_report.csv", "text/csv")
    st.dataframe([{
        "word": a["word"], "meaning": a["meaning"], "destination": c["target_translation"],
        "interval_days": a["interval"], "next_review": a["due"], "last_review": a["last"],
    } for a, c in mappings], use_container_width=True)
    if st.button("Import matched progress", disabled=not mappings, key="anki_import_confirm"):
        conn = db()
        try:
            # Additive migrations. PostgreSQL uses IF NOT EXISTS; SQLite checks its schema.
            try:
                conn.execute("ALTER TABLE v2_vocab_progress ADD COLUMN IF NOT EXISTS interval_days INTEGER NOT NULL DEFAULT 0")
                conn.execute("ALTER TABLE v2_vocab_progress ADD COLUMN IF NOT EXISTS lapses INTEGER NOT NULL DEFAULT 0")
            except Exception:
                columns = {r[1] for r in conn.execute("PRAGMA table_info(v2_vocab_progress)").fetchall()}
                if "interval_days" not in columns:
                    conn.execute("ALTER TABLE v2_vocab_progress ADD COLUMN interval_days INTEGER NOT NULL DEFAULT 0")
                if "lapses" not in columns:
                    conn.execute("ALTER TABLE v2_vocab_progress ADD COLUMN lapses INTEGER NOT NULL DEFAULT 0")
            imported = import_progress(conn, mappings)
            conn.commit()
        except Exception:
            if hasattr(conn, "raw"):
                conn.raw.rollback()
            else:
                conn.rollback()
            raise
        finally:
            conn.close()
        st.session_state.pop("vocab_queue_ids", None)
        st.success(f"Imported progress to {imported} untouched Mochi cards. Existing progress was preserved.")
