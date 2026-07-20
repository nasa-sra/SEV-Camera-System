# Six Wheel Drive

This branch provides a physically accurate backup camera overlay that correctly predicts the motion of the SEV, based on SEV wheel odometry data.

Use SixWheelControls.py and six-wheel-backup-lines.html to view the physically accurate backup camera overlay.

Right now, this system is not actually hooked up to odometry data from the SEV. It simulates wheel movement as follows:
- You can toggle between Car Drive, Crab Drive, and Spin-in-Place modes with the '1', '2', and '3' keys.
- The 'a' and 'd' keys steer the vehicle (in different ways depending on the current drive mode)
- The 'space' key resets the steering to point directly forward

This system first simulates wheel orientations, then derives a backup overlay. Thus, true wheel orientations from odometry can easily be inserted in the future, and the backup overlay will naturally follow.

Still TODO on the physically accurate backup camera:
- Connect to true SEV wheel odometry (the plan is to insert code in the SEV that broadcasts wheel orientations via UDP; listen to these broadcasts and utilize the given wheel orientations)
- Track the back of the vehicle, not the middle. Instead of tracking the movement of the middle of the SEV and adding width to the centerline, the code should be modified to track the entire back edge of the SEV.
- Clean rendering: render fewer polygons, having just the backup line take up the whole screen. The display should be transparent so the camera feed is visible beneath the trajectory overlay.
- Physically accurate parameters: adjust the SEV wheelbase dimensions to match the CAD. The camera position and orientation is the one given in CAD, but seems to be somewhat different from the actual camera on the SEV. Adjust these values for further physical accuracy.