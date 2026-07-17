# SEV Backup Camera and Object Detection
This project is a proof-of-concept for how camera streams can be taken from the SEV and processed to be displayed on OBS for driver assistance. 


## How to Set Up OBS

### HTML Sources
To set up an OBS html source you need to add a "Browser" source and then paste the path in your "Local File" box after checking the "Local File" checkbox:
    `C:\...\SEV-Backup-Camera\src\html\object-detection.html`
    or
    `C:\...\SEV-Backup-Camera\src\html\backup-lines.html`

### Video Stream Sources 
To set up an OBS video stream source you need to add a "Media" source and have "Local File" **unchecked** so you can paste the following into the "Input" box:
    `udp://127.0.0.1:5000?pkt_size=1316`

Note however that the port (in the exaple it is "5000") changes based on what you want to be displayed:
- 5000 = Primary Stream
- 5001 = Secondary Stream (for testing)
- 5002 = Raw Camera Stream (for testing)

Feel free to create multiple OBS sources for each of the three ports to display multiple at once.

## How to Run Birds Eye View (BEV)
To run the BEV simply open the terminal and cd into the src file before running the following command:
    `python -m pyth.bev.camera`