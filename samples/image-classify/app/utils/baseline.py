

# This module establishes a good image normalization baseline based on metadata.
# It leverages an LLM completion API to recommend parameters.
# All parameters are validated for sanity; failures are reported and the process stops gracefully (no fallback).

import logging
import json



import pandas as pd
from collections import Counter

from .llm import llm_complete
from .config import BASELINE_USER_PROMPT, BASELINE_SYSTEM_PROMPT, BASELINE_SCHEMA_CRITERIA, BASELINE_SCHEMA_STATIC
def generate_llm_system_prompt():
	"""
	Generate the system prompt for the LLM using the configured system prompt and baseline schema+criteria (compact string).
	"""
	# Use the new compact schema+criteria string directly
	# Remove static fields from schema+criteria string for LLM
	static_fields = [
		'preserve_aspect_ratio', 'strip_metadata', 'timestamp', 'output_format'
	]
	# Remove static fields from the schema string
	schema_parts = BASELINE_SCHEMA_CRITERIA.split('|')
	filtered_parts = [p for p in schema_parts if not any(f in p for f in static_fields)]
	filtered_schema = '|'.join(filtered_parts)
	prompt = f"{BASELINE_SYSTEM_PROMPT} Baseline schema+criteria: {filtered_schema}"
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
	summary = {
		'num_images': int(len(df)),
		'width': width_stats,
		'height': height_stats,
		'file_size': file_size_stats,
		'color_modes_top': top_n(color_mode_counter),
		'formats_top': top_n(format_counter)
	}
	return json.dumps(summary)

def generate_llm_prompt(metadata_summary):
	"""
	Generate the user prompt for the LLM using the template from config and including the baseline schema+criteria (compact string).
	"""
	# Remove static fields from schema+criteria string for LLM
	static_fields = [
		'preserve_aspect_ratio', 'strip_metadata', 'timestamp', 'output_format'
	]
	schema_parts = BASELINE_SCHEMA_CRITERIA.split('|')
	filtered_parts = [p for p in schema_parts if not any(f in p for f in static_fields)]
	filtered_schema = '|'.join(filtered_parts)
	prompt = BASELINE_USER_PROMPT.strip()
	# If the template contains {metadata_summary}, substitute it; else, append summary at the end.
	if '{metadata_summary}' in prompt:
		prompt = prompt.replace('{metadata_summary}', metadata_summary)
	else:
		prompt = f"{prompt} Metadata summary: {metadata_summary}"
	# Add filtered schema+criteria at the end
	prompt = f"{prompt} Baseline schema+criteria: {filtered_schema}"
	return prompt

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
	# __baseline_marker__
	marker = params.get('baseline_marker')
	if marker != 'v1':
		raise ValueError(f"baseline_marker must be 'v1', got {marker}")
	# target_width
	w = params.get('target_width')
	if not (isinstance(w, int) and 100 <= w <= 10000):
		raise ValueError(f"target_width {w} is out of bounds (100-10000).")
	# target_height (can be int or None)
	h = params.get('target_height')
	if h is not None and not (isinstance(h, int) and 100 <= h <= 10000):
		raise ValueError(f"target_height {h} is not None or out of bounds (100-10000).")
	# resize_mode
	resize_mode = params.get('resize_mode')
	if resize_mode not in {'fit', 'crop'}:
		raise ValueError(f"resize_mode {resize_mode} is not supported.")
	# color_mode
	mode = params.get('color_mode')
	if mode not in {'RGB', 'L'}:
		raise ValueError(f"color_mode {mode} is not supported.")
	# quality (for JPEG)
	q = params.get('quality')
	if not (isinstance(q, int) and 1 <= q <= 100):
		raise ValueError(f"quality {q} is out of bounds (1-100).")
	# crop
	crop = params.get('crop')
	if crop not in {'center', 'none'}:
		raise ValueError(f"crop {crop} is not supported.")
	# background_color
	bg = params.get('background_color')
	if not (isinstance(bg, str) and bg.startswith('#') and len(bg) == 7):
		raise ValueError(f"background_color {bg} is not a valid hex color.")
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
		# Extract the first JSON object from the response and select the one with baseline_marker == 'v1'
		import json
		marker = "baseline_marker"
		params = None
		start = llm_response.find('{')
		end = llm_response.rfind('}')
		if start != -1 and end != -1 and end > start:
			try:
				obj = json.loads(llm_response[start:end+1])
				if isinstance(obj, dict) and obj.get(marker) == "v1":
					params = obj
			except Exception:
				pass
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