# Weather Plugin Usage Guide

## Overview

The weather plugin `get_weather` is one of the core features of the Xiaozhi ESP32 voice assistant, supporting voice queries for weather information across the country. The plugin is based on the QWeather API and provides real-time weather and 7-day weather forecast functionality.

## API Key Application Guide

### 1. Register QWeather Account

1. Visit [QWeather Console](https://console.qweather.com/)
2. Register an account and complete email verification
3. Login to the console

### 2. Create Application to Get API Key

1. After entering the console, click ["Project Management"](https://console.qweather.com/project?lang=zh) on the right → "Create Project"
2. Fill in project information:
   - **Project Name**: e.g., "Xiaozhi Voice Assistant"
3. Click Save
4. After the project is created, click "Create Credentials" in the project
5. Fill in credential information:
    - **Credential Name**: e.g., "Xiaozhi Voice Assistant"
    - **Authentication Method**: Select "API Key"
6. Click Save
7. Copy the `API Key` from the credentials - this is the first key configuration information

### 3. Get API Host

1. In the console, click ["Settings"](https://console.qweather.com/setting?lang=zh) → "API Host"
2. View your assigned exclusive `API Host` address - this is the second key configuration information

The above operations will give you two important configuration pieces: `API Key` and `API Host`

## Configuration Methods (Choose One)

### Method 1: If you are using Control Panel deployment (Recommended)

1. Login to the Control Panel
2. Go to "Role Configuration" page
3. Select the agent you want to configure
4. Click "Edit Functions" button
5. Find the "Weather Query" plugin in the right parameter configuration area
6. Check "Weather Query"
7. Enter the first key configuration `API Key` into `Weather Plugin API Key`
8. Enter the second key configuration `API Host` into `Developer API Host`
9. Save configuration, then save agent configuration

### Method 2: If you are only deploying single module xiaozhi-server

Configure in `data/.config.yaml`:

1. Enter the first key configuration `API Key` into `api_key`
2. Enter the second key configuration `API Host` into `api_host`
3. Enter your city into `default_location`, e.g., `Guangzhou`

```yaml
plugins:
  get_weather:
    api_key: "Your QWeather API key"
    api_host: "Your QWeather API host address"
    default_location: "Your default query city"
```
