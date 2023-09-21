# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of your application's source code to the container
COPY api /app/api
COPY classes /app/classes
COPY logger /app/logger
COPY utils /app/utils
COPY requirements.txt syncModule.py /app
COPY syncModule.py /app

# Define a mount point for the volume
VOLUME /app/sync_jobs.json

# Define environment variables if needed
# ENV MY_VARIABLE=value
ENV MAX_NUMBER_OF_CONCURRENT_RUNNING_THREADS=2
ENV BULK_MEMBER_COUNT=5000
ENV MINUTES_NEEDED_TO_PERFORM_A_PARTIAL_SYNC_OF_A_SINGLE_BULK=1
ENV POLLING_TIME_IN_SECONDS=60
ENV MAILCHIMP_API_KEY=""
ENV OMETRIA_API_KEY=""


# Run your Python application
CMD ["python", "syncModule.py"]
