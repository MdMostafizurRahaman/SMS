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
async def send_sms(data: list[dict]):
    sent_count = 0
    failed_count = 0
    
    # SMS.net.bd API configuration
    api_key = os.getenv("SMS_API_KEY")
    api_url = os.getenv("SMS_API_URL", "https://api.sms.net.bd/sendsms")
    sms_dry_run = os.getenv("SMS_DRY_RUN", "false").lower() in ("1", "true", "yes")
    
    if not api_key:
        return {"message": "SMS API key not configured"}
    
    print(f"send-sms called with {len(data)} items")
    # print first few items for debug (avoid huge logs)
    for i, it in enumerate(data[:5]):
        print(f"item[{i}]:", it)

    # Possible column name variants to look for in uploaded Excel
    phone_keys = [
        'Guardian  Phone No',
        'Guardian Phone No',
        'Guardian Phone',
        'GuardianPhone',
        'Student Phone No',
        'Student Phone'
    ]

    for item in data:
        # find first phone key present in the row
        guardian_phone = None
        used_key = None
        for k in phone_keys:
            if k in item and item.get(k) not in (None, ''):
                guardian_phone = item.get(k)
                used_key = k
                break

        sms_text = item.get('Result')

        # If guardian phone missing, try student phone as fallback
        if (not guardian_phone or str(guardian_phone).strip() == '') and 'Student Phone No' in item:
            guardian_phone = item.get('Student Phone No')
            used_key = 'Student Phone No'

        if guardian_phone and str(guardian_phone).strip() and sms_text:
            phone = str(guardian_phone).strip()
            print(f"Found phone in column '{used_key}': {phone}")
            # normalize phone: remove spaces, dashes and parentheses
            phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            # remove any non-digit characters
            phone = ''.join(ch for ch in phone if ch.isdigit())

            # If Excel stripped a leading zero and resulted in a 10-digit number (e.g. 1566...), assume missing leading 0 and add country code
            if phone.startswith('880'):
                norm_phone = phone
            elif phone.startswith('0'):
                norm_phone = '880' + phone.lstrip('0')
            elif len(phone) == 10:
                # likely missing leading 0 -> add country code
                norm_phone = '880' + phone
            elif len(phone) == 11 and phone.startswith('1'):
                # e.g., '1XXXXXXXXXX' (missing 0) -> treat as 880 + phone
                norm_phone = '880' + phone
            else:
                norm_phone = phone

            print(f"Normalized phone: {norm_phone}")

            try:
                print(f"Attempting send to {norm_phone} (msg len={len(str(sms_text))})")
                payload = {'api_key': api_key, 'msg': sms_text, 'to': norm_phone}
                if sms_dry_run:
                    print(f"DRY RUN enabled - would POST to {api_url} with:")
                    print(payload)
                    sent_count += 1
                else:
                    response = requests.post(api_url, data=payload, timeout=10)
                    # log response status
                    print(f"SMS API response status: {response.status_code}, body: {response.text}")
                    result = {}
                    try:
                        result = response.json()
                    except Exception:
                        # non-json response
                        pass
                    if result.get('error') == 0:
                        print(f"SMS sent to {norm_phone}: {result.get('msg')}")
                        sent_count += 1
                    else:
                        print(f"Failed to send SMS to {norm_phone}: {result}")
                        failed_count += 1
            except Exception as e:
                print(f"Error sending SMS to {norm_phone}: {e}")
                failed_count += 1
    
    return {"message": f"SMS sent to {sent_count} numbers. Failed: {failed_count}"}

@app.get("/balance")
async def get_balance():
    api_key = os.getenv("SMS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="SMS API key not configured")
    
    try:
        response = requests.get(f"https://api.sms.net.bd/user/balance/?api_key={api_key}")
        result = response.json()
        if result.get('error') == 0:
            return {"balance": result['data']['balance']}
        else:
            raise HTTPException(status_code=400, detail=result.get('msg', 'Failed to get balance'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)