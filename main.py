# Simple program to connect to a Meshtastic node and listen for incoming messages
import meshtastic.tcp_interface
from flask import Flask, Response, render_template
import threading
import time
import datetime
import os


from pubsub import pub
from meshtastic.protobuf import mesh_pb2, telemetry_pb2, portnums_pb2
from google.protobuf.json_format import MessageToDict
from collections import deque

# Config
NODE_IP = "192.168.86.243"
TIME_DISPLAY = "central"  # utc, central, epoch by default (empty)
LOG_FILE = "logoutput.txt"
MAX_LOG_LINES = 50000  # User-defined maximum number of lines for the log file

log_buffer = []
log_deque = deque(maxlen=MAX_LOG_LINES)  # Keep track of logs in memory

def log_output(message, first_in_block=False):
    """Append log messages to buffer, write to log file, and enforce max log size."""

    if first_in_block:
        message = f"*{message}"  # Prepend special character for first line in block

    print(message)  # Output to terminal
    log_buffer.append(message)  # Add to web stream buffer

    # Append to deque (maintaining MAX_LOG_LINES limit)
    log_deque.append(message)

    # Write to file while keeping line limit
    with open(LOG_FILE, "w", encoding="utf-8") as log_file:
        log_file.writelines("\n".join(log_deque) + "\n")


