# Meshtastic Web Console

## Overview
The **Meshtastic Web Console** is a (SIMPLE) real-time logging application developed in python that connects to a Meshtastic node via WiFi and displays incoming messages in:
- **Terminal output**
- **A web-based console with real-time streaming**
- **A log file (`logoutput.txt`) with up to 50,000 retained lines**

### ✅ Features
- **Server-Sent Events (SSE) for real-time updates**
- **Synchronous logging to terminal, web, and file**
- **Timestamp formatting (Epoch, UTC, Central Time)**
- **Clickable links & stylized separators**
- **Logs are retained up to a user-defined limit**
- **Displays real-time telemetry, position, and text messages**

---

## 🔧 Installation

### **1️⃣ Install Python & Virtual Environment**
Ensure you have **Python 3.8+** installed.

```sh
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### **2️⃣ Install Dependencies**
Install required Python packages:
```sh
pip install -r requirements.txt
```

---

## 🚀 Running the Application
```sh
python main.py
```
This will:
1. Connect to your **Meshtastic Node** via **TCP**.
2. Start the **Flask Web Server** on `http://localhost:5000/`.
3. Stream messages to:
   - The terminal
   - The web app (`http://localhost:5000/`)
   - The log file (`logoutput.txt`)

---

## ⚙️ Configuration Parameters
Modify these in `.env` before running:

| Parameter          | Default Value      | Description |
|-------------------|--------------------|-------------|
| `NODE_IP`         | `"192.168.xx.xxx"` | IP Address of the Meshtastic node |
| `TIME_DISPLAY`    | `"central"`        | Timestamp format (`epoch`, `utc`, or `central`) |
| `LOG_FILE`        | `"logoutput.txt"`  | Path to the log file |
| `MAX_LOG_LINES`   | `50000`            | Maximum lines retained in the log file |

---

## 🖥️ Web Console
Once running, access the web interface at:
```
http://localhost:5000/
```
The console features:
- **Live real-time message streaming**
- **Automatic scrolling**
- **Clickable URLs**
- **Stylized message separators**
- **The first message in a block highlighted in red**

---

## 📄 Log File (`logoutput.txt`)
- All incoming messages are stored here.
- The **latest 50,000 lines** are retained (configurable in `MAX_LOG_LINES`).

---

## ❌ Stopping the Application
To stop the listener, use:
```sh
CTRL + C
```
Or, manually close the Python process.

---

## 📜 License
This project is open-source and free to use.

---

## 📸 Screenshot

![Screenshot 2025-02-17 112012](https://github.com/user-attachments/assets/8c355f60-837d-4261-8633-b8c0852183f5)

---

## 📝 To Do
- Handle TRACEROUTE_APP Messaging
- Implement Encryption
- Restart command/endpoint 
- Implement Bluetooth
- Implement a node.db for message correlation
