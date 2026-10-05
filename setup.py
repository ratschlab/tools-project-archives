#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as f:
    requirements = list(f.readlines())

setup(
    author="Noah Fleischmann",
    author_email="noah.fleischmann@inf.ethz.ch",
    maintainer="Andre Kahles",
    maintainer_email='andre.kahles@inf.ethz.ch',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="A CLI tool to handle the archiving of large project data.",
    entry_points={
        "console_scripts": ['archiver = archiver.main:main']
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords=['archiving', 'data lifecycle', 'research'],
    name='project-archiver',
    packages=['archiver'],
    url="https://github.com/ratschlab/tools-project-archives",
    version='0.6.2',
    zip_safe=False,
)
