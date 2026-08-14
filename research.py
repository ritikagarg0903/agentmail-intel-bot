"""
AI-powered company research using Google Gemini (free tier).

Uses the google-genai SDK to call Gemini 2.0 Flash for generating
structured intel briefs about prospect companies.
"""

import os
import json
from google import genai
from google.genai import types

from config import AI_MODEL


def _get_client() -> genai.Client:
    """Get a configured Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get a free API key at https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=api_key)


def _parse_json_response(text: str) -> dict:
    """
    Robustly parse JSON from LLM response text.
    Handles cases where the model wraps JSON in markdown code fences.
    """
    text = text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        first_newline = text.index("\n")
        text = text[first_newline + 1:]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3].strip()

    return json.loads(text)


def research_company(sender_info: dict, forwarded_content: str) -> dict:
    """
    Use AI to research the sender's company and generate an intel brief.

    Args:
        sender_info: dict with email, name, domain, company_domain
        forwarded_content: the text of the original forwarded email

    Returns:
        dict with structured research results
    """
    client = _get_client()

    domain = sender_info.get("company_domain", "unknown")
    name = sender_info.get("name", "Unknown")
    email = sender_info.get("email", "unknown")

    prompt = f"""You are a GTM research analyst. A prospect has emailed us. Analyze the information below and generate a comprehensive intel brief.

SENDER INFORMATION:
- Name: {name}
- Email: {email}
- Company Domain: {domain}

ORIGINAL EMAIL CONTENT:
{forwarded_content[:3000]}

Based on the sender's email domain and the content of their email, generate a research brief with the following sections. Use your knowledge of companies and technology to provide realistic, useful intelligence. If you're not sure about something, make reasonable inferences based on the domain and email content, and flag them as inferences.

Respond in the following JSON format:
{{
    "company_name": "Company name (infer from domain if needed)",
    "company_description": "1-2 sentence description of what the company does",
    "industry": "Industry vertical",
    "estimated_size": "Estimated company size (startup/SMB/mid-market/enterprise)",
    "likely_tech_stack": "Likely tech stack or relevant technologies they use",
    "sender_likely_role": "Likely role/title of the sender based on their name and email content",
    "email_intent": "What the sender is asking for or interested in (based on their email content)",
    "key_insights": ["3-5 bullet points of useful intelligence about the company or the opportunity"],
    "agentmail_use_case": "How this company could specifically benefit from AgentMail (be specific about which AgentMail features map to their needs)",
    "suggested_response": "A drafted 3-4 sentence response email to the sender, professional and helpful",
    "urgency": "low/medium/high — how urgently should we respond",
    "confidence": "low/medium/high — confidence in the research accuracy"
}}

Be concise but substantive. Focus on actionable intelligence, not generic fluff.
Return ONLY valid JSON, no markdown fences or extra text."""

    response = client.models.generate_content(
        model=AI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are a GTM research analyst specializing in developer tools and AI infrastructure. You provide structured, actionable intelligence briefs. Always respond with valid JSON only.",
            temperature=0.3,
            response_mime_type="application/json",
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    return _parse_json_response(response.text)


# Common generic/free email providers — domain is NOT useful for company research
GENERIC_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in",
    "outlook.com", "hotmail.com", "live.com", "msn.com",
    "aol.com", "icloud.com", "me.com", "mac.com",
    "protonmail.com", "proton.me", "zoho.com",
    "mail.com", "yandex.com", "gmx.com", "tutanota.com",
}


def is_generic_email(email: str) -> bool:
    """Check if an email address is from a generic/free provider."""
    if not email or "@" not in email:
        return True
    domain = email.split("@")[1].lower()
    return domain in GENERIC_EMAIL_DOMAINS


def research_direct_email(sender_info: dict, email_content: str) -> dict:
    """
    Handle direct emails (not forwarded) — someone emails the agent directly.

    Smart handling for generic email domains (gmail, yahoo, etc.):
    the AI is told to extract company/organization info from the email body
    rather than relying on the sender's domain.
    """
    client = _get_client()

    domain = sender_info.get("company_domain") or sender_info.get("domain", "unknown")
    name = sender_info.get("name", "Unknown")
    email = sender_info.get("email", "unknown")
    is_generic = is_generic_email(email)

    # Build domain context — different instructions for generic vs. company emails
    if is_generic:
        domain_instruction = f"""NOTE: The sender is using a personal email address ({email}), NOT a company email.
This is common for SMBs, freelancers, and early-stage startups.
You MUST look for company/organization mentions in the EMAIL CONTENT below.
Look for patterns like: "I'm from X", "I work at X", "my company X", "at X we...",
company names, URLs, product names, or any other organizational references.
If you find a company mention, research THAT company (not {domain}).
If no company is mentioned, infer what you can from context and flag your confidence as low."""
    else:
        domain_instruction = f"""The sender's email domain is {domain} — use this as the primary signal for company research."""

    prompt = f"""You are a GTM research analyst. Someone has emailed an AI research agent directly. Analyze their email and generate an intel brief.

SENDER INFORMATION:
- Name: {name}
- Email: {email}
- Sender Domain: {domain}

{domain_instruction}

EMAIL CONTENT:
{email_content[:3000]}

Generate a research brief in the following JSON format:
{{
    "company_name": "Company name (extract from email body if sender uses personal email)",
    "company_description": "1-2 sentence description",
    "industry": "Industry vertical",
    "estimated_size": "startup/SMB/mid-market/enterprise",
    "likely_tech_stack": "Likely tech stack or relevant technologies",
    "sender_likely_role": "Likely role of sender",
    "email_intent": "What they're asking about",
    "key_insights": ["3-5 useful intelligence points"],
    "agentmail_use_case": "How AgentMail could help this company",
    "suggested_response": "A 3-4 sentence professional response draft",
    "urgency": "low/medium/high",
    "confidence": "low/medium/high"
}}

Return ONLY valid JSON, no markdown fences or extra text."""

    response = client.models.generate_content(
        model=AI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction="You are a GTM research analyst. When the sender uses a personal email (gmail, yahoo, etc.), pay extra attention to company mentions in the email body. Always respond with valid JSON only.",
            temperature=0.3,
            response_mime_type="application/json",
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    return _parse_json_response(response.text)

