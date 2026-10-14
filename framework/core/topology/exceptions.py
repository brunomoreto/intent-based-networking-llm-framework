"""Exceptions for the topology domain and serialization layer."""


class TopologyError(Exception):
    """Base exception for topology-related errors."""


class SerializationError(TopologyError):
    """Base exception for topology serialization errors."""


class TopologyFileError(SerializationError):
    """Raised when a topology file cannot be read or written."""


class TopologyFormatError(SerializationError):
    """Raised when a topology document has invalid JSON syntax or structure."""


class UnsupportedSchemaVersionError(SerializationError):
    """Raised when the JSON schema version is not supported."""


class TopologyValidationError(TopologyError):
    """Raised when a topology violates structural validation rules."""


__all__ = [
    "TopologyError",
    "SerializationError",
    "TopologyFileError",
    "TopologyFormatError",
    "UnsupportedSchemaVersionError",
    "TopologyValidationError",
]
