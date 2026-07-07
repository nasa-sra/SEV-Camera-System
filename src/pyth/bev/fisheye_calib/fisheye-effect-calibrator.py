import cv2
import numpy as np
import glob

CHECKERBOARD = (10, 7)

objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[0, :, :2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)

objpoints = []
imgpoints = []

images = glob.glob("src/res/calib_images/*.jpg") # if 

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD)

    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)

h, w = img.shape[:2]

ret, K, D, rvecs, tvecs = cv2.fisheye.calibrate(
    objpoints,
    imgpoints,
    gray.shape[::-1],
    None,
    None
)

print("Camera matrix:\n", K)
print("Distortion:\n", D)