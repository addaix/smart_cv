"""Base objects for the smart_cv package."""

from dol import Files, add_ipython_key_completions, wrap_kvs
from raglab.retrieval.lib_alexis import (
    extension_based_wrap,
    get_config as config_getter_factory,
)

from smart_cv.util import pkg_defaults, app_filepath, app_config_path, data_dir

import json
import pathlib
from i2 import AttributeMutableMapping
from functools import partial
from dol import Files

# from config2py import (
#     user_gettable,
#     get_config as config_getter_factory,
# )


@add_ipython_key_completions
@wrap_kvs(obj_of_data=json.loads)  # TODO add reading function for Docx files
class CvsInfoStore(Files):
    """Get cv info dicts from folder"""

    def __init__(self, rootdir, *args, **kwargs):
        super().__init__(rootdir, *args, **kwargs)


mall = AttributeMutableMapping(
    data=extension_based_wrap(Files(app_filepath("data"))),
    stack_mining=extension_based_wrap(Files(app_filepath("data", "stacks_mining"))),
    cvs=extension_based_wrap(Files(app_filepath("data", "cvs"))),
    cvs_info=CvsInfoStore(app_filepath("data", "cvs_info")),
    filled=extension_based_wrap(Files(app_filepath("data", "filled"))),
    configs=extension_based_wrap(Files(app_filepath("configs"))),
    pkg_data_store=Files(data_dir),
)

# -----------------------------------------------------------
# Populate what's missing in local user space
from smart_cv.util import pkg_data_files


# def copy_if_missing(key, dest_store, src_files_obj=pkg_data_files):
#     if key not in dest_store:
#         dest_store[key] = (src_files_obj / key).read_bytes()


default_store = Files(str(pkg_defaults))


def populate_local_user_folders(defaults, local_user_folders):
    for k in defaults:
        if k not in local_user_folders:
            try:
                local_user_folders[k] = defaults[k].read_bytes()
            except Exception:
                print(f"Could not read default for {k}, skipping...")
    return defaults


populate_local_user_folders(default_store, mall.configs)

# copy_if_missing('config.json', mall.configs)
# copy_if_missing('stacks_keywords.txt', mall.config)
# copy_if_missing('json_example.txt', mall.configs)

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
    mall.configs.rootdir,  # user local configs
    # json.loads(mall.configs['config.json']),  # package config.json
    # json.loads(pathlib.Path(app_config_path).read_text()),  # package config.json
    # pkg_defaults,  # package defaults
]

# TODO: Recover (the commented out lines below isn't working)
# dflt_config = mall.configs.get("config.json", {})  # or? ChainMap(*config_sources)  # a config mapping
dflt_config = {}
# dflt_stacks = mall.configs["stacks_keywords.txt"].splitlines()
dflt_stacks = []

# dflt_json_example = mall.configs["json_example.txt"]
dflt_json_example = {}

# a config getter, enhanced by the user_gettable store
get_config = partial(config_getter_factory, sources=[mall.configs])
