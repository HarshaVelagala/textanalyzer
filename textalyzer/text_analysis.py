import re
from collections import Counter
from textblob import TextBlob
import textstat

STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be because been before
being below between both but by can't cannot could couldn't did didn't do does doesn't doing
don't down during each few for from further had hadn't has hasn't have haven't having he he'd
he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into
is isn't it it's its itself let's me more most mustn't my myself no nor not of off on once only
or other ought our ours ourselves out over own same shan't she she'd she'll she's should
shouldn't so some such than that that's the their theirs them themselves then there there's
these they they'd they'll they're they've this those through to too under until up very was
wasn't we we'd we'll we're we've were weren't what what's when when's where where's which
while who who's whom why why's with won't would wouldn't you you'd you'll you're you've your
yours yourself yourselves this that
""".split())

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
WORD_RE = re.compile(r"[A-Za-z']+")


def split_sentences(text):
    text = text.strip()
    if not text:
        return []
    return [s for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]


def get_words(text):
    return WORD_RE.findall(text.lower())


def basic_stats(text):
    words = get_words(text)
    sentences = split_sentences(text)
    word_count = len(words)
    sentence_count = max(len(sentences), 1)
    avg_word_len = round(sum(len(w) for w in words) / word_count, 2) if word_count else 0
    avg_sentence_len = round(word_count / sentence_count, 2)
    return {
        "characters": len(text),
        "words": word_count,
        "sentences": sentence_count,
        "avg_word_length": avg_word_len,
        "avg_words_per_sentence": avg_sentence_len,
    }


def sentiment_analysis(text):
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 3)
    subjectivity = round(blob.sentiment.subjectivity, 3)
    if polarity > 0.15:
        label = "Positive"
    elif polarity < -0.15:
        label = "Negative"
    else:
        label = "Neutral"
    return {"polarity": polarity, "subjectivity": subjectivity, "label": label}


def readability(text):
    try:
        return {
            "flesch_reading_ease": round(textstat.flesch_reading_ease(text), 2),
            "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(text), 2),
            "gunning_fog": round(textstat.gunning_fog(text), 2),
        }
    except Exception:
        return {"flesch_reading_ease": None, "flesch_kincaid_grade": None, "gunning_fog": None}


def keyword_extraction(text, top_n=10):
    words = [w for w in get_words(text) if w not in STOPWORDS and len(w) > 2]
    return Counter(words).most_common(top_n)


def analyze_text(text):
    return {
        "stats": basic_stats(text),
        "sentiment": sentiment_analysis(text),
        "readability": readability(text),
        "keywords": keyword_extraction(text),
    }
