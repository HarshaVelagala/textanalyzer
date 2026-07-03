import networkx as nx
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import text_analysis


def extract_text_from_pdf(file) -> str:
    """file: a file-like object (e.g. from st.file_uploader). Returns extracted text, or '' on failure."""
    try:
        reader = PdfReader(file)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()
    except Exception:
        return ""


def textrank_summarize(text: str, num_sentences: int = 5):
    """
    Extractive summarization: ranks sentences by importance using TF-IDF
    similarity + PageRank (TextRank algorithm), fully local, no API calls.
    Returns the top sentences in their original order.
    """
    sentences = [s.strip() for s in text_analysis.split_sentences(text) if len(s.split()) > 3]
    if not sentences:
        return []
    if len(sentences) <= num_sentences:
        return sentences

    try:
        vectors = TfidfVectorizer(stop_words="english").fit_transform(sentences)
        sim_matrix = cosine_similarity(vectors)
        graph = nx.from_numpy_array(sim_matrix)
        scores = nx.pagerank(graph)
    except Exception:
        return sentences[:num_sentences]

    top_indices = sorted(scores, key=scores.get, reverse=True)[:num_sentences]
    top_indices.sort()  # restore original reading order
    return [sentences[i] for i in top_indices]
