# 📧 Gmail AI Assistant with RAG

An intelligent email automation system that reads incoming emails, understands context, and generates human-like replies using AI.

This project integrates the Gmail API with an AI-powered response engine and a lightweight Retrieval-Augmented Generation (RAG) system to produce context-aware replies.

---

## 🚀 Features

* 📥 **Automated Email Reading**
  Fetches unread emails using Gmail API.

* 🤖 **AI-Powered Reply Generation**
  Uses OpenAI models to generate smart, human-like responses.

* 🧠 **RAG (Retrieval-Augmented Generation)**
  Enhances replies using:

  * Custom knowledge base
  * Email thread history

* 🧵 **Thread Awareness**
  Maintains conversation context by analyzing previous emails.

* 🚫 **Spam & Automated Email Filtering**
  Skips newsletters, no-reply emails, and system-generated messages.

* ⚡ **Fallback Safety Mode**
  If AI fails (quota/API issues), sends a safe default response.

* 🔁 **Continuous Monitoring Loop**
  Checks inbox at regular intervals and replies automatically.

---

## 🏗️ Architecture Overview

```
Incoming Email
      ↓
Gmail API Fetch
      ↓
Filter (Spam / Automated)
      ↓
RAG Layer
  ├── Knowledge Base Matching
  └── Thread History Retrieval
      ↓
Prompt Builder
      ↓
OpenAI API (LLM)
      ↓
Generated Reply
      ↓
Send via Gmail API
```

---

## 🛠️ Tech Stack

* **Python**
* **Gmail API (Google API Client)**
* **OAuth 2.0 Authentication**
* **OpenAI API**
* **dotenv (Environment Management)**

---

## 📂 Project Structure

```
gmail-ai-bot/
│
├── gmail_ai_bot_rag.py    # Main bot logic
├── generate_token.py      # OAuth authentication flow
├── credentials.json       # Google API credentials (ignored)
├── token.json             # OAuth token (ignored)
├── .env                   # Environment variables (ignored)
├── .gitignore             # Sensitive files excluded
└── bot.log                # Runtime logs
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```
git clone https://github.com/your-username/gmail-ai-bot.git
cd gmail-ai-bot
```

---

### 2️⃣ Install dependencies

```
pip install google-auth google-auth-oauthlib google-api-python-client openai python-dotenv
```

---

### 3️⃣ Setup environment variables

Create a `.env` file:

```
OPEN_API_KEY=your_openai_api_key
CHECK_INTERVAL=60
YOUR_NAME=Your Name
YOUR_ROLE=Your Role
REPLY_TONE=professional and friendly
```

---

### 4️⃣ Setup Gmail API

* Enable Gmail API in Google Cloud Console
* Download `credentials.json`
* Place it in the project folder

---

### 5️⃣ Generate OAuth token

```
python generate_token.py
```

---

### 6️⃣ Run the bot

```
python gmail_ai_bot_rag.py
```

---

## ⚠️ Limitations

* OpenAI API usage depends on quota and billing
* If quota is exceeded, the system switches to fallback responses
* Basic keyword-based RAG (no vector database)

---

## 🔮 Future Improvements

* 🔍 Vector database integration (FAISS / ChromaDB)
* 📊 Email classification using ML models
* 🧾 Smart summarization of long threads
* 🌐 Web dashboard for monitoring
* ⚡ Rate limiting & batching for API efficiency

---

## 💡 Key Concepts Demonstrated

* Retrieval-Augmented Generation (RAG)
* API Integration (Gmail + OpenAI)
* OAuth 2.0 Authentication
* Prompt Engineering
* Error Handling & Fallback Design
* Automation Systems Design

---

## 👨‍💻 Author

**Thanvant R**

---

## ⭐ Notes

This project focuses on system design and integration of AI into real-world workflows.
Even with API limitations, the architecture is fully functional and extensible.

---

## 📌 Summary

A production-style AI email assistant demonstrating how LLMs can be combined with real APIs and contextual retrieval to automate communication intelligently.
