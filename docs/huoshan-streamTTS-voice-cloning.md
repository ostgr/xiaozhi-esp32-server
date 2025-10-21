# Control Panel Volcano Double Stream TTS + Voice Cloning Configuration Tutorial

This tutorial is divided into 4 stages: Preparation Stage, Configuration Stage, Cloning Stage, and Usage Stage. It mainly introduces the process of configuring Volcano Double Stream TTS + Voice Cloning through the control panel.

## Stage 1: Preparation Stage
The super administrator should first open the Volcano Engine service and obtain the App Id and Access Token. By default, Volcano Engine will provide one voice resource. This voice resource needs to be copied to this project.

If you want to clone multiple voices, you need to purchase and open multiple voice resources. Just copy each voice resource's Voice ID (S_xxxxx) to this project. Then assign them to system accounts for use. Here are the detailed steps:

### 1. Open Volcano Engine Service
Visit https://console.volcengine.com/speech/app, create an application in Application Management, check Speech Synthesis Large Model and Voice Cloning Large Model.

### 2. Get Voice Resource ID
Visit https://console.volcengine.com/speech/service/9999, copy three items: App Id, Access Token, and Voice ID (S_xxxxx). As shown in the image:

![Get Voice Resource](images/image-clone-integration-01.png)

## Stage 2: Configure Volcano Engine Service

### 1. Fill in Volcano Engine Configuration

Use the super administrator account to login to the control panel, click [Model Configuration] at the top, then click [Speech Synthesis] on the left side of the model configuration page, search and find "Volcano Double Stream Speech Synthesis", click modify, fill your Volcano Engine's `App Id` into the [Application ID] field, fill `Access Token` into the [Access Token] field. Then save.

### 2. Assign Voice Resource ID to System Account

Use the super administrator account to login to the control panel, click [Voice Cloning], [Voice Resources] at the top.

Click the add button, select "Volcano Double Stream Speech Synthesis" in [Platform Name];

Fill in your Volcano Engine's Voice Resource ID (S_xxxxx) in [Voice Resource ID], press Enter after filling;

Select the system account you want to assign to in [Belonging Account], you can assign it to yourself. Then click save.

## Stage 3: Cloning Stage

If after logging in, clicking [Voice Cloning] >> [Voice Cloning] at the top shows [Your account currently has no voice resources, please contact administrator to assign voice resources], it means you haven't assigned voice resource ID to this account in Stage 2. Then go back to Stage 2 and assign voice resources to the corresponding account.

If after logging in, clicking [Voice Cloning] >> [Voice Cloning] at the top, you can see the corresponding voice list. Please continue.

You will see the corresponding voice list in the list. Select one of the voice resources and click the [Upload Audio] button. After uploading, you can preview the sound or cut a certain segment of sound. After confirmation, click the [Upload Audio] button.
![Upload Audio](images/image-clone-integration-02.png)

After uploading audio, you will see in the list that the corresponding voice will change to "Pending Cloning" status. Click the [Clone Now] button. Wait 1~2 seconds for the result.

If cloning fails, please hover your mouse over the "Error Information" icon, which will display the reason for failure.

If cloning succeeds, you will see in the list that the corresponding voice will change to "Training Successful" status. At this time, you can click the modify button in the [Voice Name] column to modify the name of the voice resource for easier selection and use later.

## Stage 4: Usage Stage

Click [Agent Management] at the top, select any agent, and click the [Configure Role] button.

Select "Volcano Double Stream Speech Synthesis" for Text-to-Speech (TTS). In the list, find the voice resource with "Cloned Voice" in the name (as shown in the image), select it, and click save.
![Select Voice](images/image-clone-integration-03.png)

Next, you can wake up Xiaozhi and have a conversation with it.
