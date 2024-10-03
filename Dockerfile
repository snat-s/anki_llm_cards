# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Redis and other necessary packages
RUN apt-get update && apt-get install -y redis-server

# Create a non-root user
RUN useradd -m ankiuser

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV API_KEY API_KEY

# Create a script to run multiple processes
RUN echo '#!/bin/bash\n\
redis-server --daemonize yes\n\
celery -A app.celery worker --loglevel=info &\n\
gunicorn -b 0.0.0.0:8000 app:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Change ownership of the application files to the non-root user
RUN chown -R ankiuser:ankiuser /app

# Switch to the non-root user
USER ankiuser

# Run the script when the container launches
CMD ["/app/start.sh"]
