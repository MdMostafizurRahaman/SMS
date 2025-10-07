from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI()

# Allow CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    print("Received file upload request")
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format")

    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))

    # Normalize header names: replace NBSP, collapse whitespace, strip
    def norm_header(h):
        if h is None:
            return ''
        s = str(h).replace('\u00A0', ' ')
        s = ' '.join(s.split())
        return s

    df.columns = [norm_header(c) for c in df.columns]
    print("Columns found:", df.columns.tolist())

    # Map common variants to canonical column names so downstream code can rely on them
    guardian_col = None
    student_col = None
    result_col = None
    for c in df.columns:
        lc = c.lower()
        if 'result' in lc:
            result_col = c
        if 'guardian' in lc and 'phone' in lc:
            guardian_col = c
        if 'student' in lc and 'phone' in lc:
            student_col = c

    if result_col is None:
        raise HTTPException(status_code=400, detail=f"Excel must have a 'Result' column. Found: {df.columns.tolist()}")

    # Rename detected columns to canonical names expected by frontend/backend
    rename_map = {}
    if guardian_col:
        rename_map[guardian_col] = 'Guardian Phone No'
    if student_col:
        rename_map[student_col] = 'Student Phone No'
    rename_map[result_col] = 'Result'

    if rename_map:
        df = df.rename(columns=rename_map)

    data = df.to_dict('records')
    # Replace NaN with None for JSON serialization
    for row in data:
        for key, value in row.items():
            if pd.isna(value):
                row[key] = None
        print(f"Extracted {len(data)} rows")
    return {"data": data}

@app.post("/send-sms")
async def send_sms(request: dict):
    data = request.get('data', [])
    selected_indices = request.get('selectedIndices', None)  # Optional: indices of selected rows

    sent_count = 0
    failed_count = 0

    # BulkSMS BD API configuration
    api_key = os.getenv("SMS_API_KEY")
    api_url = os.getenv("SMS_API_URL", "http://bulksmsbd.net/api/smsapi")
    sender_id = os.getenv("SMS_SENDER_ID", "8809617624071")
    sms_dry_run = os.getenv("SMS_DRY_RUN", "false").lower() in ("1", "true", "yes")

    if not api_key:
        return {"message": "SMS API key not configured"}

    print(f"send-sms called with {len(data)} items")
    if selected_indices:
        print(f"Selected indices: {selected_indices}")

    # Filter data if specific indices are selected
    if selected_indices is not None:
        filtered_data = [data[i] for i in selected_indices if i < len(data)]
    else:
        filtered_data = data

    print(f"Processing {len(filtered_data)} items for SMS")

    # Send individual SMS to each phone number
    for item in filtered_data:
        sms_text = item.get('Result')
        if not sms_text:
            continue

        # Get both student and guardian phone numbers
        phones_to_send = []

        # Look for guardian phone in various column names
        guardian_phone = None
        student_phone = None

        phone_keys = ['Guardian Phone No', 'Guardian  Phone No', 'Guardian Phone', 'GuardianPhone']
        for key in phone_keys:
            if key in item and item.get(key) not in (None, '', 'nan'):
                guardian_phone = str(item.get(key)).strip()
                break

        # Look for student phone
        student_keys = ['Student Phone No', 'Student Phone']
        for key in student_keys:
            if key in item and item.get(key) not in (None, '', 'nan'):
                student_phone = str(item.get(key)).strip()
                break

        # Add guardian phone if available
        if guardian_phone and guardian_phone.lower() not in ('nan', 'none', ''):
            phones_to_send.append(guardian_phone)

        # Add student phone if available
        if student_phone and student_phone.lower() not in ('nan', 'none', ''):
            phones_to_send.append(student_phone)

        # Send individual SMS to each phone number
        for phone in phones_to_send:
            print(f"Processing phone: {phone}")

            # Normalize phone: remove spaces, dashes and parentheses
            phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            # Remove any non-digit characters
            phone = ''.join(ch for ch in phone if ch.isdigit())

            # Normalize phone number format for Bangladesh
            if phone.startswith('880'):
                norm_phone = phone
            elif phone.startswith('0'):
                norm_phone = '880' + phone.lstrip('0')
            elif len(phone) == 10:
                norm_phone = '880' + phone
            elif len(phone) == 11 and phone.startswith('1'):
                norm_phone = '880' + phone
            else:
                norm_phone = phone

            print(f"Normalized phone: {norm_phone}")

            try:
                # BulkSMS BD API format - individual SMS to each phone
                payload = {
                    'api_key': api_key,
                    'senderid': sender_id,
                    'number': norm_phone,
                    'message': str(sms_text)
                }

                if sms_dry_run:
                    print("DRY RUN enabled - would POST to", api_url, "with:")
                    print(payload)
                    sent_count += 1
                else:
                    response = requests.post(api_url, data=payload, timeout=30)
                    print(f"SMS API response status: {response.status_code}")
                    print(f"Response body: {response.text}")

                    if response.status_code == 200:
                        try:
                            result = response.text.strip()
                            
                            # Check if it's JSON response
                            if result.startswith('{'):
                                import json
                                json_result = json.loads(result)
                                
                                # Check for IP whitelisting error
                                if json_result.get('response_code') == 1032 or 'not Whitelisted' in str(json_result.get('error_message', '')):
                                    failed_count += 1
                                    print(f"IP Whitelisting error for {norm_phone}: {json_result.get('error_message')}")
                                    continue
                                
                                # Check for success
                                if json_result.get('response_code') == 1001 or 'success' in str(json_result.get('success_message', '')).lower():
                                    sent_count += 1
                                    print(f"SMS sent successfully to {norm_phone}")
                                else:
                                    failed_count += 1
                                    print(f"Failed to send SMS to {norm_phone}: {json_result}")
                            else:
                                # Check BulkSMS BD text response format
                                if result and 'success' in result.lower():
                                    sent_count += 1
                                    print(f"SMS sent successfully to {norm_phone}")
                                elif result and any(code in result for code in ['1001', '200', '201']):
                                    sent_count += 1
                                    print(f"SMS sent successfully to {norm_phone}")
                                else:
                                    failed_count += 1
                                    print(f"Failed to send SMS to {norm_phone}: {result}")
                        except Exception as e:
                            print(f"Error parsing response: {e}")
                            # If we can't parse, check for common success indicators
                            response_text = response.text.lower()
                            if 'not whitelisted' in response_text:
                                failed_count += 1
                                print(f"IP Whitelisting error for {norm_phone}")
                            elif any(indicator in response_text for indicator in ['success', 'sent', 'ok', '1001']):
                                sent_count += 1
                                print(f"SMS sent successfully to {norm_phone}")
                            else:
                                failed_count += 1
                                print(f"Failed to send SMS to {norm_phone}: {response.text}")
                    else:
                        failed_count += 1
                        print(f"API request failed with status {response.status_code}: {response.text}")

            except Exception as e:
                print(f"Error sending SMS to {norm_phone}: {e}")
                failed_count += 1

    return {"message": f"SMS sent to {sent_count} numbers. Failed: {failed_count}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)