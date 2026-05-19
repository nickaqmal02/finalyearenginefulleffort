import re
from datetime import datetime

def parse_whatsapp_file(file_content):
    """
    Parse WhatsApp exported .txt file
    Supports multiple formats:
    1. [13/10/2024, 23:23:42] sender: message
    2. 12/03/2026, 09:30:15 - sender: message
    """
    conversations = []
    
    # Pattern 1: [13/10/2024, 23:23:42] sender: message
    pattern1 = r'\[(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}:\d{2})\]\s+([^:]+):\s*(.+)'
    
    # Pattern 2: 12/03/2026, 09:30:15 - sender: message
    pattern2 = r'(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}:\d{2})\s+-\s+([^:]+):\s*(.+)'
    
    for line_num, line in enumerate(file_content.split('\n'), 1):
        line = line.strip()
        if not line:
            continue
        
        # Skip sticker/image messages
        if 'sticker omitted' in line or 'image omitted' in line or 'document omitted' in line:
            continue
        
        match = None
        
        # Try pattern 1 first (bracket format)
        match = re.match(pattern1, line)
        if not match:
            # Try pattern 2 (dash format)
            match = re.match(pattern2, line)
        
        if match:
            date_str, time_str, sender, message = match.groups()
            
            try:
                # Convert to proper date/time objects
                date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
                
                # Clean sender name (remove extra spaces)
                sender = sender.strip()
                
                conversations.append({
                    'date': date_obj,
                    'time': time_obj,
                    'username': sender,
                    'message': message.strip(),
                })
            except ValueError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
    
    print(f"Parsed {len(conversations)} messages from file")
    return conversations