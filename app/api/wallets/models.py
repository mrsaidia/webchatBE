from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List, Optional


class WalletCreateModel(BaseModel):
    user_id: str
    balance: float


class TransferModel(BaseModel):
    sender_wallet_id: str
    receiver_wallet_id: str
    amount: float
