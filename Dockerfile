# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Copy the environment file into the container
COPY .env .env


# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app's code
COPY . .

# Expose port 5000
EXPOSE 5000

# Start the app using gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
