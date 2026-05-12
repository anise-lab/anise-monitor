#!/usr/bin/env python3
import time
from datetime import datetime
import os
import argparse
import gc
import shutil

def record(args,counter):
	if not args.camera == 'usb':
		import cv2
		from picamera2 import Picamera2
		# for now this will only record from camera port 0 or 1 (Rpi 5)
		if not counter:
			# Initialise camera
			print('Configuring camera...')
			picam2 = Picamera2(int(args.camera))
			video_config = picam2.create_video_configuration(main={"size": (args.width, args.height),
																	"format": args.format})
			picam2.configure(video_config)
			# Start camera
			picam2.start()
			# Adjust focus for cameras with adjustable focus (e.g. v3)
			if args.lenspos:
				from libcamera import controls
				picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": args.lenspos})
				print("Lens position manually adjusted to "+str(round(args.lenspos,2)))
		# Set up output path
		# get hostname
		device_id = os.uname()[1]
		# Create output folder if it does not exist
		# get time
		dt = datetime.now() # get current time
		datetag = dt.strftime("%Y_%m_%d")
		# Check if writing directly to external drive is enabled
		output_path = os.path.join(args.out,device_id+'_'+datetag) # default path
		if not os.path.exists(output_path):
			os.makedirs(output_path)
		str_dt = dt.strftime("%Y_%m_%d-%H_%M_%S") # convert timestamp to string in yyyy-mm-dd_HH-MM-SS
		# construct filename
		filename = device_id+'_cam'+str(args.camera)+'_'+str_dt
		# final output path
		out_path = os.path.join(output_path,filename+'.mp4')
		# temporary path
		tmp_path = os.path.join('/tmp',filename+'.mp4')
		# set up cv2
		fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Use "avc1" or "H264" if supported
		out = cv2.VideoWriter(tmp_path, fourcc, args.framerate, (args.width, args.height))
		# preview
		if args.preview:
			picam2.start_preview(Preview.QTGL)
		# record
		print('Starting to record '+tmp_path)
		t0 = time.time() # time of recording start
		th = t0
		while time.time() - t0 < args.length:
			t1 = time.time() # time of frame start
			rgb_frame = picam2.capture_array()
			rgb_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGBA2BGR)
			out.write(rgb_frame)
			#print(time.time() - t1)
			while time.time() - t1 < 1/args.framerate:
				time.sleep(0.01)
				#print(time.time() - t1)
			#print('new frame')
			if time.time() - th > args.beat:
				os.system(f'echo "$(date \'+%Y-%m-%d %H:%M:%S\')" > "{args.heartbeat}"')
				th = time.time()
				print('Heartbeat updated')
		print('Finished recording '+tmp_path)
		# stop preview
		if args.preview:
			picam2.stop_preview()
	# TODO
	else: # USB camera
		# Set up output path
		# get hostname
		device_id = os.uname()[1]
		# Create output folder if it does not exist
		# get time
		dt = datetime.now() # get current time
		datetag = dt.strftime("%Y_%m_%d")
		# Check if writing directly to external drive is enabled
		output_path = os.path.join(args.out,device_id+'_'+datetag) # default path
		if not os.path.exists(output_path):
			os.makedirs(output_path)
		str_dt = dt.strftime("%Y_%m_%d-%H_%M_%S") # convert timestamp to string in yyyy-mm-dd_HH-MM-SS
		# construct filename
		filename = device_id+'_cam'+str(args.camera)+'_'+str_dt
		# final output path
		out_path = os.path.join(output_path,filename+'.mp4')
		# temporary path
		tmp_path = os.path.join('/tmp',filename+'.mp4')
		# construct command for v4l2 settings
		command_v4l2 = 'v4l2-ctl -d /dev/video0 --set-fmt-video=width='+str(args.width)+',height='+str(args.height)+',pixelformat=MJPG --set-parm='+str(args.framerate)
		print(command_v4l2)
		os.system(command_v4l2)
		# construct command to record via ffmpeg
		command_record = 'ffmpeg -t '+str(args.length)+' -f v4l2 -input_format mjpeg -i '+args.usb+' '+tmp_path
		print(command_record)
		# record
		print('Starting to record '+tmp_path)
		os.system(command_record)
		print('Finished recording '+tmp_path)
	# export frame
	if args.framen is not None:
		if not os.path.exists(args.frameout):
			os.makedirs(args.frameout)
		cmd_frame = 'ffmpeg -i '+tmp_path+' -vf "select=eq(n\,'+str(args.framen)+')" -vsync vfr -frames:v 1 '+args.frameout+'/'+filename+'_f'+str(args.framen)+'.jpg'
		print(cmd_frame)
		os.system(cmd_frame)
    # move to final output path
	if args.recipient:
		os.system("age --recipients-file "+args.recipient+" -o "+out_path+".age "+tmp_path)
	else:
		shutil.move(tmp_path, out_path)
	print('Moved '+tmp_path+' to '+out_path)
	# garbage collection
	del tmp_path
	gc.collect()
    ## hack for not losing last file if usb drive not ejected safely
    #if var_record_external and len(var_external_paths):
    #    if os.path.exists(os.path.join(output_path,'hack.lock')):
    #        os.system("rm "+os.path.join(output_path,'hack.lock'))
    #    os.system("touch "+os.path.join(output_path,'hack.lock'))
    #    os.system("rm "+os.path.join(output_path,'hack.lock'))
    # close camera
	if not args.camera == 'usb':
		if counter == (args.repeat - 1):
			picam2.stop()
			picam2.close()
			print('Camera closed')

