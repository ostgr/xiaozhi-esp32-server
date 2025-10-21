# Deployment Architecture Diagram
![Please refer to - Full Module Installation Architecture Diagram](../docs/images/deploy2.png)

# Method 1: Docker Running Full Module
Starting from version `0.8.2`, the docker images released by this project only support `x86 architecture`. If you need to deploy on `arm64 architecture` CPU, you can compile `arm64 images` locally according to [this tutorial](docker-build.md).

## 1. Install Docker

If your computer doesn't have docker installed yet, you can follow the tutorial here to install it: [Docker Installation](https://www.runoob.com/docker/ubuntu-docker-install.html)

Docker installation for full module has two methods. You can [use the lazy script](./Deployment_all.md#11-lazy-script) (author [@VanillaNahida](https://github.com/VanillaNahida))  
The script will automatically help you download the required files and configuration files. You can also use [manual deployment](./Deployment_all.md#12-manual-deployment) to build from scratch.

### 1.1 Lazy Script
Simple deployment, you can refer to [video tutorial](https://www.bilibili.com/video/BV17bbvzHExd/), text tutorial as follows:
> [!NOTE]  
> Currently only supports Ubuntu server one-click deployment, other systems have not been tried and may have some strange bugs

Use SSH tool to connect to the server and execute the following script with root privileges:
```bash
sudo bash -c "$(wget -qO- https://ghfast.top/https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/main/docker-setup.sh)"
```

The script will automatically complete the following operations:
> 1. Install Docker
> 2. Configure image sources
> 3. Download/pull images
> 4. Download speech recognition model files
> 5. Guide server configuration
>

After execution and simple configuration, refer to [4. Run Program](#4-run-program) and [5. Restart xiaozhi-esp32-server](#5-restart-xiaozhi-esp32-server) for the 3 most important things mentioned, complete these three configurations and you can use it.

### 1.2 Manual Deployment

#### 1.2.1 Create Directory

After installation, you need to find a directory to place the configuration files for this project. For example, we can create a new folder called `xiaozhi-server`.

After creating the directory, you need to create `data` folder and `models` folder under `xiaozhi-server`, and create `SenseVoiceSmall` folder under `models`.

The final directory structure is as follows:

```
xiaozhi-server
  ├─ data
  ├─ models
     ├─ SenseVoiceSmall
```

#### 1.2.2 Download Speech Recognition Model Files

This project's speech recognition model uses the `SenseVoiceSmall` model by default for speech-to-text conversion. Because the model is large, it needs to be downloaded separately. After downloading, put the `model.pt` file in the `models/SenseVoiceSmall` directory. Choose one of the two download routes below.

- Route 1: Alibaba ModelScope download [SenseVoiceSmall](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt)
- Route 2: Baidu Netdisk download [SenseVoiceSmall](https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna) Extraction code: `qvna`

#### 1.2.3 Download Configuration Files

You need to download two configuration files: `docker-compose_all.yaml` and `config_from_api.yaml`. You need to download these two files from the project repository.

##### 1.2.3.1 Download docker-compose_all.yaml

Open [this link](../main/xiaozhi-server/docker-compose_all.yml) with your browser.

Find the button named `RAW` on the right side of the page. Next to the `RAW` button, find the download icon, click the download button to download the `docker-compose_all.yml` file. Download the file to your `xiaozhi-server`.

Or directly execute `wget https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/refs/heads/main/main/xiaozhi-server/docker-compose_all.yml` to download.

After downloading, return to this tutorial to continue.

##### 1.2.3.2 Download config_from_api.yaml

Open [this link](../main/xiaozhi-server/config_from_api.yaml) with your browser.

Find the button named `RAW` on the right side of the page. Next to the `RAW` button, find the download icon, click the download button to download the `config_from_api.yaml` file. Download the file to the `data` folder under your `xiaozhi-server`, then rename the `config_from_api.yaml` file to `.config.yaml`.

Or directly execute `wget https://raw.githubusercontent.com/xinnan-tech/xiaozhi-esp32-server/refs/heads/main/main/xiaozhi-server/config_from_api.yaml` to download and save.

After downloading the configuration files, let's confirm that the files in the entire `xiaozhi-server` are as follows:

```
xiaozhi-server
  ├─ docker-compose_all.yml
  ├─ data
    ├─ .config.yaml
  ├─ models
     ├─ SenseVoiceSmall
       ├─ model.pt
```

If your file directory structure is also as above, continue. If not, carefully check if you missed any operations.

## 2. Backup Data

If you have successfully run the control panel before and have saved your key information, please first copy important data from the control panel. Because during the upgrade process, the original data may be overwritten.

## 3. Clear Historical Version Images and Containers
Next, open command line tool, use `Terminal` or `Command Line` tool to enter your `xiaozhi-server`, execute the following commands:

```
docker compose -f docker-compose_all.yml down

docker stop xiaozhi-esp32-server
docker rm xiaozhi-esp32-server

docker stop xiaozhi-esp32-server-web
docker rm xiaozhi-esp32-server-web

docker stop xiaozhi-esp32-server-db
docker rm xiaozhi-esp32-server-db

docker stop xiaozhi-esp32-server-redis
docker rm xiaozhi-esp32-server-redis

docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
docker rmi ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:web_latest
```

## 4. Run Program
Execute the following command to start new version containers:

```
docker compose -f docker-compose_all.yml up -d
```

After execution, execute the following command to view log information:

```
docker logs -f xiaozhi-esp32-server-web
```

When you see output logs, it means your `Control Panel` has started successfully.

```
2025-xx-xx 22:11:12.445 [main] INFO  c.a.d.s.b.a.DruidDataSourceAutoConfigure - Init DruidDataSource
2025-xx-xx 21:28:53.873 [main] INFO  xiaozhi.AdminApplication - Started AdminApplication in 16.057 seconds (process running for 17.941)
http://localhost:8002/xiaozhi/doc.html
```

Please note that at this moment only the `Control Panel` can run. If port 8000 `xiaozhi-esp32-server` reports errors, don't worry about it for now.

At this time, you need to use a browser to open the `Control Panel`, link: http://127.0.0.1:8002, register the first user. The first user is the super administrator, and subsequent users are regular users. Regular users can only bind devices and configure agents; super administrators can perform model management, user management, parameter configuration and other functions.

Next, you need to do three important things:

### First Important Thing

Use the super administrator account to login to the control panel, find `Parameter Management` in the top menu, find the first data in the list, parameter code is `server.secret`, copy it to `Parameter Value`.

`server.secret` needs explanation. This `Parameter Value` is very important, its function is to let our `Server` side connect to `manager-api`. `server.secret` is a key that is automatically randomly generated each time the manager module is deployed from scratch.

After copying the `Parameter Value`, open the `.config.yaml` file in the `data` directory under `xiaozhi-server`. At this moment, your configuration file content should be like this:

```
manager-api:
  url:  http://127.0.0.1:8002/xiaozhi
  secret: your_server.secret_value
```
1. Copy the `Parameter Value` of `server.secret` you just copied from the `Control Panel` to the `secret` in the `.config.yaml` file.

2. Because you are using docker deployment, change the `url` to `http://xiaozhi-esp32-server-web:8002/xiaozhi`

3. Because you are using docker deployment, change the `url` to `http://xiaozhi-esp32-server-web:8002/xiaozhi`

4. Because you are using docker deployment, change the `url` to `http://xiaozhi-esp32-server-web:8002/xiaozhi`

Similar to this effect:
```
manager-api:
  url: http://xiaozhi-esp32-server-web:8002/xiaozhi
  secret: 12345678-xxxx-xxxx-xxxx-123456789000
```

After saving, continue to do the second important thing.

### Second Important Thing

Use the super administrator account to login to the control panel, find `Model Configuration` in the top menu, then click `Large Language Model` in the left sidebar, find the first data `Zhipu AI`, click the `Modify` button, after the modification box pops up, fill in the key you registered for `Zhipu AI` into `API Key`. Then click save.

## 5. Restart xiaozhi-esp32-server

Next, open command line tool, use `Terminal` or `Command Line` tool to input:
```
docker restart xiaozhi-esp32-server
docker logs -f xiaozhi-esp32-server
```
If you can see logs similar to the following, it indicates successful Server startup:

```
25-02-23 12:01:09[core.websocket_server] - INFO - Websocket address is      ws://xxx.xx.xx.xx:8000/xiaozhi/v1/
25-02-23 12:01:09[core.websocket_server] - INFO - =======The above address is websocket protocol address, please do not access with browser=======
25-02-23 12:01:09[core.websocket_server] - INFO - If you want to test websocket, please use Google Chrome to open test_page.html in the test directory
25-02-23 12:01:09[core.websocket_server] - INFO - =======================================================
```

Since you are using full module deployment, you have two important interfaces that need to be written into esp32.

OTA Interface:
```
http://your_host_machine_lan_ip:8002/xiaozhi/ota/
```

Websocket Interface:
```
ws://your_host_machine_ip:8000/xiaozhi/v1/
```

### Third Important Thing

Use the super administrator account to login to the control panel, find `Parameter Management` in the top menu, find parameter code `server.websocket`, enter your `Websocket Interface`.

Use the super administrator account to login to the control panel, find `Parameter Management` in the top menu, find parameter code `server.ota`, enter your `OTA Interface`.

Next, you can start operating your esp32 device. You can either `compile esp32 firmware yourself` or configure to use `Brother Xia's compiled firmware version 1.6.1 or above`. Choose one of the two:

1. [Compile your own esp32 firmware](firmware-build.md).

2. [Configure custom server based on Brother Xia's compiled firmware](firmware-setting.md).

# Method 2: Local Source Code Running Full Module

## 1. Install MySQL Database

If MySQL is already installed on the local machine, you can directly create a database named `xiaozhi_esp32_server` in the database.

```sql
CREATE DATABASE xiaozhi_esp32_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

If you don't have MySQL yet, you can install mysql through docker:

```
docker run --name xiaozhi-esp32-server-db -e MYSQL_ROOT_PASSWORD=123456 -p 3306:3306 -e MYSQL_DATABASE=xiaozhi_esp32_server -e MYSQL_INITDB_ARGS="--character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci" -e TZ=Asia/Shanghai -d mysql:latest
```

## 2. Install Redis

If you don't have Redis yet, you can install redis through docker:

```
docker run --name xiaozhi-esp32-server-redis -d -p 6379:6379 redis
```

## 3. Run manager-api Program

3.1 Install JDK21, set JDK environment variables

3.2 Install Maven, set Maven environment variables

3.3 Use VSCode programming tool, install Java environment related plugins

3.4 Use VSCode programming tool to load manager-api module

Configure database connection information in `src/main/resources/application-dev.yml`:

```
spring:
  datasource:
    username: root
    password: 123456
```
Configure Redis connection information in `src/main/resources/application-dev.yml`:
```
spring:
    data:
      redis:
        host: localhost
        port: 6379
        password:
        database: 0
```

3.5 Run main program

This project is a SpringBoot project, startup method is:
Open `Application.java` and run the `Main` method to start:

```
Path address:
src/main/java/xiaozhi/AdminApplication.java
```

When you see output logs, it means your `manager-api` has started successfully.

```
2025-xx-xx 22:11:12.445 [main] INFO  c.a.d.s.b.a.DruidDataSourceAutoConfigure - Init DruidDataSource
2025-xx-xx 21:28:53.873 [main] INFO  xiaozhi.AdminApplication - Started AdminApplication in 16.057 seconds (process running for 17.941)
http://localhost:8002/xiaozhi/doc.html
```

## 4. Run manager-web Program

4.1 Install nodejs

4.2 Use VSCode programming tool to load manager-web module

Terminal command enter manager-web directory:

```
npm install
```
Then start:
```
npm run serve
```

Please note, if your manager-api interface is not at `http://localhost:8002`, please modify the path in `main/manager-web/.env.development` during development.

After successful running, you need to use a browser to open the `Control Panel`, link: http://127.0.0.1:8001, register the first user. The first user is the super administrator, and subsequent users are regular users. Regular users can only bind devices and configure agents; super administrators can perform model management, user management, parameter configuration and other functions.

Important: After successful registration, use the super administrator account to login to the control panel, find `Model Configuration` in the top menu, then click `Large Language Model` in the left sidebar, find the first data `Zhipu AI`, click the `Modify` button, after the modification box pops up, fill in the key you registered for `Zhipu AI` into `API Key`. Then click save.

Important: After successful registration, use the super administrator account to login to the control panel, find `Model Configuration` in the top menu, then click `Large Language Model` in the left sidebar, find the first data `Zhipu AI`, click the `Modify` button, after the modification box pops up, fill in the key you registered for `Zhipu AI` into `API Key`. Then click save.

Important: After successful registration, use the super administrator account to login to the control panel, find `Model Configuration` in the top menu, then click `Large Language Model` in the left sidebar, find the first data `Zhipu AI`, click the `Modify` button, after the modification box pops up, fill in the key you registered for `Zhipu AI` into `API Key`. Then click save.

## 5. Install Python Environment

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

## 6. Install Project Dependencies

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

### 7. Download Speech Recognition Model Files

This project's speech recognition model uses the `SenseVoiceSmall` model by default for speech-to-text conversion. Because the model is large, it needs to be downloaded separately. After downloading, put the `model.pt` file in the `models/SenseVoiceSmall` directory. Choose one of the two download routes below.

- Route 1: Alibaba ModelScope download [SenseVoiceSmall](https://modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt)
- Route 2: Baidu Netdisk download [SenseVoiceSmall](https://pan.baidu.com/share/init?surl=QlgM58FHhYv1tFnUT_A8Sg&pwd=qvna) Extraction code: `qvna`

## 8. Configure Project Files

Use the super administrator account to login to the control panel, find `Parameter Management` in the top menu, find the first data in the list, parameter code is `server.secret`, copy it to `Parameter Value`.

`server.secret` needs explanation. This `Parameter Value` is very important, its function is to let our `Server` side connect to `manager-api`. `server.secret` is a key that is automatically randomly generated each time the manager module is deployed from scratch.

If your `xiaozhi-server` directory doesn't have `data`, you need to create the `data` directory.
If you don't have the `.config.yaml` file under `data`, you can copy the `config_from_api.yaml` file from the `xiaozhi-server` directory to `data` and rename it to `.config.yaml`.

After copying the `Parameter Value`, open the `.config.yaml` file in the `data` directory under `xiaozhi-server`. At this moment, your configuration file content should be like this:

```
manager-api:
  url: http://127.0.0.1:8002/xiaozhi
  secret: your_server.secret_value
```

Copy the `Parameter Value` of `server.secret` you just copied from the `Control Panel` to the `secret` in the `.config.yaml` file.

Similar to this effect:
```
manager-api:
  url: http://127.0.0.1:8002/xiaozhi
  secret: 12345678-xxxx-xxxx-xxxx-123456789000
```

## 5. Run Project

```
# Make sure to execute in xiaozhi-server directory
conda activate xiaozhi-esp32-server
python app.py
```

If you can see logs similar to the following, it indicates that this project service has started successfully:

```
25-02-23 12:01:09[core.websocket_server] - INFO - Server is running at ws://xxx.xx.xx.xx:8000/xiaozhi/v1/
25-02-23 12:01:09[core.websocket_server] - INFO - =======The above address is websocket protocol address, please do not access with browser=======
25-02-23 12:01:09[core.websocket_server] - INFO - If you want to test websocket, please use Google Chrome to open test_page.html in the test directory
25-02-23 12:01:09[core.websocket_server] - INFO - =======================================================
```

Since you are using full module deployment, you have two important interfaces.

OTA Interface:
```
http://your_computer_lan_ip:8002/xiaozhi/ota/
```

Websocket Interface:
```
ws://your_computer_lan_ip:8000/xiaozhi/v1/
```

You must write the above two interface addresses into the control panel: they will affect websocket address distribution and automatic upgrade functionality.

1. Use the super administrator account to login to the control panel, find `Parameter Management` in the top menu, find parameter code `server.websocket`, enter your `Websocket Interface`.

2. Use the super administrator account to login to the control panel, find `Parameter Management` in the top menu, find parameter code `server.ota`, enter your `OTA Interface`.

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
7. [News plugin source configuration guide](./newsnow_plugin_config.md)<br/>
8. [Weather plugin usage guide](./weather-integration.md)<br/>

## Voice Cloning and Local Voice Deployment Related Tutorials
1. [How to deploy and integrate index-tts local voice](./index-stream-integration.md)<br/>
2. [How to deploy and integrate fish-speech local voice](./fish-speech-integration.md)<br/>
3. [How to deploy and integrate PaddleSpeech local voice](./paddlespeech-deploy.md)<br/>

## Performance Testing Tutorials
1. [Component speed testing guide](./performance_tester.md)<br/>
2. [Regular public test results](https://github.com/xinnan-tech/xiaozhi-performance-research)<br/>
