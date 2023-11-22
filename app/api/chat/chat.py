from fastapi import APIRouter, Depends, HTTPException, Form
from app.core.database import database
from .models import MessageModel
from .models import MessageInDB
from .models import conversation
from .models import ImageData
from app.api.auth.dependencies import get_current_user
from datetime import datetime
from fastapi import UploadFile, File
import base64
from PIL import Image
import io
import os
import uuid

router = APIRouter()

messages_collection = database.get_collection("messages")
UPLOAD_DIRECTORY = "./data/"


def get_image_data_from_db(folderPath, image_name):
    """
    Lấy dữ liệu ảnh từ file.

    :param folderPath: Đường dẫn đến thư mục chứa file ảnh.
    :param image_name: Tên file ảnh.
    :return: Dữ liệu ảnh dạng base64.
    """
    # Tạo đường dẫn đến file ảnh
    image_path = os.path.join(folderPath, image_name) + ".png"

    # Đọc dữ liệu ảnh từ file
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Chuyển dữ liệu ảnh thành dạng base64
    image_data_base64 = base64.b64encode(image_data)

    return image_data_base64


def get_audio_data_from_db(folderPath, audio_name):
    """
    Lấy dữ liệu audio từ file.

    :param folderPath: Đường dẫn đến thư mục chứa file audio.
    :param audio_name: Tên file audio.
    :return: Dữ liệu audio dạng base64.
    """
    # Tạo đường dẫn đến file audio
    audio_path = os.path.join(folderPath, audio_name) + ".mp3"

    # Đọc dữ liệu audio từ file
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    # Chuyển dữ liệu audio thành dạng base64
    audio_data_base64 = base64.b64encode(audio_data)

    return audio_data_base64


def get_video_data_from_db(folderPath, video_name):
    """
    Lấy dữ liệu video từ file.

    :param folderPath: Đường dẫn đến thư mục chứa file video.
    :param video_name: Tên file video.
    :return: Dữ liệu video dạng base64.
    """
    # Tạo đường dẫn đến file video
    video_path = os.path.join(folderPath, video_name) + ".mp4"

    # Đọc dữ liệu video từ file
    with open(video_path, "rb") as f:
        video_data = f.read()

    # Chuyển dữ liệu video thành dạng base64
    video_data_base64 = base64.b64encode(video_data)

    return video_data_base64


@router.get("/get-messages", response_model=list[MessageInDB])
async def get_messages(
    chat: conversation,
    sender: str = Depends(get_current_user),
):
    if sender != chat.sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )

    messages = (
        await messages_collection.find(
            {
                "$or": [
                    {"sender": sender, "receiver": chat.receiver},
                    {"sender": chat.receiver, "receiver": sender},
                ]
            }
        )
        .sort("timestamp", 1)
        .to_list(length=100)
    )
    # Xác định đường dẫn lưu trữ dựa trên người gửi và người nhận
    if sender < chat.receiver:
        folderPath = UPLOAD_DIRECTORY + sender + "-" + chat.receiver
    else:
        folderPath = UPLOAD_DIRECTORY + chat.receiver + "-" + sender

    # Lấy danh sách tin nhắn
    messages = await messages_collection.find(
        {"sender": sender, "receiver": chat.receiver}
    ).to_list(length=100)

    # Lấy dữ liệu ảnh từ file
    for message in messages:
        if message["format"] == "image":
            message["content"] = get_image_data_from_db(folderPath, message["content"])

    # Lấy dữ liệu audio từ file
    for message in messages:
        if message["format"] == "audio":
            message["content"] = get_audio_data_from_db(folderPath, message["content"])

    # Lấy dữ liệu video từ file
    for message in messages:
        if message["format"] == "video":
            message["content"] = get_video_data_from_db(folderPath, message["content"])

    return messages


def show_image_from_db(image_data_base64):
    """
    Giải mã dữ liệu ảnh từ base64 và hiển thị ảnh.

    :param image_data_base64: Dữ liệu ảnh được mã hóa dạng base64.
    """
    # Giải mã dữ liệu ảnh từ base64
    image_data = base64.b64decode(image_data_base64)

    # Chuyển dữ liệu nhị phân thành đối tượng ảnh
    image = Image.open(io.BytesIO(image_data))

    # Hiển thị ảnh
    image.show()


