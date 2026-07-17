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

    # backup_streamer = Streamer(
    #     config.SCALED_W,
    #     config.SCALED_H,
    #     config.CAPTURE_FPS,
    #     config.BACKUP_STREAM_PORT
    # )

    raw_streamer = Streamer(
        config.SCALED_W,
        config.SCALED_H,
        config.CAPTURE_FPS,
        config.RAW_STREAM_PORT
    )
    

    warp.initialize()
    # rays.initialize()
    
    while True:

        ret, frame = cap.read()
        if not ret:
            continue
        
        if(config.SHOW_CALIB_CORNERS):
            raw_stream = draw_pts(frame, warp.get_raw_pts())
        else:
            raw_stream = frame.copy()

        bev_warp = warp.process_frame(frame)
        # bev_rays = rays.process_frame(frame)

        streamer.send(bev_warp)
        # backup_streamer.send(bev_rays)
        raw_streamer.send(raw_stream)

def draw_pts(frame, raw_pts):
    raw_pts = warp.get_raw_pts()
    raw_stream = frame.copy()

    if raw_pts is not None:
        for pt in raw_pts:
            cv2.circle(
                raw_stream,
                tuple(pt),
                5,
                (0, 0, 255),
                -1
            )
            
    return raw_stream

if __name__ == "__main__":
    main()