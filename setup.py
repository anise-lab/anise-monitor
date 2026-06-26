import os
import socket
import keyboard

print('Hello, I will now run the setup script for anise-monitor...')

# Dependencies
print('I will start with dependencies...')
os.system('apt install python3-libcamera')
os.system('apt install python3-opencv')

# Create local-wrappers
print('I will now create a local copy for the wrappers, these are the ones you should configure for your requirements')
hostname = socket.gethostname()
path_local_wrappers = '/home/'+hostname+'/local-wrappers'
os.system('mkdir -p '+path_local_wrappers)
if os.path.isfile('path_local_wrappers/wrapper-rgb.sh'):
    print("wrapper-rgb.sh already exists. Do you want me to overwrite it? (y)es or (n)o")
    while True:
        if keyboard.is_pressed("y"):
            os.system('cp /home/'+hostname+'/anise-monitor/wrapper-templates/wrapper-template.sh path_local_wrappers/wrapper-rgb.sh')
            print('Overwrote wrapper-rgb.sh')
            break
        elif keyboard.is_pressed("n"):
            print('Keeping original wrapper-rgb.sh')
            break
else:
    os.system('cp /home/'+hostname+'/anise-monitor/wrapper-templates/wrapper-template.sh path_local_wrappers/wrapper-rgb.sh')
os.system('chmod -R 777 '+path_local_wrappers)
print(path_local_wrappers+' added and I created wrapper-rgb.sh inside - feel free to clone or rename it, depending what you would like to do')



