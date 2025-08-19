
import os
import uuid
import json
from PIL import Image

def normalize_image(
	input_path,
	output_dir,
	log_path,
	baseline=None
):
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

	# Resize if above baseline
	max_width = baseline.get('max_width')
	if max_width and img.width > max_width:
		new_height = int(img.height * max_width / img.width)
		img = img.resize((max_width, new_height), Image.LANCZOS)
		actions.append(f"resize:{orig_size}->{img.size}")

	# Convert color mode if needed
	color_mode = baseline.get('color_mode')
	if color_mode and img.mode != color_mode:
		img = img.convert(color_mode)
		actions.append(f"convert:{orig_mode}->{color_mode}")

	# Prepare output filename
	ext = os.path.splitext(input_path)[1].lower()
	out_name = f"{uuid.uuid4().hex}{ext}"
	out_path = os.path.join(output_dir, out_name)

	# Save with quality/compression if specified
	save_kwargs = {}
	if ext in ['.jpg', '.jpeg']:
		save_kwargs['quality'] = baseline.get('quality', 85)
		save_kwargs['optimize'] = True
	img.save(out_path, **save_kwargs)

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
	with open(log_path, 'a', encoding='utf-8') as logf:
		logf.write(json.dumps(log_entry) + '\n')

# ---
# Future hooks for EXIF, MCP, LLM integration can be added here
# def extract_exif(...): ...
# def call_mcp(...): ...
# def prompt_llm(...): ...
