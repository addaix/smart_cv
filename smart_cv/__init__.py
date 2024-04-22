"""
The smart_cv package provides functionality for creating and managing smart CVs (resumes).

This package contains modules for parsing and analyzing CV data, generating 
CV templates, and extracting information from CV documents.
"""

from smart_cv.base import mall, CvsInfoStore, get_config
from smart_cv.interface import cv_content, fill_template, cv_text, _mk_parser, dag_pipeline
from smart_cv.resume_parser import ContentRetriever, TemplateFiller
