# OpenVino scripts for Object Detection

OpenVino code set to run Object Detection models

## 1. Install Python, Git and GPU drivers (optional)

You may need to install some additional libraries on Ubuntu Linux. These steps work on a clean install of Ubuntu Desktop 20.04, and should also work on Ubuntu 22.>

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python3-venv build-essential python3-dev git-all
```

## 2. Install the Notebook

After installing Python 3 and Git, run each step below in a terminal. Note: If OpenVINO is installed globally, please do not run any of these commands in a termin>

## 3. Create a Virtual Environment

Note: If you already installed openvino-dev and activated the openvino_env environment, you can skip to [Step 4](#4-clone-the-repository). If you use Anaconda, pl>

```bash
python3 -m venv openvino_env
```

## 4. Activate the Environment

```bash
source openvino_env/bin/activate
```

## 5. Clone the Repository

> Note: Using the `--depth=1` option for git clone reduces download size.

```bash
git clone --depth=1 https://github.com/DataSciNAll/vinoobject.git
