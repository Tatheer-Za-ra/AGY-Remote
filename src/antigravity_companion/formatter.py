import html
from typing import List, Optional

def chunk_text(text: str, max_chars: int = 3800) -> List[str]:
    """Splits a long message into readable chunks preserving line breaks."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks = []
    lines = text.split("\n")
    current_chunk: List[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_chars:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
            # If a single line exceeds max_chars, hard-slice it
            while len(line) > max_chars:
                chunks.append(line[:max_chars])
                line = line[max_chars:]
        current_chunk.append(line)
        current_len += len(line) + 1

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks

def format_notification(title: str, message: str, code: Optional[str] = None) -> List[str]:
    """Formats an alert into clean HTML for Telegram with code block handling."""
    safe_title = html.escape(title)
    safe_message = html.escape(message)
    
    header = f"<b>🔔 {safe_title}</b>\n\n{safe_message}"
    
    if code:
        safe_code = html.escape(code.strip())
        full_content = f"{header}\n\n<pre><code>{safe_code}</code></pre>"
    else:
        full_content = header

    return chunk_text(full_content)

