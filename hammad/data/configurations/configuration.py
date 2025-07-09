"""hammad.data.configurations.configuration"""

import os
import configparser
from pathlib import Path
from typing import Any, Self
from dotenv import load_dotenv, dotenv_values
import httpx
import msgspec
import yaml

from ..types.file import File, FileSource
from ..models.fields import field

__all__ = (
    "Configuration",
    "read_configuration_from_file",
    "read_configuration_from_url",
    "read_configuration_from_os_vars",
    "read_configuration_from_os_prefix",
    "read_configuration_from_dotenv",
)


class Configuration(File):
    """Model / structure representation for configuration objects
    for both module or application level usage. This class is
    nothing more than a glorified key-value store with a
    few extra features.

    Inherits from File to provide file operations and extends
    with configuration-specific functionality."""

    # Configuration-specific fields
    config_data: dict[str, Any] = field(default_factory=dict)
    """The actual configuration key-value pairs."""

    format_type: str | None = field(default=None)
    """The format type of the configuration (json, toml, yaml, ini, env)."""

    def __post_init__(self):
        """Initialize configuration data from file data if available."""
        super().__post_init__()

        # If we have data but no config_data, try to parse it
        if self.data is not None and not self.config_data:
            self._parse_data()

    def _parse_data(self) -> None:
        """Parse the file data into configuration format."""
        if not self.data:
            return

        content = self.data if isinstance(self.data, str) else self.data.decode("utf-8")

        # Determine format from extension or type
        format_type = self._detect_format()

        try:
            if format_type == "json":
                self.config_data = msgspec.json.decode(content.encode("utf-8"))
            elif format_type == "toml":
                self.config_data = msgspec.toml.decode(content.encode("utf-8"))
            elif format_type == "yaml":
                # Use PyYAML with unsafe_load for YAML tags like !!python/name:
                # This is needed for files like mkdocs.yml that use custom constructors
                try:
                    self.config_data = yaml.unsafe_load(content)
                except yaml.constructor.ConstructorError:
                    # Fallback to safe_load if unsafe_load fails
                    self.config_data = yaml.safe_load(content)
            elif format_type == "ini":
                parser = configparser.ConfigParser()
                parser.read_string(content)
                self.config_data = {
                    section: dict(parser[section]) for section in parser.sections()
                }
            elif format_type == "env":
                # Parse as dotenv format
                lines = content.strip().split("\n")
                config_data = {}
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config_data[key.strip()] = value.strip().strip("\"'")
                self.config_data = config_data

            self.format_type = format_type
        except Exception as e:
            raise ValueError(
                f"Failed to parse configuration data as {format_type}: {e}"
            )

    def _detect_format(self) -> str:
        """Detect the configuration format from extension or content."""
        if self.format_type:
            return self.format_type

        # Try to detect from file extension
        # Get extension directly from source path to avoid caching issues
        if self.source.path:
            ext = self.source.path.suffix.lower()
            if ext in [".json"]:
                return "json"
            elif ext in [".toml"]:
                return "toml"
            elif ext in [".yaml", ".yml"]:
                return "yaml"
            elif ext in [".ini", ".cfg", ".conf"]:
                return "ini"
            elif ext in [".env"]:
                return "env"
        elif self.extension:
            ext = self.extension.lower()
            if ext in [".json"]:
                return "json"
            elif ext in [".toml"]:
                return "toml"
            elif ext in [".yaml", ".yml"]:
                return "yaml"
            elif ext in [".ini", ".cfg", ".conf"]:
                return "ini"
            elif ext in [".env"]:
                return "env"

        # Try to detect from MIME type
        if self.type:
            if "json" in self.type:
                return "json"
            elif "yaml" in self.type:
                return "yaml"

        # Default fallback - try to parse as JSON first
        return "json"

    def _serialize_data(self, format_type: str | None = None) -> str:
        """Serialize configuration data to string format."""
        format_type = format_type or self.format_type or "json"

        if format_type == "json":
            return msgspec.json.encode(self.config_data).decode("utf-8")
        elif format_type == "toml":
            return msgspec.toml.encode(self.config_data).decode("utf-8")
        elif format_type == "yaml":
            return yaml.dump(
                self.config_data, default_flow_style=False, allow_unicode=True
            )
        elif format_type == "ini":
            parser = configparser.ConfigParser()
            for section_name, section_data in self.config_data.items():
                parser[section_name] = section_data
            import io

            output = io.StringIO()
            parser.write(output)
            return output.getvalue()
        elif format_type == "env":
            lines = []
            for key, value in self.config_data.items():
                # Simple escaping for shell variables
                if isinstance(value, str) and (
                    " " in value or '"' in value or "'" in value
                ):
                    value = f'"{value}"'
                lines.append(f"{key}={value}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    @classmethod
    def from_dotenv(cls, path: str | Path | None = None) -> Self:
        """Loads a .env file and creates a configuration object
        from it.

        NOTE: This does not set any environment variables.

        Args:
            path: The path to the .env file to load. If not provided,
                the .env file in the current working directory will be used.
        """
        if path is None:
            path = Path.cwd() / ".env"
        else:
            path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Environment file not found: {path}")

        # Use dotenv_values to parse without setting environment variables
        config_data = dotenv_values(path)

        return cls(
            config_data=dict(config_data),
            format_type="env",
            source=FileSource(
                is_file=True,
                path=path,
                size=path.stat().st_size if path.exists() else None,
            ),
            type="text/plain",
        )

    @classmethod
    def from_os_prefix(cls, prefix: str) -> Self:
        """Creates a new configuration object using all variables
        that begin with the given prefix.

        Args:
            prefix: The prefix to use to filter the variables.
        """
        config_data = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix) :].lstrip("_").lower()
                config_data[config_key] = value

        return cls(
            config_data=config_data,
            format_type="env",
            source=FileSource(),
            type="text/plain",
        )

    @classmethod
    def from_os_vars(cls, vars: list[str]) -> Self:
        """Pulls a certain set of environment variables and
        creates a configuration object from them.

        Args:
            vars: A list of environment variable names to pull.
        """
        config_data = {}
        for var in vars:
            if var in os.environ:
                config_data[var] = os.environ[var]

        return cls(
            config_data=config_data,
            format_type="env",
            source=FileSource(),
            type="text/plain",
        )

    @classmethod
    def from_file(
        cls,
        path: str | Path,
    ) -> Self:
        """Parses a file to return a configuration object. This
        utilizes the following file types:

        - json
        - toml
        - yaml
        - ini
        - env
        """
        # Use the parent File class to load the file
        file_obj = File.from_path(path, lazy=False)

        # Create a Configuration object from the File object
        config = cls(
            data=file_obj.data,
            type=file_obj.type,
            source=file_obj.source,
        )

        # Parse the data
        config._parse_data()

        return config

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> Self:
        """Load configuration from a URL supporting various formats.

        Args:
            url: The URL to load configuration from
            timeout: Request timeout in seconds
            headers: Optional HTTP headers to include in the request

        Returns:
            A new Configuration instance
        """
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers or {})
            response.raise_for_status()

            # Get content as text
            content = response.text

            # Determine format from URL extension or content-type
            format_type = None
            if url.endswith(".json"):
                format_type = "json"
            elif url.endswith((".yaml", ".yml")):
                format_type = "yaml"
            elif url.endswith(".toml"):
                format_type = "toml"
            elif url.endswith((".ini", ".cfg", ".conf")):
                format_type = "ini"
            elif url.endswith(".env"):
                format_type = "env"
            else:
                # Try to detect from content-type header
                content_type = response.headers.get("content-type", "").lower()
                if "json" in content_type:
                    format_type = "json"
                elif "yaml" in content_type:
                    format_type = "yaml"

        config = cls(
            data=content,
            type=response.headers.get("content-type"),
            format_type=format_type,
            source=FileSource(
                is_url=True,
                url=url,
                size=len(content.encode("utf-8")),
                encoding=response.encoding,
            ),
        )

        config._parse_data()
        return config

    def to_file(
        self,
        path: str | Path,
        *,
        overwrite: bool = False,
        format_type: str | None = None,
    ) -> None:
        """Saves the configuration object to a file. This
        utilizes the following file types:

        - json
        - toml
        - yaml
        - ini
        - env

        Args:
            path: The path to the file to save the configuration to.
            overwrite: Whether to overwrite the file if it already exists.
            format_type: Override the format type for saving.
        """
        save_path = Path(path)

        if save_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {save_path}")

        # Determine format from path extension if not specified
        if format_type is None:
            ext = save_path.suffix.lower()
            if ext in [".json"]:
                format_type = "json"
            elif ext in [".toml"]:
                format_type = "toml"
            elif ext in [".yaml", ".yml"]:
                format_type = "yaml"
            elif ext in [".ini", ".cfg", ".conf"]:
                format_type = "ini"
            elif ext in [".env"]:
                format_type = "env"
            else:
                format_type = self.format_type or "json"

        # Serialize and save
        content = self._serialize_data(format_type)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(content, encoding="utf-8")

    def update_file(
        self,
        path: str | Path,
        exclude: list[str] | None = None,
        exclude_none: bool = True,
    ) -> None:
        """Updates a valid configuration file with only the
        differing values.

        Args:
            path: The path to the file to update.
            exclude: A list of keys to exclude from the update.
            exclude_none: Whether to exclude keys with None values.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        # Load existing configuration
        existing_config = Configuration.from_file(path)

        # Prepare data to update
        update_data = self.config_data.copy()

        if exclude:
            for key in exclude:
                update_data.pop(key, None)

        if exclude_none:
            update_data = {k: v for k, v in update_data.items() if v is not None}

        # Merge with existing data
        existing_config.config_data.update(update_data)

        # Save back to file
        existing_config.to_file(path, overwrite=True)

    def to_os(
        self,
        prefix: str | None = None,
        exclude: list[str] | None = None,
    ) -> None:
        """Pushes the configuration object's values as active
        environment variables. This will overwrite any existing
        values for the session.

        Args:
            prefix: The prefix to use to filter the variables.
            exclude: A list of keys to exclude from the update.
        """
        exclude = exclude or []

        for key, value in self.config_data.items():
            if key in exclude:
                continue

            # Convert value to string
            env_value = str(value) if value is not None else ""

            # Apply prefix if specified
            env_key = f"{prefix}_{key}".upper() if prefix else key.upper()

            # Set environment variable
            os.environ[env_key] = env_value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: The configuration key
            default: Default value if key is not found

        Returns:
            The configuration value or default
        """
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: The configuration key
            value: The value to set
        """
        self.config_data[key] = value

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dict-like access."""
        return self.config_data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value using dict-like access."""
        self.config_data[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if configuration contains a key."""
        return key in self.config_data

    def keys(self):
        """Return configuration keys."""
        return self.config_data.keys()

    def values(self):
        """Return configuration values."""
        return self.config_data.values()

    def items(self):
        """Return configuration key-value pairs."""
        return self.config_data.items()


