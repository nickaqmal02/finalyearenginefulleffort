import re
from datetime import datetime

def normalize_phone_number(phone):
    """ convert any phone format to Whatsapp standard format: +60 16-935 9999"""

    if not phone:
        return phone
    
    # remove all non-digits
    digits = re.sub(r'\D', '', phone)

    # Malaysian number starting with 0 (e.g., 0178718878)
    if digits.startswith('0') and len(digits) >= 9:
        digits = '60' + digits[1:]

    # malaysian number without country code but has 10-11 digits
    elif len(digits) == 9 or len(digits) == 10:
        if not digits.startswith('60'):
            digits = '60' + digits

    # format as +60 xx-xxx xxxx
    if len(digits) >= 11:
        country = digits[:2] # 60
        area = digits[2:4] # 16
        first_part = digits[4:7] # 111
        second_part = digits[7:11] # 6676
        formatted = f"+{country} {area}-{first_part} {second_part}"
        return formatted # we will return formatted if it is not formatted 

    return phone

def format_phone_display(phone):
    return normalize_phone_number


import uuid

def generate_batch_id():
    """Generate unique batch ID for upload tracking"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
    random_part = uuid.uuid4().hex[:8].upper()
    return f"BATCH_{timestamp}_{random_part}"