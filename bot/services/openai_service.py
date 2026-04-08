"""OpenAI API integration for message analysis and response generation."""

import json
import logging

from openai import AsyncOpenAI

from bot.config import OPENAI_API_KEY, PROFESSIONAL_PROFILE

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = f"""You are a professional, polite assistant for an independent professional.

Professional's profile: {PROFESSIONAL_PROFILE}

Your role:
- Respond in the SAME language the client uses (Dutch, French, or English).
- If the message is spam or irrelevant, respond very briefly and dismiss it.
- If the message is rude or disrespectful, politely decline to continue.
- Answer common questions about services, availability, and pricing in a helpful way.
- Ask qualifying questions to understand the client's needs: preferred date/time, service needed, location.
- Once you have enough info (service needed + date/time or urgency), mark the lead as qualified for escalation.

You MUST respond with valid JSON only, no other text. Use this exact structure:
{{
  "action": "respond" | "ignore" | "escalate",
  "response_text": "Your response to the client",
  "lead_qualified": true | false,
  "lead_summary": "Brief summary of the lead (only when escalating, otherwise empty string)"
}}

Rules for "action":
- "respond": Normal conversation, answering questions, asking qualifying questions.
- "ignore": Message is spam or completely irrelevant. Still provide a brief response_text.
- "escalate": Lead is qualified — client has expressed a clear need with enough detail. Provide a helpful response_text AND a lead_summary.
"""


async def analyze_message(
    message_text: str, conversation_history: list[dict]
) -> dict:
    """Analyze a message using GPT-4o-mini and return structured action/response."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": message_text})

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        return {
            "action": result.get("action", "respond"),
            "response_text": result.get("response_text", ""),
            "lead_qualified": result.get("lead_qualified", False),
            "lead_summary": result.get("lead_summary", ""),
        }

    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        return {
            "action": "respond",
            "response_text": (
                "I'm sorry, I'm having trouble processing your message "
                "right now. Please try again in a moment."
            ),
            "lead_qualified": False,
            "lead_summary": "",
        }
