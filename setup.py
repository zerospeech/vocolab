#!/usr/bin/env python
"""Setup script for the zerospeech back-end tools"""
import setuptools
import codecs

with codecs.open('requirements.txt', encoding='utf-8') as fp:
    requirements = fp.read()

# todo: add namespace for evaluation scripts
# todo: add console-script for admin utilities

setuptools.setup(
    name='zerospeech',
    description="Back-end for the Zerospeech Challenge",
    packages=setuptools.find_packages(where='.'),
    author='CoML team',
    author_email='contanct@zerospeech.com',
    license='GPL3',
    url='https://zerospeech.com/',
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
)
