# Xiaozhi ESP32 Open Source Server and Home Assistant Integration Guide

[TOC]

-----

## Introduction

This document will guide you on how to integrate ESP32 devices with Home Assistant.

## Prerequisites

- Home Assistant is already installed and configured
- For this tutorial, I chose the model: free ChatGLM, which supports function call

## Pre-setup Operations (Required)

### 1. Get HA Network Address Information

Please visit your Home Assistant network address. For example, my HA address is 192.168.4.7, and the port is the default 8123, so open in browser:

```
http://192.168.4.7:8123
```

> Manual method to query HA's IP address **(only applicable when xiaozhi esp32-server and HA are deployed on the same network device [e.g., same wifi])**:
>
> 1. Enter Home Assistant (frontend).
>
> 2. Click bottom left **Settings** → **System** → **Network**.
>
> 3. Scroll to the bottom `Home Assistant website` area, in the `local network` section, click the `eye` button to see the currently used IP address (like `192.168.1.10`) and network interface. Click `copy link` to copy directly.
>
>    ![image-20250504051716417](images/image-ha-integration-01.png)

Or, if you have already set up a directly accessible Home Assistant OAuth address, you can also directly access in browser:

```
http://homeassistant.local:8123
```

### 2. Login to Home Assistant to Get Development Key

Login to Home Assistant, click `bottom left avatar -> Personal`, switch to `Security` tab, scroll to bottom `Long-lived access tokens` to generate api_key, and copy and save it. All subsequent methods need this api key and it only appears once (tip: You can save the generated QR code image, and later scan the QR code to extract the api key again).

## Method 1: HA Control Function Co-built by Xiaozhi Community

### Function Description

- If you need to add new devices later, this method requires manually restarting the `xiaozhi-esp32-server service` to update device information **(Important)**.

- You need to ensure that you have integrated `Xiaomi Home` in Home Assistant and imported Mijia devices into Home Assistant.

- You need to ensure that `xiaozhi-esp32-server Control Panel` can be used normally.

- My `xiaozhi-esp32-server Control Panel` and `Home Assistant` are deployed on the same machine on another port, version is `0.3.10`

  ```
  http://192.168.4.7:8002
  ```

### Configuration Steps

#### 1. Login to Home Assistant to Organize Device List to Control

Login to Home Assistant, click `Settings` in the bottom left, then enter `Devices & Services`, then click `Entities` at the top.

Then search for the switches you want to control in entities. After results appear, click one of the results in the list, which will show a switch interface.

In the switch interface, try clicking the switch to see if it turns on/off with our clicks. If it can be operated, it means it's properly connected to the network.

Then find the settings button in the switch panel, click it, and you can view the `Entity ID` of this switch.

Open a notepad and organize data in this format:

Location + English comma + Device name + English comma + `Entity ID` + English semicolon

For example, I'm at the office, I have a toy light, its identifier is switch.cuco_cn_460494544_cp1_on_p_2_1, then I write this data:

```
Office,Toy Light,switch.cuco_cn_460494544_cp1_on_p_2_1;
```

Of course, I might need to control two lights eventually, so my final result is:

```
Office,Toy Light,switch.cuco_cn_460494544_cp1_on_p_2_1;
Office,Desk Lamp,switch.iot_cn_831898993_socn1_on_p_2_1;
```

This string, we call it "device list string", needs to be saved for later use.

#### 2. Login to Control Panel

![image-20250504051716417](images/image-ha-integration-06.png)

Use administrator account to login to the Control Panel. In `Agent Management`, find your agent, then click `Configure Role`.

Set intent recognition to `Function Call` or `LLM Intent Recognition`. You will see an `Edit Functions` button on the right. Click the `Edit Functions` button, and a `Function Management` box will pop up.

In the `Function Management` box, you need to check `Home Assistant Device Status Query` and `Home Assistant Device Status Modification`.

After checking, click `Home Assistant Device Status Query` in `Selected Functions`, then configure your Home Assistant address, key, and device list string in `Parameter Configuration`.

After editing, click `Save Configuration`. The `Function Management` box will hide, then click save agent configuration.

After successful saving, you can wake up the device for control.

#### 3. Wake Up Device for Control

Try saying to esp32, "Turn on XXX light"

## Method 2: Using Home Assistant's Voice Assistant as LLM Tool for Xiaozhi

### Function Description

- This method has a serious drawback - **this method cannot use the function_call plugin capabilities of Xiaozhi's open source ecosystem**, because using Home Assistant as Xiaozhi's LLM tool transfers intent recognition capabilities to Home Assistant. However, **this method allows you to experience native Home Assistant operation functions, and Xiaozhi's chat capabilities remain unchanged**. If you mind this, you can use [Method 3](##Method 3: Using Home Assistant's MCP Service (Recommended)) which is also supported by Home Assistant and allows maximum experience of Home Assistant functions.

### Configuration Steps:

#### 1. Configure Home Assistant's Large Model Voice Assistant.

**You need to configure Home Assistant's voice assistant or large model tool in advance.**

