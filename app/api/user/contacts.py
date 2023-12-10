from fastapi import APIRouter, HTTPException, Depends
from app.core.database import database
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
from app.api.auth.dependencies import get_current_user
from app.api.user.models import FriendRequestModel
from app.api.user.models import FriendListModel
from app.api.user.models import AcceptFriendRequestModel
from app.api.user.models import RejectFriendRequestModel
from typing import List
from bson import ObjectId, json_util

router = APIRouter()

# Định nghĩa MongoDB collection
user_collection = database.get_collection("contacts")


@router.post("/send-friend-request")
async def send_friend_request(
    request: FriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    if request.receiver_id == current_user_id["user_id"]:
        raise HTTPException(
            status_code=400, detail="Cannot send friend request to yourself."
        )

    # Lưu lời mời kết bạn vào cơ sở dữ liệu
    existing_request = await user_collection.find_one(
        {
            "sender_id": current_user_id["user_id"],
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
    request: AcceptFriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    if request.receiver_id != current_user_id["user_id"]:
        raise HTTPException(
            status_code=400, detail="Cannot accept friend request sent to someone else."
        )

    # find friend request
    friend_request = await user_collection.find_one(
        {
            "sender_id": request.sender_id,
            "receiver_id": request.receiver_id,
            "status": "pending",
        }
    )

    # update friend request
    if friend_request:
        await user_collection.update_one(
            {"_id": friend_request["_id"]},
            {"$set": {"status": "accepted"}},
        )
    else:
        raise HTTPException(status_code=400, detail="Friend request not found.")

    return {"message": "Friend request accepted."}


@router.post("/reject-friend")
async def reject_friend_request(
    request: RejectFriendRequestModel, current_user_id: str = Depends(get_current_user)
):
    # check current user is receiver
    if (
        request.receiver_id != current_user_id["user_id"]
        and request.sender_id != current_user_id["user_id"]
    ):
        raise HTTPException(
            status_code=400, detail="Cannot reject friend request sent to someone else."
        )

    # Xóa lời mời kết bạn khỏi cơ sở dữ liệu
    await user_collection.delete_one(
        {"sender_id": request.sender_id, "receiver_id": request.receiver_id}
    )
    await user_collection.delete_one(
        {"sender_id": request.receiver_id, "receiver_id": request.sender_id}
    )

    return {"message": "Friend request rejected."}


async def get_friends_list(user_id: str):
    friends_list = []
    # Lấy danh sách lời mời kết bạn
    friend_requests = await user_collection.find(
        {"sender_id": user_id, "status": "pending"}
    ).to_list(length=1000)

    # Lấy danh sách bạn bè
    friends = await user_collection.find(
        {
            "$or": [{"sender_id": user_id}, {"receiver_id": user_id}],
            "status": "accepted",
        }
    ).to_list(length=1000)

    return friends_list


@router.get("/get-all-friends/{user_id}")
async def get_all_friends(current_user_id: str = Depends(get_current_user)):
    user_id = current_user_id["user_id"]
    # Lấy thông tin người dùng hiện tại
    user = await database.users.find_one({"_id": ObjectId(current_user_id["user_id"])})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    friends_list = await get_friends_list(current_user_id["user_id"])

    return friends_list
