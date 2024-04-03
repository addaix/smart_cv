"""
The smart_cv package provides functionality for creating and managing smart CVs (resumes).

This package contains modules for parsing and analyzing CV data, generating 
CV templates, and extracting information from CV documents.
"""

from smart_cv.base import CvsInfoStore, CvsFilesReader
from smart_cv.ResumeParser import ContentRetriever, TemplateFiller
