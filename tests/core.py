# flake8: noqa
"""Usage: from repo root, run `python -m unittest tests/core.py -v`
"""
import sys
import unittest
from unittest.mock import MagicMock

sublime = MagicMock()
sys.modules['sublime'] = sublime

def load_settings(file):
    return {'timeout_env': 15}
sublime.load_settings = load_settings

from core import RequestCommandMixin, helpers, parsers, responses


class TestCore(unittest.TestCase):
    def test_core(self):
        pass

if __name__ == '__main__':
    unittest.main()
