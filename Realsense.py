import pyrealsense2 as rs
import numpy as np
from tabulate import tabulate
import os
import time

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

NUM_SECTORS = 5

# left_distance      = sector_min_distances[0]
# left_center        = sector_min_distances[1]
# center_distance    = sector_min_distances[2]
# right_center       = sector_min_distances[3]
# right_distance     = sector_min_distances[4]

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

        # Clear terminal
        os.system("cls" if os.name == "nt" else "clear")

        table = []

        for i, distance in enumerate(sector_min_distances):
            table.append([
                f"Sector {i+1}",
                f"{distance:.3f} m" if not np.isnan(distance) else "No Data"
            ])

        print(tabulate(
            table,
            headers=["Sector", "Closest Surface"],
            tablefmt="grid"
        ))

        time.sleep(0.05)

finally:
    pipeline.stop()