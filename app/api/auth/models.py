from pydantic import BaseModel


class RegistrationRequest(BaseModel):
    email: str
    verification_code: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    access_token: str


class EmailRequest(BaseModel):
    email: str
