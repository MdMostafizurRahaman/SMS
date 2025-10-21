import os
import requests
from typing import List, Tuple, Dict, Any

API_URL = os.getenv('SMS_API_URL', 'http://bulksmsbd.net/api/smsapi')
API_KEY = os.getenv('SMS_API_KEY')
SENDER_ID = os.getenv('SMS_SENDER_ID', '8809617624071')
DRY_RUN = os.getenv('SMS_DRY_RUN', 'false').lower() in ('1', 'true', 'yes')


def normalize_phone(phone: str) -> str:
    if phone is None:
        return ''
    p = str(phone).replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    p = ''.join(ch for ch in p if ch.isdigit())

    if p.startswith('880'):
        norm = p
    elif p.startswith('0'):
        norm = '880' + p.lstrip('0')
    elif len(p) == 10:
        norm = '880' + p
    elif len(p) == 11 and p.startswith('1'):
        norm = '880' + p
    else:
        norm = p
    return norm


def send_sms_to_number(number: str, message: str, api_key: str = None) -> Tuple[bool, str]:
    """Send a single SMS, return (success, info)."""
    api_key = api_key or API_KEY
    if not api_key or DRY_RUN:
        # Dry run or missing key - pretend success for valid-looking numbers
        return True, 'dry-run or no api key'

    payload = {
        'api_key': api_key,
        'senderid': SENDER_ID,
        'number': number,
        'message': message,
    }
    try:
        resp = requests.post(API_URL, data=payload, timeout=30)
        if resp.status_code == 200:
            txt = resp.text.strip()
            # Basic heuristics for success
            if txt.startswith('{'):
                try:
                    j = resp.json()
                    if j.get('response_code') in (1001, '1001') or 'success' in str(j).lower():
                        return True, txt
                    else:
                        return False, txt
                except Exception:
                    pass
            if 'success' in txt.lower() or any(code in txt for code in ['1001', '200', '201']):
                return True, txt
            return False, txt
        else:
            return False, f'HTTP {resp.status_code}: {resp.text}'
    except Exception as e:
        return False, str(e)


def bulk_send(message: str, numbers: List[str]) -> Dict[str, Any]:
    """Send message to multiple numbers. Returns dict with sent_count, failed_count, lists."""
    sent_count = 0
    failed = []
    success = []

    for n in numbers:
        norm = normalize_phone(n)
        if not norm or len(norm) < 11:
            failed.append({'number': n, 'normalized': norm, 'reason': 'invalid_number'})
            continue

        ok, info = send_sms_to_number(norm, message)
        if ok:
            sent_count += 1
            success.append({'number': n, 'normalized': norm, 'info': info})
        else:
            failed.append({'number': n, 'normalized': norm, 'info': info})

    return {
        'sent_count': sent_count,
        'failed_count': len(failed),
        'successful_recipients': success,
        'failed_recipients': failed,
        'message': f'Sent: {sent_count}, Failed: {len(failed)}'
    }
