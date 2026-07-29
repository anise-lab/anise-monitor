#!/bin/bash

## Configuration
ACTIVITY_NAME="template"

# Script variables
SCRIPT_LENGTH=60 # length of each recording in seconds
SCRIPT_REPEATS=15 # number of repeats within the script
WIDTH_RGB=1280
HEIGHT_RGB=720
FRAME_PER_SECOND=8

ACTIVE_TIME_RANGES=("0:25") # Active recording hours (24-hour format), up to the hour
REBOOT_AFTER_RUN=0 # Reboot after each run

# Paths
PYTHON="/usr/bin/python3"
HOME_PATH="/home/pi/"
SCRIPT_PATH="${HOME_PATH}/anise-monitor/record-video/record-video.py"
DATA_PATH="${HOME_PATH}/Data/"
LOG_PATH="${HOME_PATH}/Logs/"
HEARTBEAT="/tmp/heartbeat"
RESTARTFILE="/tmp/restartme"

# Thresholds
# Lower threshold for the complete batch. If it finishes earlier than this, reboot
LOWER_THRESHOLD=$(echo "$SCRIPT_LENGTH * $SCRIPT_REPEATS * 0.8" | bc)
# Script timeout for the complete batch. If exceeds, timeout and reboot
SCRIPT_TIMEOUT="$((SCRIPT_LENGTH * SCRIPT_REPEATS * 120 / 100))s"
# Grace period for script to exit before kill
TIMEOUT_KILL_AFTER="15s"

# Construct scripts
SCRIPT_VARIABLES_ACTIVE=(-o "$DATA_PATH"
    -c 0
    -W "$WIDTH_RGB"
    -H "$HEIGHT_RGB"
    -fps "$FRAME_PER_SECOND"
    -L "$SCRIPT_LENGTH"
    -rep "$SCRIPT_REPEATS"
)
SCRIPT_VARIABLES_PASSIVE=()

printf '%q ' "$PYTHON" "$SCRIPT_PATH" "${SCRIPT_VARIABLES_ACTIVE[@]}"
printf '\n'

# Set up folders, log and locks
mkdir -p "$DATA_PATH"
mkdir -p "$LOG_PATH"
LOGFILE="${LOG_PATH}/${ACTIVITY_NAME}_$(date +%Y_%m_%d).log"
LOCKFILE="/tmp/${ACTIVITY_NAME}.lock"

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
    timeout --signal=TERM --kill-after="$TIMEOUT_KILL_AFTER" "$SCRIPT_TIMEOUT" \
        "$PYTHON" -u "$SCRIPT_PATH" "${SCRIPT_VARIABLES_ACTIVE[@]}" >> "$LOGFILE" 2>&1
    script_status=$?
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))

    if [ "$script_status" -eq 124 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Recording timed out after $SCRIPT_TIMEOUT; creating restart flag." >> "$LOGFILE"
        touch "$RESTARTFILE"
    elif [ "$script_status" -ne 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Recording exited with status $script_status; creating restart flag." >> "$LOGFILE"
        touch "$RESTARTFILE"
    elif (( $(echo "$elapsed < $LOWER_THRESHOLD" | bc -l) )); then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Recording exited early after ${elapsed}s; creating restart flag." >> "$LOGFILE"
        touch "$RESTARTFILE"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Finished active in ${elapsed}s." >> "$LOGFILE"
    fi
    
    # Restart Pi after every run
    if $REBOOT_AFTER_RUN; then
        touch "$RESTARTFILE"
    fi
    
    # Update heartbeat (used by watchdog)
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$HEARTBEAT"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Heartbeat updated" >> "$LOGFILE"
else
    # Run the passive script
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting passive" >> "$LOGFILE"
    $PYTHON "$SCRIPT_PATH" "${SCRIPT_VARIABLES_PASSIVE[@]}" >> "$LOGFILE" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Finished passive" >> "$LOGFILE"
    # Update heartbeat (used by watchdog)
    echo "$(date '+%Y-%m-%d %H:%M:%S')" > "$HEARTBEAT"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Heartbeat updated" >> "$LOGFILE"
fi

# if sudo, make sure outputs are 777 and optionally reboot
if [ "$EUID" -eq 0 ]; then
    # Make sure outputs are 777
    chmod -R 777 "$DATA_PATH"
    chmod -R 777 "$LOGFILE"
    chmod -R 777 "$HEARTBEAT"
    
    # Check if restartme exists, if yes, restart the Pi
    if [ -f "$RESTARTFILE" ]; then
        rm -f "$RESTARTFILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Restart triggered by restartme flag" >> "$LOGFILE"
        /sbin/shutdown -r +1 # reboot in 1 minute
    fi
fi



