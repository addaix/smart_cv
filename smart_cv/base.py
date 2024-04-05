"""Base objects for the smart_cv package."""

from dol import Files, add_ipython_key_completions, wrap_kvs
from smart_cv.util import extension_base_wrap
import json
import pathlib
from i2 import Namespace
from pdfdol import PdfFilesReader
from dol import Files, TextFiles
from config2py import (
    user_gettable,
    get_config as config_getter_factory,
)
from smart_cv.util import app_filepath, app_config_path, data_dir


@add_ipython_key_completions
@wrap_kvs(obj_of_data=json.loads) # TODO add reading function for Docx files
class CvsInfoStore(Files):
    """Get cv info dicts from folder"""

    def __init__(self, rootdir, *args, **kwargs):
        super().__init__(rootdir, *args, **kwargs)

# class CvsFilesReader(PdfFilesReader):
#     """Read CV files as text"""

#     def __init__(self, rootdir, *args, **kwargs):
#         super().__init__(rootdir, *args, **kwargs)


mall = Namespace(
    data=Files(app_filepath('data')),
    cvs= extension_base_wrap(Files(app_filepath('data', 'cvs'))), #CvsFilesReader(app_filepath('data', 'cvs')),
    cvs_info=CvsInfoStore(app_filepath('data', 'cvs_info')),
    filled=Files(app_filepath('data', 'filled')),
    configs=TextFiles(app_filepath('configs')),
    stacks=Files(app_filepath('data', 'stacks')),
    pkg_data_store=Files(data_dir),
)


# -----------------------------------------------------------
# Configs
from collections import ChainMap
from smart_cv.util import data_dir

pkg_defaults = {
    'template_path': str(data_dir + '/DT_Template.docx'),
}

config_sources = [
    mall.configs,  # user local configs
    json.loads(pathlib.Path(app_config_path).read_text()),  # package config.json
    pkg_defaults,  # package defaults
]

dflt_config = ChainMap(*config_sources)  # a config mapping

# a config getter, enhanced by the user_gettable store
get_config = config_getter_factory(
    sources=config_sources + [user_gettable(mall.configs)],
)


# -----------------------------------------------------------
dflt_stacks = ChainMap([
    mall.stacks,
])
