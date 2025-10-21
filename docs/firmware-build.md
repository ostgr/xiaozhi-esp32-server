# ESP32 Firmware Compilation

## Step 1: Prepare Your OTA Address

If you are using version 0.3.12 of this project, whether it's simple Server deployment or full module deployment, you will have an OTA address.

Since the OTA address setup methods for simple Server deployment and full module deployment are different, please choose the specific method below:

### If You're Using Simple Server Deployment
At this moment, please open your OTA address with a browser, for example, my OTA address:
```
http://192.168.1.25:8003/xiaozhi/ota/
```
If it displays "OTA interface is running normally, websocket address sent to device is: ws://xxx:8000/xiaozhi/v1/"

You can use the project's built-in `test_page.html` to test whether you can connect to the websocket address output by the OTA page.

If you can't access it, you need to modify the `server.websocket` address in the configuration file `.config.yaml`, restart and test again until `test_page.html` can access normally.

After success, proceed to Step 2.

### If You're Using Full Module Deployment
At this moment, please open your OTA address with a browser, for example, my OTA address:
```
http://192.168.1.25:8002/xiaozhi/ota/
```

If it displays "OTA interface is running normally, websocket cluster count: X", then proceed to Step 2.

If it displays "OTA interface is not running normally", it's probably because you haven't configured the `Websocket` address in the `Control Panel`. Then:

- 1. Login to the Control Panel as super administrator

- 2. Click `Parameter Management` in the top menu

- 3. Find the `server.websocket` item in the list and enter your `Websocket` address. For example, mine is:

```
ws://192.168.1.25:8000/xiaozhi/v1/
```

After configuration, refresh your OTA interface address with the browser to see if it's normal. If it's still not normal, confirm again whether Websocket has started normally and whether the Websocket address is configured.

## Step 2: Configure Environment
First configure the project environment according to this tutorial: [《Windows Setup ESP IDF 5.3.2 Development Environment and Compile Xiaozhi》](https://icnynnzcwou8.feishu.cn/wiki/JEYDwTTALi5s2zkGlFGcDiRknXf)

## Step 3: Open Configuration File
After configuring the compilation environment, download Brother Xia's xiaozhi-esp32 project source code.

Download Brother Xia's [xiaozhi-esp32 project source code](https://github.com/78/xiaozhi-esp32) from here.

After downloading, open the `xiaozhi-esp32/main/Kconfig.projbuild` file.

## Step 4: Modify OTA Address

Find the `default` content of `OTA_URL` and change `https://api.tenclass.net/xiaozhi/ota/` to your own address. For example, if my interface address is `http://192.168.1.25:8002/xiaozhi/ota/`, change the content to this.

Before modification:
```
config OTA_URL
    string "Default OTA URL"
    default "https://api.tenclass.net/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```
After modification:
```
config OTA_URL
    string "Default OTA URL"
    default "http://192.168.1.25:8002/xiaozhi/ota/"
    help
        The application will access this URL to check for new firmwares and server address.
```

## Step 5: Set Compilation Parameters

Set compilation parameters:

```
# Enter xiaozhi-esp32 root directory in terminal command line
cd xiaozhi-esp32
# For example, I'm using esp32s3 board, so set compilation target to esp32s3. If your board is another model, please replace with the corresponding model
idf.py set-target esp32s3
# Enter menu configuration
idf.py menuconfig
```

After entering menu configuration, go to `Xiaozhi Assistant` and set `BOARD_TYPE` to your board's specific model.
Save and exit, return to terminal command line.

## Step 6: Compile Firmware

```
idf.py build
```

## Step 7: Package bin Firmware

```
cd scripts
python release.py
```

After the above packaging command is completed, the firmware file `merged-binary.bin` will be generated in the `build` directory under the project root directory.
This `merged-binary.bin` is the firmware file to be flashed to the hardware.

Note: If you get a "zip" related error after executing the second command, please ignore this error. As long as the firmware file `merged-binary.bin` is generated in the `build` directory, it won't have much impact on you. Please continue.

## Step 8: Flash Firmware
Connect the esp32 device to your computer, use Chrome browser, and open the following URL:

```
https://espressif.github.io/esp-launchpad/
```

Open this tutorial: [Flash Tool/Web-based Firmware Flashing (No IDF Development Environment)](https://ccnphfhqs21z.feishu.cn/wiki/Zpz4wXBtdimBrLk25WdcXzxcnNS).
Go to: `Method 2: ESP-Launchpad Browser Web-based Flashing`, starting from `3. Flash Firmware/Download to Development Board`, follow the tutorial.

After successful flashing and successful networking, wake up Xiaozhi with the wake word and pay attention to the console information output by the server.

## Common Issues
Here are some common issues for reference:

[1. Why does Xiaozhi recognize a lot of Korean, Japanese, and English when I speak?](./FAQ.md)

[2. Why does "TTS task error file does not exist" appear?](./FAQ.md)

[3. TTS often fails, often times out](./FAQ.md)

[4. Can connect to self-built server using Wifi, but can't connect in 4G mode](./FAQ.md)

[5. How to improve Xiaozhi's conversation response speed?](./FAQ.md)

[6. I speak slowly, Xiaozhi always interrupts when I pause](./FAQ.md)

[7. I want to control lights, air conditioning, remote power on/off through Xiaozhi](./FAQ.md)
