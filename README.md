# OpenVino scripts for Object Detection

OpenVino code set to run Object Detection models

## 1. Install Python, Git and GPU drivers (optional)

You may need to install some additional libraries on Ubuntu Linux. These steps work on a clean install of Ubuntu Desktop 20.04, and should also work on Ubuntu 22.>

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3-venv build-essential python3-dev git-all
```

## 2. Create virtual environment folder

This will be the directory from the root of your home/<usr> directory.  We assume you have setup your local git repo in the same directory but this is optional.  Change the path to your local git repo.

```bash
mkdir /home/<usr>/venv
```
## 3. Create a Virtual Environment

```bash
python3 -m venv /home/<usr>/venv/openvino_env
```

## 4. Activate the Environment

Suggested Local repo on is home/<usr>/github.  If you have it in a differnt location update Path

```bash
source /home/biadmin/github/venv/object_detect/bin/activate
```

## 5. Clone the Repository

```bash
git clone https://github.com/DataSciNAll/vinoobject.git
```

## 6. Install the Packages

This setup installs OpenVINO and dependencies.  Install PIP to latest version and install dependencies.

```bash
python -m pip install --upgrade pip 
pip install wheel setuptools
pip install -r requirements.txt
```
## 7. Setup environment and run python script

Python script is using Public SSDlite_mobilenet_v2 IR file.  It has already been converted to IR format.  This model is trained from the COCO data set

```bash
python3 /home/<usr>/github/vinoobject/object_detection_script.py
```

OpenCV leverages Video Player to frame the different video segments and it is configured to leverage Source = 0 which should be the webcam define that is streaming from the local machine to the script.
