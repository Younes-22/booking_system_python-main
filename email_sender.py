# email_sender.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_confirmation_email(user_email, staff_email, user_name, booking_details):
    # Outlook SMTP server settings
    smtp_server = 'smtp-mail.outlook.com'
    smtp_port = 587
    smtp_user = 'your_email@outlook.com'
    smtp_password = 'your_app_password'

    subject = 'Booking Confirmation'
    body = f"Dear {user_name},\n\nYour booking has been confirmed.\n\nDetails: {booking_details}\n\nThank you!"

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)

        # Send email to the user
        msg['To'] = user_email
        server.sendmail(smtp_user, user_email, msg.as_string())

        # Send email to staff
        msg['To'] = staff_email
        server.sendmail(smtp_user, staff_email, msg.as_string())

        server.quit()
        print(f"Confirmation email sent to {user_email} and {staff_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
