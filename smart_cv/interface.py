"""Interface objects"""

from typing import Optional, MutableMapping, Union
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
    save_to: Optional[Union[str, MutableMapping]] = None,
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

    if save_to is not None:
        if isinstance(save_to, str):
            filepath = save_to
            with open(filepath, "wb") as f:
                f.write(save_bytes)
        elif isinstance(save_to, MutableMapping):
            # compute save_key by replacing the cv_path filename
            # extension with docx extension
            cv_path_filename = cv_path.split('/')[-1]
            save_key = cv_path_filename.replace('.pdf', '.docx')
            # get the filename only
            save_to[save_key] = save_bytes

    return save_bytes
