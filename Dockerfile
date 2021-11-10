# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8-slim

RUN pip install --upgrade pip

ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy local code to the container image.
COPY . .

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

# Install dependencies.
RUN pip install -r requirements.txt
RUN pip install streamlit==1.1.0


# Service must listen to $PORT environment variable.
# This default value facilitates local development.
ENV PORT 80
ENV TZ="America/Bogota"
RUN date

# Setting this ensures print statements and log messages
# promptly appear in Cloud Logging.
ENV PYTHONUNBUFFERED TRUE


# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 