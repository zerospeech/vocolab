#!/usr/bin/env python
"""Setup script for the zerospeech back-end tools"""
import setuptools
import codecs
from pathlib import Path
from datetime import datetime

with codecs.open('requirements.txt', encoding='utf-8') as fp:
    requirements = fp.read()

with (Path.home() / '.voco-installation').open('w') as fp:
    fp.write(datetime.now().isoformat())

# run setup with setup.cfg
setuptools.setup(
    install_requires=requirements,
    # include_package_data=True,
    package_data={
        '': ['*.jinja2', '*.service', '*.socket', '*.wsgi', '*.conf', '*.env', '*.config']
    },
)
