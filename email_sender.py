import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Outlook email configuration
sender_email = "city.room.booking.system@outlook.com"  # Replace with your Outlook email
sender_password = "your_app_password"  # Replace with your Outlook app password
receiver_email = "younes.bekhti.2@city.ac.uk"  # Replace with the recipient's email
subject = "Room Booking Confirmation"
body = """
Dear User,

Your room booking has been confirmed. Thank you for using our service!

Best regards,
Room Booking System
"""

# Create the email
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

# Send the email using Outlook's SMTP server
try:
    with smtplib.SMTP("smtp.office365.com", 587) as server:  # Outlook's SMTP server
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")