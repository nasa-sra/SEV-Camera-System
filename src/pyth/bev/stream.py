import subprocess


class Streamer:
    def __init__(self, width, height, fps, port):

        self.width = width
        self.height = height
        self.fps = fps
        self.port = port

        self.ffmpeg = subprocess.Popen([
            "ffmpeg",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",

            "-an",

            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",

            "-tune", "zerolatency",

            "-f", "mpegts",
            f"udp://127.0.0.1:{self.port}?pkt_size=1316"
        ], stdin=subprocess.PIPE)

    def send(self, frame):
        self.ffmpeg.stdin.write(frame.tobytes())
        self.ffmpeg.stdin.flush()