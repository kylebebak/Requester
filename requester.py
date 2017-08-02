# flake8: noqa
import sys


if sys.version_info[0] == 2:
    raise ImportWarning("Requester does not support Sublime Text 2.")
else:
    from .commands import *
