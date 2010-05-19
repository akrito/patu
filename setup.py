from setuptools import setup
import os

try:
    long_desc = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()
except (IOError, OSError):
    long_desc = ''

setup(
    name = "patu",
    version = '0.1',
    url = 'http://github.com/akrito/patu',
    author = 'Alex Kritikos',
    author_email = 'alex@8bitb.us',
    description = 'Patu is a small spider',
    long_description = long_desc,
    scripts = ['scripts/patu'],
    install_requires = ['httplib2', 'lxml'],
    py_modules = ['patu'],
)
