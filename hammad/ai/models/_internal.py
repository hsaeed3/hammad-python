"""hammad.ai.models._internal"""

__all__ = ("_get_litellm_resource",)


# ------------------------------------------------------------
# LITELLM
# ------------------------------------------------------------


_LITELLM = None


def _get_litellm_resource():
    """Get the litellm resource."""
    global _LITELLM
    if _LITELLM is None:
        try:
            import litellm

            litellm.drop_params = True
            litellm.modify_params = True
            _LITELLM = litellm
        except ImportError:
            raise ImportError(
                "litellm is not installed. Please install it with `pip install hammad-python[ai]`"
            )

    return _LITELLM
