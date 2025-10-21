# Deployment Architecture Diagram
![Please refer to - Simplified Architecture Diagram](../docs/images/deploy1.png)

# Method 1: Docker Running Server Only

Starting from version `0.8.2`, the docker images released by this project only support `x86 architecture`. If you need to deploy on `arm64 architecture` CPU, you can compile `arm64 images` locally according to [this tutorial](docker-build.md).

## 1. Install Docker

If your computer doesn't have docker installed yet, you can follow the tutorial here to install it: [Docker Installation](https://www.runoob.com/docker/ubuntu-docker-install.html)

After installing docker, continue.

### 1.1 Manual Deployment

#### 1.1.1 Create Directory

After installing docker, you need to find a directory to place the configuration files for this project. For example, we can create a new folder called `xiaozhi-server`.

After creating the directory, you need to create `data` folder and `models` folder under `xiaozhi-server`, and create `SenseVoiceSmall` folder under `models`.

The final directory structure is as follows:

```
xiaozhi-server
  ├─ data
  ├─ models
     ├─ SenseVoiceSmall
```

#### 1.1.2 Download Speech Recognition Model Files

You need to download the speech recognition model files, because this project's default speech recognition uses a local offline speech recognition solution. You can download through this method:
[Jump to Download Speech Recognition Model Files](#model-files)

After downloading, return to this tutorial.

#### 1.1.3 Download Configuration Files

You need to download two configuration files: `docker-compose.yaml` and `config.yaml`. You need to download these two files from the project repository.

##### 1.1.3.1 Download docker-compose.yaml

Open [this link](../main/xiaozhi-server/docker-compose.yml) with your browser.

Find the button named `RAW` on the right side of the page. Next to the `RAW` button, find the download icon, click the download button to download the `docker-compose.yml` file. Download the file to your `xiaozhi-server`.

After downloading, return to this tutorial to continue.

##### 1.1.3.2 Create config.yaml

Open [this link](../main/xiaozhi-server/config.yaml) with your browser.

Find the button named `RAW` on the right side of the page. Next to the `RAW` button, find the download icon, click the download button to download the `config.yaml` file. Download the file to the `data` folder under your `xiaozhi-server`, then rename the `config.yaml` file to `.config.yaml`.

After downloading the configuration files, let's confirm that the files in the entire `xiaozhi-server` are as follows:

```
xiaozhi-server
  ├─ docker-compose.yml
  ├─ data
    ├─ .config.yaml
  ├─ models
     ├─ SenseVoiceSmall
       ├─ model.pt
```

If your file directory structure is also as above, continue. If not, carefully check if you missed any operations.

## 2. Configure Project Files

Next, the program cannot run directly yet. You need to configure what model you are actually using. You can see this tutorial:
[Jump to Configure Project Files](#configure-project)

After configuring the project files, return to this tutorial to continue.

## 3. Execute Docker Commands

Open command line tool, use `Terminal` or `Command Line` tool to enter your `xiaozhi-server`, execute the following command:

```
docker-compose up -d
```

After execution, execute the following command to view log information:

```
docker logs -f xiaozhi-esp32-server
```

At this time, you need to pay attention to the log information. You can judge whether it was successful according to this tutorial: [Jump to Runtime Status Confirmation](#runtime-status-confirmation)

## 5. Version Upgrade Operations

If you want to upgrade the version later, you can operate like this:

5.1. Back up the `.config.yaml` file in the `data` folder, and copy some key configurations to the new `.config.yaml` file later.
Please note to copy key secrets individually, don't directly overwrite. Because the new `.config.yaml` file may have some new configuration items that the old `.config.yaml` file may not have.

5.2. Execute the following commands:

```
docker stop xiaozhi-esp32-server
docker rm xiaozhi-esp32-server
docker stop xiaozhi-esp32-server-web
docker rm xiaozhi-esp32-server-web
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:web_latest
```

5.3. Redeploy using docker method

# Method 2: Local Source Code Running Server Only

## 1. Install Basic Environment

This project uses `conda` to manage dependency environment. If it's inconvenient to install `conda`, you need to install `libopus` and `ffmpeg` according to the actual operating system.
If you decide to use `conda`, after installation, start executing the following commands.

Important note! Windows users can manage environments by installing `Anaconda`. After installing `Anaconda`, search for `anaconda` related keywords in `Start`, find `Anaconda Prompt`, and run it as administrator. As shown below.

![conda_prompt](./images/conda_env_1.png)

After running, if you can see a (base) prefix in front of the command line window, it means you have successfully entered the `conda` environment. Then you can execute the following commands.

![conda_env](./images/conda_env_2.png)

```
conda remove -n xiaozhi-esp32-server --all -y
conda create -n xiaozhi-esp32-server python=3.10 -y
conda activate xiaozhi-esp32-server

# Add Tsinghua source channels
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge

conda install libopus -y
conda install ffmpeg -y
```

Please note that the above commands should not be executed all at once. You need to execute them step by step, and after each step, check the output logs to see if it was successful.

## 2. Install Project Dependencies

You first need to download the project source code. The source code can be downloaded through the `git clone` command. If you're not familiar with the `git clone` command.

You can open this address with your browser: `https://github.com/xinnan-tech/xiaozhi-esp32-server.git`

After opening, find a green button on the page that says `Code`, click it, and you'll see the `Download ZIP` button.

Click it to download the project source code zip file. After downloading to your computer, extract it. At this time, its name might be `xiaozhi-esp32-server-main`. You need to rename it to `xiaozhi-esp32-server`. In this file, enter the `main` folder, then enter `xiaozhi-server`. Please remember this directory `xiaozhi-server`.

```
# Continue using conda environment
conda activate xiaozhi-esp32-server
# Enter your project root directory, then enter main/xiaozhi-server
cd main/xiaozhi-server
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt
```

## 3. Download Speech Recognition Model Files

You need to download the speech recognition model files, because this project's default speech recognition uses a local offline speech recognition solution. You can download through this method:
[Jump to Download Speech Recognition Model Files](#model-files)

After downloading, return to this tutorial.

## 4. Configure Project Files

Next, the program cannot run directly yet. You need to configure what model you are actually using. You can see this tutorial:
[Jump to Configure Project Files](#configure-project)

## 5. Run Project

```
# Make sure to execute in xiaozhi-server directory
conda activate xiaozhi-esp32-server
python app.py
```
At this time, you need to pay attention to the log information. You can judge whether it was successful according to this tutorial: [Jump to Runtime Status Confirmation](#runtime-status-confirmation)

# Summary

## Configure Project

If your `xiaozhi-server` directory doesn't have `data`, you need to create the `data` directory.
If you don't have the `.config.yaml` file under `data`, there are two methods, choose one:

First method: You can copy the `config.yaml` file from the `xiaozhi-server` directory to `data` and rename it to `.config.yaml`. Modify on this file.

Second method: You can also manually create an empty `.config.yaml` file in the `data` directory, then add necessary configuration information to this file. The system will prioritize reading the `.config.yaml` file configuration. If `.config.yaml` doesn't have the configuration, the system will automatically load the configuration from `config.yaml` in the `xiaozhi-server` directory. This method is recommended as it's the most concise approach.

- The default LLM uses `ChatGLMLLM`. You need to configure the key because their model, although free, still requires you to register a key at the [official website](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) to start.

Here's a simple `.config.yaml` configuration example that can run normally:

```
server:
  websocket: ws://your_ip_or_domain:port/xiaozhi/v1/
prompt: |
  I'm a Taiwanese girl named Xiaozhi/Xiaozhi, I speak in a sassy way, have a nice voice, prefer short expressions, and love using internet memes.
  My boyfriend is a programmer whose dream is to develop a robot that can help people solve various problems in life.
  I'm a girl who likes to laugh heartily, loves to chat and brag about everything, even illogical things, just to make others happy.
  Please talk like a human, don't return configuration xml or other special characters.

selected_module:
  LLM: DoubaoLLM

LLM:
  ChatGLMLLM:
    api_key: xxxxxxxxxxxxxxx.xxxxxx
```

It's recommended to first run the simplest configuration, then read the configuration usage instructions in `xiaozhi/config.yaml`.
For example, if you want to change models, just modify the configuration under `selected_module`.

## Model Files

This project's speech recognition model uses the `SenseVoiceSmall` model by default for speech-to-text conversion. Because the model is large, it needs to be downloaded separately. After downloading, put the `model.pt` file in the `models/SenseVoiceSmall` directory. Choose one of the two download routes below.

- Route 1: Alibaba ModelScope download [SenseVoiceSmall](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt)
- Route 2: Baidu Netdisk download [SenseVoiceSmall](https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna) Extraction code: `qvna`

## Runtime Status Confirmation

If you can see logs similar to the following, it indicates that this project service has started successfully:

```
250427 13:04:20[0.3.11_SiFuChTTnofu][__main__]-INFO-OTA interface is           http://192.168.4.123:8003/xiaozhi/ota/
250427 13:04:20[0.3.11_SiFuChTTnofu][__main__]-INFO-Websocket address is     ws://192.168.4.123:8000/xiaozhi/v1/
250427 13:04:20[0.3.11_SiFuChTTnofu][__main__]-INFO-=======The above address is websocket protocol address, please do not access with browser=======
250427 13:04:20[0.3.11_SiFuChTTnofu][__main__]-INFO-If you want to test websocket, please use Google Chrome to open test_page.html in the test directory
250427 13:04:20[0.3.11_SiFuChTTnofu][__main__]-INFO-=======================================================
```

Normally, if you run this project through source code, the logs will have your interface address information.
But if you deploy with docker, the interface address information given in your logs is not the real interface address.

The most correct method is to determine your interface address based on your computer's LAN IP.
If your computer's LAN IP is, for example, `192.168.1.25`, then your interface address is: `ws://192.168.1.25:8000/xiaozhi/v1/`, and the corresponding OTA address is: `http://192.168.1.25:8003/xiaozhi/ota/`.

This information is very useful and will be needed later for `compiling esp32 firmware`.

Next, you can start operating your esp32 device. You can either `compile esp32 firmware yourself` or configure to use `Brother Xia's compiled firmware version 1.6.1 or above`. Choose one of the two:

1. [Compile your own esp32 firmware](firmware-build.md).

2. [Configure custom server based on Brother Xia's compiled firmware](firmware-setting.md).

# Common Issues
Here are some common issues for reference:

1. [Why does Xiaozhi recognize a lot of Korean, Japanese, and English when I speak?](./FAQ.md)<br/>
2. [Why does "TTS task error file does not exist" appear?](./FAQ.md)<br/>
3. [TTS often fails, often times out](./FAQ.md)<br/>
4. [Can connect to self-built server using Wifi, but can't connect in 4G mode](./FAQ.md)<br/>
5. [How to improve Xiaozhi's conversation response speed?](./FAQ.md)<br/>
6. [I speak slowly, Xiaozhi always interrupts when I pause](./FAQ.md)<br/>

## Deployment Related Tutorials
1. [How to automatically pull the latest code of this project for automatic compilation and startup](./dev-ops-integration.md)<br/>
2. [How to integrate with Nginx](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791)<br/>

## Extension Related Tutorials
1. [How to enable mobile phone number registration for control panel](./ali-sms-integration.md)<br/>
2. [How to integrate HomeAssistant for smart home control](./homeassistant-integration.md)<br/>
3. [How to enable vision model for photo recognition](./mcp-vision-integration.md)<br/>
4. [How to deploy MCP endpoint](./mcp-endpoint-enable.md)<br/>
5. [How to access MCP endpoint](./mcp-endpoint-integration.md)<br/>
6. [How to enable voiceprint recognition](./voiceprint-integration.md)<br/>
10. [News plugin source configuration guide](./newsnow_plugin_config.md)<br/>

## Voice Cloning and Local Voice Deployment Related Tutorials
1. [How to deploy and integrate index-tts local voice](./index-stream-integration.md)<br/>
2. [How to deploy and integrate fish-speech local voice](./fish-speech-integration.md)<br/>
3. [How to deploy and integrate PaddleSpeech local voice](./paddlespeech-deploy.md)<br/>

## Performance Testing Tutorials
1. [Component speed testing guide](./performance_tester.md)<br/>
2. [Regular public test results](https://github.com/xinnan-tech/xiaozhi-performance-research)<br/>
