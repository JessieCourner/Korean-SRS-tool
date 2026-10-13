#!/usr/bin/env python3
"""Extract supplied TOPIK list PDFs and their supplemental example dictionary."""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).parent
UPLOAD = ROOT.parent / "upload"
OUT = ROOT / "topik_source_audit.json"
LEVEL_FILES = {
    1: "Topik 1 vocab(1).pdf",
    2: "TOPIK 2 VOCABULARY(1).pdf",
    3: "TOPIK 3 VOCABULARY(1).pdf",
    4: "TOPIK 4 VOCABULARY(1).pdf",
    5: "TOPIK 5 VOCABULARY(1).pdf",
    6: "TOPIK 6 VOCABULARY(1).pdf",
}
ADVANCED_FILE = "TOPIK advanced vocabulary(1).pdf"


def extract(path: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                          capture_output=True, text=True).stdout


def parse_level(level: int, filename: str) -> list[dict]:
    lines = extract(UPLOAD / filename).splitlines()
    lo, hi = {1:(1,1000),2:(1001,2000),3:(2001,3000),4:(3001,4000),5:(4001,5000),6:(5001,5666)}[level]
    starts = []
    for i, line in enumerate(lines):
        m = re.match(r"^\s*(\d+)\s*(.*)$", line)
        if m and lo <= int(m.group(1)) <= hi:
            starts.append((int(m.group(1)), i, m.group(2).strip()))
    rows = []
    for j, (n, i, first) in enumerate(starts):
        end = starts[j + 1][1] if j + 1 < len(starts) else len(lines)
        raw_lines = [x.strip() for x in lines[i:end] if x.strip()]
        cols = re.split(r"\s{2,}", first) if first else []
        word = cols[0].strip() if cols else ""
        # A few source rows place the headword on the preceding visual line.
        if not word and i:
            prev_cols = re.split(r"\s{2,}", lines[i - 1].strip())
            if prev_cols and re.search(r"[가-힣]", prev_cols[0]):
                word = prev_cols[0].strip()
        # Remove editorial sense numbers printed after the actual Korean lemma.
        word = re.sub(r"\s+\d{1,2}$", "", word)
        # In the supplied level-4 PDF, index 3755 is only the continuation of
        # index 3754's definition; the table row contains no Korean headword.
        if not re.search(r"[가-힣]", word):
            word = ""
        body = " ".join(raw_lines)
        body = re.sub(r"^\d+\s*", "", body)
        if word and body.startswith(word):
            body = body[len(word):].strip()
        if not word and i:
            # The line before the ID is often the word followed by the start of its gloss.
            prev = lines[i - 1].strip()
            prev_cols = re.split(r"\s{2,}", prev)
            if prev_cols and re.search(r"[가-힣]", prev_cols[0]):
                word = prev_cols[0].strip()
                body = " ".join(prev_cols[1:] + raw_lines[1:]).strip()
        rows.append({"source_id": n, "level": level, "word": word,
                     "source_gloss": body, "source_file": filename,
                     "source_row_text": " ".join(raw_lines)})
    return rows


def parse_advanced() -> list[dict]:
    rows=[]
    for line in extract(UPLOAD / ADVANCED_FILE).splitlines():
        cols = re.split(r"\s{2,}", line.strip())
        if len(cols) >= 5 and cols[0].isdigit():
            rows.append({"source_id": int(cols[0]), "word": cols[1], "meaning": cols[2],
                         "example": cols[3], "example_translation": " ".join(cols[4:])})
    return rows


def main():
    vocab = [row for level, filename in LEVEL_FILES.items() for row in parse_level(level, filename)]
    examples = parse_advanced()
    by_word: dict[str, list[dict]] = {}
    for row in examples:
        by_word.setdefault(row["word"], []).append(row)
    for row in vocab:
        row["example_candidates"] = by_word.get(row["word"], [])
    present = {r["source_id"] for r in vocab}
    expected = set(range(1, 5667))
    result = {
        "notice": "Extracted source records, not yet reviewed final study cards. Preserve same-spelling entries because the source may assign different senses. Rows with an empty headword require manual source repair.",
        "expected_numbered_range": [1,5666],
        "parsed_topik_records": len(vocab),
        "records_with_headword": sum(bool(r["word"]) for r in vocab),
        "missing_source_numbers": sorted(expected - present),
        "rows_without_headword": [r["source_id"] for r in vocab if not r["word"]],
        "duplicate_source_numbers": sorted(n for n in present if sum(1 for r in vocab if r["source_id"] == n)>1),
        "advanced_dictionary_records": len(examples),
        "advanced_dictionary_unique_headwords": len(by_word),
        "exact_headword_matches": sum(bool(r["example_candidates"]) for r in vocab),
        "unique_topik_headwords_with_candidates": len({r["word"] for r in vocab if r["example_candidates"]}),
        "vocabulary": vocab,
        "advanced_examples": examples,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for level in LEVEL_FILES:
        count=sum(1 for r in vocab if r["level"]==level)
        print(f"TOPIK {level}: {count} records")
    print(f"TOPIK records: {len(vocab)}; missing numbers: {result['missing_source_numbers']}")
    print(f"Advanced examples: {len(examples)}; unique headwords: {len(by_word)}")
    print(f"Exact headword matches: {result['exact_headword_matches']} records; {result['unique_topik_headwords_with_candidates']} distinct TOPIK words")
    print(f"Saved {OUT}")

if __name__ == "__main__":
    main()
