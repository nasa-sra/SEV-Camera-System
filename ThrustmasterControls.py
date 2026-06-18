import pygame
import json
import threading
from websocket_server import WebsocketServer

# =========================
# CONFIG
# =========================

WS_HOST = "127.0.0.1"
WS_PORT = 8765

DEADZONE = 0.06
SMOOTHING = 0.18

# WARTHOG DEFAULT MAPPING
# Axis 0 = roll (left/right) → BEST steering input
STEERING_AXIS = 0

# Optional fallback if your system remaps axes
FALLBACK_AXES = [0, 1]

# =========================
# STATE
# =========================

running = True
current = 0.0
target = 0.0
clients = []

# =========================
# WEBSOCKET
# =========================

def on_client_connected(client, server):
    clients.append(client)

def on_client_left(client, server):
    if client in clients:
        clients.remove(client)

server = WebsocketServer(host=WS_HOST, port=WS_PORT)
server.set_fn_new_client(on_client_connected)
server.set_fn_client_left(on_client_left)

def ws_thread():
    server.run_forever()

# =========================
# JOYSTICK INIT
# =========================

def init_joystick():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        raise Exception("No joystick detected")

    js = pygame.joystick.Joystick(0)
    js.init()

    print("Detected:", js.get_name())
    print("Axes:", js.get_numaxes())

    # WARTHOG FIX:
    # We explicitly use axis 0 (X roll)
    # because Warthog does NOT behave like generic gamepads
    return js, STEERING_AXIS

# =========================
# INPUT PROCESSING
# =========================

def apply_deadzone(v):
    if abs(v) < DEADZONE:
        return 0.0
    return v

# =========================
# LOOP
# =========================

def joystick_loop(js, axis):

    global running, current, target

    clock = pygame.time.Clock()

    while running:

        pygame.event.pump()

        raw = js.get_axis(axis)
        raw = apply_deadzone(raw)

        # invert if needed (Warthog often feels reversed depending setup)
        target = -raw * 100

        # smoothing (prevents jitter in OBS overlay)
        current += (target - current) * SMOOTHING

        msg = json.dumps({
            "type": "steering",
            "angle": current
        })

        for c in clients:
            try:
                server.send_message(c, msg)
            except:
                pass

        # ESC exit
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        clock.tick(60)

# =========================
# START
# =========================

def main():

    js, axis = init_joystick()

    threading.Thread(target=ws_thread, daemon=True).start()

    try:
        joystick_loop(js, axis)
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()