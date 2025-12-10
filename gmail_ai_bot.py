import os
import time
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI
from dotenv import load_dotenv
import logging

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))  # seconds

# ---------------------------
# Initialize OpenAI client
# ---------------------------
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# Logging setup
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------------------
# AI reply generator
# ---------------------------
def ai_reply(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content  # fixed for latest SDK
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "Sorry, couldn't generate a reply."

# ---------------------------
# Extract email body
# ---------------------------
def get_email_body(message):
    payload = message.get("payload", {})
    parts = payload.get("parts", [])

    if not parts:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8")

    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8")
    return ""

# ---------------------------
# Extract sender email
# ---------------------------
def get_sender_email(msg):
    headers = msg.get("payload", {}).get("headers", [])
    sender = next((h["value"] for h in headers if h["name"] == "From"), None)
    if sender:
        # Extract email from format "Name <email@example.com>"
        if "<" in sender and ">" in sender:
            return sender.split("<")[1].split(">")[0].strip()
        return sender.strip()
    return None

# ---------------------------
# Send reply
# ---------------------------
def send_reply(service, original_message, reply_text):
    to_email = get_sender_email(original_message)
    if not to_email:
        logging.error("No valid sender email found, skipping...")
        return

    reply = MIMEText(reply_text)
    reply["To"] = to_email
    reply["Subject"] = "Re: Your Email"

    raw_msg = base64.urlsafe_b64encode(reply.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw_msg}
    ).execute()

# ---------------------------
# MAIN BOT LOOP
# ---------------------------
def main():
    logging.info("Bot running... checking emails every %d seconds", CHECK_INTERVAL)

    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/gmail.modify"])
    service = build("gmail", "v1", credentials=creds)

    replied_ids = set()  # Track already replied emails

    while True:
        try:
            results = service.users().messages().list(userId="me", q="is:unread").execute()
            messages = results.get("messages", [])

            for m in messages:
                msg = service.users().messages().get(userId="me", id=m["id"]).execute()
                msg_id = msg["id"]

                sender_email = get_sender_email(msg)
                if not sender_email:
                    logging.error("Skipping email with no valid sender")
                    continue

                sender_lower = sender_email.lower()

                # ---------------------------
                # Option 4: Skip automated/newsletter emails
                # ---------------------------
                if any(x in sender_lower for x in ["no-reply", "noreply", "newsletter", "subscription", "mailer"]):
                    logging.info("Skipping automated/newsletter email from: %s", sender_email)
                    continue

                if msg_id in replied_ids:
                    logging.info("Already replied to %s, skipping...", sender_email)
                    continue

                # ---------------------------
                # Process email
                # ---------------------------
                email_body = get_email_body(msg)
                reply_text = ai_reply(f"Write a polite reply email for this:\n\n{email_body}")

                send_reply(service, msg, reply_text)
                replied_ids.add(msg_id)

                # Mark email as read
                service.users().messages().modify(
                    userId="me",
                    id=msg_id,
                    body={"removeLabelIds": ["UNREAD"]}
                ).execute()

                logging.info("Replied to: %s", sender_email)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error("Error: %s", e)
            time.sleep(30)  # wait before retrying

if __name__ == "__main__":
    main()