@router.post("/send-message", response_model=MessageModel)
async def send_message(
    message: MessageModel,
    sender: str = Depends(get_current_user),
):
    message_dict = message.dict(by_alias=True)
    if sender != message.sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )
    # check if receiver is in database
    if not await database.users.find_one({"username": message.receiver}):
        raise HTTPException(
            status_code=400,
            detail="Receiver is not in database.",
        )

    message_dict["sender"] = sender
    message_dict["receiver"] = message.receiver
    message_dict["timestamp"] = datetime.now()
    message_dict["format"] = "text"

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )
    return MessageModel(**created_message)


def save_image_to_db(image_data_base64, folderPath, filename):
    # tao folder neu chua co
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # Giải mã dữ liệu ảnh từ base64
    image_data = base64.b64decode(image_data_base64)

    # Tạo đường dẫn đến file ảnh
    image_path = os.path.join(folderPath, filename + ".png")

    # Lưu dữ liệu ảnh vào file
    with open(image_path, "wb") as f:
        f.write(image_data)
    print("Image saved to", image_path)


@router.post("/send-image")
async def send_image(
    sender: str = Form(...),
    receiver: str = Form(...),
    image: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    image_data = await image.read()
    image_data = base64.b64encode(image_data)
    # image_data = image_data.decode("utf-8")

    if current_user != sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )

    # check if receiver is in database
    if not await database.users.find_one({"username": receiver}):
        raise HTTPException(
            status_code=400,
            detail="Receiver is not in database.",
        )

    if sender < receiver:
        folderPath = UPLOAD_DIRECTORY + sender + "-" + receiver
    else:
        folderPath = UPLOAD_DIRECTORY + receiver + "-" + sender

    # save image file to folder data in server, create folder if not exist
    save_image_to_db(image_data, folderPath, image.filename)

    message_dict = {
        "content": image.filename,
        "sender": sender,
        "receiver": receiver,
        "timestamp": datetime.now(),
        "format": "image",
    }

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )
    return MessageModel(**created_message)


def save_audio_to_db(audio_data, folderPath, filename):
    # tao folder neu chua co
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # Tạo đường dẫn đến file
    audio_path = os.path.join(folderPath, filename + ".mp3")

    # Lưu dữ liệu vào file
    with open(audio_path, "wb") as f:
        f.write(audio_data)

    print("Audio saved to", audio_path)


@router.post("/send-audio")
async def send_audio(
    sender: str = Form(...),
    receiver: str = Form(...),
    audio: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    if current_user != sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )

    # check if receiver is in database
    if not await database.users.find_one({"username": receiver}):
        raise HTTPException(
            status_code=400,
            detail="Receiver is not in database.",
        )

    if sender < receiver:
        folderPath = UPLOAD_DIRECTORY + sender + "-" + receiver
    else:
        folderPath = UPLOAD_DIRECTORY + receiver + "-" + sender

    audio_data = await audio.read()
    save_audio_to_db(audio_data, folderPath, audio.filename)

    message_dict = {
        "content": audio.filename,
        "sender": sender,
        "receiver": receiver,
        "timestamp": datetime.now(),
        "format": "audio",
    }

    new_message = await messages_collection.insert_one(message_dict)

    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )

    return MessageModel(**created_message)


def save_video_to_db(video_data, folderPath, filename):
    # Tạo folder nếu chưa có
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # Tạo đường dẫn đến file video
    video_path = os.path.join(folderPath, filename + ".mp4")

    # Lưu dữ liệu video vào file
    with open(video_path, "wb") as f:
        f.write(video_data)

    print("Video saved to", video_path)


@router.post("/send-video")
async def send_video(
    sender: str = Form(...),
    receiver: str = Form(...),
    video: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
):
    if current_user != sender:
        raise HTTPException(
            status_code=400,
            detail="You are not authorized to send messages on behalf of another user.",
        )

    # Kiểm tra xem người nhận có trong cơ sở dữ liệu không
    if not await database.users.find_one({"username": receiver}):
        raise HTTPException(
            status_code=400,
            detail="Receiver is not in database.",
        )

    # Xác định đường dẫn lưu trữ dựa trên người gửi và người nhận
    if sender < receiver:
        folderPath = UPLOAD_DIRECTORY + sender + "-" + receiver
    else:
        folderPath = UPLOAD_DIRECTORY + receiver + "-" + sender

    # Lưu video vào hệ thống file
    video_data = await video.read()
    save_video_to_db(video_data, folderPath, video.filename)

    # Lưu thông tin video vào MongoDB
    message_dict = {
        "content": video.filename,
        "sender": sender,
        "receiver": receiver,
        "timestamp": datetime.now(),
        "format": "video",
    }

    new_message = await messages_collection.insert_one(message_dict)
    created_message = await messages_collection.find_one(
        {"_id": new_message.inserted_id}
    )

    return MessageModel(**created_message)
