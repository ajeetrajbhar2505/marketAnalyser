from __future__ import annotations

import re
from typing import Iterable, List

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Ensure resources lazily
try:
    _ = stopwords.words("english")
except LookupError:  # pragma: no cover - downloaded at runtime
    nltk.download("stopwords")

ps = PorterStemmer()
stop_words = set(stopwords.words("english"))


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [ps.stem(tok) for tok in text.split() if tok not in stop_words and len(tok) > 2]
    return " ".join(tokens)


def batch_clean(texts: Iterable[str]) -> List[str]:
    return [clean_text(t) for t in texts]
