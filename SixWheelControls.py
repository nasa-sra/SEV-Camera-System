import math
import keyboard
from websocket_server import WebsocketServer
import threading
import time
import json
import numpy as np

# =========================
# CONFIG
# =========================

PORT = 8765
CAR_DRIVE = 1
CRAB_DRIVE = 2
SPIN = 3
TIMESTEP = 0.01 # seconds
STEER_RATE = 15 # degrees per second
WHEELBASE = 4 # meters
WIDTH = 2.5 # meters
PI = 3.141592

# =========================
# STATE
# =========================

running = True
shutdown_once = False
clients = []
steer_mode = CAR_DRIVE
steering = 0
prev_motion_dir = None
MOTION_SCALE = 1.0

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
# INPUT LOOP
# =========================

def input_loop():
    global running, steering, steer_mode, prev_motion_dir

    current_time = time.time()
    last_time = current_time - TIMESTEP

    last_sent = None

    while running:
        if keyboard.is_pressed("esc"):
            close_server()
            break

        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        if keyboard.is_pressed("1"):
            steer_mode = CAR_DRIVE
        elif keyboard.is_pressed("2"):
            steer_mode = CRAB_DRIVE
        elif keyboard.is_pressed("3"):
            steer_mode = SPIN

        if keyboard.is_pressed("space"):
            steering = 0
        else:
            left = keyboard.is_pressed("a")
            right = keyboard.is_pressed("d")
            if left and not right:
                steering -= STEER_RATE * dt * (PI / 180)
            elif right and not left:
                steering += STEER_RATE * dt * (PI / 180)

        # =========================
        # BASIC MECHANICS
        # =========================

        # Calculate all 6 wheel angles...
        # Then dx/dt, dy/dt, and dtheta/dt
        dx_dt = 0
        dy_dt = 0
        dtheta_dt = 0
        
        # Front left, front right, middle left, middle right, rear left, rear right
        w = [0, 0, 0, 0, 0, 0]

        wheel_x = [-WIDTH / 2, WIDTH / 2, -WIDTH / 2, WIDTH / 2, -WIDTH / 2, WIDTH / 2]
        wheel_y = [WHEELBASE / 2, WHEELBASE / 2, 0, 0, -WHEELBASE / 2, -WHEELBASE / 2]

        if steer_mode == CAR_DRIVE:
            w[0] = steering
            w[1] = steering
            w[2] = 0
            w[3] = 0
            w[4] = -steering
            w[5] = -steering
        elif steer_mode == CRAB_DRIVE:
            w[0] = steering
            w[1] = steering
            w[2] = steering
            w[3] = steering
            w[4] = steering
            w[5] = steering
        elif steer_mode == SPIN:
            # All wheels should be tangent to a circle centered at the vehicle center, extending out to their position
            for i in range(6):
                # Wheel angles are measured from +y (forward), not +x.
                w[i] = -math.atan2(wheel_y[i], wheel_x[i])

        # Simulate small odometry errors by adding a small random offset to each wheel angle
        # for i in range(6):
        #     w[i] += np.random.normal(0, 0.01)

        # The following code calculates the instantaneous velocity of the vehicle from wheel orientations.
        # The final code is surprisingly simple, but the derivation is too long to fit in this comment.
        # For the complete derivation, see docs/TrajectoryDerivation/main.tex
        # Or see the compiled PDF in the Google Drive folder (BackupCameraDerivation.pdf)
        
        # Define s_x to be a list of the x-components of the wheel orientation vectors
        # You may be surprised to see that the x-component is sin(theta), but that's because our coordinate system is defined with the positive y-axis at the 0-degree angle instead of the positive x-axis.
        s_x = [math.sin(w[0]), math.sin(w[1]), math.sin(w[2]), math.sin(w[3]), math.sin(w[4]), math.sin(w[5])]

        # Define s_y to be a list of the y-components of the wheel orientation vectors
        s_y = [math.cos(w[0]), math.cos(w[1]), math.cos(w[2]), math.cos(w[3]), math.cos(w[4]), math.cos(w[5])]

        A = np.zeros((6, 3))
        for i in range(6):
            A[i, 0] = -s_y[i]
            A[i, 1] = s_x[i]
            A[i, 2] = s_y[i] * wheel_y[i] + s_x[i] * wheel_x[i]

        # Solve for the motion direction in the nullspace of A, then normalize it.
        # Wheel directions alone do not provide absolute speed magnitude.
        _, _, vt = np.linalg.svd(A)
        motion_dir = vt[-1, :]

        norm = np.linalg.norm(motion_dir)
        if norm < 1e-9:
            dx_dt, dy_dt, dtheta_dt = 0.0, 0.0, 0.0
        else:
            motion_dir = motion_dir / norm

            # We just solved for the SEV trajectory... but it could be either forwards or backwards.
            # This is a backup camera, so we want to prefer the backwards direction. The positive y-axis points to the front of the vehicle...
            # ...so we just need to ensure that dy_dt < 0.
            if motion_dir[1] > 0:
                motion_dir = -motion_dir

            # Keep direction sign consistent frame-to-frame to avoid flickering.
            #if prev_motion_dir is not None and np.dot(motion_dir, prev_motion_dir) < 0:
            #    motion_dir = -motion_dir

            prev_motion_dir = motion_dir.copy()
            dx_dt = float(MOTION_SCALE * motion_dir[0])
            dy_dt = float(MOTION_SCALE * motion_dir[1])
            dtheta_dt = float(MOTION_SCALE * motion_dir[2])

        # =========================
        # SEND TO OBS
        # =========================
        #if last_sent is None or abs(steering - last_sent) > 0.01:
        if True:
            msg = json.dumps({
                "type": "six_wheel_controls",
                "dx_dt": dx_dt,
                "dy_dt": dy_dt,
                "dtheta_dt": dtheta_dt
            })
            send_all(msg)
            last_sent = steering

        # Timestep enforcement
        # This is only approximate since all the operations in the loop take some time as well
        time.sleep(TIMESTEP)

# =========================
# START
# =========================

threading.Thread(target=input_loop, daemon=True).start()

print("====================================")
print(" Six Wheel Controls")
print(" ws://127.0.0.1:8765")
print(" ESC to quit")
print("====================================")

try:
    server.run_forever()
finally:
    close_server()