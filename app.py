from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static')

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',  # Replace with your MySQL user
        password='',  # Empty if no password
        database='room_booking_system'
    )
    return conn

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
    return render_template('index.html')

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    if request.method == 'POST':
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

            # Check if the date is in the past
            if booking_date < today:
                return jsonify({"error": "The date must be today or in the future."}), 400

            # Check if the date is more than 2 weeks in advance
            max_booking_date = today + timedelta(days=14)  # 2 weeks from today
            if booking_date > max_booking_date:
                return jsonify({"error": "Rooms cannot be booked more than 2 weeks in advance."}), 400

            # Check if the date is a weekend (Saturday or Sunday)
            if booking_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
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

        # Insert the new booking into the database
        cursor.execute("INSERT INTO booking (email, fullName, room, timeSlot, date) VALUES (%s, %s, %s, %s, %s)", (email, full_name, room, time_slot, date))
        conn.commit()
        cursor.close()
        conn.close()

        # Render the confirmation page with booking details
        return render_template('confirmation.html', 
                              success_message="Booking successful!", 
                              booking_details={
                                  "email": email,
                                  "full_name": full_name,
                                  "room": room,
                                  "date": date,
                                  "time_slot": time_slot
                              })

if __name__ == '__main__':
    app.run(debug=True)