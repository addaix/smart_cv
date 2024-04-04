"""Base objects for the smart_cv package."""

from dol import Files, add_ipython_key_completions, wrap_kvs
import json
from docx import Document
from smart_cv.util import cvs_info_dirpath, cvs_dirpath

from pdfdol import PdfFilesReader

@add_ipython_key_completions
@wrap_kvs(obj_of_data=json.loads) # TODO add reading function for Docx files
class CvsInfoStore(Files):
    """Get cv info dicts from folder"""

    def __init__(self, rootdir=str(cvs_info_dirpath), *args, **kwargs):
        super().__init__(rootdir, *args, **kwargs)

class CvsFilesReader(PdfFilesReader):
    """Read CV files as text"""

    def __init__(self, rootdir=str(cvs_dirpath), *args, **kwargs):
        super().__init__(rootdir, *args, **kwargs)
