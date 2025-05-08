from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import mysql.connector
from datetime import datetime, timedelta
import smtplib
import string
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY')  # Load from .env

GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
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
    print(f"Deleted {cursor.rowcount} past bookings.")
    
    cursor.close()
    conn.close()

# Function to send booking confirmation email
def send_booking_email(to_email, subject, body):
    from_email = GMAIL_EMAIL
    password = GMAIL_PASSWORD

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
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

def generate_unique_code(length=8):
    characters = string.ascii_letters + string.digits
    unique_code = ''.join(random.choice(characters) for _ in range(length))
    return unique_code

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    delete_past_bookings()

    email = request.form['email']
    confirm_email = request.form['confirm_email']
    room = request.form['room']
    time_slot = request.form['time_slot']
    date = request.form['date']

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

    unique_code = generate_unique_code()

    cursor.execute("INSERT INTO booking (room, timeSlot, date, unique_code) VALUES (%s, %s, %s, %s)", 
                   (room, time_slot, date, unique_code))
    conn.commit()

    booking_id = cursor.lastrowid  
    cursor.close()
    conn.close()

    subject = "Booking Confirmation"
    body = f"""
    Dear User,

    Thank you for booking a Green Screen Room! Below are your booking details:

    - Booking ID: {booking_id}
    - Unique Cancellation Code: {unique_code}
    - Room: {room}
    - Date: {date}
    - Time Slot: {time_slot}

    Best regards,
    Journalism Tech Team
    """
    send_booking_email(email, subject, body)

    session['booking_details'] = {
        "booking_id": booking_id,
        "unique_code": unique_code,
        "email": email,
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

@app.route("/cancel")
def cancel_booking_page():
    return render_template("cancel.html")

@app.route("/cancel_booking", methods=["POST"])
def cancel_booking():
    unique_code = request.form.get("unique_code")

    if not unique_code:
        flash("Please enter a valid unique code.", "error")
        return redirect(url_for("cancel_booking_page"))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM booking WHERE unique_code = %s", (unique_code,))
        booking = cursor.fetchone()

        if booking:
            cursor.execute("DELETE FROM booking WHERE unique_code = %s", (unique_code,))
            conn.commit()
            flash("Your booking has been successfully cancelled.", "success")
        else:
            flash("Invalid unique code. No booking found.", "error")
    except Exception as e:
        print(f"Error cancelling booking: {e}")
        flash("An error occurred while cancelling your booking.", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("cancel_booking_page"))

@app.route('/availability')
def availability():
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_room = request.args.get('room', 'Room 1')
    
    # List of all rooms
    rooms = ['Room 1', 'Room 2']
    
    # Get all booked slots for the selected date and room
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timeSlot FROM booking WHERE date = %s AND room = %s", 
                  (selected_date, selected_room))
    booked_slots = [slot[0] for slot in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    # All possible time slots
    all_slots = [
        "09:00-09:45", "09:45-10:30", "10:30-11:15", "11:15-12:00",
        "12:00-12:45", "12:45-13:30", "13:30-14:15", "14:15-15:00",
        "15:00-15:45", "15:45-16:30", "16:30-17:15", "17:15-18:00",
        "18:00-18:45", "18:45-19:30"
    ]
    
    # Create availability data
    availability_data = [
        {'time_slot': slot, 'is_available': slot not in booked_slots}
        for slot in all_slots
    ]
    
    return render_template('availability.html',
                         selected_date=selected_date,
                         selected_room=selected_room,
                         rooms=rooms,
                         availability_data=availability_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
