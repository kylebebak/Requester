# flake8: noqa
import sys

from .add_path import add_path


if sys.version_info[0] == 2:
    raise ImportWarning("Requester does not support Sublime Text 2.")
else:
    with add_path(__file__, '..', 'deps'):
        from .commands import *
