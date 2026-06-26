# anise-monitor
ANISE Monitor

## Setup
After cloning, run
```
sudo python3 ./anise-monitor/setup.py
```
to install dependencies and set up things locally.

## record-video
Record video on a Raspberry Pi using a camera connected via the CSI (Camera Serial Interface) port or USB.

### Usage
```console
python3 record-video.py -o out [options]

    -o out                 Output directory, e.g. '/home/pi/Data/
    -c camera              Camera ID (default: 0, use 1 for the second CSI port on the Pi 5 or 'usb' for USB camera)
    -W width               Camera resolution width (default: 2304)
    -H height              Camera resolution height (default: 1296)
    -fps framerate         Framerate for output video (default: 30)
    -fmt format            Image format. Use 'XBGR8888' for colour and 'YUV420' for greyscale (default: XBGR8888)
    -L length              Length in seconds (default: 30)
    -pir pirgpio           GPIO pin for PIR, e.g. 17 (default: None)
    -f lenspos             Lens position value for focusable lens (e.g. v3). Value range: 0.0 to 10.0. (default: None)
    -p preview             Enable camera preview
    -rep repeat            Number of repeated recordings (default: 1)
    -hb heartbeat          Heartbeat file to update (default: /tmp/heartbeat)
    -hbb beat              How often update heartbeat in seconds (default: 10)
    -rec recipient         Path to age recipient txt file for encryption (default: None)
    -u --usb               Path to USB camera, to list devices: v4l2-ctl --list-device (default: /dev/video0)
    -fexn framen           Export nth frame from video (default: None)
    -fexo frameout         Output directory for frames (default: None)
    -he hardware_encoder   Use H264 hardware encoder
    -v verbose             Verbose mode
```

The most robust way to use `record-video.py` is to run via a wrapper. Use `setup.py` to create a folder called `local-wrappers` in your home directory (outside the folder linked to git). When run as sudo, the wrapper (e.g. `wrapper-rgb.sh`) reboots the Pi if the process (e.g. video recording) finishes too early as this is usually a sign that there is a software issue with the sensor. To do this, run the wrapper via `sudo crontab`, e.g. `* * * * * bash /home/pi/local-wrappers/wrapper-rgb.sh`

### Watchdog
While the wrapper that triggers record-video.py is designed to reboot if the camera fails, it does not protect against a situation when the Pi itself hangs. To add an additional layer of robustness, we recommend to install and set up the `watchdog` daemon that monitors the Pi and reboots if it not responding anymore.

```
# install watchdog
sudo apt install watchdog
# create a backup of the original configuration
sudo cp /etc/watchdog.conf /etc/watchdog.conf.bak
# replace the configuration with one configured for the Pi
cd ./anise-monitor/watchdog-pi.conf /etc/watchdog.conf
# enable and start watchdog
sudo systemctl enable --now watchdog
# check that it is running
sudo systemctl status watchdog

# to stop and disable it
sudo systemctl stop watchdog
sudo systemctl disable watchdog
```

For an extra layer of robustness you can also enable heartbeat monitoring; this is commented out in our watchdog.conf by default. If you enable `file = /tmp/heartbeat/`, watchdog will monitor the date written into that file by `record-video.py`. This is useful in situations when the Python scripts somehow ends up getting stuck, while the Pi remains responsive. By setting `change = 60`, watchdog will reboot if the heartbeat is not updated for 60 seconds. However, be careful because if `record-video.py` (or its wrapper) is not running, there is nobody to updated the heartbeat and watchdog will swing into action. For most usecases it is better to 1. let wrapper check if the Python does not exit prematurely, 2. let watchdog check for the health of the Pi, and 3. restart the Pi after a couple of Python runs.