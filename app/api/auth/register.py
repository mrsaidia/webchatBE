from app.api.auth.models import RegistrationRequest  # Mô hình mới cho yêu cầu đăng ký
import hashlib

from fastapi import APIRouter, HTTPException
from app.core.database import database
from app.api.auth.models import EmailRequest  # Mô hình mới để xử lý yêu cầu email
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()
user_collection = database.get_collection("users")


sender_email = "huy8bit@gmail.com"
sender_password = "tvyd ppnk lxhg saka"


def send_email(sender_email, sender_password, receiver_email, subject, message):
    # Create a multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Add body to email
    msg.attach(MIMEText(message, "plain"))

    # Create SMTP session
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


def send_verification_email(email: str, code: str):
    sender_email = "huy8bit@gmail.com"  # Địa chỉ email của bạn
    sender_password = "tvyd ppnk lxhg saka"  # Mật khẩu email của bạn
    receiver_email = email  # Địa chỉ email của người nhận
    subject = "Webchat Verification Code"  # Chủ đề email
    message = f"Your verification code is {code}"  # Nội dung email

    send_email(sender_email, sender_password, receiver_email, subject, message)


@router.post("/request-verification")
async def request_verification(email_request: EmailRequest):
    # Tạo mã xác nhận
    verification_code = str(random.randint(100000, 999999))

    # Lưu mã xác nhận và email vào cơ sở dữ liệu tạm thời
    temp_data = {
        "email": email_request.email,
        "verification_code": verification_code,
    }
    await user_collection.insert_one(temp_data)

    # Gửi email với mã xác nhận
    send_verification_email(email_request.email, verification_code)

    return {"message": "Verification email sent"}


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
async def register(registration_request: RegistrationRequest):
    # Tìm kiếm mã xác nhận trong cơ sở dữ liệu
    temp_data = await user_collection.find_one({"email": registration_request.email})
    if (
        not temp_data
        or temp_data["verification_code"] != registration_request.verification_code
    ):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Băm mật khẩu
    hashed_password = hash_password(registration_request.password)

    # Tạo document người dùng
    user_document = {
        "email": registration_request.email,
        "password": hashed_password,
    }

    # Chèn vào cơ sở dữ liệu người dùng
    result = await user_collection.insert_one(user_document)

    # Xóa dữ liệu tạm thời
    await user_collection.delete_one({"email": registration_request.email})

    return {"user_id": str(result.inserted_id), "email": registration_request.email}
