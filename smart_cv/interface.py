"""Interface objects"""

from smart_cv.base import dflt_config, get_config, dflt_stacks, dflt_json_example, mall
from smart_cv.resume_parser import ContentRetriever, TemplateFiller
from smart_cv.util import dt_template_dir, filled_dir
from functools import partial
config = dflt_config


def _mk_parser(
    cv_text: str,
    language: str = "french",
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
        language_list=config["language_list"],
        language=language,
        json_example=dflt_json_example,
        chunk_overlap=chunk_overlap,
        temperature=temperature,
        optional_content=config.get("optional_content", {}),
        empty_label=config.get("empty_label", "To be filled"))


def cv_content(
    cv_text: str,
    language: str = "french",
    *,
    chunk_overlap: int = config.get("chunk_overlap", 50),
    temperature: float = config.get("temperature", 0),
    empty_label: str = config.get("empty_label", "To be filled")
):
    """Returns the filled template"""
    parser = _mk_parser(
        cv_text=cv_text,
        language=language,
        chunk_overlap=chunk_overlap,
        temperature=temperature,
        empty_label=empty_label)
    content = parser()

    return content


def cv_text(cv_name):
    assert cv_name in mall.cvs, f"CV name {cv_name} not found in the mall."
    cv_text = cv_text = mall.cvs[cv_name]
    return cv_text


def fill_template(cv_content:dict, cv_name, template_path=dt_template_dir, save_to=filled_dir):
    """Fill a template with the given content"""
    filler = TemplateFiller(template_path=template_path, content=cv_content)
    if save_to is not None:
        if isinstance(save_to, str):
            if not save_to.endswith("docx"):
                filepath = save_to + f"/{cv_name.split('.')[0]}_filled.docx"
            else:
                filepath = save_to
            filler.save_template(filepath)
    return filepath