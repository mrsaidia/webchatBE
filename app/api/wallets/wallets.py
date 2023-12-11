from fastapi import APIRouter, HTTPException, Depends
from app.core.database import database
from app.api.auth.accesstoken import create_access_token
from app.api.auth.accesstoken import verify_access_token
from app.api.auth.dependencies import get_current_user
from app.api.wallets.models import WalletCreateModel, TransferModel
from typing import List
from bson import ObjectId, json_util


router = APIRouter()

# Định nghĩa MongoDB collection
user_collection = database.get_collection("wallets")


@router.post("/create-wallet")
async def create_wallet(
    wallet_data: WalletCreateModel, current_user_id: str = Depends(get_current_user)
):
    print("check here")
    # Kiểm tra xem người dùng đã có ví chưa
    existing_wallet = await user_collection.find_one(
        {"user_id": current_user_id["user_id"]}
    )
    print("check here")
    if existing_wallet:
        raise HTTPException(status_code=400, detail="Wallet already exists")

    # kiểm tra current_user_id có phải là người dùng mới không ( chuyển sang string rồi kiểm tra)
    if str(current_user_id["user_id"]) != str(wallet_data.user_id):
        raise HTTPException(status_code=400, detail="You are not the owner")

    # Xử lý tạo ví mới
    new_wallet = {"user_id": str(wallet_data.user_id), "balance": wallet_data.balance}
    inserted_wallet = await user_collection.insert_one(new_wallet)

    # Chuyển đổi ObjectId thành chuỗi
    new_wallet_id = str(inserted_wallet.inserted_id)
    new_wallet["_id"] = new_wallet_id

    return {"message": "Wallet created successfully", "wallet": new_wallet}


@router.post("/transfer")
async def transfer_money(
    transfer_data: TransferModel, current_user_id: str = Depends(get_current_user)
):
    # Kiểm tra người gửi có tồn tại không
    existing_sender = await user_collection.find_one(
        {"user_id": str(transfer_data.sender_wallet_id)}
    )

    if not existing_sender:
        raise HTTPException(status_code=400, detail="Sender wallet does not exist")

    # Kiểm tra người nhận có tồn tại không
    existing_receiver = await user_collection.find_one(
        {"user_id": str(transfer_data.receiver_wallet_id)}
    )
    if not existing_receiver:
        raise HTTPException(status_code=400, detail="Receiver wallet does not exist")

    # kiểm tra current_user_id có phải là người gửi không ( chuyển sang string rồi kiểm tra)
    if str(current_user_id["user_id"]) != str(existing_sender["user_id"]):
        raise HTTPException(status_code=400, detail="You are not the sender")

    # Kiểm tra số dư ví người gửi
    sender_wallet = await user_collection.find_one(
        {"user_id": str(transfer_data.sender_wallet_id)}
    )

    if sender_wallet and sender_wallet["balance"] >= transfer_data.amount:
        # Trừ tiền từ ví người gửi
        await user_collection.update_one(
            {"user_id": str(transfer_data.sender_wallet_id)},
            {"$inc": {"balance": -transfer_data.amount}},
        )
        # Cộng tiền vào ví người nhận
        await user_collection.update_one(
            {"user_id": str(transfer_data.receiver_wallet_id)},
            {"$inc": {"balance": transfer_data.amount}},
        )
        return {"message": "Transfer successful"}
    else:
        raise HTTPException(status_code=400, detail="Insufficient funds")


@router.get("/get-wallet")
async def get_wallet(current_user_id: str = Depends(get_current_user)):
    # Kiểm tra người dùng có ví không
    existing_wallet = await user_collection.find_one(
        {"user_id": current_user_id["user_id"]}
    )
    if existing_wallet:
        return {
            "wallet": str(existing_wallet["_id"]),
            "balance": existing_wallet["balance"],
        }
    else:
        raise HTTPException(status_code=400, detail="Wallet does not exist")
