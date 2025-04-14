import logging

class BaseExtractor:
    """Base class for all data extractors."""
    def __init__(self, source_config, global_config):
        self.source_config = source_config
        self.global_config = global_config # Keep global config if needed for paths etc.
        self.source_name = "base" # Override in subclasses
        logging.debug(f"Initializing BaseExtractor for source: {self.source_name}")

    def extract(self):
        """Main method to be implemented by subclasses to extract data."""
        raise NotImplementedError(f"Extract method not implemented for {self.__class__.__name__}")

    def _standardize_output(self, item_id, item_type, content, metadata):
        """Helper to create the standard dictionary output format."""
        # Ensure basic types for compatibility
        return {
            'source': self.source_name,
            'id': str(item_id),
            'type': str(item_type),
            'content': str(content) if content is not None else '',
            'metadata': metadata or {}
        } 