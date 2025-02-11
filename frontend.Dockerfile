# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

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
    && poetry install --with backend,frontend

# Copy the frontend directory into the container
COPY frontend /app/frontend

COPY app.py /app/app.py

# Expose the default Streamlit port
EXPOSE 8501

# Set Streamlit-specific environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Run the Streamlit app
CMD ["streamlit", "run", "app.py"]