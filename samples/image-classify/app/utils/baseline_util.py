# This module establishes a good image normalization baseline based on metadata.
# It leverages an LLM completion API to recommend parameters.
# All parameters are validated for sanity; failures are reported and the process stops gracefully (no fallback).

import logging
import json



import pandas as pd
from collections import Counter

from .llm import llm_complete
from .config import BASELINE_USER_PROMPT, BASELINE_SYSTEM_PROMPT, BASELINE_SCHEMA_CRITERIA, BASELINE_SCHEMA_STATIC

# Try to import allowed_color_modes from config if present
try:
	from .config import ALLOWED_COLOR_MODES
except ImportError:
	ALLOWED_COLOR_MODES = None

def build_one_shot_example():
	"""
	Dynamically build a one-shot JSON example from the schema criteria for use in the system prompt.
	"""
	static_fields = [
		'preserve_aspect_ratio', 'strip_metadata', 'timestamp', 'output_format'
	]
	schema_parts = BASELINE_SCHEMA_CRITERIA.split('|')
	filtered_parts = [p for p in schema_parts if not any(f in p for f in static_fields)]
	example_dict = {}
	for part in filtered_parts:
		field, *rest = part.split(':')
		field = field.strip()
		typ = rest[0].strip() if rest else 'str'
		# Use plausible example values
		if field == 'baseline_marker':
			val = "v1"
		elif typ == 'int':
			val = 1234
		elif typ == 'str':
			val = "example"
		else:
			val = None
		example_dict[field] = val
	# Output compact single-line JSON
	return json.dumps(example_dict, separators=(",", ":"))

def generate_llm_system_prompt():
	"""
	Generate the system prompt for the LLM using the configured system prompt, baseline schema+criteria, and a one-shot example.
	"""
	filtered_schema = get_filtered_schema()
	example_json = build_one_shot_example()
	prompt = BASELINE_SYSTEM_PROMPT.format(schema_criteria=filtered_schema, one_shot_example=example_json)
	return prompt


def marshal_metadata_for_llm(metadata_csv_path):
	"""
	Marshal metadata for LLM prompt: synthesize key stats and distributions for each field, not full lists.
	Returns a string with concise, rich, and useful metadata context.
	"""
	import numpy as np
	df = pd.read_csv(metadata_csv_path)
	df = df.dropna(subset=['width', 'height', 'mode', 'format', 'file_size'])
	# Numeric fields
	def stats(arr, bins=8):
		arr = np.array(arr)
		# Smart binning for histogram
		hist_counts, bin_edges = np.histogram(arr, bins=bins)
		# Format bins as "start-end": count
		hist = {f"{int(bin_edges[i])}-{int(bin_edges[i+1])}": int(hist_counts[i]) for i in range(len(hist_counts))}
		return {
			'min': int(np.min(arr)),
			'max': int(np.max(arr)),
			'mean': float(np.mean(arr)),
			'mode': int(Counter(arr).most_common(1)[0][0]),
			'histogram': hist
		}
	width_stats = stats(df['width'].astype(int))
	height_stats = stats(df['height'].astype(int))
	file_size_stats = stats(df['file_size'].astype(int))
	# Categorical fields: top-N
	def top_n(counter, n=3):
		return dict(counter.most_common(n))
	color_mode_counter = Counter(df['mode'])
	format_counter = Counter(df['format'])
	orientation_counter = Counter(df['orientation'].dropna().astype(int))
	bit_depth_counter = Counter(df['bit_depth'].dropna().astype(int))
	aspect_ratio_stats = stats(df['aspect_ratio'].astype(float))
	summary = {
		'num_images': int(len(df)),
		'width': width_stats,
		'height': height_stats,
		'aspect_ratio': aspect_ratio_stats,
		'file_size': file_size_stats,
		'color_modes_top': top_n(color_mode_counter),
		'formats_top': top_n(format_counter),
		'orientation_top': top_n(orientation_counter),
		'bit_depth_top': top_n(bit_depth_counter)
	}
	# Output as a compact, human-readable, non-JSON string for LLM compatibility
	def flatten(d, prefix=""):
		items = []
		for k, v in d.items():
			if isinstance(v, dict):
				items.extend(flatten(v, f"{prefix}{k}.").items())
			else:
				items.append((f"{prefix}{k}", v))
		return dict(items)
	flat = flatten(summary)
	return ", ".join(f"{k}={v}" for k, v in flat.items())

def generate_llm_prompt(metadata_summary):
	"""
	Generate the user prompt for the LLM using the template from config and including the baseline schema+criteria (compact string).
	"""
	filtered_schema = get_filtered_schema()
	prompt = BASELINE_USER_PROMPT.strip().format(metadata_summary=metadata_summary, schema_criteria=filtered_schema)
	return prompt
def get_filtered_schema():
	static_fields = [
		'preserve_aspect_ratio', 'strip_metadata', 'timestamp', 'output_format'
	]
	schema_parts = BASELINE_SCHEMA_CRITERIA.split('|')
	filtered_parts = [p for p in schema_parts if not any(f in p for f in static_fields)]
	return '|'.join(filtered_parts)

