import os
import socket
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--user", default = 'pi', help="Your username (default: pi)")
parser.add_argument("-ow", "--overwrite", action = "store_true", help = "Overwrite existing configurations" )
args = parser.parse_args()

print('Hello, I will now run the setup script for anise-monitor...')

# Dependencies
print('I will start with dependencies...')
os.system('apt install python3-libcamera')
os.system('apt install python3-opencv')

# Create local-wrappers
print('I will now create a local copy for the wrappers, these are the ones you should configure for your requirements')
path_local_wrappers = '/home/'+args.user+'/local-wrappers'
os.system('mkdir -p '+path_local_wrappers)
if os.path.isfile('path_local_wrappers/wrapper-rgb.sh'):
    if args.overwrite:
        os.system('cp /home/'+args.user+'/anise-monitor/wrapper-templates/wrapper-template.sh ' +path_local_wrappers+ '/wrapper-rgb.sh')
        print('Your ran the script in overwrite mode, therefore I overwrote wrapper-rgb.sh')
    else:
        print('wrapper-rgb.sh already exists. If you want to overwrite it, run the script with --overwrite')
else:
    os.system('cp /home/'+args.user+'/anise-monitor/wrapper-templates/wrapper-template.sh path_local_wrappers/wrapper-rgb.sh')
os.system('chmod -R 777 '+path_local_wrappers)
print(path_local_wrappers+' added and I created wrapper-rgb.sh inside - feel free to clone or rename it, depending what you would like to do')



