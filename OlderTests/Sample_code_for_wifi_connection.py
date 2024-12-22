wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# disable power management
wlan.config(pm = 0xa11140)
# start connection
print('attempting to connect to SSID: %s with password: %s' % (config.wlan['ssid'], config.wlan['password']))
wlan.connect(config.wlan['ssid'], config.wlan['password'])
# wait for connection or fail
maxwait = config.wlan['maxwait']
while maxwait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    maxwait -= 1
    print('waiting for connection...')
    time.sleep(1)
# report status and handle failure
if wlan.status() != 3:
    #errorled()
    raise RuntimeError('Network connection failed with status %s %s' % (wlan.status(), WOLSTATUS[wlan.status()]))
print('Connected. My IP is: %s' % wlan.ifconfig()[0])
