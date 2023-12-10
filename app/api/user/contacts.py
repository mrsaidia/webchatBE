from fastapi import APIRouter, HTTPException, Depends
from app.core.database import database
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
from app.api.auth.dependencies import get_current_user
from app.api.user.models import FriendRequestModel
from app.api.user.models import FriendListModel
from typing import List

router = APIRouter()

# Định nghĩa MongoDB collection
user_collection = database.get_collection("contacts")


@router.post("/send-friend-request")
async def send_friend_request(
    request: FriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    if request.receiver_id == current_user_id:
        raise HTTPException(
            status_code=400, detail="Cannot send friend request to yourself."
        )

    # Lưu lời mời kết bạn vào cơ sở dữ liệu
    existing_request = await user_collection.find_one(
        {
            "sender_id": current_user_id,
            "receiver_id": request.receiver_id,
            "status": "pending",
        }
    )
    if existing_request:
        raise HTTPException(status_code=400, detail="Friend request already sent.")
    await user_collection.insert_one(
        {"sender_id": current_user_id["user_id"], **request.dict()}
    )
    return {"message": "Friend request sent successfully."}


@router.post("/accept-friend-request")
async def accept_friend_request(
    request: FriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    if request.receiver_id != current_user_id:
        raise HTTPException(
            status_code=400, detail="Cannot accept friend request sent to someone else."
        )

    # Cập nhật danh sách bạn bè của cả hai người dùng
    await user_collection.update_one(
        {"user_id": request.sender_id},
        {"$push": {"friend_ids": request.receiver_id}},
        {"$set": {"status": "accepted"}},
        upsert=True,
    )
    await user_collection.update_one(
        {"user_id": request.receiver_id},
        {"$push": {"friend_ids": request.sender_id}},
        upsert=True,
    )
    return {"message": "Friend request accepted."}


@router.post("/reject-friend-request")
async def reject_friend_request(
    request: FriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    # Xóa lời mời kết bạn khỏi cơ sở dữ liệu
    await user_collection.delete_one(
        {"sender_id": request.sender_id, "receiver_id": request.receiver_id}
    )

    return {"message": "Friend request rejected."}


@router.get("/get-friends/{user_id}", response_model=FriendListModel)
async def get_friends(user_id: str, current_user_id: str = Depends(get_current_user)):
    friends_list = await user_collection.find_one({"user_id": user_id})
    if not friends_list:
        return {"user_id": user_id, "friend_ids": []}
    return friends_list
