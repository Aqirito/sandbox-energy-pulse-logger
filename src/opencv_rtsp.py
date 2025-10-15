import cv2, os, ast
import numpy as np
import time # Import the time module for debouncing
from dotenv import load_dotenv, dotenv_values

# Load environment variables from the .env file
load_dotenv()
config = dotenv_values(".env")

# Retrieve RTSP URL from environment variables
rtsp_url = config['RTSP_URL']

# Convert IS_RED_COLOR environment variable to a boolean
is_red_color = os.getenv("IS_RED_COLOR", "False").lower() == "true"

# Helper function to parse string to a numpy array for HSV bounds
def parse_env_list(env_key):
    """
    Parses an environment variable string into a numpy array (uint8).
    Raises ValueError if the variable is not found or has an invalid format.
    """
    value_str = os.getenv(env_key)
    if value_str is None:
        raise ValueError(f"Environment variable {env_key} not found.")
    try:
        # Use ast.literal_eval to safely parse string representation of list
        return np.array(ast.literal_eval(value_str), dtype=np.uint8)
    except Exception as e:
        raise ValueError(f"Invalid format for {env_key}: {value_str}") from e

def read_rtsp(pulse_queue, stop_flag):
    """
    Reads the RTSP stream, detects pulses, and sends signals to a queue.

    Args:
        pulse_queue (multiprocessing.Queue): A queue to put pulse detection signals.
        stop_flag (multiprocessing.Value): A shared flag to signal process termination.
    """
    def create_capture():
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            print("Error: Could not open video stream")
            return None
        return cap

    cap = create_capture()
    if cap is None:
        stop_flag.value = 1  # Set stop flag on failure to open stream
        return

    print("RTSP stream started...")

    # --- Debouncing variables for pulse detection ---
    # Tracks the time when the last valid pulse was detected.
    last_pulse_detected_time = 0
    # Minimum time (in seconds) that must pass before a new pulse can be counted.
    # This helps prevent multiple detections for a single, lingering visual pulse.
    # Adjust this value based on your meter's pulse indicator behavior (e.g., how long it stays lit).
    pulse_debounce_period = float(config['PULSE_DEBOUNCE_PERIOD'])
    print("pulse_debounce_period", pulse_debounce_period)
    # Tracks if a pulse was detected in the immediately preceding frame.
    pulse_was_on_in_previous_frame = False
    # -------------------------------------------------

    try:
        while True:
            # Check if stop signal was sent from main process
            if stop_flag.value:
                print("Stop flag received. Exiting RTSP loop.")
                break

            ret, frame = cap.read()
            if not ret:
                print("Error: Can't receive frame (stream end?). Retrying...")
                
                # Try to reconnect indefinitely until successful
                print("Attempting to reconnect...")
                cap.release()  # Release the current capture object
                
                # Keep trying to create a new connection until successful
                while True:
                    cap = create_capture()
                    if cap is not None:
                        print("Successfully reconnected to RTSP stream.")
                        break
                    else:
                        print("Failed to reconnect to RTSP stream. Retrying in 5 seconds...")
                        time.sleep(5)  # Wait before retrying
                
                continue

            # Resize frame for consistent processing and display

            # Resize frame for consistent processing and display
            frame = cv2.resize(frame, (640, 200))
            # Convert frame to HSV color space for color-based detection
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            mask = None
            if is_red_color is True:
                # For red color, two HSV ranges are often needed as red wraps around the hue spectrum
                lower_1 = parse_env_list("HSV_LOWER_1")
                upper_1 = parse_env_list("HSV_UPPER_1")

                lower_2 = parse_env_list("HSV_LOWER_2")
                upper_2 = parse_env_list("HSV_UPPER_2")

                mask1 = cv2.inRange(hsv_frame, lower_1, upper_1)
                mask2 = cv2.inRange(hsv_frame, lower_2, upper_2)
                mask = cv2.bitwise_or(mask1, mask2) # Combine masks for both red ranges
            else:
                # For other colors, a single HSV range is usually sufficient
                lower = parse_env_list("HSV_LOWER_1")
                upper = parse_env_list("HSV_UPPER_1")
                mask = cv2.inRange(hsv_frame, lower, upper)

            # Find contours in the mask. Contours represent regions of detected color.
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            pulse_currently_on = False
            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Filter contours by area to identify the pulse indicator
                # Corrected condition: area must be greater than 10 AND less than 6000
                if area < 100:
                    pulse_currently_on = True
                    # Optionally, draw a rectangle around the detected pulse for visual debugging
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    break # A pulse contour was found in this frame, no need to check others

            current_time = time.time()

            # Debouncing logic: Only count a pulse on the leading edge (transition from off to on)
            # and if enough time has passed since the last valid pulse.
            if pulse_currently_on and not pulse_was_on_in_previous_frame:
                # print((current_time - last_pulse_detected_time))
                if (current_time - last_pulse_detected_time) > pulse_debounce_period:
                    pulse_queue.put(True)  # Signal a new, debounced pulse detection
                    last_pulse_detected_time = current_time
                    # print(f"[RTSP] New pulse detected at {time.ctime(current_time)}") # Debug print

            # Update the state for the next frame's comparison
            pulse_was_on_in_previous_frame = pulse_currently_on

            # Display the original stream frame (optional, for debugging)
            # Don't use when on raspberry pi console mode
            # cv2.imshow('Original Stream', frame)
            # You can also uncomment below to see the color detection mask
            # cv2.imshow('Detection Mask', mask)

            # Waitkey is necessary for cv2.imshow() to update. 'q' to quit.
            if cv2.waitKey(1) == ord('q'):
                break

    finally:
        # Release video capture resources and destroy all OpenCV windows on exit
        print("Releasing RTSP resources...")
        cap.release()
        cv2.destroyAllWindows()
