"""Generate a WhatsApp-style reply using persona and retrieved chat context.

Example:
    python3 generation/generate_reply.py "mamey football vara?" --relationship close_friend
"""

import argparse
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
PERSONA_FILE = PROJECT_DIR / "persona.md"
PAIRS_FILE = DATA_DIR / "processed_pairs.jsonl"
CHROMA_DIR = DATA_DIR / "chroma_db"
COLLECTION_NAME = "whatsapp_pairs"
RELATIONSHIPS = ("close_friend", "friend", "unknown")
TOP_RESULTS = 5

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from dotenv import load_dotenv
from google import genai
import chromadb
from ingestion.build_relationship_map import build_relationship_map, load_pairs


def retrieve_examples(message, relationship):
    pairs = load_pairs(PAIRS_FILE)
    relationship_by_conversation = {
        item["conversation_id"]: item["relationship"]
        for item in build_relationship_map(pairs)
    }

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    result_count = collection.count()
    if result_count == 0:
        return []

    results = collection.query(
        query_texts=[message],
        n_results=result_count,
        include=["metadatas", "distances"],
    )

    examples = []
    for metadata, distance in zip(
        results["metadatas"][0], results["distances"][0]
    ):
        conversation_id = metadata.get("conversation_id", "unknown")
        result_relationship = relationship_by_conversation.get(
            conversation_id, "unknown"
        )
        if relationship and result_relationship != relationship:
            continue

        examples.append(
            {
                "conversation_id": conversation_id,
                "relationship": result_relationship,
                "distance": distance,
                "their_message": metadata.get("their_message", ""),
                "my_reply": metadata.get("my_reply", ""),
            }
        )
        if len(examples) == TOP_RESULTS:
            break

    return examples


def build_prompt(persona, relationship, message, examples):
    if examples:
        examples_text = "\n\n".join(
            (
                f"Example {rank} (relationship: {example['relationship']}):\n"
                f"Their message: {example['their_message']}\n"
                f"My reply: {example['my_reply']}"
            )
            for rank, example in enumerate(examples, start=1)
        )
    else:
        examples_text = "No relevant past conversation examples were found."

    relationship_text = relationship or "unspecified"
    return f"""You are writing one reply as this person in a WhatsApp conversation.

PERSONA:
{persona}

RELATIONSHIP:
{relationship_text}

USER'S NEW MESSAGE:
{message}

RELEVANT PAST CONVERSATION EXAMPLES:
{examples_text}

Write one fresh, natural WhatsApp-style reply to the user's new message.
Follow the persona and let the examples guide your style and context, but do
not copy any past reply verbatim. Output only the reply, with no label or
explanation."""


def main():
    parser = argparse.ArgumentParser(
        description="Generate one persona-aware WhatsApp-style reply."
    )
    parser.add_argument("message", help="The new message to reply to.")
    parser.add_argument(
        "--relationship",
        choices=RELATIONSHIPS,
        help="Optionally specify the relationship for context retrieval.",
    )
    args = parser.parse_args()

    load_dotenv(dotenv_path=PROJECT_DIR / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        parser.error("GEMINI_API_KEY is not set in the environment or .env file.")

    persona = PERSONA_FILE.read_text(encoding="utf-8")
    examples = retrieve_examples(args.message, args.relationship)
    prompt = build_prompt(persona, args.relationship, args.message, examples)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
    )
    reply = (response.text or "").strip()
    if not reply:
        raise RuntimeError("Gemini returned an empty reply.")

    print(reply)


if __name__ == "__main__":
    main()
