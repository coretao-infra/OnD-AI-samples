

# This module establishes a good image normalization baseline based on metadata.
# It leverages an LLM completion API to recommend parameters.
# All parameters are validated for sanity; failures are reported and the process stops gracefully (no fallback).

import logging
import json



import pandas as pd
from collections import Counter

from .llm import llm_complete
from .config import BASELINE_USER_PROMPT, BASELINE_SYSTEM_PROMPT


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
	Generate the user prompt for the LLM using the template from config.
	"""
	prompt = BASELINE_USER_PROMPT.strip()
	# Add explicit instruction for JSON-only response
	if 'Respond in JSON' not in prompt:
		prompt += " Respond with only a JSON object and nothing else."
	# If the template contains {metadata_summary}, substitute it; else, append summary at the end.
	if '{metadata_summary}' in prompt:
		prompt = prompt.replace('{metadata_summary}', metadata_summary)
	else:
		prompt = f"{prompt}\nMetadata summary: {metadata_summary}"
	return prompt

def call_llm_completion(prompt):
	"""
	Call the canonical llm_complete function from llm.py, passing the baseline system prompt as the system message.
	Returns the LLM's response as a string.
	"""
	messages = [{"role": "user", "content": prompt}]
	return llm_complete(messages, system_prompt=BASELINE_SYSTEM_PROMPT)

def validate_baseline_params(params):
	"""
	Validate normalization parameters for sanity. Raise ValueError if invalid.
	"""
	if not isinstance(params, dict):
		raise ValueError("Baseline params must be a dict.")
	w = params.get('max_width')
	if not (isinstance(w, int) and 100 <= w <= 10000):
		raise ValueError(f"max_width {w} is out of bounds (100-10000).")
	mode = params.get('color_mode')
	if mode not in {'RGB', 'L'}:
		raise ValueError(f"color_mode {mode} is not supported.")
	q = params.get('quality')
	if not (isinstance(q, int) and 1 <= q <= 100):
		raise ValueError(f"quality {q} is out of bounds (1-100).")
	return True

def establish_baseline_from_metadata(metadata_csv_path):
	"""
	Main entry: marshal metadata, prompt LLM, validate response, return baseline dict.
	On any failure, log and raise an error (no fallback).
	"""
	metadata_summary = marshal_metadata_for_llm(metadata_csv_path)
	prompt = generate_llm_prompt(metadata_summary)
	try:
		llm_response = call_llm_completion(prompt)
		logging.debug(f"[baseline.py] Raw LLM response: {llm_response}")
		# Try to extract the first JSON object from the response
		import re
		match = re.search(r'\{.*?\}', llm_response, re.DOTALL)
		if match:
			json_str = match.group(0)
			params = json.loads(json_str)
		else:
			raise ValueError("No JSON object found in LLM response.")
		validate_baseline_params(params)
		return params
	except Exception as e:
		logging.error(f"Failed to establish baseline: {e}\nRaw LLM response: {locals().get('llm_response', None)}")
		raise SystemExit(f"[baseline.py] Baseline establishment failed: {e}")