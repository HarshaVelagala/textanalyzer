# AI Text Analyzer (Streamlit, no API keys)

A single-deployment Streamlit app (frontend + backend both in Streamlit) that provides:

- **Login / Signup** — SQLite-backed accounts, passwords hashed with PBKDF2-HMAC-SHA256 (stdlib `hashlib`, no third-party auth service).
- **Text Analyzer** — word/sentence stats, sentiment (TextBlob), readability (Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog via `textstat`), and keyword frequency — all computed locally.
- **Plagiarism Checker** — TF-IDF + cosine similarity (scikit-learn), giving a 0–100% similarity score, either against a community corpus (everyone's previously analyzed texts) or against a reference text you paste in directly.
- **Explain / Simplify** — upload a PDF (text extracted with `pypdf`) or paste a long block of text, and get back a short, plain-language explanation: the most important sentences, picked with a local TextRank-style algorithm (TF-IDF + PageRank via `networkx`), shown as a simple numbered list with a word-count reduction stat.
- **Per-user History** — every analysis, plagiarism check, and explanation is saved to SQLite and shown back to that user only.

Nothing in this app calls an external AI API, so there's no key to manage and nothing that can fail because a key is missing, rate-limited, or expired.

## Project structure

```
textalyzer/
├── app.py            # Streamlit UI + page routing (this is the file you run)
├── database.py        # SQLite setup: users + history tables
├── auth_utils.py       # Password hashing/verification
├── text_analysis.py     # Sentiment, readability, keyword extraction
├── plagiarism.py       # TF-IDF similarity scoring
├── summarizer.py       # PDF text extraction + TextRank summarization
└── requirements.txt
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## Deploy (Streamlit Community Cloud — fully free, single deployment)

1. Push this folder to a GitHub repo.
2. Go to https://share.streamlit.io, connect the repo.
3. Set **Main file path** to `app.py`.
4. Deploy. No secrets/API keys need to be configured.

## Important note on data persistence

This app stores users and history in a local SQLite file (`app_data.db`) next to the code. On Streamlit Community Cloud, the filesystem is **ephemeral** — it resets whenever the app restarts, sleeps, or you push a new commit. For a class project / demo this is fine. If you need accounts and history to survive redeploys permanently, swap `database.py` to point at a persistent store later (e.g. a hosted Postgres/SQLite file via `st.connection`) — the rest of the app doesn't need to change.

## How the "AI" pieces work without an API key

| Feature | Technique | Library |
|---|---|---|
| Sentiment | Lexicon-based polarity/subjectivity scoring | `textblob` |
| Readability | Flesch/Gunning-Fog formulas | `textstat` |
| Keywords | Stopword-filtered frequency counting | stdlib |
| Plagiarism score | TF-IDF vectorization + cosine similarity | `scikit-learn` |
| PDF explanation / text simplification | Text extraction (`pypdf`) + TextRank sentence ranking (TF-IDF + PageRank) | `pypdf`, `scikit-learn`, `networkx` |

All of these run in-process — no network calls, so nothing breaks due to API downtime, quotas, or missing credentials.
