import pyrealsense2 as rs
import numpy as np
from tabulate import tabulate
from websocket_server import WebsocketServer
import threading
import json
import os
import time

# =========================
# WEBSOCKET
# =========================

PORT = 8766
clients = []

def new_client(client, server):
    clients.append(client)
    print("[OBS] client connected")
  
def client_left(client, server):
    if client in clients:
        clients.remove(client)

def send_all(msg):
    for c in clients:
        try:
            server.send_message(c, msg)
        except:
            pass

server = WebsocketServer(host="127.0.0.1", port=PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)

# -----------------------------
# RealSense Setup
# -----------------------------
pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(
    rs.stream.depth,
    640,
    480,
    rs.format.z16,
    30
)

profile = pipeline.start(config)

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()


THRESHOLD = 0.1
last_values = []

def detectDifference(curr_values):
    if len(curr_values) != len(last_values):
        return 1

    for a, b in zip(curr_values, last_values):
        if abs(a - b) > THRESHOLD:
            return 1

    return 0


NUM_SECTORS = 5

# left_distance      = sector_min_distances[0]
# left_center        = sector_min_distances[1]
# center_distance    = sector_min_distances[2]
# right_center       = sector_min_distances[3]
# right_distance     = sector_min_distances[4]
def input_loop():
    global last_values
    try:
        while True:

            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()

            if not depth_frame:
                continue

            # Convert depth frame to numpy array
            depth_image = np.asanyarray(depth_frame.get_data())

            height, width = depth_image.shape

            sector_width = width // NUM_SECTORS

            # -------------------------------------------------
            # This variable contains all 5 closest distances
            # -------------------------------------------------
            sector_min_distances = []

            for sector in range(NUM_SECTORS):

                x_start = sector * sector_width

                if sector == NUM_SECTORS - 1:
                    x_end = width
                else:
                    x_end = (sector + 1) * sector_width

                sector_depth = depth_image[:, x_start:x_end]

                # Remove invalid pixels (0 depth)
                valid_depths = sector_depth[sector_depth > 0]

                if valid_depths.size == 0:
                    closest_distance_m = float("nan")
                else:
                    # Minimum depth in raw units
                    closest_distance_m = np.percentile(valid_depths, 5) * depth_scale

                sector_min_distances.append(closest_distance_m)


            table = []

            # =================================
            # Use for debugging purposes only
            # =================================

            # os.system("cls" if os.name == "nt" else "clear") # Clear terminal
            # for i, distance in enumerate(sector_min_distances):
            #     table.append([
            #         f"Sector {i+1}",
            #         f"{distance:.3f} m" if not np.isnan(distance) else "No Data"
            #     ])
            # print(tabulate(
            #     table,
            #     headers=["Closest Surface"],
            #     tablefmt="grid"
            # ))

            # =========================
            # SEND TO OBS
            # =========================
            if last_values is None or detectDifference(sector_min_distances):
                msg = json.dumps({
                    "type": "realsense",
                    "distances": sector_min_distances
                })

                send_all(msg)
                last_values = sector_min_distances
            

            time.sleep(0.05)

    finally:
        pipeline.stop()


# =========================
# START
# =========================

threading.Thread(target=input_loop, daemon=True).start()

print("====================================")
print(" Camera Distance Capture")
print(" ws://127.0.0.1:8766")
print("====================================")

try:
    server.run_forever()
finally:
    running = False