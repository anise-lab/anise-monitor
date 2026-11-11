from picamera2 import Picamera2
from libcamera import controls
from datetime import datetime
import time
import argparse
import os
import gc

# set up camera
def record(args):
	# set up camera
	picam2 = Picamera2()
	config = picam2.create_still_configuration(
		main={"size": (args.width,args.height)},
		controls={"AfMode": controls.AfModeEnum.Continuous},
		queue=False,
		)
	picam2.configure(config)
	# start camera
	picam2.start()
	time.sleep(2) # allow camera to settle
	# get hostname
	device_id = os.uname()[1]
	# start counter
	counter = 0
	# record photos
	next_capture = time.monotonic()
	try:
		while True:
			time.sleep(max(0, next_capture - time.monotonic()))
			# construct output path and filename
			dt = datetime.now() # get current time
			datetag = dt.strftime("%Y_%m_%d")
			str_dt = dt.strftime("%Y_%m_%d-%H_%M_%S") # convert timestamp to string in yyyy-mm-dd_HH-MM-SS
			output_path = os.path.join(args.out,device_id+'_'+datetag) # default path
			if not os.path.exists(output_path):
				os.makedirs(output_path)
			filename = f"{device_id}_cam{args.camera}_{str_dt}_{counter:03d}.jpg"
			# take photo
			picam2.capture_file(os.path.join(args.out,output_path,filename))
			current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			print(current_time+' - '+ filename +" Saved")
			os.system(f'echo "$(date \'+%Y-%m-%d %H:%M:%S\')" > "{args.heartbeat}"')
			print(current_time+' - '+ "Heartbeat updated")
			# set next capture
			next_capture += args.interval
			# skip missed intervals if saving took too long
			now = time.monotonic()
			if next_capture < now:
				missed = int((now - next_capture) // args.interval) + 1
				next_capture += missed * args.interval
			counter = counter + 1
			# stop if enough photos are taken
			if counter == args.number:
				break
	except KeyboardInterrupt:
		print("\nCapture stopped.")
	finally:
		picam2.close()
		gc.collect()

def main():
	# argument parser
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--out", help="Output directory, e.g. '/home/pi/Data/")
	parser.add_argument("-c", "--camera", default = '0', help="Camera ID")
	parser.add_argument("-W", "--width", type = int, default = 2304, help="Camera resolution width")
	parser.add_argument("-H", "--height", type = int, default = 1296, help="Camera resolution height")
	# Raspberry Pi camera resolutions
	# Camera V1: 2592 × 1944 - 1296 x 972 - 648 x 486
	# Camera V2: 3280 × 2464 - 1640 x 1232 - 820 x 616
	# Camera V3: 4608 × 2592 - 2304 x 1296 - 1152 x 648
	parser.add_argument("-I", "--interval", type = int, default = 1, help="Interval between photos in seconds")
	parser.add_argument("-N", "--number", type = int, default = 1, help="Number of photos to take")
	parser.add_argument("-hb", "--heartbeat", default = '/tmp/heartbeat', help="Heartbeat file to update")
	parser.add_argument("-pir", "--pirgpio", default = None, help="GPIO pin for PIR, e.g. 17")
	args = parser.parse_args()
	# record
	# motion sensor
	if args.pirgpio:
		from gpiozero import MotionSensor
		pir = MotionSensor(args.pirgpio)
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print(current_time+' - '+"Waiting for motion...")
		pir.wait_for_motion()
		current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print(current_time+' - '+'Motion detected, recording...')
		record(args,1)
	else:
		# report available RAM before recording
		#memory = psutil.virtual_memory()
		#available_mb = memory.available / (1024 * 1024)
		#total_mb = memory.total / (1024 * 1024)
		#used_percent = memory.percent
		#current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		#print(f"{current_time} - Available RAM: {available_mb:.1f} MB")
		#print(f"{current_time} - Total RAM:     {total_mb:.1f} MB")
		#print(f"{current_time} - RAM usage:     {used_percent:.1f}%")
		# record
		record(args)
		# report available RAM after recording
		#memory = psutil.virtual_memory()
		#available_mb = memory.available / (1024 * 1024)
		#total_mb = memory.total / (1024 * 1024)
		#used_percent = memory.percent
		#current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		#print(f"{current_time} - Available RAM: {available_mb:.1f} MB")
		#print(f"{current_time} - Total RAM:     {total_mb:.1f} MB")
		#print(f"{current_time} - RAM usage:     {used_percent:.1f}%")

if __name__ == '__main__':
    main()

	
