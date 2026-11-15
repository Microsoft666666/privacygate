"""Pluggable detectors; modules must not retain message text."""
from importlib import import_module
MODULES = ('phones', 'ids', 'secrets', 'address', 'national_id')

def find(text):
    return [finding for name in MODULES for finding in import_module('recognizers.' + name).find(text)]
