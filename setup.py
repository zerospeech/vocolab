#!/usr/bin/env python
"""Setup script for the zerospeech back-end tools"""
import setuptools
import codecs

with codecs.open('requirements.txt', encoding='utf-8') as fp:
    requirements = fp.read()

with codecs.open('README.md', encoding='utf-8') as fp:
    readme = fp.read()

# todo: add namespace for evaluation scripts (?)

setuptools.setup(
    name='zerospeech',
    description="Back-end for the Zerospeech Challenge",
    long_description=readme,
    packages=setuptools.find_packages(where='.'),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'zr=zerospeech.admin.cli.main:run_cli',
        ]
    },
    author='Nicolas Hamilakis, CoML team ENS/Inria Paris',
    author_email='contanct@zerospeech.com',
    license='GPL3',
    url='https://zerospeech.com/',
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
)
