import argparse
from pathlib import Path
import sys

# Import the existing retriever logic.
# This keeps the new script small and reuses the current search behavior.
RETRIEVER_PATH = Path(__file__).resolve().parent / "retriever.py"
if str(RETRIEVER_PATH) not in sys.path:
    sys.path.insert(0, str(RETRIEVER_PATH.parent))

import retriever


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve the top relevant WhatsApp pairs for a search query."
    )
    parser.add_argument("query", help="Search query to look up in prior chat pairs.")
    args = parser.parse_args()

    pairs = retriever.load_pairs(retriever.DATA_FILE)
    results = retriever.search_pairs(args.query, pairs, top_n=5)

    if not results:
        print("No matches found.")
        return

    print(f"Query: {args.query}\n")
    for index, result in enumerate(results, start=1):
        print(f"Rank: {index}")
        print(f"Conversation ID: {result['conversation_id']}")
        print(f"Similarity score: {result['similarity']:.6f}")
        print("Their message:")
        print(result["their_message"])
        print("My reply:")
        print(result["my_reply"])
        print("-" * 60)


if __name__ == "__main__":
    main()
