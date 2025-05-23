import os
import requests
from dotenv import load_dotenv, dotenv_values
load_dotenv()
config = dotenv_values(".env")

TOKEN = config['TOKEN']
API_URL = config['API_URL']
IS_ADAFRUIT_IO = os.getenv("IS_ADAFRUIT_IO", "False").lower() == "true"

HEADERS = {
    "Content-Type": "application/json"
}

if IS_ADAFRUIT_IO is True:
    HEADERS["X-AIO-Key"] = TOKEN
elif TOKEN != "" and IS_ADAFRUIT_IO is False:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

def send(measurement_data, stop_flag):
    # Store previous data to compare
    previous_data = {'timestamp': '', 'pulses': 0, 'kWh': '0.000000'}

    while True:
        # Check for graceful shutdown
        if stop_flag.value:
            print("Send process: Shutdown flag detected. Exiting.")
            break

        # Check if data has changed
        if measurement_data.copy() != previous_data:
            if IS_ADAFRUIT_IO is False:            
                # originally, the data was sent to the API
                try:
                    response = requests.post(API_URL, headers=HEADERS, json=measurement_data.copy())
                    response.raise_for_status()
                    print(f"[Send] Sending data: {measurement_data.copy()}")
                    
                    # Update previous data
                    previous_data = measurement_data.copy()
                except requests.exceptions.RequestException as e:
                    print(f"Error sending data: {e}")
                    stop_flag.value = 1  # Set stop flag on error
            else:
                try:
                    # Send kWh value to Adafruit IO
                    payload = measurement_data.copy()

                    energy_data = {
                        'created_at': payload['timestamp'],
                        'value': payload['kWh'],
                    }
                    response = requests.post(f"{API_URL}/feeds/energy/data", headers=HEADERS, json=energy_data)
                    response.raise_for_status()
                    print(f"[Send] Sending Energy data: {energy_data}")

                    pulses_data = {
                        'created_at': payload['timestamp'],
                        'value': payload['pulses'],
                    }
                    response = requests.post(f"{API_URL}/feeds/pulses/data", headers=HEADERS, json=pulses_data)
                    response.raise_for_status()
                    print(f"[Send] Sending Pulses data: {pulses_data}")
                    
                    # Update previous data
                    previous_data = measurement_data.copy()
                except requests.exceptions.RequestException as e:
                    print(f"Error sending data: {e}")
                    stop_flag.value = 1  # Set stop flag on error