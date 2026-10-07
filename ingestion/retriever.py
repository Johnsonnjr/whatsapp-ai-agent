import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "processed_pairs.jsonl"
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def load_pairs(path):
    pairs = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                pair = json.loads(line)
                pairs.append(pair)
            except json.JSONDecodeError:
                pass
    return pairs


def tokenize(text):
    if text is None:
        return []
    return TOKEN_RE.findall(str(text).lower())


def compute_idf(documents):
    if not documents:
        return {}

    doc_count = len(documents)
    df = Counter()
    for tokens in documents:
        df.update(set(tokens))

    return {
        term: math.log((doc_count + 1.0) / (freq + 1.0)) + 1.0
        for term, freq in df.items()
    }


def tfidf_vector(tokens, idf):
    if not tokens:
        return {}

    counts = Counter(tokens)
    total = len(tokens)
    vector = {}
    for term, count in counts.items():
        vector[term] = (count / total) * idf.get(term, 1.0)
    return vector


def cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0

    terms = set(vec_a) | set(vec_b)
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for term in terms:
        va = vec_a.get(term, 0.0)
        vb = vec_b.get(term, 0.0)
        dot += va * vb
        norm_a += va * va
        norm_b += vb * vb

    if dot == 0.0:
        return 0.0

    denom = math.sqrt(norm_a) * math.sqrt(norm_b)
    if denom == 0.0:
        return 0.0

    return dot / denom


def search_pairs(query, pairs, top_n=5):
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    documents = [tokenize(pair.get("their_message", "")) for pair in pairs]
    idf = compute_idf(documents)
    query_vector = tfidf_vector(query_tokens, idf)

    MIN_SIMILARITY = 0.05

    results = []
    for pair in pairs:
        their_message = pair.get("their_message", "")
        doc_tokens = tokenize(their_message)
        doc_vector = tfidf_vector(doc_tokens, idf)
        score = cosine_similarity(query_vector, doc_vector)

        if score >= MIN_SIMILARITY:
            results.append({
                "conversation_id": pair.get("conversation_id", "unknown"),
                "their_message": their_message,
                "my_reply": pair.get("my_reply", ""),
                "similarity": score,
            })

    results.sort(key=lambda item: item["similarity"], reverse=True)
    return results[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Search processed WhatsApp pairs by TF-IDF similarity.")
    parser.add_argument("query", help="User message to search for.")
    parser.add_argument("--top", type=int, default=5, help="Number of results to return.")
    args = parser.parse_args()

    pairs = load_pairs(DATA_FILE)
    if not pairs:
        print("No data found in data/processed_pairs.jsonl")
        return

    results = search_pairs(args.query, pairs, args.top)

    if not results:
        print("No matches found.")
        return

    for index, result in enumerate(results, 1):
        print(f"{index}. conversation_id: {result['conversation_id']}")
        print(f"   similarity: {result['similarity']:.6f}")
        print("   their_message:")
        print(f"     {result['their_message']}")
        print("   my_reply:")
        print(f"     {result['my_reply']}")
        print()


if __name__ == "__main__":
    main()
