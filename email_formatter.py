"""
Format the AI-generated intel brief as a professional HTML email.
Uses inline CSS for maximum email client compatibility.
"""

from config import SIGNATURE


def format_intel_brief(research: dict, sender_info: dict) -> str:
    """
    Format the research results as a clean HTML email.
    """
    company = research.get("company_name", "Unknown Company")
    description = research.get("company_description", "")
    industry = research.get("industry", "Unknown")
    size = research.get("estimated_size", "Unknown")
    tech_stack = research.get("likely_tech_stack", "Unknown")
    role = research.get("sender_likely_role", "Unknown")
    intent = research.get("email_intent", "Unknown")
    insights = research.get("key_insights", [])
    use_case = research.get("agentmail_use_case", "")
    suggested = research.get("suggested_response", "")
    urgency = research.get("urgency", "medium")
    confidence = research.get("confidence", "medium")

    # Urgency color
    urgency_colors = {
        "high": "#dc2626",    # red
        "medium": "#f59e0b",  # amber
        "low": "#22c55e"      # green
    }
    urgency_color = urgency_colors.get(urgency, "#f59e0b")

    # Build insights list
    insights_html = ""
    for insight in insights:
        insights_html += f'<li style="margin-bottom: 6px;">{insight}</li>'

    html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; color: #1a1a1a;">

    <div style="background: #f8f9fa; border-left: 4px solid #000; padding: 16px 20px; margin-bottom: 24px;">
        <h2 style="margin: 0 0 4px 0; font-size: 18px;">🔍 Prospect Intel Brief</h2>
        <p style="margin: 0; color: #666; font-size: 13px;">
            for <strong>{sender_info.get('email', 'unknown')}</strong>
            &nbsp;•&nbsp;
            <span style="color: {urgency_color}; font-weight: 600;">⬤ {urgency.upper()} priority</span>
            &nbsp;•&nbsp;
            Confidence: {confidence}
        </p>
    </div>

    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-weight: 600; width: 140px; color: #444;">Company</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{company}</td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-weight: 600; color: #444;">Description</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{description}</td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-weight: 600; color: #444;">Industry</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{industry}</td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-weight: 600; color: #444;">Company Size</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{size}</td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-weight: 600; color: #444;">Tech Stack</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{tech_stack}</td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-weight: 600; color: #444;">Sender Role</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{role}</td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; font-weight: 600; color: #444;">Intent</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee;">{intent}</td>
        </tr>
    </table>

    <div style="margin-bottom: 20px;">
        <h3 style="font-size: 14px; color: #444; margin-bottom: 8px;">📌 Key Insights</h3>
        <ul style="margin: 0; padding-left: 20px; color: #333; font-size: 14px; line-height: 1.6;">
            {insights_html}
        </ul>
    </div>

    <div style="background: #f0f7ff; border: 1px solid #d0e3ff; padding: 16px; margin-bottom: 20px;">
        <h3 style="font-size: 14px; color: #1a56db; margin: 0 0 8px 0;">🎯 AgentMail Use Case</h3>
        <p style="margin: 0; font-size: 14px; color: #333; line-height: 1.5;">{use_case}</p>
    </div>

    <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 16px; margin-bottom: 20px;">
        <h3 style="font-size: 14px; color: #166534; margin: 0 0 8px 0;">💬 Suggested Response Draft</h3>
        <p style="margin: 0; font-size: 14px; color: #333; line-height: 1.5; font-style: italic;">{suggested}</p>
    </div>

    {SIGNATURE}
</div>
"""
    return html


def format_error_response(error_msg: str) -> str:
    """Format an error response email."""
    return f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; color: #1a1a1a;">
    <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 16px 20px;">
        <h3 style="margin: 0 0 8px 0; color: #dc2626;">⚠️ Processing Error</h3>
        <p style="margin: 0; font-size: 14px; color: #333;">{error_msg}</p>
        <p style="margin: 8px 0 0 0; font-size: 13px; color: #666;">
            <strong>Tip:</strong> Make sure you're forwarding an email that contains a sender address.
            The agent looks for "From:" headers in the forwarded content.
        </p>
    </div>
    {SIGNATURE}
</div>
"""


def format_direct_message_response(research: dict, sender_info: dict) -> str:
    """
    Format response for direct emails (not forwarded).
    Same format as intel brief but with slightly different header.
    """
    html = format_intel_brief(research, sender_info)
    html = html.replace("Prospect Intel Brief", "Sender Intel Brief")
    return html
