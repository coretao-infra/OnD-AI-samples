"""
yolo_infer.py: Model abstraction for YOLOv8 ONNX models (object detection, segmentation, pose, etc.)
- Self-initializing: loads model on first use
- Exports: load_model(), infer(image), get_model_info()
- All other details (preprocessing, postprocessing, provider selection) are private
"""

import os
import threading
import numpy as np
import onnxruntime as ort
import cv2
from . import config


class YOLOv8Model:
    def __init__(self, task):
        self._task = task
        self._model_path = config.get_config('vision_yolo_infer', f'{task}_model_path', required=True)
        providers = config.get_config('vision_yolo_infer', f'{task}_providers', required=False)
        if providers:
            self._providers = [p.strip() for p in providers.split(',') if p.strip()]
        else:
            self._providers = ["DirectMLExecutionProvider", "CPUExecutionProvider"]
        self._session = None
        self._input_shape = None
        self._lock = threading.Lock()
        self._init_model()

    def _init_model(self):
        with self._lock:
            if self._session is not None:
                return
            if not os.path.exists(self._model_path):
                raise FileNotFoundError(f"Model not found: {self._model_path}")
            self._session = ort.InferenceSession(self._model_path, providers=self._providers)
            self._input_shape = self._session.get_inputs()[0].shape

    def _preprocess(self, image):
        # Resize, normalize, and convert to NCHW float32
        h, w = self._input_shape[2], self._input_shape[3]
        img = cv2.resize(image, (w, h))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))[None, ...]
        return img

    def _postprocess(self, outputs):
        # Placeholder: downstream should handle task-specific postprocessing
        return outputs

    def infer(self, image):
        self._init_model()
        input_tensor = self._preprocess(image)
        ort_inputs = {self._session.get_inputs()[0].name: input_tensor}
        ort_outs = self._session.run(None, ort_inputs)
        return self._postprocess(ort_outs)

    def get_model_info(self):
        self._init_model()
        return {
            "model_path": self._model_path,
            "input_shape": self._input_shape,
            "providers": self._session.get_providers(),
        }

# Usage: from .yolo_infer import YOLOv8Model
