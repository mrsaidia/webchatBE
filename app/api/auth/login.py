# # app/api/auth/register.py
# from fastapi import APIRouter, HTTPException
# from motor.motor_asyncio import AsyncIOMotorClient
# from app.core.database import database
# from app.api.auth.models import UserLogin, User
# from app.api.auth.accesstoken import create_access_token

# from app.api.auth.accesstoken import verify_access_token

# import hashlib

# router = APIRouter()

# # Define the MongoDB collection
# user_collection = database.get_collection("users")


# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()


# async def check_info_login(username, password):
#     user = await user_collection.find_one({"username": username})
#     if user:
#         if user["password"] == hash_password(password):
#             return True
#         else:
#             return False
#     else:
#         return False


# @router.get("/login")
# async def login(user: UserLogin):
#     # Hash the password before saving it to the database (you should never save passwords in plain text)
#     # You can use the security module from your core folder for password hashing
#     # Check user
#     if not await check_info_login(user.username, user.password):
#         raise HTTPException(status_code=400, detail="Incorrect username or password")
#     # return message susscess and access_token
#     access_token = create_access_token(user.username)
#     # return access_token and user_id
#     return {"access_token": access_token, "user_id": user.username}


# @router.get("/verify")
# async def verify(user: User):
#     if not verify_access_token(user.access_token):
#         raise HTTPException(status_code=400, detail="Token is invalid")
#     return {"message": "Token is valid"}


from fastapi import APIRouter, HTTPException
from app.core.database import database
from app.api.auth.models import (
    UserLogin,
    User,
)  # Đảm bảo UserLogin có trường email và password
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
import hashlib

router = APIRouter()

# Định nghĩa MongoDB collection
user_collection = database.get_collection("users")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


async def check_user_login(email, password):
    user = await user_collection.find_one({"email": email})
    if user and user["password"] == hash_password(password):
        return True
    return False


@router.post("/login")  # Sử dụng POST thay vì GET cho đăng nhập
async def login(user: UserLogin):
    # Kiểm tra thông tin đăng nhập
    if not await check_user_login(user.email, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # find userId
    user = await user_collection.find_one({"email": user.email})
    if user:
        user_id = str(user["_id"])
    else:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Tạo và trả về access token
    access_token = create_access_token({"user_id": user_id})
    return {
        "access_token": access_token,
        "user_id": user_id,
    }


@router.get("/verify")
async def verify(user: User):
    if not verify_access_token(user.access_token):
        raise HTTPException(status_code=400, detail="Token is invalid")
    return {"message": "Token is valid"}
