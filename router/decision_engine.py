"""Decide whether to reply to an incoming WhatsApp message.

Examples:
    python3 router/decision_engine.py "mamey football vara?" --relationship close_friend
    python3 router/decision_engine.py "okay" --relationship friend
"""

import argparse
import re


RELATIONSHIPS = ("close_friend", "friend", "unknown")
ACKNOWLEDGEMENTS = {"ok", "okay", "k", "kk", "hmm", "thanks"}
QUESTION_STARTS = {
    "are", "can", "could", "did", "do", "does", "how", "is", "may",
    "should", "what", "when", "where", "which", "who", "why", "will",
    "would",
}
REQUEST_STARTS = {
    "come", "help", "let", "send", "tell", "please", "share", "call",
}
CONVERSATION_STARTS = {"hello", "hi", "hey", "vanakkam"}


def decide(message, relationship=None):
    normalized = re.sub(r"[^\w\s]", "", message.lower()).split()
    if not normalized:
        return "IGNORE"

    if all(word in ACKNOWLEDGEMENTS for word in normalized):
        return "IGNORE"

    if relationship == "unknown":
        first_word = normalized[0]
        clearly_directed = (
            "?" in message
            or first_word in QUESTION_STARTS
            or first_word in REQUEST_STARTS
            or first_word in CONVERSATION_STARTS
        )
        return "REPLY" if clearly_directed else "IGNORE"

    return "REPLY"


def main():
    parser = argparse.ArgumentParser(
        description="Decide whether to reply to an incoming WhatsApp message."
    )
    parser.add_argument("message", help="The incoming message.")
    parser.add_argument(
        "--relationship",
        choices=RELATIONSHIPS,
        help="Optionally specify the relationship with the sender.",
    )
    args = parser.parse_args()

    print(f"Decision: {decide(args.message, args.relationship)}")


if __name__ == "__main__":
    main()