# HELPERS


def read_configuration_from_file(path: str | Path) -> Configuration:
    """Parse a filepath into a `Configuration` object.

    Valid file types:
    - json
    - toml
    - yaml
    - ini
    - env

    Args:
        path: The path to the file to parse.

    Returns:
        A `Configuration` object.
    """
    file_obj = File.from_path(path, lazy=False)
    return Configuration.from_file(file_obj)


def read_configuration_from_url(url: str) -> Configuration:
    """Parse a URL into a `Configuration` object.

    Args:
        url: The URL to parse.

    Returns:
        A `Configuration` object.
    """
    return Configuration.from_url(url)


def read_configuration_from_os_vars(vars: list[str]) -> Configuration:
    """Parse a list of environment variables into a `Configuration` object.

    Args:
        vars: The list of environment variables to parse.

    Returns:
        A `Configuration` object.
    """
    return Configuration.from_os_vars(vars)


def read_configuration_from_os_prefix(prefix: str) -> Configuration:
    """Parse a list of environment variables into a `Configuration` object.

    Args:
        prefix: The prefix to use to filter the variables.

    Returns:
        A `Configuration` object.
    """
    return Configuration.from_os_prefix(prefix)


def read_configuration_from_dotenv(path: str | Path = ".env") -> Configuration:
    """Parse a .env file into a `Configuration` object.

    NOTE: Defaults to `.env` in the current working directory.

    Args:
        path: The path to the .env file to parse.

    Returns:
        A `Configuration` object.
    """
    return Configuration.from_dotenv(path)
