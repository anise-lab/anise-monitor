# anise-monitor
ANISE Monitor

## record-video
Record video on a Raspberry Pi using a camera connected via the CSI (Camera Serial Interface) port or USB.

### Dependencies
```
sudo apt install python3-libcamera
sudo apt install python3-opencv
```

### Usage
```console
python3 record-video.py -o out [options]

    -o out              Output directory, e.g. '/home/pi/Data/
    -c camera           Camera ID (default: 0, use 1 for the second CSI port on the Pi 5 or 'usb' for USB camera)
    -W width            Camera resolution width (default: 2304)
    -H height           Camera resolution height (default: 1296)
    -fps framerate      Framerate for output video (default: 30)
    -fmt format         Image format. Use 'XBGR8888' for colour and 'YUV420 for greyscale (default: XBGR8888)
    -L length           Length in seconds (default: 30)
    -pir pirgpio        GPIO pin for PIR, e.g. 17 (default: None)
    -f lenspos          Lens position value for focusable lens (e.g. v3). Value range: 0.0 to 10.0. (default: None)
    -p preview          Enable camera preview
    -rep repeat         Number of repeated recordings (default: 1)
    -hb heartbeat       Heartbeat file to update (default: /tmp/heartbeat)
    -hbb beat           How often update heartbeat in seconds (default: 10)
    -rec recipient      Path to age recipient txt file for encryption (default: None)
    -u --usb            Path to USB camera, to list devices: v4l2-ctl --list-device (default: /dev/video0)
    -fexn framen        Export nth frame from video (default: None)
    -fexo frameout      Output directory for frames (default: None)
```
