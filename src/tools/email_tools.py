from __future__ import annotations
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email_zoho_smtp(subject: str, html_body: str, to_email: str) -> None:
    user = os.environ["ZOHO_SMTP_USER"]
    app_pw = os.environ["ZOHO_SMTP_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.zoho.com", 465, timeout=10) as server:
        server.login(user, app_pw)
        server.sendmail(user, [to_email], msg.as_string())
