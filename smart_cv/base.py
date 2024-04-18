"""Base objects for the smart_cv package."""

from dol import Files, add_ipython_key_completions, wrap_kvs
from smart_cv.util import extension_base_wrap
import json
import pathlib
from i2 import Namespace
from dol import Files
from config2py import (
    user_gettable,
    get_config as config_getter_factory,
)
from smart_cv.util import app_filepath, app_config_path, data_dir


@add_ipython_key_completions
@wrap_kvs(obj_of_data=json.loads)  # TODO add reading function for Docx files
class CvsInfoStore(Files):
    """Get cv info dicts from folder"""

    def __init__(self, rootdir, *args, **kwargs):
        super().__init__(rootdir, *args, **kwargs)


mall = Namespace(
    data=extension_base_wrap(Files(app_filepath('data'))),
    cvs=extension_base_wrap(Files(app_filepath('data', 'cvs'))),
    cvs_info=CvsInfoStore(app_filepath('data', 'cvs_info')),
    filled=extension_base_wrap(Files(app_filepath('data', 'filled'))),
    configs=extension_base_wrap(Files(app_filepath('configs'))),
    pkg_data_store=Files(data_dir),
)

# -----------------------------------------------------------
# Populate what's missing in local user space
from smart_cv.util import pkg_data_files


def copy_if_missing(key, dest_store, src_files_obj=pkg_data_files):
    if key not in dest_store:
        dest_store[key] = (src_files_obj / key).read_bytes()

copy_if_missing('config.json', mall.configs)
copy_if_missing('stacks_keywords.txt', mall.data)
copy_if_missing('json_example.txt', mall.configs)

# if 'config.json' not in mall.configs:
#     mall.configs['config.json'] = pkg_data_files / 'config.json'

# if 'stacks_keywords.txt' not in mall.data:
#     mall.data['stacks_keywords.txt'] = pkg_data_files / 'stacks_keywords.txt'

# if 'json_example.txt' not in mall.configs:
#     mall.configs['json_example.txt'] = pkg_data_files / 'json_example.txt'

# -----------------------------------------------------------
# Configs
from collections import ChainMap
from smart_cv.util import data_dir

# pkg_defaults = {
#     'template_path': str(data_dir + '/DT_Template.docx'),
# }

config_sources = [
    mall.configs,  # user local configs
    # json.loads(mall.configs['config.json']),  # package config.json
    # json.loads(pathlib.Path(app_config_path).read_text()),  # package config.json
    #pkg_defaults,  # package defaults
]

dflt_config = mall.configs['config.json'] #ChainMap(*config_sources)  # a config mapping
dflt_stacks = mall.data['stacks_keywords.txt'].splitlines()
dflt_json_example = mall.configs['json_example.txt']

# a config getter, enhanced by the user_gettable store
get_config = config_getter_factory(
    sources=config_sources + 
    [user_gettable(mall.configs)]
)