def main():
	# argument parser
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--camera", default = '0', help="Camera ID")
	parser.add_argument("-W", "--width", type = int, default = 2304, help="Camera resolution width")
	parser.add_argument("-H", "--height", type = int, default = 1296, help="Camera resolution height")
	# Raspberry Pi camera resolutions
	# Camera V1: 2592 × 1944 - 1296 x 972 - 648 x 486
	# Camera V2: 3280 × 2464 - 1640 x 1232 - 820 x 616
	# Camera V3: 4608 × 2592 - 2304 x 1296 - 1152 x 648
	parser.add_argument("-fps", "--framerate", type = int, default = 30, help="Frame per second")
	parser.add_argument("-fmt", "--format", default = 'XBGR8888', help="Image format. Use 'XBGR8888' for colour and 'YUV420 for greyscale")
	parser.add_argument("-L", "--length", type = int, default = 10, help="Length in seconds")
	parser.add_argument("-pir", "--pirgpio", default = None, help="GPIO pin for PIR, e.g. 17")
	parser.add_argument("-o", "--out", help="Output directory, e.g. '/home/pi/Data/")
	parser.add_argument("-f", "--lenspos", default = None,
		help="Lens position value for focusable lens (e.g. v3). Value range: 0.0 to 10.0. Leave it -1 for non-adjustable cameras.")
	parser.add_argument("-p", "--preview", action = "store_true", help="Enable camera preview")
	parser.add_argument("-rep", "--repeat", default = 1, help="Repeated recordings")
	parser.add_argument("-hb", "--heartbeat", default = '/tmp/heartbeat', help="Heartbeat file to update")
	parser.add_argument("-hbb", "--beat", type = int, default = 10, help="How often update heartbeat in seconds")
	parser.add_argument("-rec", "--recipient", default = None, help="Path to age recipient txt file for encryption")
	parser.add_argument("-u", "--usb", default = '/dev/video0', help="Path to USB camera, to list devices: v4l2-ctl --list-device")
	parser.add_argument("-fexn", "--framen", type = int, default = None, help="Export nth frame from video")
	parser.add_argument("-fexo", "--frameout", default = None, help="Output director for frames")
	# TODO
    #var_vflip = False # vertical flip
	#var_hflip = False # horizontal flip
	#var_format = 'XBGR8888' # Image format. Use 'XBGR8888' for colour and 'YUV420 for greyscale
	args = parser.parse_args()
	# record
	# motion sensor
	if args.pirgpio:
		from gpiozero import MotionSensor
		pir = MotionSensor(args.pirgpio)
		print("Waiting for motion...")
		pir.wait_for_motion()
		print('Motion detected, recording...')
		record(args,1)
	else:
		for counter in range(args.repeat):
			record(args,counter)

if __name__ == '__main__':
    main()
