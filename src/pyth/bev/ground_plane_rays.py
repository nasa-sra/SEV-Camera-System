import cv2
import numpy as np
import pyth.bev.config as config

# ========================
# TO BE INITIALIZED
# ========================
BX = []
BY = []
VALID = []
bev = np.zeros((config.SCALED_H, config.SCALED_W, 3), dtype=np.uint8)

def initialize():
    
    global BX
    global BY
    global VALID
    global bev

    # =================
    # BEV Calcs
    # =================

    u = np.tile(np.arange(config.SCALED_W), config.SCALED_H)
    v = np.repeat(np.arange(config.SCALED_H), config.SCALED_W)
    pixels = np.stack([u, v, np.ones_like(u)], axis=-1)

    rays_cam = pixels @ config.K_INV_SCALED.T
    rays_cam /= (np.linalg.norm(rays_cam, axis=1, keepdims=True) + 1e-9)

    rays_world = rays_cam @ config.ROT_MATRIX.T

    ray_y = rays_world[:, 1]
    valid = np.abs(ray_y) > 1e-6

    t = np.zeros_like(ray_y)
    t[valid] = -config.CAMERA_POSITION[1] / ray_y[valid]

    valid &= t > 0

    # ---------------------------------
    # PROJECT TO BEV IMAGE (XZ PLANE)
    # ---------------------------------
    x = config.CAMERA_POSITION[0] + rays_world[:, 0] * t
    z = config.CAMERA_POSITION[2] + rays_world[:, 2] * t

    cx = config.SCALED_W // 2
    cy = config.SCALED_H

    BX = (cx + x * config.PIXELS_PER_METER).astype(np.int32)
    BY = (cy - z * config.PIXELS_PER_METER).astype(np.int32)

    # --------------------------
    # 6. FILTER VALID PIXELS
    # --------------------------
    in_bounds = (
        (BX >= 0) & (BX < config.SCALED_W) &
        (BY >= 0) & (BY < config.SCALED_H) &
        valid
    )

    VALID = np.flatnonzero(in_bounds)

    BX = BX[in_bounds]
    BY = BY[in_bounds]

    bev = np.zeros((config.SCALED_H, config.SCALED_W, 3), dtype=np.uint8)

# =================
# MAIN PIPELINE
# =================
def process_frame(frame):

    global bev

    frame = cv2.resize(frame, (config.SCALED_W, config.SCALED_H), interpolation=cv2.INTER_AREA)

    bev.fill(0)

    colors = frame.reshape(-1, 3)[VALID]
    bev[BY, BX] = colors

    return bev