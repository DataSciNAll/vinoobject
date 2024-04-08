#Build latest Python environment from docker image
FROM python:3.11

#Setup working directory for Object Detection script
WORKDIR /vinoobject

#Copy requirements file to container for setup of python libraries
COPY requirements.txt .

#Pip install libraries into python container
RUN pip install wheel setuptools
RUN pip install -r requirements.txt

#Copy repo into container
COPY ./model ./model
COPY object_detection_script.py .
COPY videoplayer.py .

#Create folder for video frames and json document with model scores
RUN mkdir ./frame
RUN mkdir ./data

#Setup permissions on video frame folder to write images to it and share with host
RUN chown -R 1000 ./frame
RUN chown -R 1000 ./data
RUN chmod -R 777 ./frame
RUN chmod -R 777 ./data

#Execute command at runtime.  IP Address if the VETHERNET IP Address.  This address should be used in FFMPEG To setup RTSP address.
CMD ["python", "./object_detection_script.py", "--source", "rtsp://<IPADDRESS_VETHERNET>:8554/webcam.h264"]