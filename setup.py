from setuptools import setup

def fetch_property(property: str) -> str:
    for line in open("baseline.py", "r").readlines():
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
    py_modules=["baseline"],
    install_requires=open("requirements.txt", "r").readlines(),
)