# Configure Custom Server Based on Brother Xia's Compiled Firmware

## Step 1: Confirm Version
Flash Brother Xia's pre-compiled [firmware version 1.6.1 or above](https://github.com/78/xiaozhi-esp32/releases)

## Step 2: Prepare Your OTA Address
If you followed the tutorial and used full module deployment, you should have an OTA address.

At this moment, please open your OTA address with a browser, for example, my OTA address:
```
https://2662r3426b.vicp.fun/xiaozhi/ota/
```

If it displays "OTA interface is running normally, websocket cluster count: X", then proceed.

If it displays "OTA interface is not running normally", it's probably because you haven't configured the `Websocket` address in the `Control Panel`. Then:

- 1. Login to the Control Panel as super administrator

- 2. Click `Parameter Management` in the top menu

- 3. Find the `server.websocket` item in the list and enter your `Websocket` address. For example, mine is:

```
wss://2662r3426b.vicp.fun/xiaozhi/v1/
```

After configuration, refresh your OTA interface address with the browser to see if it's normal. If it's still not normal, confirm again whether Websocket has started normally and whether the Websocket address is configured.

## Step 3: Enter Network Configuration Mode
Enter the machine's network configuration mode, click "Advanced Options" at the top of the page, enter your server's `ota` address, click save, and restart the device.
![Please refer to - OTA Address Setting](../docs/images/firmware-setting-ota.png)

## Step 4: Wake Up Xiaozhi and Check Log Output

Wake up Xiaozhi and see if the logs are output normally.

## Common Issues
Here are some common issues for reference:

[1. Why does Xiaozhi recognize a lot of Korean, Japanese, and English when I speak?](./FAQ.md)

[2. Why does "TTS task error file does not exist" appear?](./FAQ.md)

[3. TTS often fails, often times out](./FAQ.md)

[4. Can connect to self-built server using Wifi, but can't connect in 4G mode](./FAQ.md)

[5. How to improve Xiaozhi's conversation response speed?](./FAQ.md)

[6. I speak slowly, Xiaozhi always interrupts when I pause](./FAQ.md)

[7. I want to control lights, air conditioning, remote power on/off through Xiaozhi](./FAQ.md)
