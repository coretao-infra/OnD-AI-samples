"""
vision_actions.py: Generalized vision actions for the demo app
- Self-initializing: manages model registry and action dispatch
- Exports: detect_objects(image), segment_objects(image), detect_pose(image), classify_image(image)
- Internally manages model loading and task routing
"""

from .yolo_infer import YOLOv8Model
from . import config
import threading


class VisionActions:
    def __init__(self):
        self._models = {}
        self._lock = threading.Lock()
        # Read task mapping from config
        self._tasks = {}
        for task in ['detection', 'segmentation', 'pose', 'classification']:
            enabled = config.get_config('vision_actions', f'enable_{task}', required=False)
            if enabled is None or enabled.lower() == 'true':
                self._tasks[task] = True

    def _get_model(self, task):
        with self._lock:
            if task not in self._models:
                self._models[task] = YOLOv8Model(task)
            return self._models[task]


    def detect_objects(self, image):
        if not self._tasks.get('detection', False):
            raise RuntimeError('Detection task is disabled in config.')
        model = self._get_model('detection')
        return model.infer(image)


    def segment_objects(self, image):
        if not self._tasks.get('segmentation', False):
            raise RuntimeError('Segmentation task is disabled in config.')
        model = self._get_model('segmentation')
        return model.infer(image)


    def detect_pose(self, image):
        if not self._tasks.get('pose', False):
            raise RuntimeError('Pose task is disabled in config.')
        model = self._get_model('pose')
        return model.infer(image)


    def classify_image(self, image):
        if not self._tasks.get('classification', False):
            raise RuntimeError('Classification task is disabled in config.')
        model = self._get_model('classification')
        return model.infer(image)

# Usage example:
# In config.ini, set e.g.:
# [vision_yolo_infer]
# detection_model_path = assets/models/yolov8n.onnx
# segmentation_model_path = assets/models/yolov8n-seg.onnx
# pose_model_path = assets/models/yolov8n-pose.onnx
# classification_model_path = assets/models/yolov8n-cls.onnx
# [vision_actions]
# enable_detection = true
# enable_segmentation = true
# enable_pose = true
# enable_classification = true
#
# vision = VisionActions()
# results = vision.detect_objects(image)
