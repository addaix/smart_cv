"""Utils for smart_cv"""

from importlib.resources import files
import json
from functools import partial
import pdfplumber
import tiktoken
from i2 import Namespace
from config2py import (
    get_app_data_folder,
    process_path,
)
from dol import wrap_kvs, Pipe
from pypdf import PdfReader
from msword import bytes_to_doc, get_text_from_docx  # pip install msword
from io import BytesIO
import json
import os

pkg_name = "smart_cv"
# -----------------------------------------------------------
# Paths and stores

# The following is the original way, due to be replaced by the next "app folder" way
pkg_files = files(pkg_name)
pkg_data_files = pkg_files / "data"
pkg_data_path = str(pkg_data_files)
pkg_defaults = pkg_data_files / "defaults"
# pkg_files_path = str(pkg_files)
# pkg_config_path = str(pkg_data_files / "config.json")


# The "app folder" way
app_dir = get_app_data_folder(pkg_name, ensure_exists=True)
app_filepath = partial(process_path, ensure_dir_exists=False, rootdir=app_dir)
data_dir = app_filepath('data')
dt_template_dir = app_filepath('data/DT_Template.docx')
app_config_path = app_filepath('configs/config.json')
filled_dir = app_filepath('data/filled')


# def copy_if_missing(src, dest):
#     if not os.path.isfile(dest):
#         with open(dest, 'w') as f:
#             with open(src) as f2:
#                 f.write(f2.read())


# -----------------------------------------------------------


def return_save_bytes(save_function):
    """Return bytes from a save function.

    :param save_function: A function that saves to a file-like object
    :return: The serialization bytes

    """
    import io

    io_target = io.BytesIO()
    with io_target as f:
        save_function(f)
        io_target.seek(0)
        return io_target.read()


def num_tokens(string: str, encoding_name: str = "cl100k_base") -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def read_pdf_text(pdf_reader):
    text_pages = []
    for page in pdf_reader.pages:
        text_pages.append(page.extract_text())
    return text_pages


def read_pdf(file, *, page_sep="\n--------------\n") -> str:
    with pdfplumber.open(file) as pdf:
        return page_sep.join(read_pdf_text(pdf))


# Map file extensions to decoding functions
extension_to_decoder = {
    '.txt': lambda obj: obj.decode('utf-8'),
    '.json': json.loads,
    '.pdf': Pipe(BytesIO, read_pdf),
    '.docx': Pipe(bytes_to_doc, get_text_from_docx),
}

extension_to_encoder = {
    '.txt': lambda obj: obj.encode('utf-8'),
    '.json': json.dumps,
    '.pdf': lambda obj: obj,
    '.docx': lambda obj: obj,
}

def extension_based_decoding(k, v):
    ext = '.' + k.split('.')[-1]
    decoder = extension_to_decoder.get(ext, None)
    if decoder is None:
        decoder = extension_to_decoder['.txt']
    return decoder(v)

def extension_base_encoding(k, v):
    ext = '.' + k.split('.')[-1]
    encoder = extension_to_encoder.get(ext, None)
    if encoder is None:
        encoder = extension_to_encoder['.txt']
    return encoder(v)


def extension_base_wrap(store):
    return wrap_kvs(store, postget=extension_based_decoding) #, preset=extension_base_encoding)




# --------------------------  Missed content analysis  --------------------------------

# TODO
