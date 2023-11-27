import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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


# Example usage
sender_email = "huy8bit@gmail.com"
sender_password = "tvyd ppnk lxhg saka"
receiver_email = "webchat6969@gmail.com"
subject = "Hello from Python!"
message = "This is a test email sent from Python."

send_email(sender_email, sender_password, receiver_email, subject, message)
