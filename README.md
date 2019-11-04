# Rawige - the WebSocket client
Small yet powerful WebSocket debugging/reversing tool. Made with Python 3 + PyQt5 frontend and
[lomond][1] as a WebSocket library.

## Prerequisites
 - Python 3.7+ (will probably work with lower, but untested)
 
## Installation
(adapt commands for your system setup, e.g substitute `python` with `python3`)
```bash
git clone https://github.com/teidesu/rawige
cd rawige
# unnecessary but recommended
python -m venv venv
source venv/bin/activate
# /unnecessary but recommended
pip install -r requirements.txt
python -m rawige
```
You can then build a standalone binary:
```bash
pip install pyinstaller
pyinstaller rawige.spec 
```

## Features
 - SSL support (thanks to [lomond][1])
 - Proxy support
 - Compression suppport
 - Custom headers
 - Messages history
 - Favourite messages
 - Saving ans loading sessions
 - Multiple tabs
 - Multiple modes: plain, binary, hex, base64, json, bson

[1]: (https://github.com/wildfoundry/dataplicity-lomond)