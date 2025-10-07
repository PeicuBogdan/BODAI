import re
import math
from collections import Counter
from typing import List, Dict, Tuple


# -------------------- UTILITARE TEXT --------------------

def remove_diacritics(text: str) -> str:
    """Elimină diacriticele românești dintr-un text."""
    replacements = {
        "ă": "a", "â": "a", "î": "i",
        "ș": "s", "ş": "s", "ț": "t", "ţ": "t",
        "Ă": "A", "Â": "A", "Î": "I",
        "Ș": "S", "Ş": "S", "Ț": "T", "Ţ": "T"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def tokenize(text: str) -> List[str]:
    """Transformă textul în listă de cuvinte simple, fără semne de punctuație."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9ăâîșşțţ]", " ", text)
    return [t for t in text.split() if t]


# -------------------- TF-IDF --------------------

def build_tfidf(docs: List[List[str]]) -> Tuple[Dict[str, int], Dict[str, int], int]:
    """
    Construiește vocabularul și calculează frecvența documentelor (DF).
    Returnează: (vocab, df, N)
    """
    vocab: Dict[str, int] = {}
    df: Dict[str, int] = {}
    N = len(docs)

    for doc in docs:
        for token in set(doc):
            vocab.setdefault(token, len(vocab))
            df[token] = df.get(token, 0) + 1

    return vocab, df, N


def tfidf_vector(doc: List[str], vocab: Dict[str, int], df: Dict[str, int], N: int) -> Dict[str, float]:
    """
    Calculează vectorul TF-IDF al unui document dat.
    Returnează un dict {token: valoare_tfidf}.
    """
    tf = Counter(doc)
    vec: Dict[str, float] = {}
    for term, count in tf.items():
        if term in vocab:
            idf = math.log((N + 1) / (df.get(term, 1) + 1)) + 1
            vec[term] = count * idf
    return vec


def cosine_sim(vecA: Dict[str, float], vecB: Dict[str, float]) -> float:
    """Calculează similaritatea cosinus între doi vectori TF-IDF."""
    if not vecA or not vecB:
        return 0.0

    common = set(vecA.keys()) & set(vecB.keys())
    num = sum(vecA[t] * vecB[t] for t in common)
    denA = math.sqrt(sum(v * v for v in vecA.values()))
    denB = math.sqrt(sum(v * v for v in vecB.values()))
    if denA == 0 or denB == 0:
        return 0.0
    return num / (denA * denB)
