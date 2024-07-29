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
COPY ./8k/*.py ./8k/*.py
COPY *.py .
COPY sc13/*.py ./sc13/*.py

# Ensure the Python script is executable (if needed)
RUN chmod +x ./8k/8k.py

# Command to run the application
CMD ["python", "8k/8k.py"]
