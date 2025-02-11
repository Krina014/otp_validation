import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, root_validator
from database import users_collection
from typing import Optional
import pytz
from email_validator import EmailNotValidError, validate_email
import base64
import os
from fastapi import Depends, Security, status
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv


# for authentication
load_dotenv()  # Load environment variables
API_KEY = os.getenv("KEY", "default_value")  # Store your API key as an environment variable
API_KEY_NAME = "OTP-KEY"  # The header name for the API key
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return API_KEY

router = APIRouter(
    prefix='/otp', 
    tags=['otp'],
    dependencies=[Depends(get_api_key)]
)

OTP_EXPIRE_TIME = 5  # OTP expires in 5 minutes

# Define Indian Standard time
IST = pytz.timezone("Asia/Kolkata")

class UserField(BaseModel):
    userId: str
    emailTo: Optional[str] = None
    smsTo: Optional[int] = None
    voiceTo: Optional[int] = None
    smsISDCode: Optional[int] = None
    voiceISDCode: Optional[int] = None
    emailTemplateB64: Optional[str] = None
    emailSubject: Optional[str] = None
    smsTemplateB64: Optional[str] = None
    smsTemplateId: Optional[int] = None
    
    # for format validations

    @root_validator(pre=True)
    def convert_sms_to_string(cls, values):
        # Ensure userId is present
        if 'userId' not in values or values['userId'] is None:
            raise HTTPException(status_code=400, detail="userId is mandatory")
        # Convert userId to string (ensures it can be both int or str)
        values['userId'] = str(values['userId'])
        
        # Validate email format
        if 'emailTo' in values and values['emailTo'] is not None:
            try:
                validate_email(values['emailTo'], check_deliverability=False)  # Only check format, not deliverability
            except EmailNotValidError as e:
                raise HTTPException(status_code=400, detail=f"Invalid email format: {str(e)}")
            
        if 'smsTo' in values and values['smsTo'] is not None:
            # Convert smsTo to string and check if it's a valid phone number
            sms_to_str = str(values['smsTo'])
            if not sms_to_str.isdigit() or len(sms_to_str) != 10:
                raise HTTPException(status_code=400, detail="smsTo must be a 10-digit number")
            values['smsTo'] = sms_to_str  # Convert back to string
            
        if 'voiceTo' in values and values['voiceTo'] is not None:
            # Convert voiceTo to string and check if it's a valid phone number
            voice_to_str = str(values['voiceTo'])
            if not voice_to_str.isdigit() or len(voice_to_str) != 10:
                raise HTTPException(status_code=400, detail="voiceTo must be a 10-digit number")
            values['voiceTo'] = voice_to_str  # Convert back to string
            
        if 'smsISDCode' in values and values['smsISDCode'] is not None:
            smsISDCode_to_str = str(values['smsISDCode'])
            if not smsISDCode_to_str.isdigit():
                raise HTTPException(status_code=400, detail="smsISDCode must be integer")
            values['smsISDCode'] = smsISDCode_to_str  # Convert back to string
            
        if 'voiceISDCode' in values and values['voiceISDCode'] is not None:
            voiceISDCode_to_str = str(values['voiceISDCode'])
            if not voiceISDCode_to_str.isdigit():
                raise HTTPException(status_code=400, detail="voiceISDCode must be integer")
            values['voiceISDCode'] = voiceISDCode_to_str  # Convert back to string
            
        if 'smsTemplateId' in values and values['smsTemplateId'] is not None:
            smsTemplateId_to_str = str(values['smsTemplateId'])
            if not smsTemplateId_to_str.isdigit():
                raise HTTPException(status_code=400, detail="smsTemplateId must be integer")
            values['smsTemplateId'] = smsTemplateId_to_str  # Convert back to string
            
        return values

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(str(secrets.randbelow(10)) for _ in range(6))

# Function to encode SMS template with OTP
def encode_sms_with_otp(template: str, otp: str):
    """Replace {{otp}} with actual OTP and encode to Base64"""
    updated_template = template.replace("{{otp}}", f"{{{otp}}}")  # Replace with {{123456}}
    encoded_template = base64.b64encode(updated_template.encode("utf-8")).decode("utf-8")
    return encoded_template

# Function to encode email template with OTP
def encode_email_with_otp(template: str, otp: str):
    """Replace {{otp}} with actual OTP and encode to Base64"""
    updated_template = template.replace("{{otp}}", f"{{{otp}}}")  # Replace with {{123456}}
    encoded_template = base64.b64encode(updated_template.encode("utf-8")).decode("utf-8")
    return encoded_template
    
