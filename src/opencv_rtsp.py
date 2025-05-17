import cv2
import numpy as np
from dotenv import load_dotenv, dotenv_values
load_dotenv()
config = dotenv_values(".env")

rtsp_url = config['RTSP_URL']

def read_rtsp(pulse_queue, stop_flag):

    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("Error: Could not open video stream")
        return

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

            frame = cv2.resize(frame, (640, 480))

            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lower_red1 = np.array([0, 120, 70])
            upper_red1 = np.array([10, 255, 255])

            lower_red2 = np.array([170, 120, 70])
            upper_red2 = np.array([180, 255, 255])

            mask1 = cv2.inRange(hsv_frame, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv_frame, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(mask1, mask2)

            contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 500 < area < 6000:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    pulse_queue.put(True)  # Signal pulse detection

            # Uncomment to display a frame
            cv2.imshow('Original Stream', frame)
            # cv2.imshow('Red Detection Mask', red_mask)
            # cv2.imshow('Red Only', red_only)

            # Must have to display cv2.imshow()
            if cv2.waitKey(1) == ord('q'):
                # Local exit (optional), but better handled by main process
                break

    finally:
        print("Releasing RTSP resources...")
        cap.release()
        cv2.destroyAllWindows()