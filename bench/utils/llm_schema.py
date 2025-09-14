class Model:
    """Canonical schema for a model."""
    def __init__(self, id, alias, device, size, cached, loaded, backend):
        self.id = id  # Unique identifier for the model
        self.alias = alias  # Alias name for the model
        self.device = device  # Device type (e.g., GPU, CPU)
        self.size = size  # Size of the model in MB
        self.cached = cached  # Boolean indicating if the model is cached
        self.loaded = loaded  # Boolean indicating if the model is loaded
        self.backend = backend  # Backend source of the model

    def to_dict(self):
        """Convert the model object to a dictionary."""
        return {
            "id": self.id,
            "alias": self.alias,
            "device": self.device,
            "size": self.size,
            "cached": self.cached,
            "loaded": self.loaded,
            "backend": self.backend,
        }


class BenchmarkResult:
    """
    Schema for the benchmark return object.
    Excludes the incoming/result text, which should be streamed to the console.
    """
    def __init__(self, input_tokens, output_tokens, total_tokens, latency_ms, model, backend, timestamp, is_model_loaded):
        self.input_tokens = input_tokens  # Number of tokens in the input
        self.output_tokens = output_tokens  # Number of tokens in the output
        self.total_tokens = total_tokens  # Total tokens used (input + output)
        self.latency_ms = latency_ms  # Latency in milliseconds
        self.model = model  # Model details (e.g., name, version)
        self.backend = backend  # Backend used for inference
        self.timestamp = timestamp  # Timestamp of the benchmark execution
        self.is_model_loaded = is_model_loaded  # New field to capture the loaded state

    def to_dict(self):
        """Convert the benchmark result object to a dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "model": self.model,
            "backend": self.backend,
            "timestamp": self.timestamp,
            "is_model_loaded": self.is_model_loaded,
        }