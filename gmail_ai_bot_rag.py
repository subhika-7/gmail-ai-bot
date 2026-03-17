import os
import time
import base64
import json
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI
from dotenv import load_dotenv
import logging

# ---------------------------
# Load environment variables
# ---------------------------
from dotenv import load_dotenv
import os

# Force load .env from current file directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

OPEN_API_KEY = os.getenv("OPEN_API_KEY")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60))  # seconds
YOUR_NAME = os.getenv("YOUR_NAME", "Assistant")
YOUR_ROLE = os.getenv("YOUR_ROLE", "")  # e.g. "Software Engineer at XYZ"
TONE = os.getenv("REPLY_TONE", "professional and friendly")  # e.g. "formal", "casual"

# ---------------------------
# Initialize OpenAI client
# ---------------------------
client = OpenAI(api_key=OPEN_API_KEY)

# ---------------------------
# Logging setup
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)


# ============================================================
# RAG LAYER — Knowledge Base
# ============================================================

KNOWLEDGE_BASE = [
    {
        "keywords": ["meeting", "schedule", "call", "appointment", "availability", "free", "busy", "calendar"],
        "context": (
            "Availability context: I am generally available on weekdays between 10 AM and 5 PM IST. "
            "For scheduling meetings, suggest using a calendar invite. I prefer Google Meet for virtual calls. "
            "I am not available on weekends unless it is urgent."
        )
    },
    {
        "keywords": ["resume", "cv", "job", "apply", "application", "position", "opening", "hiring", "internship", "placement"],
        "context": (
            "Career context: I am a final-year engineering student with experience in Python, REST APIs, "
            "OAuth 2.0, Gmail API integration, and AI automation. I have built projects including a Gmail AI bot "
            "using GPT-4o-mini and Google APIs. I am currently exploring full-time software engineering roles and internships. "
            "For job inquiries, express genuine interest and ask for next steps."
        )
    },
    {
        "keywords": ["price", "pricing", "cost", "quote", "rate", "charge", "fee", "invoice", "payment"],
        "context": (
            "Pricing context: For freelance or consulting work, my standard rate is negotiable based on project scope. "
            "Ask for more details about the project before committing to any pricing. "
            "Always respond politely and request a project brief first."
        )
    },
    {
        "keywords": ["deadline", "urgent", "asap", "immediately", "by when", "timeline", "due date"],
        "context": (
            "Deadline context: Before committing to a deadline, mention that timelines depend on the current workload. "
            "Offer to discuss specifics over a call. Never promise unrealistic turnaround times."
        )
    },
    {
        "keywords": ["project", "collaboration", "partner", "work together", "proposal", "idea", "startup"],
        "context": (
            "Collaboration context: I am open to interesting projects in AI, automation, and software development. "
            "Ask the sender to share a brief overview and their expected timeline before agreeing to anything."
        )
    },
    {
        "keywords": ["thank", "thanks", "appreciate", "gratitude", "grateful"],
        "context": (
            "Gratitude context: Keep the reply warm and brief. Acknowledge their thanks and offer continued help if needed."
        )
    },
    {
        "keywords": ["complaint", "issue", "problem", "not working", "bug", "broken", "error", "fail"],
        "context": (
            "Issue context: Acknowledge the problem empathetically. Ask for specific details like error messages, "
            "steps to reproduce, and the environment. Assure them that it will be looked into promptly."
        )
    },
]


def retrieve_context(email_body: str) -> str:
    """
    RAG Retrieval Step:
    Match email body keywords against the knowledge base and return
    all relevant context chunks concatenated. This simulates what a
    vector store retrieval (e.g. FAISS / Chroma) would return.
    """
    email_lower = email_body.lower()
    matched_chunks = []

    for entry in KNOWLEDGE_BASE:
        if any(kw in email_lower for kw in entry["keywords"]):
            matched_chunks.append(entry["context"])

    if matched_chunks:
        logging.info("RAG: %d context chunk(s) retrieved.", len(matched_chunks))
        return "\n\n".join(matched_chunks)

    logging.info("RAG: No specific context matched. Using general reply.")
    return ""


