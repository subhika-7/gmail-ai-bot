# Gmail AI Bot

A Python-based Gmail auto-reply bot integrated with OpenAI GPT. This bot automatically reads unread emails in your Gmail account, generates polite AI-based replies, and sends them back while skipping newsletters and automated emails.

---

## Features

- Automatically checks unread Gmail messages.
- Skips newsletters and no-reply emails.
- Generates AI-powered replies using OpenAI GPT (GPT-4o-mini).
- Marks replied emails as read.
- Fully configurable check interval.
- Easy to set up and run.

---

## Demo

![Bot Demo](demo.gif)  <!-- Optional: You can add a screen recording here -->

---

## Requirements

- Python 3.10+  
- Gmail API credentials (token.json)  
- OpenAI API key  

Install required Python packages:

```bash
pip install -r requirements.txt

Setup

Clone or upload repo
Since you uploaded manually, this step is already done.

Gmail API Setup

Follow Gmail API Python Quickstart

to generate token.json.

Keep it in the project root (DO NOT push this file to GitHub).

OpenAI API Key

Create a .env file in the project root:

OPENAI_API_KEY=your_openai_key_here
CHECK_INTERVAL=60


CHECK_INTERVAL is optional (default 60 seconds).

Usage

Run the bot:

python gmail_ai_bot.py


The bot will:

Check unread emails every CHECK_INTERVAL seconds.

Skip newsletters or automated emails.

Generate AI replies for valid emails.

Send the reply and mark the email as read.

Notes

Do not push .env or token.json — keep them local for security.

Designed for Gmail accounts with OAuth credentials.

Works best in a Python virtual environment.
