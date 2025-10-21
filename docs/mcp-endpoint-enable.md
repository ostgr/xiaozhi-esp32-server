# MCP Endpoint Deployment Usage Guide

This tutorial contains 3 parts:
- 1. How to deploy MCP endpoint service
- 2. How to configure MCP endpoint for full module deployment
- 3. How to configure MCP endpoint for single module deployment

# 1. How to Deploy MCP Endpoint Service

## Step 1: Download MCP Endpoint Project Source Code

Open [MCP endpoint project address](https://github.com/xinnan-tech/mcp-endpoint-server) in browser

After opening, find a green button on the page that says `Code`, click it, and you'll see the `Download ZIP` button.

Click it to download the project source code zip file. After downloading to your computer, extract it. At this time, its name might be `mcp-endpoint-server-main`. You need to rename it to `mcp-endpoint-server`.

## Step 2: Start Program
This project is a very simple project, it's recommended to run with docker. However, if you don't want to use docker, you can refer to [this page](https://github.com/xinnan-tech/mcp-endpoint-server/blob/main/README_dev.md) to run with source code. Below is the docker running method:

```
# Enter project source code root directory
cd mcp-endpoint-server

# Clear cache
docker compose -f docker-compose.yml down
docker stop mcp-endpoint-server
docker rm mcp-endpoint-server
docker rmi ghcr.nju.edu.cn/xinnan-tech/mcp-endpoint-server:latest

# Start docker container
docker compose -f docker-compose.yml up -d
# View logs
docker logs -f mcp-endpoint-server
```

At this time, the logs will output similar to the following:
```
250705 INFO-=====The following addresses are Control Panel/Single Module MCP endpoint addresses====
250705 INFO-Control Panel MCP parameter configuration: http://172.22.0.2:8004/mcp_endpoint/health?key=abc
250705 INFO-Single module deployment MCP endpoint: ws://172.22.0.2:8004/mcp_endpoint/mcp/?token=def
250705 INFO-=====Please choose to use according to specific deployment, do not leak to anyone======
```

Please copy the two interface addresses:

Since you are using docker deployment, you must not directly use the above addresses!

Since you are using docker deployment, you must not directly use the above addresses!

Since you are using docker deployment, you must not directly use the above addresses!

First copy the addresses and put them in a draft. You need to know what your computer's LAN IP is. For example, if my computer's LAN IP is `192.168.1.25`, then my original interface addresses:
```
Control Panel MCP parameter configuration: http://172.22.0.2:8004/mcp_endpoint/health?key=abc
Single module deployment MCP endpoint: ws://172.22.0.2:8004/mcp_endpoint/mcp/?token=def
```
should be changed to:
```
Control Panel MCP parameter configuration: http://192.168.1.25:8004/mcp_endpoint/health?key=abc
Single module deployment MCP endpoint: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

After changing, please use browser to directly access `Control Panel MCP parameter configuration`. When the browser shows code similar to this, it means success:
```
{"result":{"status":"success","connections":{"tool_connections":0,"robot_connections":0,"total_connections":0}},"error":null,"id":null,"jsonrpc":"2.0"}
```

Please keep the above two `interface addresses`, they will be used in the next step.

# 2. How to Configure MCP Endpoint for Full Module Deployment

If you are using full module deployment, use administrator account to login to control panel, click `Parameter Dictionary` at the top, select `Parameter Management` function.

Then search for parameter `server.mcp_endpoint`, at this time, its value should be `null`.
Click modify button, paste the `Control Panel MCP parameter configuration` from the previous step into `Parameter Value`. Then save.

If it can be saved successfully, it means everything is smooth, you can go to the agent to see the effect. If not successful, it means the control panel cannot access the mcp endpoint, most likely due to network firewall, or incorrect LAN IP.

# 3. How to Configure MCP Endpoint for Single Module Deployment

If you are using single module deployment, find your configuration file `data/.config.yaml`.
Search for `mcp_endpoint` in the configuration file. If not found, add `mcp_endpoint` configuration. Like mine:
```
server:
  websocket: ws://your_ip_or_domain:port/xiaozhi/v1/
  http_port: 8002
log:
  log_level: INFO

# There may be more configurations here..

mcp_endpoint: your_endpoint_websocket_address
```
At this time, please paste the `Single module deployment MCP endpoint` obtained from `How to deploy MCP endpoint service` into `mcp_endpoint`. Like this:

```
server:
  websocket: ws://your_ip_or_domain:port/xiaozhi/v1/
  http_port: 8002
log:
  log_level: INFO

# There may be more configurations here

mcp_endpoint: ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=def
```

After configuration, starting single module will output the following logs:
```
250705[__main__]-INFO-Initialize component: vad success SileroVAD
250705[__main__]-INFO-Initialize component: asr success FunASRServer
250705[__main__]-INFO-OTA interface is          http://192.168.1.25:8002/xiaozhi/ota/
250705[__main__]-INFO-Vision analysis interface is     http://192.168.1.25:8002/mcp/vision/explain
250705[__main__]-INFO-mcp endpoint is        ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
250705[__main__]-INFO-Websocket address is    ws://192.168.1.25:8000/xiaozhi/v1/
250705[__main__]-INFO-=======The above address is websocket protocol address, please do not access with browser=======
250705[__main__]-INFO-If you want to test websocket, please use Google Chrome to open test_page.html in the test directory
250705[__main__]-INFO-=============================================================
```

As above, if it can output similar `mcp endpoint is` with `ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc`, it means configuration is successful.