# ============================================================
# Email Threading — fetch prior conversation for context
# ============================================================

def get_thread_history(service, thread_id: str, limit: int = 5) -> str:
    """
    Retrieves the last `limit` messages in a Gmail thread and
    returns them as a formatted conversation string.
    This gives the LLM awareness of the prior conversation —
    a second layer of RAG using live email history.
    """
    try:
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        messages = thread.get("messages", [])[-limit:]
        history_parts = []

        for msg in messages:
            sender = get_sender_email(msg) or "Unknown"
            body = get_email_body(msg)
            if body:
                # Truncate long messages to avoid bloating the context window
                truncated = body.strip()[:600]
                history_parts.append(f"[{sender}]: {truncated}")

        return "\n\n".join(history_parts)
    except Exception as e:
        logging.warning("Could not fetch thread history: %s", e)
        return ""


# ============================================================
# Prompt Builder
# ============================================================

SYSTEM_PROMPT = f"""You are an intelligent email assistant acting on behalf of {YOUR_NAME}{f', {YOUR_ROLE}' if YOUR_ROLE else ''}.

Your job is to write email replies that are:
- Tone: {TONE}
- Concise but complete — no fluff, no unnecessary filler phrases
- Human-sounding — avoid robotic or overly formal language
- Action-oriented — always end with a clear next step or question if needed
- Signed off with the name: {YOUR_NAME}

Rules:
1. Never fabricate facts, prices, or commitments not grounded in the provided context.
2. If the email is ambiguous, ask a clarifying question rather than guessing.
3. Do not begin the reply with "I hope this email finds you well" or similar clichés.
4. Do not include a subject line in the reply body.
5. Keep the reply under 150 words unless the email genuinely requires a longer response.
"""


def build_prompt(email_body: str, retrieved_context: str, thread_history: str) -> list:
    """
    Constructs the final messages array for the Chat Completions API.

    Structure:
      - System prompt  : persona + rules
      - Context block  : RAG-retrieved knowledge + thread history (as assistant context)
      - User message   : the actual email to reply to
    """
    context_block = ""

    if thread_history:
        context_block += f"--- Prior Conversation ---\n{thread_history}\n\n"

    if retrieved_context:
        context_block += f"--- Relevant Context (use this to inform your reply) ---\n{retrieved_context}\n\n"

    user_message = (
        f"{context_block}"
        f"--- Incoming Email ---\n{email_body.strip()}\n\n"
        f"Write a reply to the above email."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]


# ============================================================
# AI Reply Generator
# ============================================================

def ai_reply(email_body: str, retrieved_context: str = "", thread_history: str = "") -> str:
    """
    Generates an AI reply using the constructed RAG-augmented prompt.
    """
    try:
        messages = build_prompt(email_body, retrieved_context, thread_history)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,        # Slightly creative but consistent
            max_tokens=400,         # Keeps replies concise
            presence_penalty=0.3,   # Discourages repetition of phrases
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error("AI Error: %s", e)
        return "Thank you for your email. I'll get back to you shortly."


# ============================================================
# Gmail Utilities
# ============================================================

def get_email_body(message: dict) -> str:
    """Extracts plain text body from a Gmail message object."""
    payload = message.get("payload", {})
    parts = payload.get("parts", [])

    if not parts:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Fallback: check nested multipart
    for part in parts:
        sub_parts = part.get("parts", [])
        for sp in sub_parts:
            if sp.get("mimeType") == "text/plain":
                data = sp.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return ""


def get_sender_email(msg: dict) -> str | None:
    """Extracts the sender's email address from Gmail message headers."""
    headers = msg.get("payload", {}).get("headers", [])
    sender = next((h["value"] for h in headers if h["name"] == "From"), None)
    if sender:
        if "<" in sender and ">" in sender:
            return sender.split("<")[1].split(">")[0].strip()
        return sender.strip()
    return None


def get_subject(msg: dict) -> str:
    """Extracts the subject line from Gmail message headers."""
    headers = msg.get("payload", {}).get("headers", [])
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "Your Email")
    return subject


