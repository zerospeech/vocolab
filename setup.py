#!/usr/bin/env python
"""Setup script for the zerospeech back-end tools"""
import setuptools
import codecs

with codecs.open('requirements.txt', encoding='utf-8') as fp:
    requirements = fp.read()

# run setup with setup.cfg
setuptools.setup(
    install_requires=requirements,
    include_package_data=True,
    package_data={
        '': ["*.jinja2"],
        'zerospeech_admin': [
            'zerospeech/templates/emails/*.jinja2',
            'zerospeech/templates/mattermost/*.jinja2',
            'zerospeech/templates/pages/*.jinja2',
            'zerospeech/templates/config/*.service',
            'zerospeech/templates/config/*.socket',
            'zerospeech/templates/config/*.wsgi',
            'zerospeech/templates/config/*.conf',
        ],
    },
)
