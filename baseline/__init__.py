"""
Library for creating macOS packages based on SecondSonConsulting's Baseline:
- https://github.com/SecondSonConsulting/Baseline

Usage:

    >>> import baseline

    >>> baseline_obj = baseline.BaselineBuilder(
    >>>                     configuration_file="ripeda.plist",
    >>>                     identifier="com.ripeda.baseline.engineering",
    >>>                     version="1.0.0",
    >>>                     output="RIPEDA Baseline.pkg")

    >>> baseline_obj.build()

    >>> baseline_obj.validate_pkg() # Optional
"""

__version__:      str = "1.7.1"
__author__:       str = "RIPEDA Consulting"
__author_email__: str = "info@ripeda.com"


from .core import BaselineBuilder