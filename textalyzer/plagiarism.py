from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_similarity_score(text, corpus_texts):
    """
    Compares `text` against every string in `corpus_texts` using TF-IDF + cosine
    similarity (fully local, no external service). Returns (best_score_percent, best_index).
    """
    if not corpus_texts:
        return 0.0, None

    documents = [text] + corpus_texts
    try:
        vectors = TfidfVectorizer(stop_words="english").fit_transform(documents).toarray()
    except ValueError:
        return 0.0, None

    target_vec = vectors[0].reshape(1, -1)
    other_vecs = vectors[1:]
    if other_vecs.shape[0] == 0:
        return 0.0, None

    sims = cosine_similarity(target_vec, other_vecs)[0]
    best_idx = int(sims.argmax())
    best_score = round(float(sims[best_idx]) * 100, 2)
    return best_score, best_idx


def compare_two_texts(text_a, text_b):
    score, _ = compute_similarity_score(text_a, [text_b])
    return score


def interpret_score(score):
    if score >= 70:
        return "High similarity — likely plagiarized", "🔴"
    elif score >= 40:
        return "Moderate similarity — review recommended", "🟠"
    elif score >= 15:
        return "Low similarity — minor overlap", "🟡"
    else:
        return "Very low similarity — appears original", "🟢"
