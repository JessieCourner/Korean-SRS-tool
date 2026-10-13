#!/usr/bin/env python3
"""Build the six supplied TOPIK levels into V2 vocabulary review cards.

The source PDFs provide headwords and English glosses. The supplemental PDF is
used only when its example has the same sense; otherwise this builder creates a
short, controlled present/past context so the card tests the word itself.
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).parent
AUDIT = json.loads((ROOT / "topik_source_audit.json").read_text(encoding="utf-8"))
OLD = json.loads((ROOT / "vocabulary_packs_v2.json").read_text(encoding="utf-8"))
OUT = ROOT / "vocabulary_packs_v2.json"

KOR = re.compile(r"[가-힣]")
VERB_ENDINGS = ("하다", "되다", "가다", "오다", "다", "르다", "돕다", "춥다", "굽다", "눕다", "줍다")
ADV_WORDS = {"아주", "매우", "너무", "점점", "계속", "오늘", "내일", "어제", "이미", "아직", "다시", "가끔", "항상", "보통", "직접", "몰래", "무조건", "그나마", "널리", "간신히", "간혹", "가까이", "천천히", "일찍", "더", "안", "못", "잘"}
ADJ_HINTS = ("하다", "롭다", "스럽다", "답다", "같다", "없다", "있다", "되다")
FUNCTION_WORDS = {"것", "거", "수", "나", "우리", "그", "이", "저", "안", "못", "더", "한", "씨", "년", "일", "말", "데", "중", "위", "명", "원", "기", "구", "야", "아니", "그러나", "만약", "만큼", "때", "곳"}

def gloss_text(gloss: str) -> str:
    g = re.sub(r"\([^)]*\)", "", gloss).replace(";", ",")
    g = re.sub(r"\s+", " ", g).strip(" ,.-")
    return g or "this word"

def pos_for(word: str, gloss: str) -> str:
    g = gloss.lower()
    adverb_like = g.endswith("ly") and not g.endswith(("lively", "likely", "lovely", "friendly", "early", "timely", "sprightly"))
    if word in ADV_WORDS or word.endswith("히") or adverb_like or g.startswith(("if ", "however", "more and", "extremely", "secretly", "widely", "only", "nearby", "about", "approximately")):
        return "adverb"
    if word in FUNCTION_WORDS or word.startswith("-"):
        return "function word"
    if any(x in g for x in ("able", "full", "special", "good", "bad", "big", "small", "many", "much", "similar", "important", "possible", "difficult", "easy", "straight", "honest", "rapid", "sudden", "close", "intimate", "simple", "clear", "obvious", "cheap", "lively", "rough", "tiny", "natural", "philosophical", "sprightly")) or word.endswith(("롭다", "스럽다", "답다")):
        return "adjective"
    if any(x in g for x in ("to ", "be ", "do ", "get ", "have ", "make ", "put ", "go ", "come ", "say ", "take ", "give ", "show ", "use ", "see ", "know ", "think ", "want ")) or word.endswith(VERB_ENDINGS):
        return "verb"
    return "noun"

def polite_stem(word: str) -> str:
    if not word.endswith("다"): return word
    return word[:-1]

def conjugate(word: str, past=False) -> str:
    if word in {"하다", "좋아하다", "공부하다", "일하다"}:
        return word[:-2] + ("했어요" if past else "해요")
    if not word.endswith("다"): return word
    stem = word[:-1]
    if word.endswith("ㅂ다"): return stem[:-1] + "웠어요" if past else stem[:-1] + "워요"
    if word.endswith("돕다"): return "도왔어요" if past else "도와요"
    if word.endswith("춥다"): return "추웠어요" if past else "추워요"
    if stem.endswith("르"):
        return stem[:-1] + ("랐어요" if past else "라요")
    if stem.endswith("하"):
        return stem[:-1] + ("했어요" if past else "해요")
    last = stem[-1:] if stem else ""
    # Controlled fallback: polite -어요 is valid for the majority of entries.
    return stem + ("었어요" if past else "어요")

def particle(word: str, marker: str) -> str:
    # Use a small syllable-final heuristic for ordinary nouns.
    if not word: return word
    code = ord(word[-1]) - 0xAC00
    final = code >= 0 and code % 28 != 0
    return word + ({"을": "을" if final else "를", "이": "이" if final else "가", "은": "은" if final else "는"}.get(marker, marker))

def english_sentence(pos: str, gloss: str, past: bool) -> str:
    g = gloss_text(gloss).lower()
    if pos == "verb":
        if g in {"to do", "do"}: return "I did it." if past else "I do it."
        if g.startswith("be "): return f"It was {g[3:]}." if past else f"It is {g[3:]} .".replace(" .", ".")
        return f"I {'did ' if past else ''}{g}." if not g.startswith("to ") else f"I {'did ' if past else ''}{g[3:]}."
    if pos == "adjective":
        adjective = g[3:] if g.startswith("be ") else g
        return f"It was {adjective}." if past else f"It is {adjective}."
    if pos == "adverb": return f"I {'worked' if past else 'work'} {g}."
    if pos == "function word": return f"I used the word <i>{g}</i> in a sentence."
    return f"I {'learned about' if past else 'learn about'} {g} in class."

def generated_target_phrase(pos: str, gloss: str, past: bool) -> str:
    g = gloss_text(gloss).lower()
    if pos == "verb":
        if g in {"to do", "do"}: return "did it" if past else "do it"
        if g.startswith("be "): return ("was " if past else "is ") + g[3:]
        return ("did " if past else "") + (g[3:] if g.startswith("to ") else g)
    if pos == "adjective": return g[3:] if g.startswith("be ") else g
    return g

def make_card(row: dict, pack_id: str, seq: int) -> dict:
    word, gloss = row["word"], gloss_text(row["source_gloss"])
    if not word:
        raise ValueError(f"Cannot build a card without a headword: source {row['source_id']}")
    pos = pos_for(word, gloss)
    candidates = row.get("example_candidates") or []
    # Accept supplemental examples only when a meaningful gloss token overlaps.
    gloss_tokens = {x for x in re.findall(r"[a-z]+", gloss.lower()) if len(x) > 3}
    candidate = next((c for c in candidates
                      if gloss_tokens & set(re.findall(r"[a-z]+", c["meaning"].lower()))
                      and set(re.findall(r"[a-z]+", c["meaning"].lower())) & set(re.findall(r"[a-z]+", c["example_translation"].lower()))), None)
    source_label = "Supplied supplemental dictionary example" if candidate else "Supplied TOPIK vocabulary list; controlled study sentence"
    source_url = "https://krdict.korean.go.kr/eng/"
    if candidate and word in candidate["example"]:
        sentence, answer = candidate["example"], word
        translation = candidate["example_translation"]
        # Keep the English target visible for the translation highlighter.
        meaning_tokens = set(re.findall(r"[a-z]+", candidate["meaning"].lower()))
        translation_tokens = re.findall(r"[a-z]+", translation.lower())
        target_en = next((token for token in translation_tokens if token in meaning_tokens), candidate["meaning"])
    else:
        past = seq % 2 == 0
        target_en = generated_target_phrase(pos, gloss, past)
        if pos == "verb":
            answer = conjugate(word, past)
            sentence = f"저는 어제 {answer}." if past else f"저는 오늘 {answer}."
        elif pos == "adjective":
            answer = conjugate(word, past)
            sentence = f"그것은 {answer}."
        elif pos == "adverb":
            answer = word
            sentence = f"저는 {answer} 일했어요."
        elif pos == "function word":
            answer = word
            sentence = f"저는 {answer}를 문장에서 배웠어요."
        else:
            answer = word + "에"
            sentence = f"오늘 수업에서 {answer} 대해 배웠어요."
        translation = english_sentence(pos, gloss, past)
    if answer not in sentence:
        sentence = sentence.replace(word, answer, 1)
    prompt = sentence.replace(answer, "___", 1)
    answer_form = {"verb":"Polite present or past form", "adjective":"Polite present or past form", "adverb":"Adverbial form (unchanged)", "function word":"Function word in context", "noun":"Noun with required particle"}[pos]
    return {"id": f"{pack_id}_{seq:04d}", "pack_id": pack_id, "card_type":"context", "target":word,
            "part_of_speech":pos, "target_translation":target_en, "prompt":prompt, "source_sentence":sentence,
            "translation":translation, "answer":answer, "base_form":f"{word} ({pos})", "answer_form":answer_form,
            "explanation":"Vocabulary practice: the blank requires this target word in the sentence.",
            "source_label":source_label, "source_url":source_url, "artist":"", "song":""}

def main():
    old_topik = {p["id"] for p in OLD["packs"] if p.get("pack_type") == "topik"}
    packs = [p for p in OLD["packs"] if p["id"] not in old_topik]
    cards = [c for c in OLD["cards"] if c["pack_id"] not in old_topik]
    by_level = {i: [r for r in AUDIT["vocabulary"] if r["level"] == i] for i in range(1,7)}
    skipped = []
    for level, rows in by_level.items():
        pid = f"topik{level}_full"
        packs.append({"id":pid, "title":f"TOPIK {level} vocabulary", "level":f"TOPIK {level}", "topic":f"TOPIK {level} · supplied list", "pack_type":"topik", "source_label":f"Supplied TOPIK {level} vocabulary PDF; supplemental dictionary examples where sense matched", "source_url":"https://krdict.korean.go.kr/eng/", "description":f"{len(rows)} source entries from the supplied TOPIK {level} list. Each word has its own contextual review card."})
        n = 0
        for row in rows:
            if not row["word"]:
                skipped.append({"level":level, "source_id":row["source_id"], "reason":"The supplied PDF row has no Korean headword."})
                continue
            n += 1
            cards.append(make_card(row, pid, n))
    # Keep all existing validation and add a report for later manual content review.
    for c in cards:
        if c["prompt"].count("___") != 1 or c["prompt"].replace("___", c["answer"], 1) != c["source_sentence"]:
            raise ValueError(f"Invalid blank reconstruction: {c['id']}")
    OUT.write_text(json.dumps({"schema_version":2, "source_note":"TOPIK levels 1–6 are built from the supplied PDFs. Supplemental examples are accepted only when their gloss overlaps the supplied meaning; remaining cards use controlled present/past study contexts.", "skipped_source_records":skipped, "packs":packs, "cards":cards}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Built {len(packs)} packs and {len(cards)} cards")
    for level, rows in by_level.items(): print(f"TOPIK {level}: {len(rows)}")

if __name__ == "__main__": main()
