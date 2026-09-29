import numpy as np

from ehr.embeddings import Embedder


def test_hash_embedder_shape_and_norm():
    e = Embedder("hash", "", 768)
    v = e.encode(["furosemide 40 mg", "spironolactone 100 mg"])
    assert v.shape == (2, 768)
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-5)


def test_hash_embedder_deterministic_and_similarity_ordering():
    e = Embedder("hash", "", 768)
    a, b, c = e.encode(["furosemide 40 mg iv", "furosemide 20 mg iv", "insulin glargine nightly"])
    assert float(a @ b) > float(a @ c)  # cosine similarity: closer text scores higher
    assert np.allclose(e.encode(["x y z"]), e.encode(["x y z"]))
