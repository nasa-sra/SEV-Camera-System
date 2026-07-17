from time import sleep

import cv2
import numpy as np
import pyth.bev.config as config

# ========================
# TO BE INITIALIZED
# ========================
H = np.zeros((3, 3), dtype=np.float64)

RAW_CORNERS = None
BEV_CORNERS = None
 
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

    x = np.linspace(config.CALIB_X_MIN, config.CALIB_X_MAX, config.CALIB_X_NUM)
    z = np.linspace(config.CALIB_Z_MIN, config.CALIB_Z_MAX, config.CALIB_Z_NUM)

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

    if config.SHOW_CALIB_CORNERS:
        calc_corners(R, t)

def calc_corners(R, t):
    global RAW_CORNERS, BEV_CORNERS

    corner_world_pts = np.array([
        [config.CALIB_X_MIN, 0.0, config.CALIB_Z_MIN],
        [config.CALIB_X_MAX, 0.0, config.CALIB_Z_MIN],
        [config.CALIB_X_MAX, 0.0, config.CALIB_Z_MAX],
        [config.CALIB_X_MIN, 0.0, config.CALIB_Z_MAX]
    ], dtype=np.float64)

    # -----------------------------
    # Project to camera image
    # -----------------------------
    cam_pts = (R @ corner_world_pts.T + t).T

    valid = cam_pts[:, 2] > 0

    cam_pts = cam_pts[valid]
    corner_world_pts = corner_world_pts[valid]

    img_pts = (config.K_SCALED @ cam_pts.T).T
    img_pts = img_pts[:, :2] / img_pts[:, 2:3]

    RAW_CORNERS = img_pts.astype(np.int32)

    # -----------------------------
    # Project to BEV
    # -----------------------------
    cx = config.SCALED_W // 2
    cy = config.SCALED_H

    bev_pts = np.empty((len(corner_world_pts), 2), dtype=np.int32)

    bev_pts[:,0] = np.round(
        cx + corner_world_pts[:,0] * config.PIXELS_PER_METER
    )

    bev_pts[:,1] = np.round(
        cy - corner_world_pts[:,2] * config.PIXELS_PER_METER
    )

    BEV_CORNERS = bev_pts

def get_raw_pts():
    return RAW_CORNERS

# =================
# MAIN PIPELINE
# =================
def process_frame(frame):

    frame = cv2.resize(frame, (config.SCALED_W, config.SCALED_H), interpolation=cv2.INTER_AREA)

    bev = cv2.warpPerspective(frame, H, (config.SCALED_W, config.SCALED_H), flags= cv2.INTER_LINEAR)
    
    if config.SHOW_CALIB_CORNERS and BEV_CORNERS is not None:
        for pt in BEV_CORNERS:
            cv2.circle(
                bev,
                tuple(pt),
                5,
                (0, 0, 255),
                -1
            )

    return bev