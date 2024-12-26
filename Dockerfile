FROM python:3.13

# Set environment variables
ENV PROJECT_ROOT=/app
ENV FLOODNS_ROOT=/app/floodns

# Install system dependencies and Java Runtime Environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        default-jre \
        maven && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR $PROJECT_ROOT

# Copy the current directory contents into the container at /app
COPY . $PROJECT_ROOT

# Install Python dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Build Java components
WORKDIR $FLOODNS_ROOT
RUN mvn clean compile assembly:single && \
    mv target/floodns-*-jar-with-dependencies.jar $FLOODNS_ROOT/floodns-basic-sim.jar

# Set the working directory back to the project root
WORKDIR $PROJECT_ROOT

# Expose the port your application runs on
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py"]
