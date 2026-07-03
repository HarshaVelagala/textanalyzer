import json
from datetime import datetime

import pandas as pd
import streamlit as st

import database as db
import auth_utils
import text_analysis
import plagiarism
import summarizer

st.set_page_config(page_title="AI Text Analyzer", page_icon="📝", layout="wide")
db.init_db()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None


def logout():
    st.session_state.user = None
    st.rerun()


# ---------------------------------------------------------------------------
# Auth screens
# ---------------------------------------------------------------------------
def signup_screen():
    st.subheader("Create an account")
    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Email (optional)")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Sign up")

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            pwd_hash, salt = auth_utils.hash_password(password)
            ok, msg = db.create_user(username.strip(), email.strip(), pwd_hash, salt)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


def login_screen():
    st.subheader("Log in")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        row = db.get_user_by_username(username.strip())
        if row and auth_utils.verify_password(password, row["salt"], row["password_hash"]):
            st.session_state.user = {"id": row["id"], "username": row["username"]}
            st.rerun()
        else:
            st.error("Invalid username or password.")


def auth_gate():
    st.title("📝 AI Text Analyzer")
    st.caption("Sentiment · Readability · Keywords · Plagiarism scoring — all computed locally, no API keys.")
    tab1, tab2 = st.tabs(["Log in", "Sign up"])
    with tab1:
        login_screen()
    with tab2:
        signup_screen()


