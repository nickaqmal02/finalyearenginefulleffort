# chat_analyzer/services/whatsapp_parser.py
import re
from datetime import datetime

# declaring the entire noise that available in text
MEDIA_OMITTED = {
    "image omitted",
    "sticker omitted",
    "video omitted",
    "audio omitted",
    "gif omitted",
    "document omitted",
    "media omitted",
    "this message was deleted"
}

SYSTEM_MARKERS = ("created the username",)

INVISIBLE_CHARS = "\u200e\u200f\u202a\u202b\u202c\u202d\u202e\ufeff\u2066\u2067\u2068\u2069"

# declaring the line pattern 
# Pattern 1: [13/10/2024, 23:23:42] sender: message  (current WhatsApp format)
PATTERN_BRACKET = re.compile(
    r'^\[(\d{1,2}/\d{1,2}/\d{4}),\s*(\d{1,2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.*)$'
)
# Pattern 2: 13/10/2024, 23:23:42 - sender: message  (older export format)
PATTERN_DASH = re.compile(
    r'^(\d{1,2}/\d{1,2}/\d{4}),\s*(\d{1,2}:\d{2}:\d{2})\s*-\s*([^:]+):\s*(.*)$'
)

EDITED_TAG = re.compile(r'\s*<this message was edited>\s*', re.IGNORECASE)

def parse_whatsapp_content(content):
    """
    Parse Whatsapp export text into a list of message dicts:
    handles dash bracket formats dates and times
    multi line continuations, noise filtering sermo dalenih
    """
    messages = []

    for line in content.split('\n'):
        # remove invsible chars (they break the regex), then we trim it
        line = ''.join(ch for ch in line if ch not in INVISIBLE_CHARS).strip()
        if not line:
            continue

        match = PATTERN_BRACKET.match(line) or PATTERN_DASH.match(line)

        if not match:
            # not a timestampled line 
            if messages:
                messages[-1]['message'] += ' ' + line
            continue

        date_str, time_str, sender, message = match.groups()
        sender = sender.strip()

        # nnow lets strip the edited tag from real messages
        message = EDITED_TAG.sub('', message).strip()

        # skip media-omitted placeholders and system messages
        if message.lower() in MEDIA_OMITTED:
            continue
        if any(marker in message.lower() for marker in SYSTEM_MARKERS):
            continue
        if not message:
            continue

        # parse the date for this whatsapp 
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            try:
                date_obj = datetime.strptime(date_str, '%m/%d/%Y').date()
            except ValueError:
                continue
        # parse time: 24-hour with seconds
        try:
            time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            try:
                time_obj = datetime.strptime(time_str, '%I:%M:%p').time()
            except ValueError:
                continue

        messages.append({
            'date': date_obj,
            'time': time_obj,
            'username': sender,
            'message': message,
        })

    return messages

# creating the calling function so any other file can called this method
def parse_whatsapp_file(file_path):
    """ Read a Whatsapp export .txt and parse it. Raises FileNotFoundError."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return parse_whatsapp_content(content)

# done mate 🤯 wohoooooooo 

