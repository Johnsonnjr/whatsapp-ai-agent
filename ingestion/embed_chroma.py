import json
from pathlib import Path

import chromadb

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "processed_pairs.jsonl"
CHROMA_DIR = Path(__file__).resolve().parent.parent / "data" / "chroma_db"

RELATIONSHIP_MAP_FILE = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "contact_relationship_map.json"
)

def load_pairs(path):
    pairs = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                pairs.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return pairs


def build_embedding_text(pair):
    their_message = (pair.get("their_message") or "").strip()
    my_reply = (pair.get("my_reply") or "").strip()
    if not their_message and not my_reply:
        return ""
    return f"Their message: {their_message}\nMy reply: {my_reply}".strip()


def main():
    pairs = load_pairs(DATA_FILE)
    if not pairs:
        print("No data found in data/processed_pairs.jsonl")
        return

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    with RELATIONSHIP_MAP_FILE.open("r", encoding="utf-8") as file:
        relationship_map = json.load(file)
    

        collections = {
        "family": client.get_or_create_collection(name="history_family"),
        "friend": client.get_or_create_collection(name="history_friend"),
        "professional": client.get_or_create_collection(name="history_professional"),
        "unknown": client.get_or_create_collection(name="history_unknown"),
    }

    collection_data = {
        "family": {"ids": [], "documents": [], "metadatas": []},
        "friend": {"ids": [], "documents": [], "metadatas": []},
        "professional": {"ids": [], "documents": [], "metadatas": []},
        "unknown": {"ids": [], "documents": [], "metadatas": []},
    }

    relationship_to_collection = {
        "family": "family",
        "friend": "friend",
        "close_friend": "friend",
        "professional": "professional",
        "unknown": "unknown",
    }

    for index, pair in enumerate(pairs):
        text = build_embedding_text(pair)

        if not text:
            continue

        conversation_id = pair.get("conversation_id", "unknown")
        their_message = pair.get("their_message", "")
        my_reply = pair.get("my_reply", "")
        timestamp = pair.get("timestamp", "")

        relationship = relationship_map.get(
            conversation_id,
            relationship_map.get("_default", "unknown")
        )

        collection_name = relationship_to_collection.get(
            relationship,
            "unknown"
        )

        doc_id = f"pair_{conversation_id}_{index}"

        collection_data[collection_name]["ids"].append(doc_id)
        collection_data[collection_name]["documents"].append(text)
        collection_data[collection_name]["metadatas"].append({
            "conversation_id": conversation_id,
            "relationship": relationship,
            "their_message": their_message,
            "my_reply": my_reply,
            "timestamp": timestamp,
        })

    for name, data in collection_data.items():
        if data["documents"]:
            collections[name].upsert(
                ids=data["ids"],
                documents=data["documents"],
                metadatas=data["metadatas"],
            )

        print(
            f"history_{name}: "
            f"{len(data['documents'])} documents"
        )


if __name__ == "__main__":
    main()
