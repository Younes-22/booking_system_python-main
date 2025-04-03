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
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY')

GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

def initialize_database():
    """Create database and tables if they don't exist"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # First connect without specifying database
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('DB_PASSWORD'),
                port=3306
            )
            cursor = conn.cursor()
            
            # Create database if not exists
            db_name = os.getenv('DB_NAME', 'room_booking_system')
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.execute(f"USE {db_name}")
            
            # Create tables
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room VARCHAR(100) NOT NULL,
                timeSlot VARCHAR(50) NOT NULL,
                date DATE NOT NULL,
                email VARCHAR(255) NOT NULL,
                unique_code VARCHAR(20) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_booking (room, timeSlot, date)
            ) ENGINE=InnoDB;
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
            ) ENGINE=InnoDB;
            """)
            
            print("Database initialization complete")
            cursor.close()
            conn.close()
            return True
            
        except mysql.connector.Error as err:
            print(f"Attempt {attempt + 1} failed: {err}")
            if attempt == max_retries - 1:
                raise err
            time.sleep(retry_delay)

def get_db_connection():
    """Establish database connection after ensuring DB exists"""
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    return conn

# Initialize database when app starts
with app.app_context():
    try:
        initialize_database()
    except Exception as e:
        print(f"Database initialization failed: {e}")

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

import time
import mysql.connector
from mysql.connector import Error

def create_db_connection():
    retries = 5
    delay = 2
    for i in range(retries):
        try:
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            return connection
        except Error as e:
            if i == retries - 1:
                raise
            time.sleep(delay)

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

    cursor.execute("INSERT INTO booking (room, timeSlot, date, email, unique_code) VALUES (%s, %s, %s, %s, %s)", 
                   (room, time_slot, date, email, unique_code))
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)