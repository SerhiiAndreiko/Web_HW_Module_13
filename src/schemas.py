from datetime import date, datetime

from pydantic import BaseModel, Field, EmailStr

from src.database.models import Role

class ContactBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birth_date: date
    additional_data: str = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birth_date: date
    additional_data: str = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
class UserModel(BaseModel):
    username: str = Field(min_length=6, max_length=12)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    roles: Role

    class Config:
        from_attributes = True


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RequestEmail(BaseModel):
    email: EmailStr