# ---------------------------------------------------------------------------
# Main app screens (post-login)
# ---------------------------------------------------------------------------
def analyzer_page():
    st.header("Text Analyzer")
    text = st.text_area("Paste your text here", height=220, placeholder="Enter at least a sentence or two...")

    if st.button("Analyze", type="primary"):
        if not text.strip():
            st.warning("Please enter some text first.")
        else:
            result = text_analysis.analyze_text(text)

            stats, sentiment, read, keywords = (
                result["stats"], result["sentiment"], result["readability"], result["keywords"]
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Words", stats["words"])
            c2.metric("Sentences", stats["sentences"])
            c3.metric("Avg word length", stats["avg_word_length"])
            c4.metric("Avg words/sentence", stats["avg_words_per_sentence"])

            st.subheader("Sentiment")
            s1, s2, s3 = st.columns(3)
            s1.metric("Label", sentiment["label"])
            s2.metric("Polarity", sentiment["polarity"])
            s3.metric("Subjectivity", sentiment["subjectivity"])

            st.subheader("Readability")
            r1, r2, r3 = st.columns(3)
            r1.metric("Flesch Reading Ease", read["flesch_reading_ease"])
            r2.metric("Flesch-Kincaid Grade", read["flesch_kincaid_grade"])
            r3.metric("Gunning Fog", read["gunning_fog"])

            st.subheader("Top Keywords")
            if keywords:
                kw_df = pd.DataFrame(keywords, columns=["keyword", "count"]).set_index("keyword")
                st.bar_chart(kw_df)
            else:
                st.info("Not enough distinct words to extract keywords.")

            summary = {
                "stats": stats, "sentiment": sentiment,
                "readability": read, "top_keywords": keywords[:5],
            }
            db.add_history(
                st.session_state.user["id"], "analysis", text, json.dumps(summary)
            )
            st.success("Saved to your history.")


def plagiarism_page():
    st.header("Plagiarism Checker")
    st.caption(
        "Runs a local TF-IDF cosine-similarity comparison — no internet lookup, "
        "no API key. Choose what to compare against below."
    )

    mode = st.radio(
        "Compare against",
        ["Other users' submitted texts (community corpus)", "A specific reference text I paste in"],
        horizontal=False,
    )

    text = st.text_area("Text to check", height=200, key="plag_text")

    reference_text = ""
    if mode == "A specific reference text I paste in":
        reference_text = st.text_area("Reference text", height=200, key="plag_ref")

    if st.button("Check Plagiarism", type="primary"):
        if not text.strip():
            st.warning("Please enter the text you want to check.")
            return

        if mode == "A specific reference text I paste in":
            if not reference_text.strip():
                st.warning("Please paste a reference text to compare against.")
                return
            score = plagiarism.compare_two_texts(text, reference_text)
            best_source = "the reference text you provided"
        else:
            corpus_rows = db.get_corpus_excluding_user(st.session_state.user["id"])
            corpus_texts = [r["input_text"] for r in corpus_rows]
            score, best_idx = plagiarism.compute_similarity_score(text, corpus_texts)
            if best_idx is not None:
                best_source = f"a text previously submitted by another user (on {corpus_rows[best_idx]['created_at'][:10]})"
            else:
                best_source = "no comparable texts found yet in the community corpus"

        verdict, icon = plagiarism.interpret_score(score)
        st.metric("Plagiarism / Similarity Score", f"{score}%")
        st.markdown(f"### {icon} {verdict}")
        st.caption(f"Closest match: {best_source}")

        db.add_history(
            st.session_state.user["id"],
            "plagiarism_check",
            text,
            json.dumps({"score": score, "verdict": verdict, "matched_against": best_source}),
        )
        st.success("Saved to your history.")


def explain_page():
    st.header("Explain / Simplify")
    st.caption(
        "Upload a PDF or paste a block of text — get back a short, plain-language "
        "explanation of what it says. Runs locally (TF-IDF + PageRank sentence ranking), no API key."
    )

    input_mode = st.radio("Input type", ["Paste text", "Upload PDF"], horizontal=True)

    raw_text = ""
    if input_mode == "Upload PDF":
        uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
        if uploaded is not None:
            with st.spinner("Extracting text from PDF..."):
                raw_text = summarizer.extract_text_from_pdf(uploaded)
            if raw_text.strip():
                st.success(f"Extracted {len(text_analysis.get_words(raw_text))} words from the PDF.")
                with st.expander("View extracted text"):
                    preview = raw_text[:3000] + ("..." if len(raw_text) > 3000 else "")
                    st.write(preview)
            else:
                st.warning(
                    "Couldn't extract any text from this PDF — it may be a scanned "
                    "or image-based PDF (this app doesn't do OCR)."
                )
    else:
        raw_text = st.text_area("Paste your text here", height=220, key="explain_text")

    num_sentences = st.slider("How many key sentences in the explanation?", 2, 10, 5)

    if st.button("Explain in Simple Terms", type="primary"):
        if not raw_text.strip():
            st.warning("Please provide some text first (paste text or upload a PDF).")
            return

        summary_sentences = summarizer.textrank_summarize(raw_text, num_sentences)
        if not summary_sentences:
            st.warning("Not enough text to summarize — try a longer document.")
            return

        original_words = len(text_analysis.get_words(raw_text))
        summary_words = len(text_analysis.get_words(" ".join(summary_sentences)))
        reduction = round((1 - summary_words / original_words) * 100, 1) if original_words else 0

        st.subheader("📌 Explanation")
        for i, s in enumerate(summary_sentences, 1):
            st.write(f"**{i}.** {s.strip()}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Original words", original_words)
        c2.metric("Explanation words", summary_words)
        c3.metric("Reduction", f"{reduction}%")

        db.add_history(
            st.session_state.user["id"],
            "explain",
            raw_text[:5000],
            json.dumps(
                {
                    "explanation": summary_sentences,
                    "original_words": original_words,
                    "summary_words": summary_words,
                    "reduction_percent": reduction,
                }
            ),
        )
        st.success("Saved to your history.")


def history_page():
    st.header("My History")
    rows = db.get_history(st.session_state.user["id"])
    if not rows:
        st.info("No activity yet. Run a text analysis or plagiarism check to see it here.")
        return

    for row in rows:
        ts = row["created_at"][:19].replace("T", " ")
        labels = {
            "analysis": "🧠 Analysis",
            "plagiarism_check": "🔍 Plagiarism check",
            "explain": "📌 Explanation",
        }
        label = labels.get(row["action_type"], row["action_type"])
        with st.expander(f"{label} — {ts}"):
            st.write("**Input text:**")
            snippet = row["input_text"]
            st.write(snippet[:500] + ("..." if len(snippet) > 500 else ""))
            st.write("**Result:**")
            try:
                st.json(json.loads(row["result_summary"]))
            except (json.JSONDecodeError, TypeError):
                st.write(row["result_summary"])


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def main():
    if st.session_state.user is None:
        auth_gate()
        return

    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.user['username']}**")
        page = st.radio(
            "Navigate",
            ["Analyze Text", "Plagiarism Checker", "Explain / Simplify", "My History"],
        )
        st.divider()
        if st.button("Log out"):
            logout()

    if page == "Analyze Text":
        analyzer_page()
    elif page == "Plagiarism Checker":
        plagiarism_page()
    elif page == "Explain / Simplify":
        explain_page()
    else:
        history_page()


if __name__ == "__main__":
    main()
