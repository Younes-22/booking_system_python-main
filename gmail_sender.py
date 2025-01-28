import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load variables from a .env file
load_dotenv()

def send_booking_email(to_email, subject, body):
    # Fetch Gmail credentials from environment variables
    from_email = os.getenv('GMAIL_EMAIL')
    password = os.getenv('GMAIL_PASSWORD')

    # Debug: Print environment variables
    print(f"From Email: {from_email}")
    print(f"Password: {password}")  # Be cautious about printing passwords in production

    if not from_email or not password:
        raise Exception("Gmail credentials are not set in environment variables.")

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add email body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Encrypt the connection

        # Log in to your Gmail account
        server.login(from_email, password)

        # Send email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)

        print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {e}")

    finally:
        server.quit()

# Example usage:
user_email = "younesbekhti04@gmail.com"
subject = "Booking Confirmation"
body = "Thank you for booking! Your booking is confirmed for 2025-01-30 at 3:00 PM."

send_booking_email(user_email, subject, body)