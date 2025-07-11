"""hammad._run

Main entrypoint for the `run` command and resource at the
top level of the hammad package.
"""


class run:
    """Top level namespace resource for running various things and stuff."""

    from ..genai import (
        # agents
        run_agent as agent,
        run_agent_iter as agent_iter,
        async_run_agent as async_agent,
        async_run_agent_iter as async_agent_iter,
        # models
        run_embedding_model as embedding_model,
        async_run_embedding_model as async_embedding_model,
        run_language_model as language_model,
        async_run_language_model as async_language_model,
        run_image_edit_model as image_edit_model,
        async_run_image_edit_model as async_image_edit_model,
        run_image_generation_model as image_generation_model,
        async_run_image_generation_model as async_image_generation_model,
        run_image_variation_model as image_variation_model,
        async_run_image_variation_model as async_image_variation_model,
        run_reranking_model as reranking_model,
        async_run_reranking_model as async_reranking_model,
        run_transcription_model as transcription_model,
        async_run_transcription_model as async_transcription_model,
        run_tts_model as tts_model,
        async_run_tts_model as async_tts_model,
    )
    from ..mcp import launch_mcp_servers as mcp_servers
    from ..runtime import (
        run_parallel as parallel,
        run_sequentially as sequentially,
        run_with_retry as with_retry,
    )
    from ..web import (
        read_web_page as web_reader,
        read_web_pages as web_reader_batch,
        run_web_search as web_search,
        run_news_search as news_search,
        run_web_request as web_request,
    )


__all__ = ["run"]
