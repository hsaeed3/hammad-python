"""hammad.data.types.multimodal.image"""

import httpx
from typing import Self

from ...types.file import File, FileSource
from ...models.fields import field

__all__ = ("Image",)


class Image(File):
    """A representation of an image, that is loadable from both a URL, file path
    or bytes."""

    # Image-specific metadata
    _width: int | None = field(default=None)
    _height: int | None = field(default=None)
    _format: str | None = field(default=None)

    @property
    def is_valid_image(self) -> bool:
        """Check if this is a valid image based on MIME type."""
        return self.type is not None and self.type.startswith("image/")

    @property
    def format(self) -> str | None:
        """Get the image format from MIME type."""
        if self._format is None and self.type:
            # Extract format from MIME type (e.g., 'image/png' -> 'png')
            self._format = self.type.split("/")[-1].upper()
        return self._format

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        lazy: bool = True,
        timeout: float = 30.0,
    ) -> Self:
        """Download and create an image from a URL.

        Args:
            url: The URL to download from.
            lazy: If True, defer loading content until needed.
            timeout: Request timeout in seconds.

        Returns:
            A new Image instance.
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

                # Validate it's an image
                if type and not type.startswith("image/"):
                    raise ValueError(f"URL does not point to an image: {type}")

        return cls(
            data=data,
            type=type,
            source=FileSource(
                is_url=True,
                url=url,
                size=size,
            ),
        )
