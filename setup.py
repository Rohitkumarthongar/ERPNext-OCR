# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import re, ast


# get version from __version__ variable in erpnext_ocr/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('erpnext_ocr/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

# Read requirements from requirements.txt
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
	name='erpnext_ocr',
	version=version,
	description='OCR',
	author='John Vincent Fiel',
	author_email='johnvincentfiel@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=requirements
)
