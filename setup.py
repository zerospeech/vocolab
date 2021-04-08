#!/usr/bin/env python
"""Setup script for the zerospeech back-end tools"""
import setuptools
import codecs


with codecs.open('requirements.txt', encoding='utf-8') as fp:
    requirements = fp.read()

# run setup with setup.cfg
setuptools.setup(
    install_requires=requirements
)
