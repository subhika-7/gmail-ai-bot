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

## Requirements

- Python 3.10+  
- Gmail API credentials (token.json)  
- OpenAI API key  

---


## 🧠 How It Works

1. Connects securely to Gmail via OAuth 2.0.
2. Reads unread emails in the inbox.
3. Extracts the email body and context.
4. Sends the content to OpenAI GPT model to generate a reply.
5. Replies are sent automatically through Gmail API.
6. Process repeats at configurable intervals.

---


## 🛠️ Tech Stack

- **Python 3**
- **Google Gmail API**
- **OAuth 2.0 Authentication**
- **OpenAI API (GPT-4o-mini or similar)**
- `google-api-python-client`, `google-auth`, `google-auth-oauthlib`, `python-dotenv`
- Virtual Environment (`venv`)

---

gmail_bot/
├── gmail_ai_bot.py # Main Python bot script
├── credentials.json # Google OAuth client configuration
├── token.json # Generated after Google login
├── .env # Environment variables (OpenAI API Key)
├── requirements.txt # Python dependencies
├── venv/ # Virtual environment folder
└── README.md # Project documentation

---

##🌱 Future Enhancements

Tone customization for replies (formal, casual, urgent).

Attachment handling in emails.

Multi-account support.

Dashboard for monitoring bot activity.
