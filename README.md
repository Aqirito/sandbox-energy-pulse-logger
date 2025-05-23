# sandbox-energy-pulse-logger
Measuring energy consumption using a pulse-output electricity meter and reading data via RTSP with OpenCV

## prerequisites
- Running RTSP server
- Electricity Meter 😀
- Python = 3.12.3

## Setup and Running
Note: If using Adafruit IO you need to create a `feed` with the name `energy` and `pulses` in your Adafruit IO account.
1. Create python virtual environment named `env/`
2. Install Required pip packages
3. Create `.env` file follow `.env-sample` and change the value needed.
4. Run `main.py`


## Debug

#### Change Color Detection
- Note: Red appears at both low and high ends of the hue spectrum so you need to get both for wide range red detections.

🔁 We need two masks for Red
In the HSV (Hue, Saturation, Value) color model:
- Hue is represented as a circular value — typically from 0 to 360 degrees or 0 to 180 in OpenCV.
- Red appears at both low and high ends of the hue spectrum:
  - Red starts near 0°
  - And loops back around at ~360° , which maps to 0° again
So in OpenCV, where hue values go from 0 to 179 , red spans two discontinuous regions:
- Lower red : ~[0–10] (dark reds)
- Upper red : ~[170–180] (magentas and bright reds)

Red → Orange → Yellow → Green → Blue → Purple → Magenta → Red ... <br>
↑ ---------------------------------------------------------------- ↑ <br>
0°- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 180°


1. GO `debug/` folder
2. Run the `get_hsv_color.py`
3. Adjust the slider to get the desired color.
4. Get the value and update it in `.env`