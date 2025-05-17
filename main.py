# main.py
import multiprocessing as mp
from src.opencv_rtsp import read_rtsp
from src.measure import pulse_detected, calculate
from src.send_data import send

if __name__ == "__main__":
    # Start a Manager for shared state
    with mp.Manager() as manager:
        # Shared value for pulse count
        pulse_count = mp.Value('i', 0)  # 'i' means integer type

        # Shared stop flag for graceful shutdown
        stop_flag = mp.Value('i', 0)  # 0 = running, 1 = stop

        # Shared dictionary for measurement data
        measurement_data = manager.dict({
            'timestamp': '',
            'pulses': 0,
            'kWh': '0.000000'
        })

        # Queues (not currently used beyond signaling; can be extended)
        pulse_queue = mp.Queue(maxsize=1)

        # Define processes
        rtsp_process = mp.Process(
            target=read_rtsp,
            args=(pulse_queue, stop_flag)
        )

        measure_process_1 = mp.Process(
            target=pulse_detected,
            args=(pulse_queue, pulse_count, stop_flag)
        )

        measure_process_2 = mp.Process(
            target=calculate,
            args=(pulse_count, measurement_data, stop_flag)
        )

        send_process = mp.Process(
            target=send,
            args=(measurement_data, stop_flag)
        )


        try:
            rtsp_process.start()
            measure_process_1.start()
            measure_process_2.start()
            send_process.start()

            rtsp_process.join()
            measure_process_1.join()
            measure_process_2.join()
            send_process.join()

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt: Initiating graceful shutdown...")

            # Set the stop flag
            stop_flag.value = 1

            # Terminate other processes
            measure_process_1.terminate()
            measure_process_2.terminate()
            send_process.terminate()
            rtsp_process.terminate()

            print("All processes terminated.")