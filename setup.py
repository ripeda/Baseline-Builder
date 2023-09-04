from setuptools import setup

setup(
    name='baseline-builder',
    version='1.0.3',
    author='RIPEDA',
    author_email='mykola@ripeda.com',
    license='',
    description='Module for generating Baseline packages for deployment',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ripeda/Baseline-Builder',
    python_requires='>=3.6',
    py_modules=["baseline"],
    install_requires=[
        'macos-pkg-builder',
    ],
)