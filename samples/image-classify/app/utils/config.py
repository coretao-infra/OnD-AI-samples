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

_config = configparser.ConfigParser()
_config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.ini')
_config.read(os.path.abspath(_config_path))


# LLM_ALIAS is the model name (e.g., 'phi-3.5-mini')
# LLM_VARIANT is only the distinguishing part (e.g., 'instruct-generic-gpu'), not including the alias

def get_config(section, key, required=True):
	"""
	Unified config accessor. If required, error on missing/empty. If not required, return None if missing.
	"""
	try:
		value = _config.get(section, key)
	except (configparser.NoSectionError, configparser.NoOptionError):
		if required:
			raise RuntimeError(f"Missing required config: [{section}] {key}")
		return None
	if required and value.strip() == "":
		raise RuntimeError(f"Config value for [{section}] {key} is empty")
	return value if value.strip() != "" else None

try:
	LLM_ALIAS = get_config('llm', 'alias', required=True)
	LLM_VARIANT = get_config('llm', 'variant', required=True)
	LLM_ENDPOINT = get_config('llm', 'endpoint', required=True)
	LLM_API_KEY = get_config('llm', 'api_key', required=False)
	NORMALIZE_META_PROMPT = get_config('normalize', 'normalize_meta_prompt', required=True)
	DEFAULT_META_PROMPT = get_config('llm', 'default_meta_prompt', required=True)
	NORMALIZE_INPUT_DIR = get_config('normalize', 'input_dir', required=True)
	NORMALIZE_META_OUT = get_config('normalize', 'meta_out', required=True)
	NORMALIZE_SCHEMA_PATH = get_config('normalize', 'schema_path', required=True)
except Exception as e:
	raise SystemExit(f"[config.py] Configuration error: {e}")

def get_llm_variant():
	"""
	Return the explicit LLM variant from config. No implicit fallback.
	"""
	return LLM_VARIANT

# If you need the full Foundry model name, combine as needed:
#   f"{LLM_ALIAS}-{LLM_VARIANT}"  (e.g., 'phi-3.5-mini-instruct-generic-gpu')
