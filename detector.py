import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

def color_list():
    # Return first 10 plt colors as (r,g,b) https://stackoverflow.com/questions/51350872/python-from-color-name-to-rgb
    def hex2rgb(h):
        return tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4))

    return [hex2rgb(h) for h in plt.rcParams['axes.prop_cycle'].by_key()['color']]


def visualize(detections):
    colors = color_list()
    images = []
    for i, (img, pred) in enumerate(zip(detections.imgs, detections.pred)):
        img = Image.fromarray(img.astype(np.uint8)) if isinstance(img, np.ndarray) else img  # from np
        if pred is not None:
            for *box, conf, cls in pred:  # xyxy, confidence, class
                ImageDraw.Draw(img).rectangle(box, width=4, outline=colors[int(cls) % 10])  # plot
        images.append(img)
    return images


class YOLODetector:
    def __init__(self, model_name='yolov5s', device='cpu'):
        self._model_name = model_name
        self._device = torch.device(device)
        self._model = torch.hub.load('ultralytics/yolov5', model_name, pretrained=True)
        self._is_initialized = device == 'cpu'

    def __call__(self, image):
        if not self._is_initialized:
            self._model = self._model.to(self._device)
            self._is_initialized = True
        results = self._model([image], size=640)
        return np.array(visualize(results)[0])
