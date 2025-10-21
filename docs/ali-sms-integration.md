# Alibaba Cloud SMS Integration Guide

Login to Alibaba Cloud Console and go to the "SMS Service" page: https://dysms.console.aliyun.com/overview

## Step 1: Add Signature
![Steps](images/alisms/sms-01.png)
![Steps](images/alisms/sms-02.png)

The above steps will generate a signature. Please enter it into the control panel parameter `aliyun.sms.sign_name`

## Step 2: Add Template
![Steps](images/alisms/sms-11.png)

The above steps will generate a template code. Please enter it into the control panel parameter `aliyun.sms.sms_code_template_code`

Note: The signature requires 7 business days for carrier registration approval before SMS can be sent successfully.

Note: The signature requires 7 business days for carrier registration approval before SMS can be sent successfully.

Note: The signature requires 7 business days for carrier registration approval before SMS can be sent successfully.

You can wait for the registration approval to complete before proceeding with the following steps.

## Step 3: Create SMS Account and Enable Permissions

Login to Alibaba Cloud Console and go to the "Access Control" page: https://ram.console.aliyun.com/overview?activeTab=overview

![Steps](images/alisms/sms-21.png)
![Steps](images/alisms/sms-22.png)
![Steps](images/alisms/sms-23.png)
![Steps](images/alisms/sms-24.png)
![Steps](images/alisms/sms-25.png)

The above steps will generate access_key_id and access_key_secret. Please enter them into the control panel parameters `aliyun.sms.access_key_id` and `aliyun.sms.access_key_secret`

## Step 4: Enable Mobile Registration Feature

1. Normally, after filling in all the above information, you should see this effect. If not, you may have missed a step.

![Steps](images/alisms/sms-31.png)

2. Enable non-administrator user registration by setting the parameter `server.allow_user_register` to `true`

3. Enable mobile registration feature by setting the parameter `server.enable_mobile_register` to `true`
![Steps](images/alisms/sms-32.png)
