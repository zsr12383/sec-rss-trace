# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY *.py .

# Ensure the Python script is executable (if needed)
RUN chmod +x sc13_to_slack.py

# Command to run the application
CMD ["python", "sc13_to_slack.py"]
