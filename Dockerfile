FROM python:3.13

# Set environment variables
ENV PROJECT_ROOT=/app
ENV FLOODNS_ROOT=/app/floodns
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PATH="/opt/poetry/bin:/usr/local/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"

# Install system dependencies and Java Runtime Environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        default-jre \
        maven && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry --version && \
    poetry config virtualenvs.create false

# Set the working directory in the container
WORKDIR $PROJECT_ROOT

# Copy the current directory contents into the container at /app
COPY . $PROJECT_ROOT

# Install Python dependencies using Poetry
RUN poetry install

# Build Java components
WORKDIR $FLOODNS_ROOT
RUN mvn clean compile assembly:single && \
    mv target/floodns-*-jar-with-dependencies.jar $FLOODNS_ROOT/floodns-basic-sim.jar

# Set the working directory back to the project root
WORKDIR $PROJECT_ROOT

# Expose the port your application runs on
EXPOSE 8501

# Make sure the entry point is executable
CMD ["python", "main.py"]
