# Fish Speech Integration Guide

Login to AutoDL and rent an image
Select image:
```
PyTorch / 2.1.0 / 3.10(ubuntu22.04) / cuda 12.1
```

After the machine starts, set up academic acceleration
```
source /etc/network_turbo
```

Enter the working directory
```
cd autodl-tmp/
```

Clone the project
```
git clone https://gitclone.com/github.com/fishaudio/fish-speech.git ; cd fish-speech
```

Install dependencies
```
pip install -e.
```

If there's an error, install portaudio
```
apt-get install portaudio19-dev -y
```

After installation, execute
```
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
```

Download models
```
cd tools
python download_models.py 
```

After downloading models, run the API server
```
python -m tools.api_server --listen 0.0.0.0:6006 
```

Then use your browser to go to the AutoDL instance page
```
https://autodl.com/console/instance/list
```

As shown in the image below, click the `Custom Service` button for your machine to enable port forwarding service
![Custom Service](images/fishspeech/autodl-01.png)

After the port forwarding service is set up, open the URL `http://localhost:6006/` on your local computer to access the fish-speech API
![Service Preview](images/fishspeech/autodl-02.png)

If you are using single module deployment, the core configuration is as follows
```
selected_module:
  TTS: FishSpeech
TTS:
  FishSpeech:
    reference_audio: ["config/assets/wakeup_words.wav",]
    reference_text: ["Hello, I'm Xiaozhi, a sweet-voiced Taiwanese girl. I'm so happy to meet you! What have you been up to lately? Don't forget to share some interesting stories with me, I love hearing gossip!",]
    api_key: "123"
    api_url: "http://127.0.0.1:6006/v1/tts"
```

Then restart the service
