
# Use the official Python base image with the desired version
FROM ubuntu:latest

RUN apt update && apt install -y ipmitool python3-pip

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Environment variables
ENV INFLUXDB_URL=
ENV INFLUXDB_TOKEN=
ENV INFLUXDB_ORG=
ENV INFLUXDB_BUCKET=
ENV MEASUREMENT=
ENV SENSOR_NAME=
ENV TURN_OFF_VOLTAGE=
ENV TURN_ON_VOLTAGE=
ENV IDRAC_IP=
ENV IDRAC_USERNAME=
ENV IDRAC_PASSWORD=
ENV WEEKDAY_START_HOUR=
ENV WEEKDAY_END_HOUR=
ENV WEEKEND_START_HOUR=
ENV WEEKEND_END_HOUR

# Copy the Python code to the container
COPY . .

EXPOSE 443
EXPOSE 22

# Run your application
CMD [ "python3", "turn-on-off-server.py" ]

