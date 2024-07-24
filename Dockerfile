# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Create a virtual environment
RUN python -m venv venv

# Activate the virtual environment and install dependencies
RUN . ./venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY *.py .

# Command to run the application
CMD ["./venv/bin/python", "sc13_to_slack.py"]
