"""Utils for smart_cv"""

from importlib.resources import files
from functools import partial
from i2 import AttributeMutableMapping
from config2py import (
    get_app_data_folder,
    process_path,
)

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
app_filepath = partial(process_path, ensure_dir_exists=True, rootdir=app_dir)
data_dir = app_filepath("data")
configs_dir = app_filepath("configs")
dt_template_dir = configs_dir + "/DT_Template.docx"
app_config_path = configs_dir + "/config.json"
filled_dir = app_filepath("data/filled")


# def copy_if_missing(src, dest):
#     if not os.path.isfile(dest):
#         with open(dest, 'w') as f:
#             with open(src) as f2:
#                 f.write(f2.read())


# -----------------------------------------------------------


# --------------------------  Missed content analysis  --------------------------------

# TODO
