# Use an official Python runtime as a parent image
FROM python:3.8

RUN pip install pipenv

# Set the working directory to /app
WORKDIR /app

COPY Pipfile.lock /app

RUN pipenv install --ignore-pipfile --keep-outdated --dev

# Copy the current directory contents into the container at /app
COPY . /app
