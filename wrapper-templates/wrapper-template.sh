
#!/bin/bash

# Configuration
SCRIPT_PATH="/home/pi/anise-monitor/record-video/record-video.py"
DATA_PATH="/home/pi/Data/"
SCRIPT_LENGTH=300 # length in seconds
THRESHOLD=$(echo "$SCRIPT_LENGTH * 0.8" | bc) # threshold for length
RESTARTFILE="/tmp/restartme" # to create RESTARTFILE, add "0 2 * * * touch /tmp/restartme"
SCRIPT_VARIABLES_ACTIVE=(-out "$DATA_PATH" -c 0 -W 2304 -H 1296 -fps 9 --restart "$RESTARTFILE")
SCRIPT_VARIABLES_PASSIVE=()
PYTHON="/usr/bin/python3"
LOGFILE="/var/log/rgb_capture.log"
LOCKFILE="/tmp/rgb.lock"
HEARTBEAT="/tmp/heartbeat"
# Active recording hours (24-hour format)
ACTIVE_TIME_RANGES=("0:25") # different than cronjob times!

# Check if lockfile exists and whether the process is still alive
if [ -f "$LOCKFILE" ]; then
    LOCKPID=$(cat "$LOCKFILE")
    if ps -p "$LOCKPID" > /dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Already running (PID $LOCKPID), exiting." >> "$LOGFILE"
        exit 1
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Stale lockfile found. Removing." >> "$LOGFILE"
        rm -f "$LOCKFILE"
    fi
fi

# Write current PID to lockfile
echo $$ > "$LOCKFILE"

# Ensure lockfile is removed on exit or crash
cleanup() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleaning up lockfile and exiting." >> "$LOGFILE"
    rm -f "$LOCKFILE"
}
trap cleanup EXIT

# Update heartbeat (used by watchdog)
echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$HEARTBEAT"

# Time-aware recording logic

hour=$(date +%H)
# Function to check if $hour is in any range
run_active=false
for range in "${ACTIVE_TIME_RANGES[@]}"; do
    start=${range%%:*}  # part before colon
    end=${range##*:}    # part after colon
    if [ "$hour" -ge "$start" ] && [ "$hour" -lt "$end" ]; then
        run_active=true
        break
    fi
done

if $run_active; then
    # Run the active script
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting active" >> "$LOGFILE"
    start_time=$(date +%s)
    $PYTHON "$SCRIPT_PATH" "${SCRIPT_VARIABLES_ACTIVE[@]}" >> "$LOGFILE" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Finished active" >> "$LOGFILE"
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))
    if (( $(echo "$elapsed < $THRESHOLD" | bc -l) )); then
        echo "Script exited early, creating restart flag" >> "$LOGFILE"
        touch"$RESTARTFILE"
    fi
    # Update heartbeat (used by watchdog)
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$HEARTBEAT"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Heartbeat updated" >> "$LOGFILE"s
else
    # Run the passive script
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting passive" >> "$LOGFILE"
    $PYTHON "$SCRIPT_PATH" "${SCRIPT_VARIABLES_PASSIVE[@]}" >> "$LOGFILE" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Finished passive" >> "$LOGFILE"
    # Update heartbeat (used by watchdog)
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$HEARTBEAT"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Heartbeat updated" >> "$LOGFILE"
fi

# Check if restartme exists, if yes, restart the Pi
if [ -f "$RESTARTFILE" ]; then
    rm -f "$RESTARTFILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Restart triggered by restartme flag" >> "$LOGFILE"
    /sbin/shutdown -r now
    #echo "$(date '+%Y-%m-%d %H:%M:%S') - Restart triggered by restartme flag" 
fi

