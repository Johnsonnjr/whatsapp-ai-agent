"""Retrieve relationship-aware WhatsApp conversation context.

Example:
    python3 ingestion/retrieve_context.py "football" --relationship close_friend
"""

import argparse
from pathlib import Path

import chromadb

from build_relationship_map import build_relationship_map, load_pairs


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PAIRS_FILE = DATA_DIR / "processed_pairs.jsonl"
CHROMA_DIR = DATA_DIR / "chroma_db"
COLLECTION_NAME = "whatsapp_pairs"
RELATIONSHIPS = ("close_friend", "friend", "unknown")
TOP_RESULTS = 5


def main():
    parser = argparse.ArgumentParser(
        description="Search WhatsApp conversation embeddings for relevant context."
    )
    parser.add_argument("message", help="The new message to search for.")
    parser.add_argument(
        "--relationship",
        choices=RELATIONSHIPS,
        help="Optionally limit results to this relationship category.",
    )
    args = parser.parse_args()

    pairs = load_pairs(PAIRS_FILE)
    relationship_by_conversation = {
        item["conversation_id"]: item["relationship"]
        for item in build_relationship_map(pairs)
    }

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    result_count = collection.count()
    if result_count == 0:
        print("No conversation pairs found in the ChromaDB collection.")
        return

    results = collection.query(
        query_texts=[args.message],
        n_results=result_count,
        include=["metadatas", "distances"],
    )

    matches = []
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    for metadata, distance in zip(metadatas, distances):
        conversation_id = metadata.get("conversation_id", "unknown")
        relationship = relationship_by_conversation.get(
            conversation_id, "unknown"
        )
        if args.relationship and relationship != args.relationship:
            continue

        matches.append(
            {
                "conversation_id": conversation_id,
                "relationship": relationship,
                "distance": distance,
                "their_message": metadata.get("their_message", ""),
                "my_reply": metadata.get("my_reply", ""),
            }
        )
        if len(matches) == TOP_RESULTS:
            break

    if not matches:
        print("No matches found.")
        return

    print(f"Query: {args.message}\n")
    for rank, result in enumerate(matches, start=1):
        print(f"Rank: {rank}")
        print(f"Conversation ID: {result['conversation_id']}")
        print(f"Relationship: {result['relationship']}")
        print(f"Distance: {result['distance']:.6f}")
        print("Their message:")
        print(result["their_message"])
        print("My reply:")
        print(result["my_reply"])
        print("-" * 60)


if __name__ == "__main__":
    main()
