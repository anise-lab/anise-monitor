from flask import Flask, Response, render_template, request, jsonify
import cv2
from picamera2 import Picamera2
import argparse

app = Flask(__name__)
# set up frame generation
def gen_frames():
        global lenspos
        while True:
                if args.v3:
                        picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": lenspos})
                # Capture frame-by-frame from Pi camera
                frame = picam2.capture_array()
                if args.yolo:
                        # Perform YOLOv8 inference
                        results = model(frame)
                        # Draw bounding boxes and labels on the frame
                        frame = results[0].plot()
                # Encode the frame in JPEG format
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                # Yield the frame for the Flask response
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                        
@app.route('/')
def index():
        return render_template('index.html', lenspos = lenspos)                        

@app.route('/video_feed')
def video_feed():
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/update_settings', methods=['POST'])
def update_settings():
        global lenspos
        data = request.get_json()
        if 'lenspos' in data:
                lenspos = max(0.0, min(10.0, lenspos + float(data['lenspos'])))
                print("Lens position adjusted to "+str(round(lenspos,2)))
        return jsonify({"lenspos": lenspos})


if __name__ == '__main__':
        # argument parser
        parser = argparse.ArgumentParser()
        parser.add_argument("-H", "--height", type = int, help = "Horizontal resolution")
        parser.add_argument("-W", "--width", type = int, help = "Vertical resolution")
        parser.add_argument("--v3", action="store_true",
                help="Enable v3 mode, which allows manual focus")
        parser.add_argument("--yolo", action="store_true",
                help="Go YOLO")
        args = parser.parse_args()
        if args.yolo:
                # Initialize YOLOv8 model
                from ultralytics import YOLO
                model = YOLO('/home/ai01/yolov8n.pt')
        # Set up the Raspberry Pi camera
        picam2 = Picamera2()
        picam2.configure(picam2.create_video_configuration(main={"format": 'XRGB8888', "size": (args.width, args.height)}))
        picam2.start()
        # lenspos is creating regardless whether it's --v3 is activate or not
        # so clicking buttons doesn't break the code for non-adjustable cameras
        global lenspos
        lenspos = 0.0
        if args.v3:
                from libcamera import controls
                print("v3 mode enabled, setting lens position to 0.0")
                picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": lenspos})
        # start app
        app.run(host='0.0.0.0', port=5000)
    
