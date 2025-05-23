# measure.py
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv, dotenv_values
load_dotenv()
config = dotenv_values(".env")

pulse_per_kWh = int(config['PULSE_PER_KWH'])
interval = int(config['INTERVAL'])


def pulse_detected(pulse_queue, pulse_count, stop_flag):
    while True:
        # Check if stop signal was sent
        if stop_flag.value:
            print("Stop flag received. Exiting RTSP loop.")
            break
        if pulse_queue.get() is True:
            with pulse_count.get_lock():  # Safely increment
                pulse_count.value += 1


def calculate(pulse_count, measurement_data, stop_flag):
    print("Starting energy measurement...")
    while True:
    # Check if stop signal was sent
        if stop_flag.value:
            print("Stop flag received. Exiting Measure loop.")
            break
        time.sleep(interval)

        with pulse_count.get_lock():  # Safely read and reset
            current_pulses = pulse_count.value
            pulse_count.value = 0

        kwh = current_pulses / pulse_per_kWh

        now_utc = datetime.now(timezone.utc)
        local_tz = ZoneInfo("Asia/Kuala_Lumpur")
        now_local = now_utc.astimezone(local_tz)
        
        data = {
            'timestamp': now_local.isoformat(),  # Standardized timestamp
            'pulses': current_pulses,
            'kWh': f"{kwh:.6f}"  # Format kWh as string for consistency
        }

        # Update shared dict all at once to prevent partial reads
        measurement_data.update(data)