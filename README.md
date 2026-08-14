# 🔍 Prospect Intel Agent

An AI-powered email agent built on [AgentMail](https://agentmail.to) that instantly
researches any prospect when you forward their email.

## How It Works

1. Someone emails you (a prospect, partner, cold outreach, etc.)
2. Forward that email to `ritika-ai@agentmail.to`
3. Within 30 seconds, you get a reply with:
   - Company overview (name, industry, size, tech stack)
   - Sender's likely role
   - What they're asking for
   - Key intelligence insights
   - How AgentMail could help them (specific use case mapping)
   - A suggested response draft
   - Urgency rating

### Smart Email Handling

- **Forwarded emails**: Parses Gmail, Outlook, and Apple Mail forwarding formats to extract the original sender's domain for research
- **Direct emails**: Also handles emails sent directly to the agent
- **Generic email domains**: When the sender uses `@gmail.com`, `@yahoo.com`, etc., the agent extracts company mentions from the email body instead of researching the email provider

## Architecture

```
┌─────────────────────┐     ┌──────────────────────────┐     ┌──────────────────┐
│  User forwards      │     │  Python Script (polling)  │     │  Google Gemini   │
│  email to           │────▶│                            │────▶│  API (free)      │
│  ritika-ai@         │     │  1. Poll for new messages  │     │                  │
│  agentmail.to       │     │  2. Parse forwarded email  │     │  Generate intel  │
│                     │     │  3. Extract sender domain  │     │  brief           │
│                     │◀────│  4. Call AI for research   │◀────│                  │
│  Receives intel     │     │  5. Format response        │     │                  │
│  brief as reply     │     │  6. Reply via AgentMail    │     │                  │
└─────────────────────┘     │  7. Mark as processed      │     └──────────────────┘
                            └──────────────────────────┘
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ritikagarg0903/agentmail-intel-bot.git
cd agentmail-intel-bot
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Get your API keys

- **AgentMail**: Sign up at [agentmail.to](https://agentmail.to) and get your API key
- **Google Gemini** (free): Get a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 4. Configure environment

Create a `.env` file with your keys:

```bash
AGENTMAIL_API_KEY=am_us_your_real_key
GEMINI_API_KEY=your_real_gemini_key
```

### 5. Run the agent

```bash
python agent.py
```

You should see:
```
🚀 Prospect Intel Agent starting...
📬 Monitoring: ritika-ai@agentmail.to
⏱️  Polling every 10 seconds
---
✅ Found existing inbox: ritika-ai@agentmail.to
🆔 Inbox ID: ritika-ai@agentmail.to
📧 Send emails to: ritika-ai@agentmail.to

🔄 Polling for new messages...
```

### 6. Test it

Forward any email to `ritika-ai@agentmail.to` — you'll receive an intel brief reply within 30 seconds.

## File Structure

```
prospect-intel-agent/
├── agent.py              # Main polling loop + message processing
├── research.py           # AI research logic (calls Google Gemini)
├── email_parser.py       # Parse forwarded emails to extract sender info
├── email_formatter.py    # Format the intel brief as HTML email
├── config.py             # Configuration constants
├── requirements.txt      # Dependencies
├── .env                  # API keys (not committed)
├── .gitignore            # Excludes .env, venv, __pycache__
└── README.md             # This file
```

## Tech Stack

- **Email Infrastructure**: [AgentMail](https://agentmail.to) — email inbox API for AI agents
- **AI/LLM**: Google Gemini 3.6 Flash — free tier, fast & capable
- **Language**: Python 3.10+
- **No server needed**: Uses polling (no webhooks, no ngrok, no deployment)

## Built By

**Ritika Garg** · M.S. Business Analytics, UC Davis
