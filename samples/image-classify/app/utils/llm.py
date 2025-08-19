# llm.py - Utilities for local LLM inferencing via Foundry Local
#
# This module provides functions to interact with locally hosted language models
# using the Foundry Local SDK and OpenAI-compatible API. It can be used to:
#   1 upon module init, discover cached models and load one
#   2 Load and manage local LLMs (e.g., phi-3.5-mini, phi-4)
#   3 Send prompts (such as metadata summaries) to the LLM for recommendations
#   4 Integrate LLM responses into the normalization pipeline
#



# llm.py - Canonical, DRY, atomic, self-initializing LLM interface for Foundry Local
import openai
from .config import LLM_ENDPOINT, LLM_API_KEY, LLM_ALIAS, LLM_VARIANT, DEFAULT_META_PROMPT

_client = None
_model = None
_meta_prompt = None

def _init_llm():
	"""
	Initialize the LLM client and model using canonical config values.
	Only runs once per process. Meta prompt is set to the default from config.
	"""
	global _client, _model, _meta_prompt
	if _client is not None and _model is not None and _meta_prompt is not None:
		return
	_client = openai.OpenAI(base_url=LLM_ENDPOINT, api_key=LLM_API_KEY)
	_model = f"{LLM_ALIAS}-{LLM_VARIANT}"
	_meta_prompt = DEFAULT_META_PROMPT

def set_meta_prompt(prompt):
	"""
	Set the meta/system prompt for LLM chat. This updates the internal state.
	"""
	global _meta_prompt
	_meta_prompt = prompt

def llm_complete(messages, **kwargs):
	"""
	Stateless LLM completion: sends a single message list (OpenAI-style) and returns the response.
	Prepends the meta/system prompt if set. Does not track or manage chat history.
	Args:
		messages: List of dicts, e.g. [{"role": "user", "content": "..."}]
		kwargs: Additional OpenAI chat params (e.g., temperature)
	Returns:
		The LLM's response message (str)
	"""
	_init_llm()
	msgs = messages[:]
	if _meta_prompt:
		msgs = [{"role": "system", "content": _meta_prompt}] + msgs
	response = _client.chat.completions.create(
		model=_model,
		messages=msgs,
		**kwargs
	)
	return response.choices[0].message.content
