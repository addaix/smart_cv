"""Utils for smart_cv"""

from importlib.resources import files

pkg_name = "smart_cv"

proj_files = files(pkg_name)
data_files = proj_files / "data"
cvs_files = data_files / "cvs"
cvs_info_files = data_files / "cvs_info"

cvs_dirpath = str(cvs_files)
cvs_info_dirpath = str(cvs_info_files)
