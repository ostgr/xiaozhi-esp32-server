# Local Docker Image Compilation Method

This project now uses GitHub automatic Docker compilation functionality. This document is prepared for friends who have local Docker image compilation needs.

1. Install Docker
```
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

2. Compile Docker Images
```
# Enter project root directory
# Compile server
docker build -t xiaozhi-esp32-server:server_latest -f ./Dockerfile-server .
# Compile web
docker build -t xiaozhi-esp32-server:web_latest -f ./Dockerfile-web .

# After compilation is complete, you can use docker-compose to start the project
# You need to modify docker-compose.yml to your own compiled image version
cd main/xiaozhi-server
docker-compose up -d
```
