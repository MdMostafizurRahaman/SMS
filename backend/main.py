from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
import pandas as pd
import io
import os
from dotenv import load_dotenv
import requests
from datetime import timedelta, datetime
from models import User, UserCreate, UserLogin, UserUpdate, Token, UserRole, UserResponse
from auth import authenticate_user, create_access_token, get_current_user, get_current_active_user, get_current_admin_user, get_password_hash
from database import init_database, get_users_collection

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_database()

    # Create admin user if not exists
    users_collection = await get_users_collection()
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    admin_full_name = os.getenv('ADMIN_FULL_NAME')

    existing_admin = await users_collection.find_one({'email': admin_email})
    if not existing_admin:
        admin_user = {
            'email': admin_email,
            'password_hash': get_password_hash(admin_password),
            'full_name': admin_full_name,
            'role': 'admin',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        await users_collection.insert_one(admin_user)
        print('Admin user created')

    yield

    # Shutdown (if needed)
    pass

app = FastAPI(lifespan=lifespan)

# Allow CORS
origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

@app.get('/healthz')
async def health_check():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        users_collection = await get_users_collection()
        # Simple ping to verify database connectivity
        await users_collection.count_documents({}, limit=1)
        return {'status': 'healthy', 'database': 'connected'}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f'Service unavailable: {str(e)}')

