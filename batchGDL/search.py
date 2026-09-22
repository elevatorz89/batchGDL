import os

from rapidfuzz import fuzz

from .constants import SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR

_MIN_SCORE = 0.68
_WORD_FUZZ_CUTOFF = 86.0
_LINE_FUZZ_CUTOFF = 78.0
_SEARCH_DIRS = (SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR)


def _single_word_score(word: str, line_lower: str) -> float:
    if not word:
        return 0.0
    if word in line_lower:
        return 1.0
    if len(word) <= 3:
        return 0.0

    score = fuzz.partial_ratio(word, line_lower, score_cutoff=_WORD_FUZZ_CUTOFF)
    return float(score) / 100.0 if score else 0.0


def _line_relevance(term_lower: str, line_lower: str) -> float:
    if not term_lower:
        return 0.0
    if term_lower in line_lower:
        return 1.0

    words = [w for w in term_lower.split() if w]
    if len(words) >= 2:
        substantive = [w for w in words if len(w) >= 2]
        if not substantive:
            return 0.0
        parts: list[float] = []
        for w in substantive:
            s = _single_word_score(w, line_lower)
            if s <= 0.0:
                return 0.0
            parts.append(s)
        token_avg = sum(parts) / len(parts)
        phrase_score = fuzz.WRatio(term_lower, line_lower, score_cutoff=_LINE_FUZZ_CUTOFF)
        if not phrase_score:
            return token_avg
        return min(0.99, (token_avg * 0.7) + ((float(phrase_score) / 100.0) * 0.3))

    return _single_word_score(term_lower, line_lower)


def search(term: str) -> list[dict]:
    term_lower = term.lower().strip()
    scored: list[tuple[float, dict]] = []

    for lists_dir in _SEARCH_DIRS:
        if not os.path.isdir(lists_dir):
            continue
        folder = os.path.basename(lists_dir)
        for fname in sorted(os.listdir(lists_dir)):
            if not fname.lower().endswith(".txt"):
                continue
            path = os.path.join(lists_dir, fname)
            with open(path, encoding="utf-8", errors="ignore") as fh:
                for lineno, raw_line in enumerate(fh, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    score = _line_relevance(term_lower, line.lower())
                    if score >= _MIN_SCORE:
                        scored.append(
                            (
                                score,
                                {
                                    "file": f"{folder}/{fname}",
                                    "line_number": lineno,
                                    "line": line,
                                },
                            )
                        )

    scored.sort(key=lambda item: (-item[0], item[1]["file"], item[1]["line_number"]))
    return [hit for _, hit in scored]
