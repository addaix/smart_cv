"""Interface objects"""

from typing import Optional
from smart_cv.base import dflt_config, get_config
from smart_cv.ResumeParser import ContentRetriever, TemplateFiller
from smart_cv.util import return_save_bytes

config = dflt_config


def _mk_parser(
    cv_path: str,
    *,
    chunk_overlap: int = config.get("chunk_overlap", 50),
    temperature: float = config.get("temperature", 0),
    empty_label: str = config.get("empty_label", "To be filled")
):
    return ContentRetriever(
        cv_path=cv_path,
        api_key=get_config('api_key'),
        prompts=config["prompts"],
        chunk_overlap=chunk_overlap,
        temperature=temperature,
        optional_content=config.get("optional_content", {}),
        empty_label=empty_label,
    )


def process_cv(
    cv_path: str,
    filled_filepath: Optional[str] = None,
    *,
    dt_template_path: str = config["template_path"],
    chunk_overlap: int = config.get("chunk_overlap", 50),
    temperature: float = config.get("temperature", 0),
    empty_label: str = config.get("empty_label", "To be filled")
) -> bytes:
    """Returns the filled template"""
    parser = _mk_parser(
        cv_path=cv_path,
        chunk_overlap=chunk_overlap,
        temperature=temperature,
        empty_label=empty_label,
    )

    content = parser()

    filler = TemplateFiller(template_path=dt_template_path, content=content)

    save_bytes = return_save_bytes(filler.save_template)

    if filled_filepath is not None:
        with open(filled_filepath, "wb") as f:
            f.write(save_bytes)

    return save_bytes
