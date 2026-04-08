# Inboq Bot

AI-powered Telegram messaging assistant for independent professionals. Inboq filters incoming messages, qualifies leads, and escalates important conversations — so you can focus on your work.

## Features

- **Message Filtering** — Automatically detects and filters spam, disrespectful, or irrelevant messages
- **Automated Responses** — AI-generated replies to common inquiries using OpenAI
- **Lead Qualification** — Scores and qualifies potential clients based on conversation context
- **Smart Escalation** — Notifies the professional when a high-value lead or urgent message arrives

## Tech Stack

- **Python 3.11+**
- **python-telegram-bot** — Telegram Bot API wrapper
- **OpenAI API** — GPT-powered message analysis and response generation
- **Railway** — Cloud deployment

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Wazaaa974/Inboq-bot.git
cd Inboq-bot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | OpenAI API key |
| `ADMIN_CHAT_ID` | Your Telegram chat ID for receiving notifications |

### 5. Run the bot

```bash
python -m bot.main
```

## Deployment (Railway)

1. Connect this repository to a new Railway project
2. Set the environment variables in Railway's dashboard
3. Railway will auto-detect the `Procfile` and deploy

## License

Proprietary — All rights reserved.
