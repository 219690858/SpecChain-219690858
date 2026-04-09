"""Clean raw reviews into data/reviews_clean.jsonl."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol


_WHITESPACE = re.compile(r"\s+")
_NON_ASCII = re.compile(r"[^\x00-\x7F]+")
_PUNCT = re.compile(r"[^a-zA-Z0-9\s]")
_DIGIT = re.compile(r"\d+")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


class _LemmaLike(Protocol):
    def lemmatize(self, token: str) -> str: ...


class _StemAsLemma:
    """
    Offline-friendly fallback: use stemming as a lemmatization proxy.

    Avoids NLTK corpus downloads (often blocked by SSL/cert issues).
    """

    def __init__(self) -> None:
        try:
            from nltk.stem import PorterStemmer  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Missing dependency `nltk`. Install dependencies first (see requirements.txt)."
            ) from e
        self._stemmer = PorterStemmer()

    def lemmatize(self, token: str) -> str:
        return self._stemmer.stem(token)


def _load_stopwords() -> set[str]:
    # sklearn provides a solid built-in English stopword list without downloads.
    try:
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Missing dependency `scikit-learn` (sklearn). Install dependencies first (see requirements.txt)."
        ) from e
    return set(ENGLISH_STOP_WORDS)


def _load_lemmatizer() -> _LemmaLike:
    # Use WordNet lemmatizer if the corpus is already available; otherwise fall back.
    try:
        import nltk  # type: ignore
        from nltk.stem import WordNetLemmatizer  # type: ignore

        try:
            nltk.data.find("corpora/wordnet")
            return WordNetLemmatizer()
        except LookupError:
            return _StemAsLemma()
    except Exception:
        return _StemAsLemma()


def _num_to_words(match: re.Match[str]) -> str:
    num = match.group(0)
    try:
        from num2words import num2words  # type: ignore
    except Exception:
        return num  # fallback: keep digits if dependency missing
    try:
        return num2words(int(num))
    except Exception:
        return num


def clean_text(text: str, stopwords_set: set[str], lemmatizer: _LemmaLike) -> str:
    t = text or ""
    t = t.strip()
    # Remove non-ascii (drops most emojis/special symbols)
    t = _NON_ASCII.sub(" ", t)
    # Convert digits to words before punctuation stripping
    t = _DIGIT.sub(_num_to_words, t)
    # Remove punctuation/special chars
    t = _PUNCT.sub(" ", t)
    t = t.lower()
    t = _WHITESPACE.sub(" ", t).strip()
    if not t:
        return ""

    tokens = [tok for tok in t.split(" ") if tok]
    tokens = [tok for tok in tokens if tok not in stopwords_set]
    tokens = [lemmatizer.lemmatize(tok) for tok in tokens]
    t = " ".join(tokens)
    return t.strip()


def main() -> int:
    repo = _repo_root()
    raw_path = repo / "data" / "reviews_raw.jsonl"
    clean_path = repo / "data" / "reviews_clean.jsonl"

    raw = _read_jsonl(raw_path)
    if not raw:
        raise RuntimeError(
            f"Raw dataset is empty or missing at {raw_path.as_posix()}. Run src/01_collect_or_import.py first."
        )

    stopwords_set = _load_stopwords()
    lemmatizer = _load_lemmatizer()

    seen_contents: set[str] = set()
    cleaned_rows: list[dict[str, Any]] = []

    for r in raw:
        rid = r.get("id")
        content = r.get("content", "")
        cleaned = clean_text(content, stopwords_set=stopwords_set, lemmatizer=lemmatizer)
        if not cleaned:
            continue
        if len(cleaned.split()) <= 3:
            continue
        if cleaned in seen_contents:
            continue
        seen_contents.add(cleaned)

        cleaned_rows.append(
            {
                "id": rid,
                "content_raw": content,
                "content_clean": cleaned,
                "score": r.get("score"),
                "at": r.get("at"),
            }
        )

    _write_jsonl(clean_path, cleaned_rows)
    print("========== CLEANING SUMMARY ==========")
    print(f"Original reviews: {len(raw)}")
    print(f"Cleaned reviews:  {len(cleaned_rows)}")
    print(f"Saved to: {clean_path.as_posix()}")
    print("=====================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())