@app.post('/register', response_model=dict)
async def register(user: UserCreate):
    users_collection = await get_users_collection()

    # Check if user already exists
    existing_user = await users_collection.find_one({'email': user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')

    # Create new user with pending role
    user_dict = {
        'email': user.email,
        'password_hash': get_password_hash(user.password),
        'full_name': user.full_name,
        'role': 'pending',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    await users_collection.insert_one(user_dict)

    return {'message': 'Registration successful. Waiting for admin approval.'}

@app.post('/token', response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    if user.role == UserRole.PENDING:
        raise HTTPException(status_code=400, detail='Account is pending approval')

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.email, 'role': user.role.value}, expires_delta=access_token_expires
    )
    return {'access_token': access_token, 'token_type': 'bearer'}

@app.post('/logout')
async def logout():
    # For JWT, logout is handled client-side by removing the token
    return {'message': 'Logged out successfully'}

@app.get('/users/me', response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # Create UserResponse from current_user data, excluding sensitive fields
    user_data = {
        'id': current_user.id,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'role': current_user.role,
        'created_at': current_user.created_at,
        'updated_at': current_user.updated_at
    }
    return UserResponse(**user_data)

@app.put('/users/me', response_model=dict)
async def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_active_user)):
    users_collection = await get_users_collection()

    update_data = {}
    if user_update.email:
        # Check if email is already taken
        existing = await users_collection.find_one({'email': user_update.email})
        if existing and str(existing['_id']) != current_user.id:
            raise HTTPException(status_code=400, detail='Email already taken')
        update_data['email'] = user_update.email
    if user_update.password:
        update_data['password_hash'] = get_password_hash(user_update.password)
    if user_update.full_name:
        update_data['full_name'] = user_update.full_name

    if update_data:
        update_data['updated_at'] = datetime.utcnow()
        from bson import ObjectId
        await users_collection.update_one({'_id': ObjectId(current_user.id)}, {'$set': update_data})

    return {'message': 'Profile updated successfully'}

@app.get('/admin/users', response_model=list[UserResponse])
async def get_pending_users(current_user: User = Depends(get_current_admin_user)):
    users_collection = await get_users_collection()

    users = []
    async for user_doc in users_collection.find({'role': 'pending'}):
        # Convert ObjectId to string and set as id field
        user_doc['id'] = str(user_doc['_id'])
        del user_doc['_id']  # Remove _id field
        users.append(UserResponse(**user_doc))
    return users

@app.post('/admin/approve/{user_id}')
async def approve_user(user_id: str, current_user: User = Depends(get_current_admin_user)):
    users_collection = await get_users_collection()

    from bson import ObjectId
    result = await users_collection.update_one(
        {'_id': ObjectId(user_id), 'role': 'pending'},
        {'$set': {'role': 'approved', 'updated_at': datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail='User not found or already approved')
    return {'message': 'User approved successfully'}

@app.delete('/admin/user/{user_id}')
async def delete_user(user_id: str, current_user: User = Depends(get_current_admin_user)):
    users_collection = await get_users_collection()

    from bson import ObjectId
    result = await users_collection.delete_one({'_id': ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='User not found')
    return {'message': 'User deleted successfully'}

@app.get('/admin/all-users', response_model=list[UserResponse])
async def get_all_users(current_user: User = Depends(get_current_admin_user)):
    users_collection = await get_users_collection()

    users = []
    async for user_doc in users_collection.find():
        # Convert ObjectId to string and set as id field
        user_doc['id'] = str(user_doc['_id'])
        del user_doc['_id']  # Remove _id field
        users.append(UserResponse(**user_doc))
    return users

@app.post('/upload')
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    print('Received file upload request')
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail='File must be Excel format')

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
    print('Columns found:', df.columns.tolist())

    # Map common variants to canonical column names so downstream code can rely on them
    guardian_col = None
    student_col = None
    result_col = None
    for c in df.columns:
        lc = c.lower()
        # More flexible result column detection
        if 'result' in lc or 'message' in lc or 'sms' in lc:
            result_col = c
        # More flexible guardian phone detection
        if ('guardian' in lc or 'parent' in lc or 'father' in lc or 'mother' in lc) and ('phone' in lc or 'mobile' in lc or 'contact' in lc):
            guardian_col = c
        # More flexible student phone detection
        if ('student' in lc or 'pupil' in lc) and ('phone' in lc or 'mobile' in lc or 'contact' in lc):
            student_col = c

    if result_col is None:
        raise HTTPException(status_code=400, detail=f'Excel must have a Result column. Found: {df.columns.tolist()}')

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
    # Replace NaN with None for JSON serialization and convert phone numbers to strings
    for row in data:
        for key, value in row.items():
            if pd.isna(value):
                row[key] = None
            elif isinstance(value, float) and value == int(value):
                # Convert float phone numbers to strings (remove .0)
                row[key] = str(int(value))
            elif key in ['Guardian Phone No', 'Student Phone No'] and value is not None:
                # Ensure phone numbers are strings
                row[key] = str(value)

        print(f'Extracted {len(data)} rows')
    return {'data': data}

@app.post('/send-sms')
async def send_sms(request: dict, current_user: User = Depends(get_current_active_user)):
    data = request.get('data', [])
    selected_indices = request.get('selectedIndices', None)  # Optional: indices of selected rows

    sent_count = 0
    failed_count = 0
    failed_recipients = []  # Track failed recipients
    successful_recipients = []  # Track successful recipients

    # BulkSMS BD API configuration
    api_key = os.getenv('SMS_API_KEY')
    api_url = os.getenv('SMS_API_URL', 'http://bulksmsbd.net/api/smsapi')
    sender_id = os.getenv('SMS_SENDER_ID', '8809617624071')
    sms_dry_run = os.getenv('SMS_DRY_RUN', 'false').lower() in ('1', 'true', 'yes')

    if not api_key:
        return {'message': 'SMS API key not configured'}

    print(f'send-sms called with {len(data)} items')
    if selected_indices:
        print(f'Selected indices: {selected_indices}')

    # Filter data if specific indices are selected
    if selected_indices is not None:
        filtered_data = [data[i] for i in selected_indices if i < len(data)]
    else:
        filtered_data = data

    print(f'Processing {len(filtered_data)} items for SMS')

    # Send individual SMS to each phone number
    for item in filtered_data:
        sms_text = item.get('Result')
        if not sms_text:
            failed_count += 1
            failed_recipients.append(item)
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

        # If no phones to send, mark as failed
        if not phones_to_send:
            failed_count += 1
            failed_recipients.append(item)
            continue

        # Send individual SMS to each phone number
        item_failed = True  # Assume failed until proven successful
        valid_phones = []  # Track valid phones for this item
        
        for phone in phones_to_send:
            print(f'Processing phone: {phone}')

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

            print(f'Normalized phone: {norm_phone}')

            # Validate phone number length (must be at least 11 digits for Bangladesh)
            if len(norm_phone) < 11:
                print(f'Phone number too short: {norm_phone} (length: {len(norm_phone)})')
                continue  # Skip this phone, try next one

            valid_phones.append(norm_phone)

            try:
                # BulkSMS BD API format - individual SMS to each phone
                payload = {
                    'api_key': api_key,
                    'senderid': sender_id,
                    'number': norm_phone,
                    'message': str(sms_text)
                }

                if sms_dry_run:
                    print('DRY RUN enabled - would POST to', api_url, 'with:')
                    print(payload)
                    sent_count += 1
                    item_failed = False  # At least one phone succeeded
                else:
                    response = requests.post(api_url, data=payload, timeout=30)
                    print(f'SMS API response status: {response.status_code}')
                    print(f'Response body: {response.text}')

                    if response.status_code == 200:
                        try:
                            result = response.text.strip()

                            # Check if it's JSON response
                            if result.startswith('{'):
                                import json
                                json_result = json.loads(result)

                                # Check for IP whitelisting error
                                if json_result.get('response_code') == 1032 or 'not Whitelisted' in str(json_result.get('error_message', '')):
                                    print(f'IP Whitelisting error for {norm_phone}: {json_result.get('error_message')}')
                                    continue

                                # Check for success
                                if json_result.get('response_code') == 1001 or 'success' in str(json_result.get('success_message', '')).lower():
                                    sent_count += 1
                                    item_failed = False  # At least one phone succeeded
                                    print(f'SMS sent successfully to {norm_phone}')
                                else:
                                    print(f'Failed to send SMS to {norm_phone}: {json_result}')
                            else:
                                # Check BulkSMS BD text response format
                                if result and 'success' in result.lower():
                                    sent_count += 1
                                    item_failed = False  # At least one phone succeeded
                                    print(f'SMS sent successfully to {norm_phone}')
                                elif result and any(code in result for code in ['1001', '200', '201']):
                                    sent_count += 1
                                    item_failed = False  # At least one phone succeeded
                                    print(f'SMS sent successfully to {norm_phone}')
                                else:
                                    print(f'Failed to send SMS to {norm_phone}: {result}')
                        except Exception as e:
                            print(f'Error parsing response: {e}')
                            # If we can't parse, check for common success indicators
                            response_text = response.text.lower()
                            if 'not whitelisted' in response_text:
                                print(f'IP Whitelisting error for {norm_phone}')
                            elif any(indicator in response_text for indicator in ['success', 'sent', 'ok', '1001']):
                                sent_count += 1
                                item_failed = False  # At least one phone succeeded
                                print(f'SMS sent successfully to {norm_phone}')
                            else:
                                print(f'Failed to send SMS to {norm_phone}: {response.text}')
                    else:
                        print(f'API request failed with status {response.status_code}: {response.text}')

            except Exception as e:
                print(f'Error sending SMS to {norm_phone}: {e}')

        # If no valid phones were found for this item, mark as failed
        if not valid_phones:
            failed_count += 1
            failed_recipients.append(item)
        # If all phones failed for this item, add to failed recipients
        elif item_failed:
            failed_count += 1
            failed_recipients.append(item)
        # If item was successful, add to successful recipients
        else:
            successful_recipients.append(item)

    # Return response with recipients data
    response_data = {
        'message': f'SMS sent to {sent_count} numbers. Failed: {failed_count}',
        'sent_count': sent_count,
        'failed_count': failed_count
    }
    
    # Include successful recipients if there are any
    if successful_recipients:
        response_data['successful_recipients'] = successful_recipients
    
    # Include failed recipients if there are any
    if failed_recipients:
        response_data['failed_recipients'] = failed_recipients

    return response_data

@app.post("/export-excel")
async def export_excel(request: dict, current_user: User = Depends(get_current_active_user)):
    """
    Export data to two separate Excel files in a ZIP:
    1. Success.xlsx - numbers that would successfully receive SMS
    2. Failed.xlsx - numbers that would fail to receive SMS
    """
    from fastapi.responses import StreamingResponse
    import pandas as pd
    from io import BytesIO
    import os
    import zipfile
    from datetime import datetime

    data = request.get('data', [])

    # Simulate SMS sending to categorize success/failure
    success_recipients = []
    failed_recipients = []

    for item in data:
        sms_text = item.get('Result')
        if not sms_text:
            # No SMS text, add to failed
            failed_recipients.append(item)
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

        # If no valid phones, add to failed
        if not phones_to_send:
            failed_recipients.append(item)
            continue

        # Simulate SMS sending for each phone
        item_success = False
        valid_phones = []
        
        for phone in phones_to_send:
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

            # Validate phone number length (must be at least 11 digits)
            if len(norm_phone) >= 11:
                valid_phones.append(norm_phone)
                item_success = True
                break  # If any phone is valid, consider the whole item successful

        # If no valid phones found, mark as failed
        if not valid_phones:
            failed_recipients.append(item)

    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create ZIP file containing both Excel files
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Create Success Excel file
        if success_recipients:
            success_output = BytesIO()
            df_success = pd.DataFrame(success_recipients)
            df_success.to_excel(success_output, index=False, engine='xlsxwriter')
            success_output.seek(0)
            zip_file.writestr(f'Success_{timestamp}.xlsx', success_output.read())
        else:
            # Create empty success file
            success_output = BytesIO()
            pd.DataFrame(columns=['No Successful Recipients Found']).to_excel(success_output, index=False, engine='xlsxwriter')
            success_output.seek(0)
            zip_file.writestr(f'Success_{timestamp}.xlsx', success_output.read())

        # Create Failed Excel file
        if failed_recipients:
            failed_output = BytesIO()
            df_failed = pd.DataFrame(failed_recipients)
            df_failed.to_excel(failed_output, index=False, engine='xlsxwriter')
            failed_output.seek(0)
            zip_file.writestr(f'Failed_{timestamp}.xlsx', failed_output.read())
        else:
            # Create empty failed file
            failed_output = BytesIO()
            pd.DataFrame(columns=['No Failed Recipients Found']).to_excel(failed_output, index=False, engine='xlsxwriter')
            failed_output.seek(0)
            zip_file.writestr(f'Failed_{timestamp}.xlsx', failed_output.read())

    zip_buffer.seek(0)

    # Return ZIP file as download
    zip_filename = f"SMS_Categorized_{timestamp}.zip"
    return StreamingResponse(
        BytesIO(zip_buffer.read()),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )

@app.post("/download-success")
async def download_success(request: dict, current_user: User = Depends(get_current_active_user)):
    """
    Download successful recipients as Excel file after SMS sending
    """
    from fastapi.responses import StreamingResponse
    import pandas as pd
    from io import BytesIO
    from datetime import datetime

    successful_recipients = request.get('successful_recipients', [])

    if not successful_recipients:
        # Return empty Excel if no successful recipients
        output = BytesIO()
        pd.DataFrame(columns=['No Successful Recipients']).to_excel(output, index=False, engine='xlsxwriter')
        output.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"No_Successful_Recipients_{timestamp}.xlsx"
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # Create Excel file with successful recipients
    output = BytesIO()
    df_success = pd.DataFrame(successful_recipients)
    df_success.to_excel(output, index=False, engine='xlsxwriter')
    output.seek(0)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Successful_Recipients_{timestamp}.xlsx"

    # Return file as download
    return StreamingResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/download-failed")
async def download_failed(request: dict, current_user: User = Depends(get_current_active_user)):
    """
    Download failed recipients as Excel file after SMS sending
    """
    from fastapi.responses import StreamingResponse
    import pandas as pd
    from io import BytesIO
    from datetime import datetime

    failed_recipients = request.get('failed_recipients', [])

    if not failed_recipients:
        # Return empty Excel if no failed recipients
        output = BytesIO()
        pd.DataFrame(columns=['No Failed Recipients']).to_excel(output, index=False, engine='xlsxwriter')
        output.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"No_Failed_Recipients_{timestamp}.xlsx"
        return StreamingResponse(
            BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # Create Excel file with failed recipients
    output = BytesIO()
    df_failed = pd.DataFrame(failed_recipients)
    df_failed.to_excel(output, index=False, engine='xlsxwriter')
    output.seek(0)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Failed_Recipients_{timestamp}.xlsx"

    # Return file as download
    return StreamingResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
