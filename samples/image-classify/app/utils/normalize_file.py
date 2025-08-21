import os
import uuid
import json
import logging
from PIL import Image, ImageOps

# normalize_file.py: modular image normalization pipeline
# -------------------------------------------------------
# Each helper function processes a specific transform using the
# given baseline parameters, appends a descriptive entry
# to the shared `actions` list, and returns the updated Image.
# The main `normalize_image` function orchestrates these steps
# in sequence:
#   1) Resize (_apply_resize)
#   2) Crop or pad (_apply_crop_pad)
#   3) Color conversion (_apply_color)
#   4) Metadata stripping (_strip_metadata)
#   5) Saving (_save_image)
# This structure ensures clear separation of concerns and
# builds a complete action trace for each image.

# --- Normalization step functions ---
def _apply_resize(img, baseline, actions):
    """Resize image to target width/height preserving aspect ratio."""
    tw, th = baseline.get('target_width'), baseline.get('target_height')
    preserve = baseline.get('preserve_aspect_ratio', True)
    if tw and img.width > tw:
        nh = int(img.height * tw / img.width)
        img = img.resize((tw, nh), Image.LANCZOS)
        actions.append(f"resize_width:{img.size}")
    if preserve and th and img.height > th:
        nw = int(img.width * th / img.height)
        img = img.resize((nw, th), Image.LANCZOS)
        actions.append(f"resize_height:{img.size}")
    return img

def _apply_crop_pad(img, baseline, actions):
    """Apply crop or pad based on resize_mode and crop settings."""
    rm = baseline.get('resize_mode', 'fit')
    crop = baseline.get('crop', 'none')
    bg = baseline.get('background_color', '#FFFFFF')
    tw, th = baseline.get('target_width'), baseline.get('target_height')
    if rm == 'crop' and crop != 'none' and tw and th:
        img = ImageOps.fit(img, (tw, th), centering=(0.5, 0.5))
        actions.append(f"crop:{crop}:{img.size}")
    elif rm == 'fit' and tw and th:
        img = ImageOps.pad(img, (tw, th), color=bg)
        actions.append(f"pad:{img.size}")
    return img

def _apply_color(img, baseline, actions):
    """Convert image color mode if needed."""
    mode = baseline.get('color_mode')
    if mode and img.mode != mode:
        orig = img.mode
        img = img.convert(mode)
        actions.append(f"convert:{orig}->{mode}")
    return img

def _strip_metadata(img, baseline, actions):
    """Strip EXIF and metadata if requested."""
    if baseline.get('strip_metadata'):
        img.info.pop('exif', None)
        actions.append('strip_metadata')
    return img

def _save_image(img, input_path, output_dir, baseline, actions):
    """Save image with quality and format; return output path."""
    ext = baseline.get('output_format', os.path.splitext(input_path)[1].lstrip('.')).lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    out = os.path.join(output_dir, name)
    kwargs = {}
    if ext in ['jpg','jpeg']:
        kwargs['quality'] = baseline.get('quality',85)
        kwargs['optimize'] = True
    img.save(out, **kwargs)
    actions.append(f"save:{out}")
    return out

def normalize_image(
	input_path,
	output_dir,
	log_path,
	baseline=None
):
	# Debug input parameters
	logging.debug(f"normalize_image called with input={input_path}, output_dir={output_dir}, log_path={log_path}, baseline keys={list(baseline.keys()) if baseline else None}")
	# Show mapping between schema key and used 'max_width'
	logging.debug(f"baseline target_width={baseline.get('target_width')}, computed max_width from baseline.get('max_width')={baseline.get('max_width')}")

	"""
	Normalize an image file according to the baseline.
	- input_path: path to the input image
	- output_dir: directory to save normalized image
	- log_path: path to log file (JSON lines)
	- baseline: dict with normalization params (e.g., {'max_width': 2048, 'color_mode': 'RGB', 'quality': 85})
	"""
	if baseline is None:
		baseline = {}

	os.makedirs(output_dir, exist_ok=True)
	os.makedirs(os.path.dirname(log_path), exist_ok=True)

	img = Image.open(input_path)
	orig_mode = img.mode
	orig_size = img.size
	actions = []

	# Pipeline: resize, crop/pad, color convert, strip metadata, save
	img = _apply_resize(img, baseline, actions)
	img = _apply_crop_pad(img, baseline, actions)
	img = _apply_color(img, baseline, actions)
	img = _strip_metadata(img, baseline, actions)
	out_path = _save_image(img, input_path, output_dir, baseline, actions)

	# Log mapping and actions
	log_entry = {
		'input': input_path,
		'output': out_path,
		'actions': actions,
		'orig_mode': orig_mode,
		'orig_size': orig_size,
		'final_mode': img.mode,
		'final_size': img.size
	}
	# Warn if no transformation occurred
	if not actions:
		logging.warning(f"No actions applied to {input_path}; size remains {orig_size}")
	with open(log_path, 'a', encoding='utf-8') as logf:
		logf.write(json.dumps(log_entry) + '\n')

# ---
# Future hooks for EXIF, MCP, LLM integration can be added here
# def extract_exif(...): ...
# def call_mcp(...): ...
# def prompt_llm(...): ...