def call_llm_completion(prompt):
	"""
	Call the canonical llm_complete function from llm.py, passing the baseline system prompt as the system message.
	Returns the LLM's response as a string.
	"""
	# Accept both user_prompt and system_prompt as arguments
	user_prompt, system_prompt = prompt
	messages = [{"role": "user", "content": user_prompt}]
	return llm_complete(messages, system_prompt=system_prompt)

def validate_baseline_params(params):
	"""
	Validate normalization parameters for sanity. Raise ValueError if invalid.
	"""
	if not isinstance(params, dict):
		raise ValueError("Baseline params must be a dict.")
	# Parse schema criteria for dynamic validation
	schema = {}
	for part in BASELINE_SCHEMA_CRITERIA.split('|'):
		if not part.strip():
			continue
		# Format: field:type[:allowed_values]
		field, *rest = part.split(':')
		if not rest:
			continue
		typ = rest[0]
		allowed = rest[1] if len(rest) > 1 else None
		schema[field.strip()] = {'type': typ.strip(), 'allowed': allowed.strip() if allowed else None}
	for field, spec in schema.items():
		if field not in params:
			# Allow missing/optional fields if allowed value says 'null ok' or similar
			if spec['allowed'] and 'null' in spec['allowed']:
				continue
			raise ValueError(f"Missing required field: {field}")
		value = params[field]
		typ = spec['type']
		allowed = spec['allowed']
		# Type checks
		if typ == 'int':
			if value is not None and not isinstance(value, int):
				raise ValueError(f"{field} must be int or null, got {type(value)}")
		elif typ == 'str':
			if value is not None and not isinstance(value, str):
				raise ValueError(f"{field} must be str or null, got {type(value)}")
		# Special handling for color_mode with allowed list from config
		if field == 'color_mode' and ALLOWED_COLOR_MODES is not None:
			if value not in ALLOWED_COLOR_MODES:
				raise ValueError(f"color_mode {value} is not in allowed set {ALLOWED_COLOR_MODES}")
			continue
		# Allowed values/range checks (if specified)
		if allowed:
			allowed_lc = allowed.lower()
			# If 'null ok' specified, any non-null is acceptable
			if 'null ok' in allowed_lc and value is not None:
				continue
			# If 'commonest' in allowed, accept any string value (LLM is supposed to pick the most common)
			if 'commonest' in allowed_lc:
				continue
			if 'null' in allowed_lc and value is None:
				continue
			if '-' in allowed and typ == 'int':
				# Range, e.g. 85-95
				try:
					minv, maxv = [int(x) for x in allowed.split('-')]
					if not (minv <= value <= maxv):
						raise ValueError(f"{field} {value} is out of bounds ({minv}-{maxv})")
				except Exception:
					pass
			elif '|' in allowed:
				# Multiple allowed values, e.g. center|none
				allowed_set = set(x.strip() for x in allowed.split('|'))
				if str(value) not in allowed_set:
					raise ValueError(f"{field} {value} is not in allowed set {allowed_set}")
			elif allowed and value is not None and allowed not in str(value):
				# Simple substring match for hints
				raise ValueError(f"{field} {value} does not match allowed: {allowed}")
	# Aspect ratio validation
	preserve = BASELINE_SCHEMA_STATIC.get('preserve_aspect_ratio', True)
	width = params.get('target_width')
	height = params.get('target_height')
	# Require at least one dimension
	if width is None and height is None:
		raise ValueError("Must specify at least one of target_width or target_height.")
	# If height is null but aspect ratio not preserved, height cannot be computed
	if height is None and not preserve:
		raise ValueError("target_height is null but preserve_aspect_ratio=False; cannot compute height.")
	# Symmetric check for width
	if width is None and not preserve:
		raise ValueError("target_width is null but preserve_aspect_ratio=False; cannot compute width.")
	return True

def establish_baseline_from_metadata(metadata_csv_path):
	"""
	Main entry: marshal metadata, prompt LLM, validate response, return baseline dict.
	On any failure, log and raise an error (no fallback).
	"""
	metadata_summary = marshal_metadata_for_llm(metadata_csv_path)
	user_prompt = generate_llm_prompt(metadata_summary)
	system_prompt = generate_llm_system_prompt()
	try:
		llm_response = call_llm_completion((user_prompt, system_prompt))
		logging.debug(f"[baseline.py] Raw LLM response: {llm_response}")
		# Robustly extract all JSON objects from the response and select the one with baseline_marker == 'v1'
		import json, re
		marker = "baseline_marker"
		params = None
		# Find all JSON objects in the response (including those in code blocks)
		json_candidates = re.findall(r'\{[\s\S]*?\}', llm_response)
		for candidate in json_candidates:
			try:
				obj = json.loads(candidate)
				if isinstance(obj, dict) and obj.get(marker) == "v1":
					params = obj
					break
			except Exception:
				continue
		if not params:
			raise ValueError(f"No JSON object with {marker} == 'v1' found in LLM response.")
		validate_baseline_params(params)
		# Append static fields from config
		from datetime import datetime, timezone
		result = dict(params)
		for k, v in BASELINE_SCHEMA_STATIC.items():
			if k == 'timestamp' and v == 'current time':
				result[k] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
			else:
				result[k] = v
		return result
	except Exception as e:
		logging.error(f"Failed to establish baseline: {e}\nRaw LLM response: {locals().get('llm_response', None)}")
		raise SystemExit(f"[baseline.py] Baseline establishment failed: {e}")