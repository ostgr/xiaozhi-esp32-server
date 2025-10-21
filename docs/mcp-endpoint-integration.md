# MCP Endpoint Usage Guide

This tutorial uses Brother Xia's open source MCP calculator function as an example to introduce how to integrate your own custom MCP service into your own endpoint.

The prerequisite for this tutorial is that your `xiaozhi-server` has already enabled MCP endpoint functionality. If you haven't enabled it yet, you can first enable it according to [this tutorial](./mcp-endpoint-enable.md).

# How to Integrate a Simple MCP Function for an Agent, Such as Calculator Function

### If You Are Using Full Module Deployment
If you are using full module deployment, you can enter the control panel, agent management, click `Configure Role`, on the right side of `Intent Recognition`, there is an `Edit Functions` button.

Click this button. In the popup page, at the bottom, there will be `MCP Endpoint`, normally it will display this agent's `MCP Endpoint Address`. Next, we will extend this agent with a calculator function based on MCP technology.

This `MCP Endpoint Address` is very important, you will use it later.

### If You Are Using Single Module Deployment
If you are using single module deployment and you have already configured the MCP endpoint address in the configuration file, then normally, when single module deployment starts, it will output the following logs:
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

As above, the output `mcp endpoint is` with `ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc` is your `MCP Endpoint Address`.

This `MCP Endpoint Address` is very important, you will use it later.

## Step 1: Download Brother Xia's MCP Calculator Project Code

Open Brother Xia's [calculator project](https://github.com/78/mcp-calculator) in browser.

After opening, find a green button on the page that says `Code`, click it, and you'll see the `Download ZIP` button.

Click it to download the project source code zip file. After downloading to your computer, extract it. At this time, its name might be `mcp-calculator-main`. You need to rename it to `mcp-calculator`. Next, we use command line to enter the project directory and install dependencies:

```bash
# Enter project directory
cd mcp-calculator

conda remove -n mcp-calculator --all -y
conda create -n mcp-calculator python=3.10 -y
conda activate mcp-calculator

pip install -r requirements.txt
```

## Step 2: Start

Before starting, first copy the MCP endpoint address from your control panel's agent.

For example, my agent's MCP address is:
```
ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
```

Start inputting command:

```bash
export MCP_ENDPOINT=ws://192.168.1.25:8004/mcp_endpoint/mcp/?token=abc
```

After inputting, start the program:

```bash
python mcp_pipe.py calculator.py
```

### If You Are Using Control Panel Deployment
If you are using control panel deployment, after starting, you can enter the control panel again, click refresh MCP access status, and you will see your extended function list.

### If You Are Using Single Module Deployment
If you are using single module deployment, when the device connects, it will output similar logs, indicating success:

```
250705 -INFO-Initializing MCP endpoint: wss://2662r3426b.vicp.fun/mcp_e 
250705 -INFO-Sending MCP endpoint initialization message
250705 -INFO-MCP endpoint connection successful
250705 -INFO-MCP endpoint initialization successful
250705 -INFO-Unified tool processor initialization complete
250705 -INFO-MCP endpoint server info: name=Calculator, version=1.9.4
250705 -INFO-MCP endpoint supported tool count: 1
250705 -INFO-All MCP endpoint tools retrieved, client ready
250705 -INFO-Tool cache refreshed
250705 -INFO-Current supported function list: [ 'get_time', 'get_lunar', 'play_music', 'get_weather', 'handle_exit_intent', 'calculator']
```
If it includes `'calculator'`, it means the device will be able to call the calculator tool based on intent recognition.
