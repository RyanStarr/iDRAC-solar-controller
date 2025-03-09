from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import time
from datetime import datetime
import ssl
import urllib3
import json
import base64
import paramiko
import subprocess
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# InfluxDB Cloud configuration
INFLUXDB_URL = os.getenv('INFLUXDB_URL')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')

# Sensor configuration
MEASUREMENT = os.getenv('MEASUREMENT')
SENSOR_NAME = os.getenv('SENSOR_NAME')
TURN_OFF_VOLTAGE = float(os.getenv('TURN_OFF_VOLTAGE'))
TURN_ON_VOLTAGE = float(os.getenv('TURN_ON_VOLTAGE'))

# iDRAC configuration
IDRAC_IP = os.getenv('IDRAC_IP')
IDRAC_USERNAME = os.getenv('IDRAC_USERNAME')
IDRAC_PASSWORD = os.getenv('IDRAC_PASSWORD')

# Time range configuration
WEEKDAY_START_HOUR = int(os.getenv('WEEKDAY_START_HOUR'))
WEEKDAY_END_HOUR = int(os.getenv('WEEKDAY_END_HOUR'))
WEEKEND_START_HOUR = int(os.getenv('WEEKEND_START_HOUR'))
WEEKEND_END_HOUR = int(os.getenv('WEEKEND_END_HOUR'))

# Create InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

def get_temperature():
    command = f"ipmitool -I lanplus -H {IDRAC_IP} -U {IDRAC_USERNAME} -P {IDRAC_PASSWORD} sdr type temperature | grep Ambient | grep degrees | grep -Po '\\d{{2}}' | tail -1"
    output = subprocess.check_output(command, shell=True).decode().strip()
    temperature = int(output.split('\n')[-1])
    print("returning temp" + str(temperature))
    return temperature

def turn_off_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(IDRAC_IP, username=IDRAC_USERNAME, password=IDRAC_PASSWORD)
        # Issue the command to ton on the server
        ssh.exec_command('racadm serveraction powerdown')
        print("Server turned off -------")
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check the username and password.")
    except paramiko.SSHException as ssh_exception:
        print("SSH connection failed:", str(ssh_exception))
    except:
        print("Server offline?")
    finally:
        ssh.close()

def turn_on_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(IDRAC_IP, username=IDRAC_USERNAME, password=IDRAC_PASSWORD)
        # Issue the command to turn on the server
        ssh.exec_command('racadm serveraction powerup')
        print("Server powered on successfully.")
    except paramiko.AuthenticationException:
        print("Authentication failed. Please check the username and password.")
    except paramiko.SSHException as ssh_exception:
        print("SSH connection failed:", str(ssh_exception))
    except:
        print("Server offline?")
    finally:
        ssh.close()

while True:
    # Get current time
    current_time = datetime.now().time()
    current_day = datetime.now().weekday()

    # Check if it's a weekend
    if current_day in [5, 6]:  # Saturday (5) or Sunday (6)
        start_hour = WEEKEND_START_HOUR
        end_hour = WEEKEND_END_HOUR
    else:
        start_hour = WEEKDAY_START_HOUR
        end_hour = WEEKDAY_END_HOUR

    # Check if the current time is within the specified range
    if start_hour <= current_time.hour <= end_hour:
        # Query latest sensor reading
        query_api = client.query_api()
        query = 'from(bucket:"2ndbucket") \
        |> range(start: -10m) \
        |> filter(fn:(r) => r._measurement == "charge_controller") \
        |> filter(fn:(r) => r._field == "Battery voltage")'
        result = query_api.query(org=INFLUXDB_ORG, query=query)
        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))

        if results:
            latest_record = results[-1]
            latest_value = latest_record[1]
            print(latest_record)
            print(latest_value)
            print("turn on?")
        else:
            latest_value = 0
            print(latest_value)

        # Check if the value matches the turn off voltage
        while True:
            try:
                print(f"Starting Temperature check. Voltage is {latest_value} v")
                temperature = get_temperature()
                print("Starting voltage check")
                if latest_value <= TURN_OFF_VOLTAGE:
                    print(f"Voltage reading is {latest_value}V! Turning OFF server")
                    turn_off_server()

                # Check if the value matches the turn on voltage
                elif latest_value >= TURN_ON_VOLTAGE:
                    print(f"Voltage reading is {latest_value}V! Checking temperature")

                    if temperature >= 32:
                        print("Turning OFF server due to temperature exceeding 32c")
                        turn_off_server()
                        print("Waiting 30 minutes to cool")
                        time.sleep(1800)

                    elif temperature < 32:
                        print("Temperature is less than 32c. Turning ON.")
                        turn_on_server()
            except:
                print(f"Couldn't read temperature. Server likely off. Checking voltage {latest_value} v")
                if latest_value <= TURN_OFF_VOLTAGE:
                    print(f"Voltage is {latest_value} v. Waiting 30 minutes to charge")
                    turn_off_server()
                    time.sleep(1800)
                elif latest_value >= TURN_ON_VOLTAGE:
                    print(f"Couldn't read temperature. Voltage is currently {latest_value} v ")
                    turn_on_server()
                    print("Turning on server. Waiting for 1 minute to respond")
                    time.sleep(60)
                else: 
                    print(f"voltage is {latest_value} v. It's in between")
                    print("waiting 30 minutes to reach 13v")
                    time.sleep(1800)
    # Sleep for a minute before checking again
    time.sleep(60)
