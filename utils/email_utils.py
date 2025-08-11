import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

# Load environment variables from .env (works locally; Render ignores this and uses dashboard vars)
load_dotenv()

# Read email configuration from environment variables
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_SMTP_SERVER = os.environ.get("EMAIL_SMTP_SERVER")
EMAIL_SMTP_PORT = os.environ.get("EMAIL_SMTP_PORT")

# Safety checks to avoid silent errors
if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT]):
    raise ValueError("Missing one or more required email settings in environment variables.")

# Ensure port is an integer
EMAIL_SMTP_PORT = int(EMAIL_SMTP_PORT)


def send_email(to_email, subject, body=None, pdf_buffer=None, pdf_filename="Minutes_of_Meeting.pdf"):
    # Create multipart message
    msg = MIMEMultipart("mixed")
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach email body
    if body:
        msg.attach(MIMEText(body, 'plain'))

    # Attach PDF if provided
    if pdf_buffer:
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.read()
        pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
        pdf_attachment.add_header('Content-Disposition',
                                  'attachment',
                                  filename=pdf_filename)
        msg.attach(pdf_attachment)

    # Send email
    try:
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
