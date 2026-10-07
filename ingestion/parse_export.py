from pathlib import Path
import argparse
import json
import re


RAW_EXPORT_DIR = Path("data/raw_export")
OUTPUT_FILE = Path("data/processed_pairs.jsonl")
MAX_PAIRS_PER_CONVERSATION = 500


SYSTEM_MESSAGE_FILTERS = [
    "Messages and calls are end-to-end encrypted",
    "<Media omitted>",
    "image omitted",
    "video omitted",
    "audio omitted",
    "sticker omitted",
    "GIF omitted",
    "document omitted",
    "Contact card omitted",
    "Document omitted",
    "<This message was edited>",
    "This message was deleted",
    "This message was deleted.",
    "You deleted this message",
    "You deleted this message.",
    "Missed voice call",
    "Missed video call",
    "created group",
    "changed the subject",
    "added you",
    "changed this group's icon",
]


ACKNOWLEDGEMENTS = {
    "ok",
    "okay",
    "k",
    "kk",
    "haan",
    "hmm",
    "thanks",
    "thank you",
    "cool",
    "nice",
}


MESSAGE_RE = re.compile(
    r"^\[(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}),\s+"
    r"(\d{1,2}:\d{2}:\d{2}\s?[APap][Mm])\]\s+"
    r"([^:]+):\s?(.*)$"
)


def slugify_conversation(filename):
    stem = Path(filename).stem

    # Handles names like:
    # WhatsApp Chat with Deena
    # whatsapp_chat_with_deena
    stem = re.sub(
        r"^whatsapp[_ ]chat[_ ]with[_ ]",
        "",
        stem,
        flags=re.IGNORECASE,
    )

    stem = stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem)

    return stem.strip("-")


def is_system_or_media(text):
    text_lower = text.lower()

    return any(
        item.lower() in text_lower
        for item in SYSTEM_MESSAGE_FILTERS
    )


def is_acknowledgement(text):
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[.!?,;:]+$", "", cleaned)

    return cleaned in ACKNOWLEDGEMENTS


def parse_chat_file(path):
    messages = []
    current = None

    with path.open("r", encoding="utf-8-sig") as file:
        for raw_line in file:
            line = raw_line.rstrip("\n")

            match = MESSAGE_RE.match(line)

            if match:
                date, time, sender, text = match.groups()

                current = {
                    "date": date,
                    "time": time,
                    "sender": sender.strip(),
                    "text": text.strip(),
                }

                messages.append(current)

            elif current is not None:
                # Continuation line
                current["text"] += "\n" + line

    return messages


def clean_messages(messages):
    cleaned = []

    for message in messages:
        text = message["text"].strip()

        if not text:
            continue

        if is_system_or_media(text):
            continue

        if is_acknowledgement(text):
            continue

        message = message.copy()
        message["text"] = text

        cleaned.append(message)

    return cleaned


def group_into_turns(messages):
    turns = []

    for message in messages:

        timestamp = (
            message["date"]
            + ", "
            + message["time"]
        )

        if turns and turns[-1]["sender"] == message["sender"]:

            turns[-1]["text"] += (
                "\n"
                + message["text"]
            )

            turns[-1]["timestamp"] = timestamp

        else:

            turns.append({
                "sender": message["sender"],
                "text": message["text"],
                "timestamp": timestamp,
            })

    return turns


def make_pairs(turns, conversation_id, my_name):
    pairs = []

    for i in range(len(turns) - 1):

        their_turn = turns[i]
        my_turn = turns[i + 1]

        if (
            their_turn["sender"] != my_name
            and my_turn["sender"] == my_name
        ):

            pairs.append({
                "conversation_id": conversation_id,
                "their_message": their_turn["text"],
                "my_reply": my_turn["text"],
                "timestamp": my_turn["timestamp"],
            })

    return pairs


def main():

    parser = argparse.ArgumentParser(
        description="Parse WhatsApp exports into conversation pairs."
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Your exact WhatsApp sender name."
    )

    args = parser.parse_args()

    all_pairs = []

    files = sorted(
        RAW_EXPORT_DIR.glob("*.txt")
    )

    if not files:

        print(
            f"No .txt files found in {RAW_EXPORT_DIR}"
        )

        return

    for path in files:

        conversation_id = slugify_conversation(
            path.name
        )

        messages = parse_chat_file(path)

        messages = clean_messages(messages)

        turns = group_into_turns(messages)

        pairs = make_pairs(
            turns,
            conversation_id,
            args.name
        )

        # Keep last 500 pairs per conversation
        pairs = pairs[
            -MAX_PAIRS_PER_CONVERSATION:
        ]

        all_pairs.extend(pairs)

        print(
            f"{path.name}: "
            f"{len(pairs)} pairs kept"
        )

        if not pairs:

            print(
                f"WARNING: {conversation_id} "
                f"produced zero pairs. "
                f"Check that --name exactly "
                f"matches your sender name."
            )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        for pair in all_pairs:

            file.write(
                json.dumps(
                    pair,
                    ensure_ascii=False
                )
                + "\n"
            )

    print(
        f"\nTotal pairs written: "
        f"{len(all_pairs)}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()