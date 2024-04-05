"""Interface objects"""

from typing import Optional, MutableMapping, Union
from smart_cv.base import dflt_config, get_config, dflt_stacks, mall
from smart_cv.resume_parser import ContentRetriever, TemplateFiller
from smart_cv.util import return_save_bytes, dt_template_dir, filled_dir
from functools import partial
config = dflt_config


def _mk_parser(
    cv_text: str,
    *,
    chunk_overlap: int = config.get("chunk_overlap", 50),
    temperature: float = config.get("temperature", 0),
    empty_label: str = config.get("empty_label", "To be filled")
):
    """Create a parser object for the given CV."""
    return ContentRetriever(
        cv_text=cv_text,
        api_key=get_config('api_key'),
        prompts=config["prompts"],
        stacks=dflt_stacks,
        chunk_overlap=chunk_overlap,
        temperature=temperature,
        optional_content=config.get("optional_content", {}),
        empty_label=empty_label,
    )


def process_cv(
    cv_text: str,
    *,
    chunk_overlap: int = config.get("chunk_overlap", 50),
    temperature: float = config.get("temperature", 0),
    empty_label: str = config.get("empty_label", "To be filled")
):
    """Returns the filled template"""
   
    parser = _mk_parser(
        cv_text=cv_text,
        chunk_overlap=chunk_overlap,
        temperature=temperature,
        empty_label=empty_label,
    )

    content = parser()
    return content

partial_process_cv = partial(process_cv, chunk_overlap=50, temperature=0, empty_label="To be filled")

def cv_content(cv_name):
    assert cv_name in mall.cvs, f"CV name {cv_name} not found in the mall."
    cv_text = cv_text = mall.cvs[cv_name]
    return partial_process_cv(cv_text)

def fill_template(cv_content:dict, cv_name, template_path=dt_template_dir, save_to=filled_dir):
    """Fill a template with the given content"""
    filler = TemplateFiller(template_path=template_path, content=cv_content)
    filler.save_template
    if save_to is not None:
        if isinstance(save_to, str):
            if not save_to.endswith("docx"):
                filepath = save_to + f"/{cv_name}_filled.docx"
            else:
                filepath = save_to
            filler.save_template(filepath)
    #save_bytes = return_save_bytes(filler.save_template)
    #return save_bytes