#### 2. Get Home Assistant's Language Assistant Agent ID.

1. Enter the Home Assistant page. Click `Developer Tools` on the left.
2. In the opened `Developer Tools`, click the `Actions` tab (as shown in operation 1), find or enter `conversation.process (Conversation - Process)` in the page's `Action` option and select `Conversation: Process` (as shown in operation 2).

![image-20250504043539343](images/image-ha-integration-02.png)

3. Check the `agent` option on the page, select your configured voice assistant name in the highlighted `conversation agent`, as shown, mine is configured as `ZhipuAi` and selected.

![image-20250504043854760](images/image-ha-integration-03.png)

4. After selection, click `Enter YAML Mode` at the bottom left of the form.

![image-20250504043951126](images/image-ha-integration-04.png)

5. Copy the agent-id value, for example, mine in the image is `01JP2DYMBDF7F4ZA2DMCF2AGX2` (for reference only).

![image-20250504044046466](images/image-ha-integration-05.png)

6. Switch to the Xiaozhi open source server `xiaozhi-esp32-server`'s `config.yaml` file, in the LLM configuration, find Home Assistant, set your Home Assistant network address, Api key and the agent_id you just queried.
7. Modify the `selected_module` property's `LLM` to `HomeAssistant` and `Intent` to `nointent` in the `config.yaml` file.
8. Restart the Xiaozhi open source server `xiaozhi-esp32-server` to use normally.

## Method 3: Using Home Assistant's MCP Service (Recommended)

### Function Description

- You need to integrate and install the HA integration in Home Assistant in advance - [Model Context Protocol Server](https://www.home-assistant.io/integrations/mcp_server/).

- This method and Method 2 are both official solutions provided by HA. Unlike Method 2, you can normally use the open source co-built plugins of Xiaozhi open source server `xiaozhi-esp32-server`, while allowing you to freely use any LLM large model that supports function_call functionality.

### Configuration Steps

#### 1. Install Home Assistant's MCP Service Integration.

Integration official website - [Model Context Protocol Server](https://www.home-assistant.io/integrations/mcp_server/).

Or follow these manual operations.

> - Go to Home Assistant page's **[Settings > Devices & Services](https://my.home-assistant.io/redirect/integrations)**.
>
> - In the bottom right corner, select the **[Add Integration](https://my.home-assistant.io/redirect/config_flow_start?domain=mcp_server)** button.
>
> - Select **Model Context Protocol Server** from the list.
>
> - Follow the on-screen instructions to complete setup.

#### 2. Configure Xiaozhi Open Source Server MCP Configuration Information

Enter the `data` directory and find the `.mcp_server_settings.json` file.

If you don't have the `.mcp_server_settings.json` file in your `data` directory:
- Please copy the `mcp_server_settings.json` file from the root directory of the `xiaozhi-server` folder to the `data` directory and rename it to `.mcp_server_settings.json`
- Or [download this file](https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/main/xiaozhi-server/mcp_server_settings.json), download it to the `data` directory, and rename it to `.mcp_server_settings.json`

Modify the content in `"mcpServers"`:

```json
"Home Assistant": {
      "command": "mcp-proxy",
      "args": [
        "http://YOUR_HA_HOST/mcp_server/sse"
      ],
      "env": {
        "API_ACCESS_TOKEN": "YOUR_API_ACCESS_TOKEN"
      }
},
```

Note:

1. **Replace configuration:**
   - Replace `YOUR_HA_HOST` in `args` with your HA service address. If your service address already includes https/http (e.g., `http://192.168.1.101:8123`), you only need to fill in `192.168.1.101:8123`.
   - Replace `YOUR_API_ACCESS_TOKEN` in `env`'s `API_ACCESS_TOKEN` with the development key api key you obtained earlier.
2. **If you add configuration in the `"mcpServers"` brackets and there are no new `mcpServers` configurations afterwards, you need to remove the last comma `,`**, otherwise parsing may fail.

**Final effect reference (as follows)**:

```json
 "mcpServers": {
    "Home Assistant": {
      "command": "mcp-proxy",
      "args": [
        "http://192.168.1.101:8123/mcp_server/sse"
      ],
      "env": {
        "API_ACCESS_TOKEN": "abcd.efghi.jkl"
      }
    }
  }
```

#### 3. Configure Xiaozhi Open Source Server System Configuration

1. **Choose any LLM large model that supports function_call as Xiaozhi's LLM chat assistant (but don't choose Home Assistant as LLM tool)**. For this tutorial, I chose the model: free ChatGLM, which supports function call, but sometimes the calls are not very stable. If you want stability, it's recommended to set LLM to: DoubaoLLM, using the specific model_name: doubao-1-5-pro-32k-250115.

2. Switch to the Xiaozhi open source server `xiaozhi-esp32-server`'s `config.yaml` file, set your LLM large model configuration, and adjust the `Intent` in `selected_module` configuration to `function_call`.

3. Restart the Xiaozhi open source server `xiaozhi-esp32-server` to use normally.
