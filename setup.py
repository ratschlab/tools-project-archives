from setuptools import setup

setup(
    author="Noah Fleischmann",
    author_email="noah.fleischmann@inf.ethz.ch",
    name="archiver",
    version=0.1,
    description="A CLI to handle the archiving of large project data.",
    url="https://github.com/ratschlab/tools-project-archives",
    packages=['archiver'],
    entry_points={
        "console_scripts": ['archiver = archiver.main:main']
    },
)
