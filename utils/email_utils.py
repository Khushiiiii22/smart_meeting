import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import config


def send_email(to_email, subject, body=None, html_body=None, pdf_buffer=None, pdf_filename="Minutes_of_Meeting.pdf"):
    sender_email = config.EMAIL_SENDER
    sender_password = config.EMAIL_PASSWORD

    # Create the root message
    msg = MIMEMultipart("mixed")
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Create the alternative part for plain text and html
    alternative_part = MIMEMultipart('alternative')

    # Attach plain text if provided
    if body:
        alternative_part.attach(MIMEText(body, 'plain'))

    # Attach HTML part if provided
    if html_body:
        alternative_part.attach(MIMEText(html_body, 'html'))

    # Attach the alternative part to the root message
    msg.attach(alternative_part)

    # Attach PDF if provided
    if pdf_buffer:
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.read()
        pdf_attachment = MIMEApplication(pdf_data, _subtype="pdf")
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg.attach(pdf_attachment)

    try:
        with smtplib.SMTP(config.EMAIL_SMTP_SERVER, config.EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


