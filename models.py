from pydantic import BaseModel

# Pydantic model for user validation
class User(BaseModel): 
    userId: int 
    emailTo: str
    smsTo: int
    voiceTo: int
    smsISDCode: int
    voiceISDCode: int
    emailTemplateB64: str
    emailSubject: str
    smsTemplateB64: str
    smsTemplateId: int