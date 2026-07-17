import json
import time
import threading
import math
import pygame
import keyboard
from websocket_server import WebsocketServer

# =========================
# CONFIG
# =========================

PORT = 8765

STEERING_MIN = -100
STEERING_MAX = 100

SMOOTHING = 0.18

# joystick settings
JOY_DEADZONE = 0.12
JOY_AXIS = 2

# =========================
# STATE
# =========================

running = True
shutdown_once = False
clients = []
steering = 0

# =========================
# WEBSOCKET
# =========================

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

# There are two threads that may attempt a shutdown (the input loop and the main thread), so we need a lock to ensure that shutdown is only performed once
shutdown_lock = threading.Lock()

def close_server():
    global running, shutdown_once

    with shutdown_lock:
        if shutdown_once:
            return
        shutdown_once = True
        running = False

    print("[OBS] shutting down websocket server")
    server.shutdown()

server = WebsocketServer(host="127.0.0.1", port=PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
# =========================
# JOYSTICK INIT
# =========================

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("[JOYSTICK] No joystick detected")
    joystick = None
else:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print("[JOYSTICK] Connected:", joystick.get_name())

# =========================
# NONLINEAR RESPONSE CURVE (OPTION 3)
# =========================

def response_curve(x: float) -> float:
    # softer near center, stronger at extremes
    return math.copysign(abs(x) ** 1.6, x)

# =========================
# INPUT LOOP
# =========================

def input_loop():
    global steering, running

    last_sent = None

    while running:

        # ESC to exit
        if keyboard.is_pressed("esc"):
            close_server()
            break

        joy_value = 0

        # =========================
        # JOYSTICK INPUT
        # =========================
        if joystick:
            pygame.event.pump()

            joy_value = joystick.get_axis(JOY_AXIS)

            # deadzone
            if abs(joy_value) < JOY_DEADZONE:
                joy_value = 0
            else:
                # normalize outside deadzone
                sign = 1 if joy_value > 0 else -1
                joy_value = (abs(joy_value) - JOY_DEADZONE) / (1 - JOY_DEADZONE)
                joy_value = sign * min(1.0, joy_value)

            joy_value = response_curve(joy_value)

            # scale to steering range
            steering = joy_value * 55

        # =========================
        # KEYBOARD OVERRIDE
        # =========================
        if keyboard.is_pressed("space"):
            steering = 0
        else:
            left = keyboard.is_pressed("a")
            right = keyboard.is_pressed("d")
            if left and not right:
                steering = -70
            elif right and not left:
                steering = 70

        # =========================
        # CLAMPING
        # =========================
        steering = max(STEERING_MIN, min(STEERING_MAX, steering))

        # =========================
        # SEND TO OBS
        # =========================
        if last_sent is None or abs(steering - last_sent) > 0.2:

            msg = json.dumps({
                "type": "steering",
                "angle": steering
            })

            send_all(msg)
            last_sent = steering

        time.sleep(0.01)

# =========================
# START
# =========================

threading.Thread(target=input_loop, daemon=True).start()

print("====================================")
print(" OBS Steering Controller")
print(" Nonlinear steering curve enabled")
print(" ws://127.0.0.1:8765")
print(" ESC to quit")
print("====================================")

try:
    server.run_forever()
finally:
    # Typically, we only reach this point when ESC is pressed, and the server is already closed
    # However, if there was an error or keyboard interrupt, the server will still be open
    # Thus, we call close_server() to ensure the server is closed properly
    close_server()
    pygame.quit()