"""Run locally (NOT on the server) to create the assistant SESSION_STRING.

    pip install pyrogram tgcrypto
    python generate_session.py

Log in with the *user account* that should join the voice chat,
then copy the printed string into the SESSION_STRING env var.
"""

from pyrogram import Client

api_id = int(input("API_ID: ").strip())
api_hash = input("API_HASH: ").strip()

with Client("gen", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
    print("\nSESSION_STRING:\n")
    print(app.export_session_string())
