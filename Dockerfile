# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install FFmpeg (Running as root inside the container)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Command to run the application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]
