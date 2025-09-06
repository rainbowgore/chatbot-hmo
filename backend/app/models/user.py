from pydantic import BaseModel, Field
from typing import Optional, List

class UserInfoRequest(BaseModel):
    message: str

class ChatRequest(BaseModel):
    user_info: dict
    message: str
    history: List[dict] = []

class UserProfile(BaseModel):
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    id_number: Optional[str] = Field(default="", description="9-digit ID")
    gender: Optional[str] = ""
    age: Optional[int] = None
    hmo: Optional[str] = ""
    hmo_card_number: Optional[str] = Field(default="", description="9-digit HMO card")
    membership_tier: Optional[str] = ""
    confirmed: bool = False  # To mark if user confirmed their details

class ChatResponse(BaseModel):
    status: str
    answer: str
    user_info_used: dict
    history_length: int
