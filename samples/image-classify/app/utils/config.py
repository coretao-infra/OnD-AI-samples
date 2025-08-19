# config.py - Configuration for image normalization and LLM integration
#
# This module defines project-wide configuration, including:
#   - all parameterization of the categorize sample canonically occurs via this config
#   - Preferred LLM alias and variant for Foundry Local (e.g., phi-3.5-mini, phi-4)
#   - Other settings for normalization, metadata, and pipeline control
#   - config should do no non-explicit fall/failbacks, unexpected config results in graceful stop
#

# Reads LLM configuration from canonical config/config.ini
import configparser
import os
import logging
import inspect

_config = configparser.ConfigParser()
_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.ini')
_config.read(os.path.abspath(_config_path))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_config(section, key, required=True):
	"""
	Unified config accessor. If required, error on missing/empty. If not required, return None if missing.
	"""
	try:
		value = _config.get(section, key)
	except (configparser.NoSectionError, configparser.NoOptionError):
		if required:
			logging.error(f"Missing required config: [{section}] {key}")
			raise RuntimeError(f"Missing required config: [{section}] {key}")
		value = None
	if required and (value is None or value.strip() == ""):
		logging.error(f"Config value for [{section}] {key} is empty")
		raise RuntimeError(f"Config value for [{section}] {key} is empty")

	# Only log if called from outside this module
	stack = inspect.stack()
	if len(stack) > 1:
		caller_frame = stack[1]
		caller_module = inspect.getmodule(caller_frame[0])
		this_module = inspect.getmodule(stack[0][0])
		if caller_module and this_module and caller_module.__file__ != this_module.__file__:
			# Try to get the variable name in the caller's code (best effort)
			import ast
			import linecache
			var_name = None
			try:
				lineno = caller_frame.lineno
				filename = caller_frame.filename
				line = linecache.getline(filename, lineno).strip()
				# Look for assignment like VAR = get_config(...)
				tree = ast.parse(line)
				for node in ast.walk(tree):
					if isinstance(node, ast.Assign):
						for target in node.targets:
							if isinstance(target, ast.Name):
								var_name = target.id
			except Exception:
				pass
			logging.info(f"Config requested by {caller_module.__name__} at {caller_frame.function}() line {caller_frame.lineno}: [{section}] {key} -> {var_name} = {value}")
	return value if value is not None and value.strip() != "" else None

logging.info("Loading configuration from config.ini")

try:
	LLM_ALIAS = get_config('llm', 'alias', required=True)
	logging.info(f"LLM_ALIAS: {LLM_ALIAS}")
	LLM_VARIANT = get_config('llm', 'variant', required=True)
	logging.info(f"LLM_VARIANT: {LLM_VARIANT}")
	LLM_ENDPOINT = get_config('llm', 'endpoint', required=True)
	logging.info(f"LLM_ENDPOINT: {LLM_ENDPOINT}")
	LLM_API_KEY = get_config('llm', 'api_key', required=False)
	NORMALIZE_META_PROMPT = get_config('normalize', 'normalize_meta_prompt', required=True)
	logging.info(f"NORMALIZE_META_PROMPT: {NORMALIZE_META_PROMPT}")
	DEFAULT_META_PROMPT = get_config('llm', 'default_meta_prompt', required=True)
	logging.info(f"DEFAULT_META_PROMPT: {DEFAULT_META_PROMPT}")
	NORMALIZE_INPUT_DIR = get_config('normalize', 'input_dir', required=True)
	logging.info(f"NORMALIZE_INPUT_DIR: {NORMALIZE_INPUT_DIR}")
	NORMALIZE_META_OUT = get_config('normalize', 'meta_out', required=True)
	logging.info(f"NORMALIZE_META_OUT: {NORMALIZE_META_OUT}")
	NORMALIZE_SCHEMA_PATH = get_config('normalize', 'schema_path', required=True)
	logging.info(f"NORMALIZE_SCHEMA_PATH: {NORMALIZE_SCHEMA_PATH}")
except Exception as e:
    logging.error(f"Configuration error: {e}")
    raise SystemExit(f"[config.py] Configuration error: {e}")

def get_llm_variant():
	"""
	Return the explicit LLM variant from config. No implicit fallback.
	"""
	return LLM_VARIANT

# If you need the full Foundry model name, combine as needed:
#   f"{LLM_ALIAS}-{LLM_VARIANT}"  (e.g., 'phi-3.5-mini-instruct-generic-gpu')
