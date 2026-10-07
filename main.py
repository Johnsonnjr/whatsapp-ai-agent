import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API key loaded:", api_key is not None)

with open("persona.md", "r", encoding="utf-8") as file:
    persona = file.read()

client = genai.Client(api_key=api_key)

while True:
    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("Chat ended da 👋")
        break

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"""
You are replying as this person's WhatsApp-style AI.

PERSONA:
{persona}

USER MESSAGE:
{user_message}

Reply naturally according to the persona.
"""
    )

    print("AI Reply:")
    print(response.text)