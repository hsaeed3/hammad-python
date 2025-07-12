"""hammad.data.types.multimodal.audio"""

import httpx
import mimetypes
from pathlib import Path
from typing import Self

from ...types.file import File, FileSource, _FILE_SIGNATURES
from ...models.fields import field


__all__ = (
    "Audio",
    "read_audio_from_path",
    "read_audio_from_url",
)


class Audio(File):
    """A representation of an audio file, that is loadable from both a URL, file path
    or bytes."""

    # Audio-specific metadata
    _duration: float | None = field(default=None)
    _sample_rate: int | None = field(default=None)
    _channels: int | None = field(default=None)
    _format: str | None = field(default=None)

    @property
    def is_valid_audio(self) -> bool:
        """Check if this is a valid audio file based on MIME type."""
        return self.type is not None and self.type.startswith("audio/")

    @property
    def format(self) -> str | None:
        """Get the audio format from MIME type."""
        if self._format is None and self.type:
            # Extract format from MIME type (e.g., 'audio/mp3' -> 'mp3')
            self._format = self.type.split("/")[-1].upper()
        return self._format

    @property
    def duration(self) -> float | None:
        """Get the duration of the audio file in seconds."""
        return self._duration

    @property
    def sample_rate(self) -> int | None:
        """Get the sample rate of the audio file in Hz."""
        return self._sample_rate

    @property
    def channels(self) -> int | None:
        """Get the number of channels in the audio file."""
        return self._channels

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        lazy: bool = True,
        timeout: float = 30.0,
    ) -> Self:
        """Download and create an audio file from a URL.

        Args:
            url: The URL to download from.
            lazy: If True, defer loading content until needed.
            timeout: Request timeout in seconds.

        Returns:
            A new Audio instance.
        """
        data = None
        size = None
        type = None

        if not lazy:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url)
                response.raise_for_status()

                data = response.content
                size = len(data)

                # Get content type
                content_type = response.headers.get("content-type", "")
                type = content_type.split(";")[0] if content_type else None

                # Validate it's audio
                if type and not type.startswith("audio/"):
                    raise ValueError(f"URL does not point to an audio file: {type}")

        return cls(
            data=data,
            type=type,
            source=FileSource(
                is_url=True,
                url=url,
                size=size,
            ),
        )

    @classmethod
    def from_path(
        cls,
        path: str | Path,
    ) -> Self:
        """Create an audio file from a file path.

        Args:
            path: The path to the audio file.

        Returns:
            A new Audio instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid audio file.
        """
        path_obj = Path(path)

        if not path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Read file data
        data = path_obj.read_bytes()

        # Determine MIME type
        type = None

        # Check file signature first
        for signature, mime_type in _FILE_SIGNATURES.items():
            if data.startswith(signature) and mime_type.startswith("audio/"):
                type = mime_type
                break

        # Fall back to mimetypes module
        if not type:
            type, _ = mimetypes.guess_type(str(path))

        # Validate it's an audio file
        if type and not type.startswith("audio/"):
            raise ValueError(f"File is not an audio file: {type}")

        return cls(
            data=data,
            type=type,
            source=FileSource(
                is_file=True,
                path=path_obj,
                size=len(data),
            ),
        )


def read_audio_from_url(
    url: str,
    *,
    lazy: bool = True,
    timeout: float = 30.0,
) -> Audio:
    """Download and create an audio file from a URL.

    Args:
        url: The URL to download from.
        lazy: If True, defer loading content until needed.
        timeout: Request timeout in seconds.

    Returns:
        A new Audio instance.

    Raises:
        httpx.RequestError: If the request fails.
        httpx.HTTPStatusError: If the response has an error status code.
        ValueError: If the URL does not point to an audio file.
    """
    return Audio.from_url(url, lazy=lazy, timeout=timeout)


def read_audio_from_path(
    path: str | Path,
) -> Audio:
    """Create an audio file from a file path.

    Args:
        path: The path to the audio file.

    Returns:
        A new Audio instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid audio file.
    """
    return Audio.from_path(path)