def send_reply(service, original_message: dict, reply_text: str):
    """Sends a reply to the original email, preserving the thread."""
    to_email = get_sender_email(original_message)
    if not to_email:
        logging.error("No valid sender email found, skipping...")
        return

    subject = get_subject(original_message)
    reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    thread_id = original_message.get("threadId")

    msg = MIMEMultipart()
    msg["To"] = to_email
    msg["Subject"] = reply_subject
    msg.attach(MIMEText(reply_text, "plain"))

    raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    body = {"raw": raw_msg}
    if thread_id:
        body["threadId"] = thread_id  # keeps reply in the same thread

    service.users().messages().send(userId="me", body=body).execute()


def is_automated_sender(email: str) -> bool:
    """Returns True if the email looks like it came from an automated system."""
    automated_patterns = [
        "no-reply", "noreply", "donotreply", "do-not-reply",
        "newsletter", "subscription", "mailer", "notifications",
        "updates@", "alerts@", "support-noreply", "bounce",
    ]
    return any(p in email.lower() for p in automated_patterns)


# ============================================================
# MAIN BOT LOOP
# ============================================================

def main():
    logging.info("Gmail AI Bot (RAG-enhanced) starting...")
    logging.info("Checking every %d seconds.", CHECK_INTERVAL)

    creds = Credentials.from_authorized_user_file(
        "token.json",
        ["https://www.googleapis.com/auth/gmail.modify"]
    )
    service = build("gmail", "v1", credentials=creds)

    # Persist replied IDs to a file so they survive restarts
    replied_ids_file = "replied_ids.json"
    if os.path.exists(replied_ids_file):
        with open(replied_ids_file, "r") as f:
            replied_ids = set(json.load(f))
        logging.info("Loaded %d previously replied IDs.", len(replied_ids))
    else:
        replied_ids = set()

    while True:
        try:
            results = service.users().messages().list(
                userId="me",
                q="is:unread -category:promotions -category:social"
                ).execute()
            messages = results.get("messages", [])
            messages=messages[:5]

            if not messages:
                logging.info("No unread emails found.")
            else:
                logging.info("Found %d unread email(s).", len(messages))

            for m in messages:
                msg = service.users().messages().get(
                    userId="me", id=m["id"], format="full"
                ).execute()
                msg_id = msg["id"]

                # Skip if already replied
                if msg_id in replied_ids:
                    continue

                sender_email = get_sender_email(msg)
                if not sender_email:
                    logging.warning("Skipping email with no sender.")
                    continue

                # Skip automated/newsletter emails
                if is_automated_sender(sender_email):
                    logging.info("Skipping automated email from: %s", sender_email)
                    replied_ids.add(msg_id)
                    continue

                email_body = get_email_body(msg)
                if not email_body.strip():
                    logging.warning("Empty email body from %s, skipping.", sender_email)
                    continue

                # --------------------------------------------------
                # RAG Step 1: Retrieve knowledge base context
                # --------------------------------------------------
                retrieved_context = retrieve_context(email_body)

                # --------------------------------------------------
                # RAG Step 2: Retrieve thread conversation history
                # --------------------------------------------------
                thread_id = msg.get("threadId")
                thread_history = get_thread_history(service, thread_id) if thread_id else ""

                # --------------------------------------------------
                # Generate AI reply with full RAG-augmented prompt
                # --------------------------------------------------
                reply_text = ai_reply(email_body, retrieved_context, thread_history)

                # Send reply
                send_reply(service, msg, reply_text)
                replied_ids.add(msg_id)

                # Persist replied IDs
                with open(replied_ids_file, "w") as f:
                    json.dump(list(replied_ids), f)

                # Mark as read
                service.users().messages().modify(
                    userId="me",
                    id=msg_id,
                    body={"removeLabelIds": ["UNREAD"]}
                ).execute()

                logging.info("[DONE] Replied to: %s | Subject: %s", sender_email, get_subject(msg)), sender_email, get_subject(msg)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error("Unexpected error: %s", e, exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    main()
