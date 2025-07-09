"""hammad.data.types.file"""

from pathlib import Path
import httpx
from typing import Any, Self
import mimetypes
from urllib.parse import urlparse

from ..models.model import Model
from ..models.fields import field

__all__ = ("File", "FileSource")


_FILE_SIGNATURES = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"%PDF": "application/pdf",
    b"PK": "application/zip",
}


_mime_cache: dict[str, str] = {}
"""Cache for MIME types."""


class FileSource(Model, kw_only=True, dict=True, frozen=True):
    """Represents the source of a `File` object."""

    is_file: bool = field(default=False)
    """Whether this data represents a file."""
    is_dir: bool = field(default=False)
    """Whether this data represents a directory."""
    is_url: bool = field(default=False)
    """Whether this data originates from a URL."""
    path: Path | None = field(default=None)
    """The file path if this is file-based data."""
    url: str | None = field(default=None)
    """The URL if this is URL-based data."""
    size: int | None = field(default=None)
    """Size in bytes if available."""
    encoding: str | None = field(default=None)
    """Text encoding if applicable."""


class File(Model, kw_only=True, dict=True):
    """Base object for all file-like structure types within
    the `hammad` ecosystem."""

    data: Any | None = field(default=None)
    """The actual data content (bytes, string, path object, etc.)"""
    type: str | None = field(default=None)
    """The MIME type or identifier for the data."""

    source: FileSource = field(default_factory=FileSource)
    """The source of the data. Contains metadata as well."""

    # Private cached attributes
    _name: str | None = field(default=None)
    _extension: str | None = field(default=None)
    _repr: str | None = field(default=None)

    @property
    def name(self) -> str | None:
        """Returns the name of this data object."""
        if self._name is not None:
            return self._name

        if self.source.path:
            self._name = self.source.path.name
        elif self.source.url:
            parsed = urlparse(self.source.url)
            self._name = parsed.path.split("/")[-1] or parsed.netloc
        else:
            self._name = ""  # Cache empty result

        return self._name if self._name else None

    @property
    def extension(self) -> str | None:
        """Returns the extension of this data object."""
        if self._extension is not None:
            return self._extension

        if self.source.path:
            self._extension = self.source.path.suffix
        elif name := self.name:
            if "." in name:
                self._extension = f".{name.rsplit('.', 1)[-1]}"
            else:
                self._extension = ""  # Cache empty result
        else:
            self._extension = ""  # Cache empty result

        return self._extension if self._extension else None

    @property
    def exists(self) -> bool:
        """Returns whether this data object exists."""
        if self.data is not None:
            return True
        if self.source.path and (self.source.is_file or self.source.is_dir):
            return self.source.path.exists()
        return False

    def read(self) -> bytes | str:
        """Reads the data content.

        Returns:
            The data content as bytes or string depending on the source.

        Raises:
            ValueError: If the data cannot be read.
        """
        if self.data is not None:
            return self.data

        if self.source.path and self.source.is_file and self.source.path.exists():
            if self.source.encoding:
                return self.source.path.read_text(encoding=self.source.encoding)
            return self.source.path.read_bytes()

        raise ValueError(f"Cannot read data from {self.name or 'unknown source'}")

    def to_file(self, path: str | Path, *, overwrite: bool = False) -> Path:
        """Save the data to a file.

        Args:
            path: The path to save to.
            overwrite: If True, overwrite existing files.

        Returns:
            The path where the file was saved.

        Raises:
            FileExistsError: If file exists and overwrite is False.
            ValueError: If data cannot be saved.
        """
        save_path = Path(path)

        if save_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {save_path}")

        # Ensure parent directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.read()
        if isinstance(data, str):
            save_path.write_text(data, encoding=self.source.encoding or "utf-8")
        else:
            save_path.write_bytes(data)

        return save_path

    def __repr__(self) -> str:
        """Returns a string representation of the data object."""
        if self._repr is not None:
            return self._repr

        parts = []

        if self.source.path:
            parts.append(f"path={self.source.path!r}")
        elif self.source.url:
            parts.append(f"url={self.source.url!r}")
        elif self.data is not None:
            parts.append(f"data={self.data!r}")

        if self.source.is_file:
            parts.append("is_file=True")
        elif self.source.is_dir:
            parts.append("is_dir=True")
        elif self.source.is_url:
            parts.append("is_url=True")

        if (size := self.source.size) is not None:
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1048576:  # 1024 * 1024
                size_str = f"{size / 1024:.1f}KB"
            elif size < 1073741824:  # 1024 * 1024 * 1024
                size_str = f"{size / 1048576:.1f}MB"
            else:
                size_str = f"{size / 1073741824:.1f}GB"
            parts.append(f"size={size_str}")

        if self.source.encoding:
            parts.append(f"encoding={self.source.encoding!r}")

        self._repr = f"<{', '.join(parts)}>"
        return self._repr

    def __eq__(self, other: Any) -> bool:
        """Returns whether this data object is equal to another."""
        return isinstance(other, File) and self.data == other.data

    @classmethod
    def from_path(
        cls,
        path: str | Path,
        *,
        encoding: str | None = None,
        lazy: bool = True,
    ) -> Self:
        """Creates a data object from a filepath and
        assigns the appropriate type and flags.

        Args:
            path: The file or directory path.
            encoding: Text encoding for reading text files.
            lazy: If True, defer loading content until needed.

        Returns:
            A new Data instance representing the file or directory.
        """
        path = Path(path)

        # Use cached stat call
        try:
            stat = path.stat()
            is_file = stat.st_mode & 0o170000 == 0o100000  # S_IFREG
            is_dir = stat.st_mode & 0o170000 == 0o040000  # S_IFDIR
            size = stat.st_size if is_file else None
        except OSError:
            is_file = is_dir = False
            size = None

        # Get MIME type for files using cache
        mime_type = None
        if is_file:
            path_str = str(path)
            if path_str in _mime_cache:
                mime_type = _mime_cache[path_str]
            else:
                mime_type, _ = mimetypes.guess_type(path_str)
                _mime_cache[path_str] = mime_type

        # Load data if not lazy and it's a file
        data = None
        if not lazy and is_file and size is not None:
            if encoding or (mime_type and mime_type.startswith("text/")):
                data = path.read_text(encoding=encoding or "utf-8")
            else:
                data = path.read_bytes()

        return cls(
            data=data,
            type=mime_type,
            source=FileSource(
                is_file=is_file,
                is_dir=is_dir,
                is_url=False,
                path=path,
                size=size,
                encoding=encoding,
            ),
        )

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        type: str | None = None,
        lazy: bool = True,
    ) -> Self:
        """Creates a data object from either a downloadable
        URL (treated as a file), or a web page itself treated as a
        document.

        Args:
            url: The URL to create data from.
            type: Optional MIME type override.
            lazy: If True, defer loading content until needed.

        Returns:
            A new Data instance representing the URL.
        """
        data = None
        size = None
        encoding = None

        # Load data if not lazy
        if not lazy:
            try:
                with httpx.Client() as client:
                    response = client.get(url)
                    response.raise_for_status()

                    data = response.content
                    size = len(data)

                    # Get content type from response headers if not provided
                    if not type:
                        content_type = response.headers.get("content-type", "")
                        type = content_type.split(";")[0] if content_type else None

                    # Get encoding from response if it's text content
                    if response.headers.get("content-type", "").startswith("text/"):
                        encoding = response.encoding
                        data = response.text

            except Exception:
                # If download fails, still create the object but without data
                pass

        return cls(
            data=data,
            type=type,
            source=FileSource(
                is_url=True,
                is_file=False,
                is_dir=False,
                url=url,
                size=size,
                encoding=encoding,
            ),
        )

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        *,
        type: str | None = None,
        name: str | None = None,
    ) -> Self:
        """Creates a data object from a bytes object.

        Args:
            data: The bytes data.
            type: Optional MIME type.
            name: Optional name for the data.

        Returns:
            A new Data instance containing the bytes data.
        """
        # Try to detect type from content if not provided
        if not type and data:
            # Check against pre-compiled signatures
            for sig, mime in _FILE_SIGNATURES.items():
                if data.startswith(sig):
                    type = mime
                    break

        return cls(
            data=data,
            type=type,
            source=FileSource(
                is_file=True,
                is_dir=False,
                is_url=False,
                size=len(data),
                path=Path(name) if name else None,
            ),
        )
