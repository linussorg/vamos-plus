![vamos_plus_logo_white](files/vamos_plus_logo_white.png)

VAMOS+ is a software for detecting meteors (shooting stars) in videos. To make the detections more reliable, a Tensorflow Convolutional Neural Network is used for prediction.

---

## Installation:

#### Required Python packages:

- OpenCV
- openpyxl
- PyQt5
- numpy
- tensorflow

#### Install with

```
pip install -r requirements.txt
```

- Install tensorflows correct version for your system from [Tensorflow](https://www.tensorflow.org/install)

### Video drivers for PyQt5

- Windows only, Linux currently not supported
- Recommended
- Download [here](https://codecguide.com/download_k-lite_codec_pack_basic.htm)

### Only for GPU use:

- CUDA
- CUDNN

## Execution

To run VAMOS+, execute the "vamos_plus.py" file with python and make sure all of the above packages are correctly installed.

## Known Linux issues

- Working with VAMOS+ on Linux has some performance benefits over Windows, but also comes with some missing features, such as the video player in the results window or the video preview during the analysis
- These problems are going to be solved with the UI overhaul that's planned for VAMOS+
