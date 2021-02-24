# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name="de_discord",
    version="1.0.0",
    package_dir={"": "python"},
    packages=find_packages(where="python"),
    description="Python tooling to support the Data Engineering Discord",
    author="Josh Holbrook",
    author_email="josh.holbrook@gmail.com",
    url="https://github.com/jfhbrook/de-discord",
    entry_points=dict(console_scripts=["de=de.cli:cli"]),
)
