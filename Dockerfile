# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Redis
RUN apt-get update && apt-get install -y redis-server

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV API_KEY your_api_key_here

# Create a script to run multiple processes
RUN echo '#!/bin/bash\n\
redis-server --daemonize yes\n\
celery -A app.celery worker --loglevel=info &\n\
gunicorn -b 0.0.0.0:8000 app:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the script when the container launches
CMD ["/app/start.sh"]