# Create user and generate OTP token
@router.post("/create_otp")
async def create_otp(user: UserField):
    """_summary_

    **Mandatory Parameter**: \n
        userId (int): It should be integer
        
    **Atleast one compulsory Identifier:** \n
        emailTo : It should be integer, \n
        smsTo : It should be integer, \n
        voiceTo : It should be integer
        
    **Optional Parameters(atleast one is mandatory):** \n
        Others are optional parameters \n
        
    **Raises**: \n
        HTTPException: "userId is mandatory"
        HTTPException: "Invalid user ID"
        HTTPException: "Please provide at least one identifier"
        HTTPException: "User ID already exists"
        HTTPException: "Error while saving user"

    **Returns**: \n
        Detail: User created successfully
    """
        
        
    # atleast one mandatory field
        
    identifiers = [user.emailTo, user.smsTo, user.voiceTo]
    provided_identifiers = [id for id in identifiers if id is not None]
    if not provided_identifiers:
        raise HTTPException(status_code=400, detail="Please provide at least one identifier")


    otp = generate_otp()
    
    # Encode SMS Template if provided
    encoded_sms_template = None
    if user.smsTemplateB64:
        if "{{otp}}" in user.smsTemplateB64:
            encoded_sms_template = encode_sms_with_otp(user.smsTemplateB64, otp)
        else:
            var = " {{otp}}"
            smsTemplate = user.smsTemplateB64+var
            encoded_sms_template = encode_sms_with_otp(smsTemplate, otp)
            
    # Encode email Template if provided
    encoded_email_template = None
    if user.emailTemplateB64:
        if "{{otp}}" in user.emailTemplateB64:
            encoded_email_template = encode_sms_with_otp(user.emailTemplateB64, otp)
        else:
            var = " {{otp}}"
            emailTemplate = user.emailTemplateB64+var
            encoded_email_template = encode_sms_with_otp(emailTemplate, otp)

    # Convert expiry time to IST
    otp_expiry_utc = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_TIME)
    otp_expiry_ist = otp_expiry_utc.replace(tzinfo=pytz.utc).astimezone(IST)


    new_user = {
        "userId": user.userId,
        "emailTemplateB64": encoded_sms_template,
        "smsTemplateB64": encoded_email_template,
        "otp": otp,
        "otp_expiry": otp_expiry_ist.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if user.emailTo is not None:
        new_user["emailTo"] = user.emailTo
        
    if user.smsTo is not None:
        new_user["smsTo"] = user.smsTo
        
    if user.voiceTo is not None:
        new_user["voiceTo"] = user.voiceTo
        
    if user.smsISDCode is not None and user.smsISDCode != 0:
        new_user["smsISDCode"] = user.smsISDCode

    if user.voiceISDCode is not None and user.voiceISDCode != 0:
        new_user["voiceISDCode"] = user.voiceISDCode
        
    if user.smsTemplateId is not None and user.smsTemplateId != 0:
        new_user["smsTemplateId"] = user.smsTemplateId
        
    if user.emailSubject is not None and user.emailSubject != "string":
        new_user["emailSubject"] = user.emailSubject
        
    
    
    # if userId is already exist
    exist_user_id = users_collection.find_one({"userId": user.userId})
    if exist_user_id:
        # Replace the existing user's OTP and expiry time
        updated_user = {
            "otp": otp,
            "otp_expiry": otp_expiry_ist.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Only update additional fields if they are not None
        if user.smsTemplateB64:
            updated_user["smsTemplateB64"] = encoded_sms_template
        if user.emailTemplateB64:
            updated_user["emailTemplateB64"] = encoded_email_template

        if user.emailTo is not None:
            updated_user["emailTo"] = user.emailTo
        if user.smsTo is not None:
            updated_user["smsTo"] = user.smsTo
        if user.voiceTo is not None:
            updated_user["voiceTo"] = user.voiceTo
        if user.smsISDCode is not None and user.smsISDCode != 0:
            updated_user["smsISDCode"] = user.smsISDCode
        if user.voiceISDCode is not None and user.voiceISDCode != 0:
            updated_user["voiceISDCode"] = user.voiceISDCode
        if user.smsTemplateId is not None and user.smsTemplateId != 0:
            updated_user["smsTemplateId"] = user.smsTemplateId
        if user.emailSubject is not None and user.emailSubject != "string":
            updated_user["emailSubject"] = user.emailSubject

        # Update the document with new OTP and expiry time
        users_collection.update_one({"userId": user.userId}, {"$set": updated_user})
        
        return {"detail": "OTP updated successfully", "user_id": user.userId}
    
    try:
        users_collection.insert_one(new_user)
        return {"detail": "OTP created successfully", "user_id": user.userId}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while saving user: {e}")
    

# Verify OTP using JWT token
@router.post("/varify_otp")
async def verify_otp(userId: str, user_otp: str):
    
    """

    **Varification of the user:** \n 

    **Raises:** \n
        HTTPException: "User not found"
        HTTPException: "No such OTP like this have found"
        HTTPException: "OTP expiry time is missing"
        HTTPException: "Invalid OTP expiry format in database"
        HTTPException: "OTP expired"
        HTTPException: "Invalid OTP"

    **Returns:**
        detail: "User Authenticated successfully"
    """
    
    
    valid_user = users_collection.find_one({"userId": userId})

    if not valid_user:
        raise HTTPException(status_code=400, detail="User not found")

    stored_otp = valid_user.get("otp")  # Retrieve OTP from DB
    otp_expiry_str = valid_user.get("otp_expiry")  # OTP expiration time from DB
    
    # to get otps stored in database
    db_otp = users_collection.find_one({"otp": user_otp})

    if not db_otp:
        raise HTTPException(status_code=400, detail="No such OTP like this have found")
    
    # Check if OTP expiry string is missing or invalid
    if not otp_expiry_str:
        raise HTTPException(status_code=400, detail="OTP expiry time is missing")

    # Convert OTP expiry string to datetime object in IST
    try:
        otp_expiry_ist = datetime.strptime(otp_expiry_str, "%Y-%m-%d %H:%M:%S")
        otp_expiry_ist = pytz.utc.localize(otp_expiry_ist).astimezone(IST)  # Convert to IST
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid OTP expiry format in database")

    # Get the current time in IST
    otp_expiry_ist = IST.localize(datetime.strptime(otp_expiry_str, "%Y-%m-%d %H:%M:%S"))
    current_time_ist = datetime.now(IST)
    
    if current_time_ist > otp_expiry_ist:
        raise HTTPException(status_code=400, detail="OTP expired")

    # If OTP is valid, compare with the user input OTP
    if stored_otp == user_otp:
        users_collection.delete_one({"_id": valid_user["_id"]})
        return {"detail": "User Authenticated successfully"}
    else:
        return {"detail": "Invalid OTP"}