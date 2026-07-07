import cv2
import numpy as np
import pyth.bev.config as config

# ========================
# TO BE INITIALIZED
# ========================
H = np.zeros((3, 3), dtype=np.float64)
 
def initialize():
    global H

    # -------------------------------
    # Camera extrinsics
    # -------------------------------
    R = config.ROT_MATRIX.T
    t = -R @ config.CAMERA_POSITION.reshape(3, 1)

    # -------------------------------
    # Generate ground points (meters)
    # -------------------------------
    x = np.linspace(-4.0, 4.0, 9)
    z = np.linspace(1.0, 10.0, 10)

    world_pts = np.array(
        [[xi, 0.0, zi] for zi in z for xi in x],
        dtype=np.float64
    )

    # -------------------------------   
    # Project world -> image
    # -------------------------------
    cam_pts = (R @ world_pts.T + t).T

    valid = cam_pts[:, 2] > 0
    cam_pts = cam_pts[valid]
    world_pts = world_pts[valid]

    img_pts = (config.K_SCALED @ cam_pts.T).T
    img_pts = img_pts[:, :2] / img_pts[:, 2:3]

    # -------------------------------
    # Desired BEV locations
    # -------------------------------
    bev_pts = np.empty((len(world_pts), 2), dtype=np.float32)

    cx = config.SCALED_W // 2
    cy = config.SCALED_H

    bev_pts[:, 0] = cx + world_pts[:, 0] * config.PIXELS_PER_METER
    bev_pts[:, 1] = cy - world_pts[:, 2] * config.PIXELS_PER_METER

    # -------------------------------
    # Compute homography
    # -------------------------------
    H, mask = cv2.findHomography(
        img_pts.astype(np.float32),
        bev_pts,
        method=0
    )

# =================
# MAIN PIPELINE
# =================
def process_frame(frame):

    frame = cv2.resize(frame, (config.SCALED_W, config.SCALED_H), interpolation=cv2.INTER_AREA)

    bev = cv2.warpPerspective(frame, H, (config.SCALED_W, config.SCALED_H), flags= cv2.INTER_LINEAR)

    return bev