def format_timestamp(timestamp):
    if isinstance(timestamp, int) and timestamp > 0:
        utc_time = datetime.datetime.fromtimestamp(timestamp, datetime.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
        central_time = datetime.datetime.fromtimestamp(
            timestamp, datetime.timezone(datetime.timedelta(hours=-6))
        ).strftime('%Y-%m-%d %H:%M:%S CST')

        if TIME_DISPLAY == 'central':
            return central_time
        elif TIME_DISPLAY == 'utc':
            return utc_time
        return str(timestamp)  # Default to epoch if no valid option is passed
    return "N/A"


def event_stream():
    """Generator function to stream logs to the web client."""
    while True:
        if log_buffer:
            yield f"data: {log_buffer.pop(0)}\n\n"
        time.sleep(0.1)


def print_local_node_info(node_info):
    """Prints local node information, formats battery level, timestamps, and generates a map link."""
    log_output("-----------------------")
    log_output("----LOCAL NODE INFO----",first_in_block=True)  # This is the first message in a block

    latitude, longitude = None, None  # Initialize variables for map link

    for key, value in node_info.items():
        if isinstance(value, dict):  # Handle nested dictionaries like deviceMetrics, localStats, and position
            log_output(f" - {key}:")
            for sub_key, sub_value in value.items():
                if key == "deviceMetrics" and sub_key == "batteryLevel":
                    battery_level = float(sub_value)  # Ensure it's treated as a float
                    battery_display = f"{battery_level}%" if battery_level <= 100 else "Powered"
                    log_output(f"   - {sub_key}: {battery_display}")
                elif key == "position" and sub_key == "time":
                    formatted_time = format_timestamp(sub_value)
                    log_output(f"   - {sub_key}: {formatted_time}")
                else:
                    log_output(f"   - {sub_key}: {sub_value}")

                # Capture latitude and longitude for map link
                if key == "position":
                    if sub_key == "latitude":
                        latitude = sub_value
                    elif sub_key == "longitude":
                        longitude = sub_value
        else:
            log_output(f" - {key}: {value}")

    if latitude is not None and longitude is not None:
        log_output(f" - Map Link: https://www.google.com/maps?q={latitude},{longitude}")

def on_receive(packet, interface):
    """Callback function to handle received messages."""
    decoded = packet.get("decoded", {})
    log_output("-----------------------")
    log_output(
        f"{format_timestamp(packet.get('rxTime', 'N/A'))}     {decoded.get('portnum', 'UNKNOWN')}     {packet.get('fromId', 'Unknown')}     {packet.get('toId', 'Unknown')}",
        first_in_block=True  # This is the first message in a block
    )

    portnum_str = decoded.get("portnum", "UNKNOWN")
    portnum = getattr(portnums_pb2.PortNum, portnum_str, None)
    payload = decoded.get("payload", None)

    if payload:
        try:
            if portnum == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
                log_output(f" - Decoded Text Message: {decoded.get('text', 'N/A')}")
                for key, value in decoded.items():
                    log_output(f" - {key}: {value}")


            elif portnum == portnums_pb2.PortNum.POSITION_APP:
                #log_output("Full Position Dict:")
                position = mesh_pb2.Position()
                position.ParseFromString(payload)
                position_dict = MessageToDict(position)
                for key, value in position_dict.items():
                    log_output(f" - {key}: {value}")
                position = mesh_pb2.Position()
                position.ParseFromString(payload)
                position_dict = MessageToDict(position)
                if "latitudeI" in position_dict and "longitudeI" in position_dict:
                    latitude = position_dict["latitudeI"] / 10 ** 7
                    longitude = position_dict["longitudeI"] / 10 ** 7
                    log_output(f" - Map Link: https://www.google.com/maps?q={latitude},{longitude}")
                    log_output(f" - GPS Coordinates: ({latitude}, {longitude})")
                else:
                    log_output(" - Err: Position data structure is different than expected.")

            elif portnum == portnums_pb2.PortNum.TELEMETRY_APP:
                telemetry = telemetry_pb2.Telemetry()
                telemetry.ParseFromString(payload)
                telemetry_dict = MessageToDict(telemetry)

                for key, value in telemetry_dict.items():
                    if isinstance(value, dict):  # Handle nested dictionaries like deviceMetrics and localStats
                        log_output(f" - {key}:")  # Print the category name
                        for sub_key, sub_value in value.items():
                            if key == "deviceMetrics" and sub_key == "batteryLevel":
                                battery_level = float(sub_value)  # Ensure it's treated as a float
                                battery_display = f"{battery_level}%" if battery_level <= 100 else "Powered"
                                log_output(f"   - {sub_key}: {battery_display}")
                            else:
                                log_output(f"   - {sub_key}: {sub_value}")
                    else:
                        log_output(f" - {key}: {value}")

            elif portnum == portnums_pb2.PortNum.NODEINFO_APP:
                try:
                    user_info = mesh_pb2.User()
                    user_info.ParseFromString(payload)
                    user_dict = MessageToDict(user_info)

                    log_output("Full Node Info:")
                    for key, value in user_dict.items():
                        log_output(f" - {key}: {value}")

                    #log_output(f" - Long Name: {user_dict.get('longName', 'N/A')}")
                    #log_output(f" - Short Name: {user_dict.get('shortName', 'N/A')}")
                    #log_output(f" - Hardware Model: {user_dict.get('hwModel', 'N/A')}")

                except Exception as e:
                    log_output(f"Error decoding NODEINFO_APP payload: {e}")
                    log_output(f"Payload string: {payload}")


            elif portnum == portnums_pb2.PortNum.NEIGHBORINFO_APP:
                neighbor_info = mesh_pb2.NeighborInfo()
                neighbor_info.ParseFromString(payload)
                neighbor_dict = MessageToDict(neighbor_info)

                log_output("Full Neighbor Dict:")
                for key, value in neighbor_dict.items():
                    log_output(f" - {key}: {value}")

                log_output(f" - Node ID: {neighbor_dict.get('nodeId', 'N/A')}")
                log_output(f" - Last Heard: {format_timestamp(neighbor_dict.get('last_heard', 'N/A'))}")

                if "neighbors" in neighbor_dict and isinstance(neighbor_dict["neighbors"], list):
                    log_output(" - Neighbors:")
                    for neighbor in neighbor_dict["neighbors"]:
                        log_output(f"   - Neighbor Node ID: {neighbor.get('nodeId', 'N/A')}")
                        log_output(f"   - RSSI: {neighbor.get('rssi', 'N/A')}")
                        log_output(f"   - SNR: {neighbor.get('snr', 'N/A')}")
                else:
                    log_output(" - No neighbors found.")
            else:
                log_output("Received data on an unknown port.")
        except Exception as e:
            log_output(f"Error decoding payload: {e}")
            log_output(f"Payload string: {payload}")
    else:
        log_output("No payload to decode.")


# Establish connection
log_output(f"Connecting to Meshtastic node at {NODE_IP}")
iface = meshtastic.tcp_interface.TCPInterface(NODE_IP)
log_output("Connection established successfully!")

# Fetch node info explicitly
my_node_info = iface.getMyNodeInfo()
print_local_node_info(my_node_info)

pub.subscribe(on_receive, "meshtastic.receive")
log_output("Listening for incoming messages...")

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype='text/event-stream')


def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    log_output("Stopping listener.")
    iface.close()
