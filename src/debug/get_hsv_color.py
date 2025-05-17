import cv2
import numpy as np
from dotenv import load_dotenv, dotenv_values
import os

# Construct the path to the .env file in the inner directory
# dotenv_path = os.path.join("../", ".env")

# Load the environment variables from the specified path
load_dotenv()

rtsp_url = os.getenv('RTSP_URL')
print(rtsp_url)

# Trackbar callback function (does nothing, required by createTrackbar)
def nothing(x):
    pass

def read_rtsp():
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("Error: Could not open video stream")
        return

    print("RTSP stream started...")

    # Create a window for sliders
    cv2.namedWindow('HSV Adjustments')
    
    # Initialize HSV trackbars
    cv2.createTrackbar('H Min', 'HSV Adjustments', 0, 179, nothing)
    cv2.createTrackbar('H Max', 'HSV Adjustments', 179, 255, nothing)
    cv2.createTrackbar('S Min', 'HSV Adjustments', 0, 255, nothing)
    cv2.createTrackbar('S Max', 'HSV Adjustments', 255, 255, nothing)
    cv2.createTrackbar('V Min', 'HSV Adjustments', 0, 255, nothing)
    cv2.createTrackbar('V Max', 'HSV Adjustments', 255, 255, nothing)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Can't receive frame. Retrying...")
                continue

            frame = cv2.resize(frame, (640, 480))

            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Get current positions of trackbars
            h_min = cv2.getTrackbarPos('H Min', 'HSV Adjustments')
            h_max = cv2.getTrackbarPos('H Max', 'HSV Adjustments')
            s_min = cv2.getTrackbarPos('S Min', 'HSV Adjustments')
            s_max = cv2.getTrackbarPos('S Max', 'HSV Adjustments')
            v_min = cv2.getTrackbarPos('V Min', 'HSV Adjustments')
            v_max = cv2.getTrackbarPos('V Max', 'HSV Adjustments')

            lower = np.array([h_min, s_min, v_min])
            upper = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(hsv_frame, lower, upper)

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 500 < area < 6000:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Display frames
            cv2.imshow('Original Stream', frame)
            cv2.imshow('Color Detection Mask', mask)

            if cv2.waitKey(1) == ord('q'):
                break

    finally:
        print("Releasing RTSP resources...")
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    read_rtsp()