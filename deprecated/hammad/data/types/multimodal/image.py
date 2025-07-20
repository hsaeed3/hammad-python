"""hammad.data.types.multimodal.image"""

import httpx
import mimetypes
from pathlib import Path
from typing import Self

from ...types.file import File, FileSource, _FILE_SIGNATURES
from ...models.fields import field


__all__ = (
    "Image",
    "read_image_from_path",
    "read_image_from_url",
)


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

    @classmethod
    def from_path(
        cls,
        path: str | Path,
    ) -> Self:
        """Create an image from a file path.

        Args:
            path: The path to the image file.

        Returns:
            A new Image instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid image.
        """
        path_obj = Path(path)

        if not path_obj.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        if not path_obj.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Read the file data
        data = path_obj.read_bytes()

        # Detect MIME type
        type = None
        for sig, mime in _FILE_SIGNATURES.items():
            if data.startswith(sig):
                type = mime
                break

        # Fallback to mimetypes module
        if not type:
            type, _ = mimetypes.guess_type(str(path))

        # Validate it's an image
        if type and not type.startswith("image/"):
            raise ValueError(f"File is not an image: {type}")

        return cls(
            data=data,
            type=type,
            source=FileSource(
                is_file=True,
                path=path_obj,
                size=len(data),
            ),
        )


def read_image_from_url(
    url: str,
    *,
    lazy: bool = True,
    timeout: float = 30.0,
) -> Image:
    """Download and create an image from a URL.

    Args:
        url: The URL to download from.
        lazy: If True, defer loading content until needed.
        timeout: Request timeout in seconds.

    Returns:
        A new Image instance.

    Raises:
        httpx.RequestError: If the request fails.
        httpx.HTTPStatusError: If the response has an error status code.
        ValueError: If the URL does not point to an image.
    """
    return Image.from_url(url, lazy=lazy, timeout=timeout)


def read_image_from_path(
    path: str | Path,
) -> Image:
    """Create an image from a file path.

    Args:
        path: The path to the image file.

    Returns:
        A new Image instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid image.
    """
    return Image.from_path(path)
