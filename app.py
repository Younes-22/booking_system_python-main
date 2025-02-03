from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import mysql.connector
from datetime import datetime, timedelta
import smtplib
import string
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import flash

app = Flask(__name__, static_folder='static')
app.secret_key = 'my_secret_key'  # Required for session management and flash messages

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

def generate_unique_code(length=8):
    # Define the characters to use in the code
    characters = string.ascii_letters + string.digits  # Letters (uppercase + lowercase) + digits
    
    # Generate a random code by selecting 'length' number of characters
    unique_code = ''.join(random.choice(characters) for _ in range(length))
    
    return unique_code

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if request.method == 'POST':
        delete_past_bookings()

        email = request.form['email']
        confirm_email = request.form['confirm_email']
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

        # Generate a unique code
        unique_code = generate_unique_code()

        # Insert booking with the unique code
        cursor.execute("INSERT INTO booking (room, timeSlot, date, unique_code) VALUES (%s, %s, %s, %s)", 
                       (room, time_slot, date, unique_code))
        conn.commit()

        # Get the booking ID
        booking_id = cursor.lastrowid  

        cursor.close()
        conn.close()

        # Send confirmation email with booking ID and unique code
        subject = "Booking Confirmation"
        body = f"""
        Dear User,

        Thank you for booking a Green Screen Room! Below are your booking details:

        - Booking ID: {booking_id}
        - Unique Cancellation Code: {unique_code}
        - Room: {room}
        - Date: {date}
        - Time Slot: {time_slot}

        If you have any questions or need to make changes, please contact us or visit AG18.

        Best regards,
        Journalism Tech Team
        """

        send_booking_email(email, subject, body)  # Send email with the unique code

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
        # Check if the booking exists
        cursor.execute("SELECT * FROM booking WHERE unique_code = %s", (unique_code,))
        booking = cursor.fetchone()

        if booking:
            # Delete the booking
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
    app.run(debug=True)