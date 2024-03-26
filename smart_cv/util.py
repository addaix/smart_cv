"""Utils for smart_cv"""

from importlib.resources import files
import json
import tiktoken
from PyPDF2 import PdfReader

pkg_name = "smart_cv"

proj_files = files(pkg_name)
data_files = proj_files / "data"
cvs_files = data_files / "cvs"
cvs_info_files = data_files / "cvs_info"

cvs_dirpath = str(cvs_files)
cvs_info_dirpath = str(cvs_info_files)

def read_config(config_file: str) -> dict:
    """Read a config file and return a dictionary"""
    with open(config_file, "r") as f:
        d = json.load(f)

    assert "template" in d, "Please provide a template path in the config file."
    assert "prompts" in d, "Please provide prompts in the config file."
    assert "api_key" in d, "Please provide an API key in the config file."
    

    return d

def num_tokens_from_string(string: str, encoding_name: str="cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def num_tokens_doc(doc: str, encoding_name: str = "cl100k_base") -> int:
    num_tokens = 0
    with open(doc, "rb") as f:  # Open in binary mode
        pdf = PdfReader(f)
        for page in pdf.pages:  # Iterate over pages directly
            text = page.extract_text()
            num_tokens += num_tokens_from_string(text, encoding_name)
    return num_tokens


def load_full_text(doc: str):
    text = ""
    with open(doc, "rb") as f:  # Open in binary mode
        pdf = PdfReader(f)
        for page in pdf.pages:  # Iterate over pages directly
            text += page.extract_text()
    return text        
