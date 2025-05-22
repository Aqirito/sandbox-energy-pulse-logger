import cv2, os, ast
import numpy as np
from dotenv import load_dotenv, dotenv_values
load_dotenv()
config = dotenv_values(".env")

rtsp_url = config['RTSP_URL']

# CHange string to truthy boolean 
is_red_color = os.getenv("IS_RED_COLOR", "False").lower() == "true"

# Helper function to parse string to list
def parse_env_list(env_key):
    value_str = os.getenv(env_key)
    if value_str is None:
        raise ValueError(f"Environment variable {env_key} not found.")
    try:
        return np.array(ast.literal_eval(value_str), dtype=np.uint8)
    except Exception as e:
        raise ValueError(f"Invalid format for {env_key}: {value_str}") from e


def read_rtsp(pulse_queue, stop_flag):

    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("Error: Could not open video stream")
        stop_flag.value = 1  # Set stop flag

    print("RTSP stream started...")

    try:
        while True:
            # Check if stop signal was sent
            if stop_flag.value:
                print("Stop flag received. Exiting RTSP loop.")
                break

            ret, frame = cap.read()
            if not ret:
                print("Error: Can't receive frame (stream end?). Retrying...")
                continue

            frame = cv2.resize(frame, (640, 200))
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Red appears at both low and high ends of the hue spectrum
            if is_red_color is True:
                lower_1 = np.array(parse_env_list("HSV_LOWER_1"))
                upper_1 = np.array(parse_env_list("HSV_UPPER_1"))

                lower_2 = np.array(parse_env_list("HSV_LOWER_2"))
                upper_2 = np.array(parse_env_list("HSV_UPPER_2"))

                mask1 = cv2.inRange(hsv_frame, lower_1, upper_1)
                mask2 = cv2.inRange(hsv_frame, lower_2, upper_2)
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                # Other colors
                lower = np.array(parse_env_list("HSV_LOWER_1"))
                upper = np.array(parse_env_list("HSV_UPPER_1"))
                mask = cv2.inRange(hsv_frame, lower, upper)

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 10 > area and area < 6000:
                    # x, y, w, h = cv2.boundingRect(cnt)
                    # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    pulse_queue.put(True)  # Signal pulse detection

            # Uncomment to display a frame
            cv2.imshow('Original Stream', frame)
            # cv2.imshow('Detection Mask', mask)

            # Must have to display cv2.imshow()
            if cv2.waitKey(1) == ord('q'):
                # Local exit (optional), but better handled by main process
                break

    finally:
        print("Releasing RTSP resources...")
        cap.release()
        cv2.destroyAllWindows()