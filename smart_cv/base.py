"""Base objects for the smart_cv package."""

from dol import Files, add_ipython_key_completions, wrap_kvs
import json
import pathlib
from i2 import Namespace
from pdfdol import PdfFilesReader
from dol import Files, TextFiles
from smart_cv.util import app_filepath, pkg_config_path
from config2py import (
    user_gettable,
    get_config as config_getter_factory,
)


@add_ipython_key_completions
@wrap_kvs(obj_of_data=json.loads)
class CvsInfoStore(Files):
    """Get cv info dicts from folder"""

    def __init__(self, rootdir, *args, **kwargs):
        super().__init__(rootdir, *args, **kwargs)


class CvsFilesReader(PdfFilesReader):
    """Read CV files as text"""

    def __init__(self, rootdir, *args, **kwargs):
        super().__init__(rootdir, *args, **kwargs)


mall = Namespace(
    data=Files(app_filepath('data')),
    cvs=CvsFilesReader(app_filepath('data', 'cvs')),
    cvs_info=CvsInfoStore(app_filepath('data', 'cvs_info')),
    filled=Files(app_filepath('data', 'filled')),
    configs=TextFiles(app_filepath('configs')),
)


# -----------------------------------------------------------
# Configs
from collections import ChainMap

config_sources = [
    json.loads(pathlib.Path(pkg_config_path).read_text()),
    mall.configs,
]

dflt_config = ChainMap(*config_sources)  # a config mapping

# a config getter, enhanced by the user_gettable store
get_config = config_getter_factory(
    sources=config_sources + [user_gettable(mall.configs)],
)
