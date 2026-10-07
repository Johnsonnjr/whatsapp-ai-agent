import json
from collections import defaultdict
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "processed_pairs.jsonl"


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


def classify_relationship(pair_count, unique_entries):
    if pair_count >= 100 or unique_entries >= 50:
        return "close_friend"
    if pair_count >= 20 or unique_entries >= 10:
        return "friend"
    return "unknown"


def build_relationship_map(pairs):
    by_conversation = defaultdict(list)
    for pair in pairs:
        conversation_id = pair.get("conversation_id", "unknown")
        by_conversation[conversation_id].append(pair)

    relationship_map = []
    for conversation_id, conv_pairs in sorted(by_conversation.items()):
        total_pairs = len(conv_pairs)
        unique_entries = len({
            (pair.get("their_message", ""), pair.get("my_reply", ""))
            for pair in conv_pairs
        })
        label = classify_relationship(total_pairs, unique_entries)

        relationship_map.append({
            "conversation_id": conversation_id,
            "total_pairs": total_pairs,
            "unique_entries": unique_entries,
            "relationship": label,
        })

    return relationship_map


def main():
    pairs = load_pairs(DATA_FILE)
    relationship_map = build_relationship_map(pairs)

    print("Relationship map")
    print("=" * 60)
    for item in relationship_map:
        print(f"Conversation ID: {item['conversation_id']}")
        print(f"Total pairs: {item['total_pairs']}")
        print(f"Unique entries: {item['unique_entries']}")
        print(f"Relationship: {item['relationship']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
