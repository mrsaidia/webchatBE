# app/api/auth/register.py

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import database
from app.api.auth.models import UserLogin
from app.api.auth.accesstoken import create_access_token

from app.api.auth.accesstoken import verify_access_token

import hashlib

router = APIRouter()

# Define the MongoDB collection
user_collection = database.get_collection("users")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


async def check_info_login(username, password):
    user = await user_collection.find_one({"username": username})
    if user:
        if user["password"] == hash_password(password):
            return True
        else:
            return False
    else:
        return False


@router.get("/login")
async def login(user: UserLogin):
    # Hash the password before saving it to the database (you should never save passwords in plain text)
    # You can use the security module from your core folder for password hashing
    # Check user
    if not await check_info_login(user.username, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # return message susscess and access_token
    access_token = create_access_token(user.username)
    return {"message": "Login success", "access_token": access_token}


@router.get("/verify")
async def verify(token: str):
    print("Verifying...")
    if not verify_access_token(token):
        raise HTTPException(status_code=400, detail="Token is invalid")
    return {"message": "Token is valid"}
