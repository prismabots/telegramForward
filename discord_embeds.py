"""
Discord embed builder for trading signals.
"""
import re
from typing import Optional, Dict, Any


# Discord color codes (decimal)
COLOR_GREEN = 0x00FF00    # BUY signals
COLOR_RED = 0xFF0000      # SELL signals, stop loss
COLOR_BLUE = 0x3498DB     # Updates
COLOR_ORANGE = 0xFF8C00   # Warnings/alerts
COLOR_GRAY = 0x95A5A6     # General messages


def parse_trading_signal(text: str) -> Dict[str, Any]:
    """
    Parse a formatted trading signal to extract components.
    
    Returns dict with:
    - type: 'buy', 'sell', 'update', 'stop_loss', 'general'
    - title: Main title line
    - fields: List of {name, value} for embed fields
    - footer: Footer text if any
    - chart_link: Chart URL if found
    """
    lines = text.strip().split('\n')
    result = {
        'type': 'general',
        'title': '',
        'description': '',
        'fields': [],
        'footer': None,
        'chart_link': None,
        'color': COLOR_GRAY,
    }
    
    # Detect signal type from first line
    first_line = lines[0] if lines else ''
    
    if 'BUY' in first_line.upper() or '💎' in first_line or '🛒' in first_line:
        result['type'] = 'buy'
        result['color'] = COLOR_GREEN
    elif 'SELL' in first_line.upper() or '📉' in first_line:
        result['type'] = 'sell'
        result['color'] = COLOR_RED
    elif 'UPDATE' in first_line.upper() or '↩️' in text:
        result['type'] = 'update'
        result['color'] = COLOR_BLUE
    elif 'STOP' in first_line.upper() and ('HIT' in first_line.upper() or '⛔' in first_line):
        result['type'] = 'stop_loss'
        result['color'] = COLOR_RED
    
    # Extract title (first bold line or first line)
    title_match = re.search(r'\*\*(.+?)\*\*', first_line)
    if title_match:
        result['title'] = title_match.group(1)
    else:
        result['title'] = first_line.strip()
    
    # Parse fields from remaining lines
    current_field = None
    description_lines = []
    
    for i, line in enumerate(lines[1:], 1):
        line = line.strip()
        if not line:
            continue
        
        # Check for chart link
        if '📊' in line or 'http' in line.lower():
            # Extract URL
            url_match = re.search(r'https?://[^\s]+', line)
            if url_match:
                result['chart_link'] = url_match.group(0)
                continue
        
        # Check for structured fields (emoji + label)
        if any(emoji in line for emoji in ['🛒', '💵', '🎯', '🚫', '⏰', '🔶', '💎']):
            # This is a field
            if ':' in line:
                parts = line.split(':', 1)
                field_name = parts[0].strip()
                field_value = parts[1].strip() if len(parts) > 1 else ''
                result['fields'].append({
                    'name': field_name,
                    'value': field_value or '—',
                    'inline': True
                })
            else:
                # No colon, add as description
                description_lines.append(line)
        else:
            # Regular text goes to description
            description_lines.append(line)
    
    if description_lines:
        result['description'] = '\n'.join(description_lines)
    
    return result


def build_embed(message_text: str, quoted_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Build a Discord embed from formatted message text.
    
    Args:
        message_text: The formatted trading signal text
        quoted_text: Optional quoted text from reply (shown in description)
    
    Returns:
        Discord embed object as dict
    """
    parsed = parse_trading_signal(message_text)
    
    embed = {
        'title': parsed['title'],
        'color': parsed['color'],
    }
    
    # Add description (including quoted text if this is a reply)
    description_parts = []
    if quoted_text:
        # Truncate quoted text to 150 chars
        preview = quoted_text[:150] + '...' if len(quoted_text) > 150 else quoted_text
        description_parts.append(f'> {preview}')
        description_parts.append('')  # Blank line
    
    if parsed['description']:
        description_parts.append(parsed['description'])
    
    if description_parts:
        embed['description'] = '\n'.join(description_parts)
    
    # Add fields
    if parsed['fields']:
        embed['fields'] = parsed['fields']
    
    # Add footer with chart link
    if parsed['chart_link']:
        embed['footer'] = {
            'text': f'📊 Chart: {parsed["chart_link"][:50]}...'
        }
        # Also add as a field for clickability
        embed['fields'] = embed.get('fields', [])
        embed['fields'].append({
            'name': '📊 Chart',
            'value': f'[View Chart]({parsed["chart_link"]})',
            'inline': False
        })
    
    return embed


def create_webhook_payload(
    message_text: str,
    role_id: Optional[str] = None,
    quoted_text: Optional[str] = None,
    username: str = "Telegram Forward",
    use_embed: bool = True,
) -> Dict[str, Any]:
    """
    Create a Discord webhook payload with optional embed.
    
    Args:
        message_text: The message text to send
        role_id: Optional Discord role ID to mention
        quoted_text: Optional quoted text from reply
        username: Webhook username
        use_embed: If True, format as embed; if False, use plain text
    
    Returns:
        Webhook payload dict
    """
    payload = {
        'username': username,
        'flags': 4,  # Suppress embeds from URLs
    }
    
    # Add role mention as content (separate from embed)
    if role_id:
        payload['content'] = f'<@&{role_id}>'
    
    if use_embed:
        embed = build_embed(message_text, quoted_text)
        payload['embeds'] = [embed]
    else:
        # Fallback to plain text
        content = payload.get('content', '')
        if content:
            content += '\n\n'
        content += message_text
        payload['content'] = content
    
    return payload
