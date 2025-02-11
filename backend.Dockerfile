# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

RUN apt-get update && apt-get install gcc -y

# Copy the pyproject.toml and poetry.lock files into the container at /app
COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock

# Install the dependencies specified in pyproject.toml using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --with backend

# Copy the current directory contents into the container at /app
COPY backend /app/backend

# Expose the port that the FastAPI app runs on
EXPOSE 8000

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]