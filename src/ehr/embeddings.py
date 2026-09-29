"""Embedding backends.

hash : deterministic signed feature-hashing of unigrams+bigrams -> L2-normalised vector.
       Lexical, NOT semantic. Exists so the whole system runs offline / in CI / on a laptop.
st   : sentence-transformers (e.g. a biomedical model). Semantic. Recommended for real use.
Changing backend changes the vector space, so re-run scripts/04_generate_embeddings.py --force.
"""
from __future__ import annotations

import hashlib
import re

import numpy as np

_TOKEN = re.compile(r"[a-z0-9][a-z0-9\-\.]*")


class Embedder:
    def __init__(self, backend: str, model: str, dim: int):
        self.backend, self.model_name, self.dim = backend, model, dim
        self._st = None
        if backend == "st":
            from sentence_transformers import SentenceTransformer  # lazy: heavy import

            self._st = SentenceTransformer(model)
            got = self._st.get_sentence_embedding_dimension()
            if got != dim:
                raise SystemExit(
                    f"Embedding dim mismatch: model={got}, EMBED_DIM={dim}. "
                    "The pgvector column must be vector(<dim>) and match the model."
                )
        elif backend != "hash":
            raise ValueError(f"unknown EMBED_BACKEND={backend!r} (use 'hash' or 'st')")

    def _hash_one(self, text: str) -> np.ndarray:
        toks = _TOKEN.findall(text.lower())
        feats = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
        v = np.zeros(self.dim, dtype=np.float32)
        for f in feats:
            h = int.from_bytes(hashlib.md5(f.encode()).digest()[:8], "little")
            v[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def encode(self, texts: list[str]) -> np.ndarray:
        if self._st is not None:
            return np.asarray(self._st.encode(texts, normalize_embeddings=True), dtype=np.float32)
        return np.vstack([self._hash_one(t) for t in texts]) if texts else np.zeros((0, self.dim))
