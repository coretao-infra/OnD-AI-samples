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