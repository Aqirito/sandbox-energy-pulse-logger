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
    # Initialize a variable to store the previous data for comparison
    previous_data = {'timestamp': '', 'pulses': 0, 'kWh': '0.000000'}

    # Continuously send data until shutdown is requested
    while True:
        # Check if the shutdown flag is set
        if stop_flag.value:
            print("Send process: Shutdown flag detected. Exiting.")
            break

        # Check if the measurement data has changed since the last send
        if measurement_data.copy() != previous_data:
            # If the data is being sent to a non-Adafruit IO API
            if IS_ADAFRUIT_IO is False:            
                # Send the data to the specified API endpoint
                try:
                    response = requests.post(API_URL, headers=HEADERS, json=measurement_data.copy())
                    response.raise_for_status()
                    print(f"[Send] Sending data: {measurement_data.copy()}")
                    
                    # Update the previous data with the current measurement data
                    previous_data = measurement_data.copy()
                except requests.exceptions.RequestException as e:
                    print(f"Error sending data: {e}")
                    stop_flag.value = 1  # Set the stop flag if an error occurs
            else:
                # If the data is being sent to Adafruit IO, send the kWh value to the energy feed
                try:
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
