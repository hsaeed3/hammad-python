"""hammad.ai.models._providers"""

__all__ = (
    "get_litellm_module",
)


LITELLM_MODULE = None


def get_litellm_module():
    """Get the litellm module."""
    global LITELLM_MODULE
    if LITELLM_MODULE is None:
        try:
            import litellm
            litellm.drop_params = True
            litellm.modify_params = True
            LITELLM_MODULE = litellm
        except ImportError:
            raise ImportError("litellm is not installed. Please install it with `pip install hammad-python[ai]`")
        
    return LITELLM_MODULE
    
    
    