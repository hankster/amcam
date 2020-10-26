# amcam
Amcrest IP security camera and NVR file download and management utilities.

The Amcrest line of network-based IP security cameras has two available software interfaces (API's) which allow control and interrogation of the camera (or Network Video Recorder - NVR).
One of these is an industry standard known as ONVIF. The ONVIF standard uses a SOAP interface with WSDL files to interrogate the camera. I was unable to find a way to download video or jpg files using ONVIF.

Amcrest also provides a proprietary CGI based web interface which allows both access to controls and settings in the camera and also download of image media. You can find the standard by searching for "Amcrest+HTTP+API+g.2020.pdf". The actual link, for now, appears to be a shared Google Drive file.

The "amcam.py" program is a Python based utility which allows download of mp4 or jpg media from the camera over a given time range. You can use the program from the command line by typing:

  amcam.py -a addr:port -c channel -d -e endtime -h -m media -n number -p password -s starttime -u user -v 

or

  amcam.py --addr=ip:port --channel=channel --debug --end=endtime --help --media=media --number=number --password=password --start=starttime --user=user --version
  
For example (first change the default IP address, user and password in the code):

  amcam.py -m mp4 -s "2020-10-10 12:00:00" -e "2020-10-10 23:59:59"
  
This will download all the mp4 video files available in the timeframe specified.

You will need to install the Python "requests" module to run this program:

  pip install requests
  


