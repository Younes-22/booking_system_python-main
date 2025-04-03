CREATE DATABASE IF NOT EXISTS room_booking_system;
USE room_booking_system;

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

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE USER IF NOT EXISTS 'booking_admin'@'%' IDENTIFIED BY 'admin';
GRANT ALL PRIVILEGES ON room_booking_system.* TO 'booking_admin'@'%';
FLUSH PRIVILEGES;


