import smtplib
from email.mime.text import MIMEText
from backend.core.config import EMAIL_USER, EMAIL_PASS
from backend.core.logger import logger


def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        logger.info(f"Reminder sent to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send reminder: {e}")