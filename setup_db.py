import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_NAME = "room_booking_system"

# Connect to MySQL without specifying a database
conn = mysql.connector.connect(
    host="127.0.0.1",  # Use 127.0.0.1 instead of localhost
    user=os.getenv("DB_USER"),  # Ensure this is set correctly in your .env file
    password=os.getenv("DB_PASSWORD"),  # Ensure this is set correctly
    port=3306  # MySQL default port
)

cursor = conn.cursor()

# Create database if it doesn't exist
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
print(f"Database '{DB_NAME}' is ready.")

# Connect to the new database
conn.database = DB_NAME

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS booking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room VARCHAR(100) NOT NULL,
    timeSlot VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    unique_code VARCHAR(10) NOT NULL UNIQUE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);
""")

print("Tables created successfully!")

cursor.close()
conn.close()
