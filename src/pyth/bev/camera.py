import cv2
import pyth.bev.config as config
import pyth.bev.ground_plane_rays as rays
import pyth.bev.warp as warp
from pyth.bev.stream import Streamer

def main():

    cap = cv2.VideoCapture(config.CAMERA_INDEX)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.IMAGE_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.IMAGE_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.CAPTURE_FPS)

    streamer = Streamer(
        config.SCALED_W,
        config.SCALED_H,
        config.CAPTURE_FPS,
        config.STREAM_PORT
    )

    backup_streamer = Streamer(
        config.SCALED_W,
        config.SCALED_H,
        config.CAPTURE_FPS,
        config.BACKUP_STREAM_PORT
    )

    rays.initialize()
    warp.initialize()
    
    while True:

        ret, frame = cap.read()
        if not ret:
            continue

        bev_warp = warp.process_frame(frame)
        bev_rays = rays.process_frame(frame)

        streamer.send(bev_warp)
        backup_streamer.send(bev_rays)


if __name__ == "__main__":
    main()