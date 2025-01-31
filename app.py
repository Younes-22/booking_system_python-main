from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import mysql.connector
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__, static_folder='static')
app.secret_key = 'my_secret_key'  # Required for session management

# Hardcoded Gmail credentials (Not Recommended for Production)
GMAIL_EMAIL = "room.city.booking@gmail.com"
GMAIL_PASSWORD = "qfrjlkudstbojawp"  # Use an App Password, NOT your real password

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',  # Replace with your MySQL user
        password='',  # Replace with your MySQL password
        database='room_booking_system'
    )
    return conn

# Function to delete past bookings
def delete_past_bookings():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    query = "DELETE FROM booking WHERE date < %s"
    cursor.execute(query, (today,))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Deleted {cursor.rowcount} past bookings.")

# Function to send booking confirmation email
def send_booking_email(to_email, subject, body):
    from_email = GMAIL_EMAIL
    password = GMAIL_PASSWORD

    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Encrypt the connection
        server.login(from_email, password)  # Log in
        server.sendmail(from_email, to_email, msg.as_string())  # Send email
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()

@app.route('/get_booked_slots', methods=['GET'])
def get_booked_slots():
    date = request.args.get('date')
    room = request.args.get('room')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timeSlot FROM booking WHERE date = %s AND room = %s", (date, room))
    booked_slots = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify([slot[0] for slot in booked_slots])

@app.route('/')
def index():
    delete_past_bookings()
    return render_template('index.html')

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if request.method == 'POST':
        delete_past_bookings()

        email = request.form['email']
        confirm_email = request.form['confirm_email']
        full_name = request.form['full_name']
        room = request.form['room']
        time_slot = request.form['time_slot']
        date = request.form['date']

        # Email validation
        if not email.endswith('@city.ac.uk'):
            return jsonify({"error": "Invalid email, must end with @city.ac.uk"}), 400

        if email != confirm_email:
            return jsonify({"error": "Emails do not match. Please check your email inputs."}), 400

        try:
            booking_date = datetime.strptime(date, '%Y-%m-%d').date()
            today = datetime.now().date()

            if booking_date < today:
                return jsonify({"error": "The date must be today or in the future."}), 400

            max_booking_date = today + timedelta(days=14)  
            if booking_date > max_booking_date:
                return jsonify({"error": "Rooms cannot be booked more than 2 weeks in advance."}), 400

            if booking_date.weekday() >= 5:  
                return jsonify({"error": "Rooms cannot be booked on weekends. Please select a weekday."}), 400

        except ValueError:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM booking WHERE date = %s AND timeSlot = %s AND room = %s", (date, time_slot, room))
        existing_booking = cursor.fetchone()

        if existing_booking:
            cursor.close()
            conn.close()
            return jsonify({"error": "This time slot is already booked for the selected room."}), 400

        cursor.execute("INSERT INTO booking (email, fullName, room, timeSlot, date) VALUES (%s, %s, %s, %s, %s)", 
                       (email, full_name, room, time_slot, date))
        conn.commit()
        cursor.close()
        conn.close()

        subject = "Booking Confirmation"
        body = f"""
        Dear {full_name},

        Thank you for booking a Green Screen Room! Below are your booking details:

        - Email: {email}
        - Room: {room}
        - Date: {date}
        - Time Slot: {time_slot}

        If you have any questions or need to make changes, please contact us or visit AG18.

        Best regards,
        Journalism Tech Team
        """

        send_booking_email(email, subject, body)

        session['booking_details'] = {
            "email": email,
            "full_name": full_name,
            "room": room,
            "date": date,
            "time_slot": time_slot
        }

        return redirect(url_for('confirmation'))

@app.route('/confirmation')
def confirmation():
    booking_details = session.get('booking_details')
    if not booking_details:
        return redirect(url_for('index'))

    session.pop('booking_details', None)

    return render_template('confirmation.html', 
                          success_message="Booking successful!", 
                          booking_details=booking_details)

if __name__ == '__main__':
    app.run(debug=True)
