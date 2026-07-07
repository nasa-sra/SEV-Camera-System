import numpy as np

# -------------------------
# CAMERA INTRINSICS
# -------------------------
IMAGE_WIDTH = 1280
IMAGE_HEIGHT = 720

CAMERA_MATRIX = np.array([
    [6.65801231e+02, 0.0, 6.40850588e+02],
    [0.0, 6.67702160e+02, 3.61158952e+02],
    [0.0, 0.0, 1.0]
], dtype=np.float64)

# -------------------------
# EXTRINSICS
# -------------------------

CAMERA_POSITION = np.array([0.0, -0.1, 0.0], dtype=np.float64)

ROLL = 0.0
PITCH = -30.0
YAW = 0.0

roll = np.deg2rad(ROLL)
pitch = np.deg2rad(PITCH)
yaw = np.deg2rad(YAW)

Rx = np.array([
    [1, 0, 0],
    [0, np.cos(pitch), -np.sin(pitch)],
    [0, np.sin(pitch), np.cos(pitch)]
])

Ry = np.array([
    [np.cos(yaw), 0, np.sin(yaw)],
    [0, 1, 0],
    [-np.sin(yaw), 0, np.cos(yaw)]
])

Rz = np.array([
    [np.cos(roll), -np.sin(roll), 0],
    [np.sin(roll), np.cos(roll), 0],
    [0, 0, 1]
])

ROT_MATRIX = Ry @ Rx @ Rz

# -------------------------
# OUTPUT
# -------------------------
RES_SCALE = 0.75

PIXELS_PER_METER = 400

CAMERA_INDEX = 0
CAPTURE_FPS = 30

STREAM_PORT = 5000
BACKUP_STREAM_PORT = 5001

# =======================
# SCALING CALCULATIONS
# =======================
K_SCALED = CAMERA_MATRIX.copy()
K_SCALED[0,0] *= RES_SCALE
K_SCALED[1,1] *= RES_SCALE
K_SCALED[0,2] *= RES_SCALE
K_SCALED[1,2] *= RES_SCALE

K_INV_SCALED = np.linalg.inv(K_SCALED)

SCALED_W = int(IMAGE_WIDTH * RES_SCALE)
SCALED_H = int(IMAGE_HEIGHT * RES_SCALE)