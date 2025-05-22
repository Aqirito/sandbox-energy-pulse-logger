import requests
from dotenv import load_dotenv, dotenv_values
load_dotenv()
config = dotenv_values(".env")

api_url = config['API_URL']

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
            try:
                response = requests.post(api_url, json=measurement_data.copy())
                response.raise_for_status()
                print(f"[Send] Sending data: {measurement_data.copy()}")
                
                # Update previous data
                previous_data = measurement_data.copy()
            except requests.exceptions.RequestException as e:
                print(f"Error sending data: {e}")
                stop_flag.value = 1  # Set stop flag on error