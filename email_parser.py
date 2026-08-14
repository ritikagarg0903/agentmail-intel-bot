"""
Parse forwarded emails to extract the original sender's information.

Handles forwarding formats from Gmail, Outlook, and Apple Mail.
"""

import re


def extract_original_sender(message) -> dict:
    """
    Extract the original sender's info from a forwarded email.

    Forwarded emails typically contain patterns like:
    - "From: John Smith <john@company.com>"
    - "---------- Forwarded message ---------"
    - "From: john@company.com"

    Returns dict with:
    - email: original sender's email
    - name: original sender's name (if available)
    - domain: sender's email domain
    - company_domain: cleaned domain (no mail., www., etc.)
    """
    body = message.text or message.html or ""

    # If HTML, do basic tag stripping for pattern matching
    if message.html and not message.text:
        body = re.sub(r'<[^>]+>', ' ', message.html)
        body = re.sub(r'\s+', ' ', body)

    result = {
        "email": None,
        "name": None,
        "domain": None,
        "company_domain": None
    }

    # Pattern 1: "From: Name <email@domain.com>"
    match = re.search(r'From:\s*([^<\n]*?)\s*<([^>]+@[^>]+)>', body, re.IGNORECASE)
    if match:
        result["name"] = match.group(1).strip().strip('"').strip("'")
        result["email"] = match.group(2).strip()

    # Pattern 2: "From: email@domain.com"
    if not result["email"]:
        match = re.search(
            r'From:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            body, re.IGNORECASE
        )
        if match:
            result["email"] = match.group(1).strip()

    # Pattern 3: Look for any email in the forwarded section
    if not result["email"]:
        fwd_match = re.search(r'(forwarded|original)\s*(message|mail)', body, re.IGNORECASE)
        if fwd_match:
            remaining = body[fwd_match.start():]
            email_match = re.search(
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                remaining
            )
            if email_match:
                result["email"] = email_match.group(1).strip()

    # Extract domain from email
    if result["email"]:
        result["domain"] = result["email"].split("@")[1]
        # Clean domain (remove common prefixes)
        domain = result["domain"]
        for prefix in ["mail.", "email.", "smtp.", "mx."]:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        result["company_domain"] = domain

    return result


def extract_forwarded_content(message) -> str:
    """
    Extract the body content of the forwarded email (the original message).
    Returns the text after the forwarding delimiter.
    """
    body = message.text or ""
    if not body and message.html:
        body = re.sub(r'<[^>]+>', '\n', message.html)
        body = re.sub(r'\n{3,}', '\n\n', body)

    # Common forwarding delimiters
    delimiters = [
        r'---------- Forwarded message ---------',
        r'-------- Original Message --------',
        r'Begin forwarded message:',
        r'--- Forwarded message ---',
        r'From:.*\nSent:.*\nTo:.*\nSubject:',
    ]

    for delimiter in delimiters:
        match = re.search(delimiter, body, re.IGNORECASE)
        if match:
            return body[match.start():].strip()

    return body


def is_forwarded_email(message) -> bool:
    """Check if this message is a forwarded email (vs. a direct message)."""
    subject = message.subject or ""
    body = message.text or message.html or ""

    # Check subject line
    if subject.lower().startswith("fwd:") or subject.lower().startswith("fw:"):
        return True

    # Check body for forwarding indicators
    forward_indicators = [
        "forwarded message",
        "original message",
        "begin forwarded message",
    ]
    body_lower = body.lower()
    return any(indicator in body_lower for indicator in forward_indicators)


def parse_from_field(from_str: str) -> dict:
    """
    Parse a 'from_' string like 'Name <email>' into name and email.
    The AgentMail SDK returns from_ as a string, not an object.
    """
    if not from_str:
        return {"name": "", "address": ""}

    # Try "Name <email>" format
    match = re.match(r'^(.*?)\s*<([^>]+)>$', from_str.strip())
    if match:
        return {
            "name": match.group(1).strip().strip('"').strip("'"),
            "address": match.group(2).strip()
        }

    # Try plain email
    match = re.match(r'^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', from_str.strip())
    if match:
        return {"name": "", "address": match.group(1)}

    return {"name": from_str.strip(), "address": ""}
