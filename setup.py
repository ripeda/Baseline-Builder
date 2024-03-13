"""
setup.py: Setup script for library.

Usage:
    python3 -m build --wheel
"""

from setuptools import setup, find_packages


def fetch_property(property: str) -> str:
    for line in open("baseline/__init__.py", "r").readlines():
        if not line.startswith(property):
            continue
        return line.split("=")[1].strip().strip('"')
    raise ValueError(f"Property {property} not found.")


setup(
    name='baseline-builder',
    version=fetch_property("__version__:"),
    author=fetch_property("__author__:"),
    author_email=fetch_property("__author_email__:"),
    license='',
    description='Module for generating Baseline packages for deployment',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ripeda/Baseline-Builder',
    python_requires='>=3.6',
    packages=find_packages(include=["baseline"]),
    package_data={
        "baseline": ["*"],
    },
    entry_points={
        "console_scripts": [
            "baseline = baseline.core:main",
        ],
    },
    py_modules=["baseline"],
    include_package_data=True,
    install_requires=open("requirements.txt", "r").readlines(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
    ],
)