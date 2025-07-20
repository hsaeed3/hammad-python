"""ham._internal._extensions

Contains a collection of extensions and utilities for the `ham` package.
"""

from logging import getLogger
logger = getLogger("ham.extensions")


def warn_deprecated(
    old_class : str | None = None,
    old_attribute : str | None = None,
    old_function : str | None = None,
    old_parameter : str | None = None,
    new_class : str | None = None,
    new_attribute : str | None = None,
    new_function : str | None = None,
    new_parameter : str | None = None,
) -> None:
    """Internal utility to warn about deprecated resources.
    
    Args:
        old : str
            The old resource name.
        new : str
            The new resource name.
    """
    # Determine the type of deprecation and construct the warning message
    if old_class and new_class:
        logger.warning(f"Class '{old_class}' is deprecated. Use '{new_class}' instead.")
    elif old_attribute and new_attribute:
        logger.warning(f"Attribute '{old_attribute}' is deprecated. Use '{new_attribute}' instead.")
    elif old_function and new_function:
        logger.warning(f"Function '{old_function}' is deprecated. Use '{new_function}' instead.")
    elif old_parameter and new_parameter:
        logger.warning(f"Parameter '{old_parameter}' is deprecated. Use '{new_parameter}' instead.")
    elif old_class:
        logger.warning(f"Class '{old_class}' is deprecated.")
    elif old_attribute:
        logger.warning(f"Attribute '{old_attribute}' is deprecated.")
    elif old_function:
        logger.warning(f"Function '{old_function}' is deprecated.")
    elif old_parameter:
        logger.warning(f"Parameter '{old_parameter}' is deprecated.")
    else:
        logger.warning("Deprecated usage detected.")


def raise_not_installed(
    module : str,
    packages : str | list[str],
    extensions : str | list[str],
) -> None:
    """
    Internal utility to raise an error if a module is not installed.

    Args:
        module : str
            The module name.
        packages : str | list[str]
            The package name(s).
        extensions : str | list[str]
            The extension name(s).
    """
    if isinstance(packages, str):
        packages = [packages]
    if isinstance(extensions, str):
        extensions = [extensions]
    
    logger.critical(
        f"Module '{module}' is not installed. "
        f"You can either:"
        f"1. Install required packages: {', '.join(packages)}. "
        f"2. Install either of the following extensions: {', '.join([f'hammad-python[{ext}]' for ext in extensions])}."
    )


__all__ = [
    "warn_deprecated",
    "raise_not_installed",
]