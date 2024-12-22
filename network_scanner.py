import subprocess


def get_connected_devices():
    # Run the arp command to get a list of all connected devices
    arp_output = subprocess.check_output(['arp', '-a']).decode('utf-8')

    for line in arp_output.split('\n'):
        print(line)


if __name__ == "__main__":
    get_connected_devices()
