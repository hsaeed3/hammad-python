"""hammad.data.types.multimodal.audio"""

import httpx
from typing import Self

from ...types.file import File, FileSource
from ...models.fields import field

__all__ = ("Audio",)


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
