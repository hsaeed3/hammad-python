"""hammad.yaml.converters"""

from msgspec.yaml import encode as encode_yaml, decode as decode_yaml
from ..data.types import Configuration as Yaml

__all__ = ("encode_yaml", "decode_yaml", "read_yaml_file", "Yaml")


def read_yaml_file(path: str) -> Yaml:
    """Parses a YAML file to return a Configuration object.
    This utilizes the following file types:

    Args:
        path (str): The path to the YAML file.

    Returns:
        Yaml: A Configuration object.
    """
    return Yaml.from_file(path)
