# flake8: noqa
"""Usage: from repo root, run `python -m unittest tests.core -v`

This test module makes sure that the `commands` packages is not imported
"""
import sys
import unittest
from unittest.mock import MagicMock
from collections import defaultdict

sublime = MagicMock()
sys.modules['sublime'] = sublime


# patch class method before importing `RequestCommandMixin`
from core.responses import ResponseThreadPool

def handle_special(self, req):
    """Mock this on ResponseThreadPool so that it doesn't touch anything in
    `commands` package.
    """
    if req.skwargs.get('filename') or req.skwargs.get('streamed') or req.skwargs.get('chunked'):
        return True
    return False
ResponseThreadPool.handle_special = handle_special

from core import RequestCommandMixin, helpers, parsers


# mock `sublime` module
def load_settings(*args, **kwargs):
    return {
        'timeout': 15, 'timeout_env': 15, 'allow_redirects': True,
        'scheme': 'http', 'fmt': 'indent_sort', 'max_content_length_kb': 5000,
        'change_focus_after_request': True, 'reorder_tabs_after_requests': False,
        'pin_tabs_by_default': False, 'history_file': 'Requester.history.json',
        'history_max_entries': 250, 'chunk_size': 1024, 'only_download_for_200': True
    }

error_messages = []
def error_message(msg):
    """Error messages for a given test run are logged here.
    """
    global error_messages
    error_messages.append(msg)
    print(msg)

def set_timeout(f, *args, **kwargs):
    f()

def set_timeout_async(f, *args, **kwargs):
    f()

def Region(*args, **kwargs):
    return None

def packages_path():
    return None

sublime.load_settings = load_settings
sublime.error_message = error_message
sublime.set_timeout = set_timeout
sublime.set_timeout_async = set_timeout_async
sublime.Region = Region
sublime.packages_path = packages_path


# mock `view`, which is an instance property referenced by `RequestCommandMixin`
class CustomDict(dict):
    def set(self, k, v):
        self.__setitem__(k, v)

class View:
    def __init__(self):
        self._settings = CustomDict()
        self._status = defaultdict(list)

    def set_status(self, k, v):
        """Accumulate all strings written to status so they can inspected later.
        """
        self._status[k].append(v)

    def substr(self, region):
        return ''

    def settings(self):
        return self._settings

    def size(self):
        return 0

    def file_name(self):
        return ''


class RequestCommand(RequestCommandMixin):
    """A class inheriting from `RequestCommandMixin`, designed so that env is
    configurable and responses and errors are inspectable.
    """
    def __init__(self, requests=None, env=None, env_string=''):
        self.view = View()
        self._requests = requests or []
        self._env = env or {}
        self._env_string = env_string

    def get_requests(self):
        """Requests strings are set in constructor, not by reading from file.
        Integration tests handle this.
        """
        return self._requests

    def get_env(self):
        """Env is set in constructor, not by reading from file. Integration tests
        handle this.
        """
        return self._env, self._env_string

    def persist_requests(self, responses):
        """Persist them so they can be inspected later.
        """
        self._persisted = responses

    def handle_responses(self, responses):
        """Persist them so they can be inspected later.
        """
        self._responses = responses

    def handle_errors(self, responses):
        """Persist them so they can be inspected later.
        """
        self._errors = responses


class TestCore(unittest.TestCase):
    def setUp(self):
        global error_messages
        error_messages = []
        self.config = sublime.load_settings('')

    def tearDown(self):
        pass

    def test_single_request(self):
        c = RequestCommand(["get('http://127.0.0.1:8000/get')", "get('http://127.0.0.1:8000/get' params=1)"])
        c.run(None)
        print(error_messages)
        print(c._responses)
        print(c.view._status)


if __name__ == '__main__':
    unittest.main()
