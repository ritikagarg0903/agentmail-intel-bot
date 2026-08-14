"""
Prospect Intel Agent — Main polling loop + message processing.

Monitors the ritika-ai@agentmail.to inbox for new messages,
processes forwarded emails by researching the sender's company,
and replies with a structured intel brief.

Updated for AgentMail SDK v0.5.9 API.
"""

import os
import time
import traceback
from dotenv import load_dotenv

# Load env BEFORE importing AgentMail so the API key is available
load_dotenv()

from agentmail import AgentMail

from config import INBOX_USERNAME, INBOX_DOMAIN, POLL_INTERVAL, PROCESSED_LABEL
from email_parser import (
    extract_original_sender,
    extract_forwarded_content,
    is_forwarded_email,
    parse_from_field,
)
from research import research_company, research_direct_email
from email_formatter import format_intel_brief, format_error_response, format_direct_message_response

client = AgentMail()


def get_or_create_inbox():
    """Get the existing inbox or create a new one."""
    target_email = f"{INBOX_USERNAME}@{INBOX_DOMAIN}"

    # Try to list existing inboxes and find ours
    inboxes = client.inboxes.list()
    for inbox in inboxes.inboxes:
        if inbox.email == target_email:
            print(f"✅ Found existing inbox: {inbox.email}")
            return inbox

    # Create new inbox if not found
    inbox = client.inboxes.create(username=INBOX_USERNAME, domain=INBOX_DOMAIN)
    print(f"📬 Created new inbox: {inbox.email}")
    return inbox


def get_unprocessed_messages(inbox_id: str):
    """Get messages that haven't been processed yet."""
    target_email = f"{INBOX_USERNAME}@{INBOX_DOMAIN}"
    messages = client.inboxes.messages.list(inbox_id=inbox_id)
    unprocessed = []

    for msg in messages.messages:
        # Skip messages we've already processed
        labels = msg.labels or []
        if PROCESSED_LABEL in labels:
            continue

        # Skip messages sent BY us (our own replies)
        from_info = parse_from_field(msg.from_ or "")
        if from_info["address"] == target_email:
            continue

        unprocessed.append(msg)

    return unprocessed


def process_message(inbox_id: str, message):
    """Process a single incoming message."""
    msg_id = message.message_id
    subject = message.subject or "(no subject)"

    # Get the full message content (with body text/html)
    full_msg = client.inboxes.messages.get(inbox_id=inbox_id, message_id=msg_id)

    # Determine the reply-to address (the person who forwarded / sent the email)
    from_info = parse_from_field(full_msg.from_ or "")
    reply_to = from_info["address"]

    if not reply_to:
        print(f"  ⚠️ No reply-to address found, skipping")
        return

    print(f"  📧 From: {reply_to}")
    print(f"  📝 Subject: {subject}")

    try:
        if is_forwarded_email(full_msg):
            # FORWARDED EMAIL — extract original sender and research them
            print(f"  🔄 Detected forwarded email")
            sender_info = extract_original_sender(full_msg)
            forwarded_content = extract_forwarded_content(full_msg)

            if not sender_info.get("email"):
                # Couldn't find original sender — send error response
                print(f"  ⚠️ Could not extract original sender")
                error_html = format_error_response(
                    "I couldn't find the original sender's email address in the forwarded message. "
                    "Please make sure you're forwarding an email that contains a 'From:' field."
                )
                send_reply(inbox_id, msg_id, error_html)
                return

            print(f"  🔍 Researching: {sender_info['email']} ({sender_info.get('company_domain', 'unknown')})")
            research = research_company(sender_info, forwarded_content)
            response_html = format_intel_brief(research, sender_info)

        else:
            # DIRECT EMAIL — someone emailed the agent directly
            print(f"  📩 Direct email (not forwarded)")
            sender_info = {
                "email": reply_to,
                "name": from_info.get("name", ""),
                "domain": reply_to.split("@")[1] if "@" in reply_to else "unknown",
                "company_domain": reply_to.split("@")[1] if "@" in reply_to else "unknown"
            }

            email_content = full_msg.text or full_msg.html or ""
            research = research_direct_email(sender_info, email_content)
            response_html = format_direct_message_response(research, sender_info)

        # Send the intel brief as a reply
        send_reply(inbox_id, msg_id, response_html)
        print(f"  ✅ Intel brief sent to {reply_to}")

    except Exception as e:
        print(f"  ❌ Error processing message: {e}")
        traceback.print_exc()
        error_html = format_error_response(f"An error occurred while processing this email: {str(e)}")
        try:
            send_reply(inbox_id, msg_id, error_html)
        except Exception:
            pass


def send_reply(inbox_id: str, message_id: str, body_html: str):
    """Send a reply email using the SDK's reply method."""
    client.inboxes.messages.reply(
        inbox_id=inbox_id,
        message_id=message_id,
        html=body_html,
    )


def mark_as_processed(inbox_id: str, message_id: str):
    """Mark a message as processed so we don't re-process it."""
    try:
        client.inboxes.messages.update(
            inbox_id=inbox_id,
            message_id=message_id,
            add_labels=[PROCESSED_LABEL]
        )
    except Exception as e:
        print(f"  ⚠️ Could not mark as processed: {e}")


def run():
    """Main polling loop."""
    print("🚀 Prospect Intel Agent starting...")
    print(f"📬 Monitoring: {INBOX_USERNAME}@{INBOX_DOMAIN}")
    print(f"⏱️  Polling every {POLL_INTERVAL} seconds")
    print(f"---")

    inbox = get_or_create_inbox()
    inbox_id = inbox.inbox_id

    print(f"🆔 Inbox ID: {inbox_id}")
    print(f"📧 Send emails to: {INBOX_USERNAME}@{INBOX_DOMAIN}")
    print(f"\n🔄 Polling for new messages...\n")

    while True:
        try:
            messages = get_unprocessed_messages(inbox_id)

            if messages:
                print(f"\n📨 Found {len(messages)} new message(s)")

                for msg in messages:
                    print(f"\n  Processing message {msg.message_id[:40]}...")
                    process_message(inbox_id, msg)
                    mark_as_processed(inbox_id, msg.message_id)

        except KeyboardInterrupt:
            print("\n\n👋 Agent shutting down. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Polling error: {e}")
            traceback.print_exc()

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
