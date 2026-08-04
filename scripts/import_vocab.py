"""Extract annotated vocabulary from the project's PDF into JSON.

Usage:
    python scripts/import_vocab.py "path/to/withMarginNotes.pdf" --out data/words.json

The importer is intentionally conservative: it keeps source pages and raw text
for manual review instead of pretending every PDF layout is perfectly regular.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader

WORD_RE = re.compile(
    r"(?P<formline>[A-Za-z][A-Za-z-]*(?:;\s*[A-Za-z][A-Za-z-]*){0,8})\s+"
    r"🔈(?P<phonetic>[^⭐🏷✍👀#]{1,48})"
    r"(?P<stars>⭐*)"
    r"(?:🏷(?P<levels>[^✍👀#]{0,80}))?"
    r"(?:✍(?P<meaning>[^👀#]{0,180}))?"
)
YEAR_RE = re.compile(r"#(20\d\d(?:EN1?|EN))")
SECTION_RE = re.compile(r"Section\s*(I{1,3}|Ⅲ|Ⅱ)[^\n]{0,70}")


def clean(value: str) -> str:
    return " ".join(value.replace("ﬁ", "fi").replace("ﬂ", "fl").split())


def parse(pdf: Path) -> list[dict]:
    reader = PdfReader(str(pdf))
    records: dict[str, dict] = {}
    for page_number, page in enumerate(reader.pages, 1):
        raw = page.extract_text() or ""
        text = clean(raw)
        section = SECTION_RE.search(text)
        section_name = section.group(0) if section else ""
        if "Section I" in text or "Section  I" in text:
            question_type = "完形"
        elif "Section II" in text or "Section Ⅱ" in text:
            question_type = "阅读"
        elif "Section III" in text or "Section Ⅲ" in text:
            question_type = "写作"
        else:
            question_type = "未识别题型"
        years = YEAR_RE.findall(text)
        for match in WORD_RE.finditer(text):
            forms = [part.lower() for part in re.split(r";\s*", match.group("formline"))]
            word = forms[0]
            item = records.setdefault(word, {
                "word": word, "phonetic": "", "forms": [], "meanings": [],
                "partOfSpeech": [], "importanceLevel": 1, "years": [],
                "questionTypes": [], "examples": [], "sourcePages": [],
                "confusableWords": [], "rawSnippets": []
            })
            item["forms"] = sorted(set(item["forms"] + forms[1:]))
            phonetic = clean(match.group("phonetic")).strip()
            if phonetic and not item["phonetic"]:
                item["phonetic"] = phonetic
            meaning = clean(match.group("meaning") or "").strip()
            if meaning and meaning not in item["meanings"]:
                item["meanings"].append(meaning)
            if meaning:
                pos = re.match(r"([a-z]{1,4})\.", meaning, re.I)
                if pos and pos.group(1).lower() not in item["partOfSpeech"]:
                    item["partOfSpeech"].append(pos.group(1).lower())
            item["importanceLevel"] = max(item["importanceLevel"], min(5, len(match.group("stars")) + 1))
            item["sourcePages"].append({"file": pdf.name, "page": page_number})
            item["years"].extend(years)
            item["questionTypes"].append(question_type)
            start = max(0, match.start() - 100); end = min(len(text), match.end() + 260)
            item["rawSnippets"].append(text[start:end])
    for item in records.values():
        item["years"] = sorted(set(item["years"]))
        item["questionTypes"] = sorted(set(item["questionTypes"]))
        item["sourcePages"] = item["sourcePages"][:20]
        item["rawSnippets"] = item["rawSnippets"][:3]
        item["importanceLevel"] = min(5, max(1, item["importanceLevel"], len(item["years"])))
    return sorted(records.values(), key=lambda item: (-item["importanceLevel"], item["word"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/words.json"))
    args = parser.parse_args()
    words = parse(args.pdf)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"source": args.pdf.name, "count": len(words), "words": words}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(words)} vocabulary records to {args.out}")


if __name__ == "__main__":
    main()
