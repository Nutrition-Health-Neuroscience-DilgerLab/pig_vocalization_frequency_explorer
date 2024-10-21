# Dockerfile

FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Tkinter and X11
ENV DISPLAY=${DISPLAY}
ENV XAUTHORITY=/.Xauthority

# Copy the entire project into the container
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the entrypoint to run the application
CMD ["python", "-m", "app.gui"]
