# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . /app/

# Expose port 5000 for the Flask app
EXPOSE 5000

# Define environment variable names without values
# These should be provided at runtime
ENV NEWS_API_KEY=""
ENV FACT_CHECK_API_KEY=""

# Run the Gunicorn server for production
CMD ["./start.sh"]
