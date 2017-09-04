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
    if 'filename' in req.skwargs or 'streamed' in req.skwargs or 'chunked' in req.skwargs:
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


class TestCore(unittest.TestCase):
    def setUp(self):
        global error_messages
        error_messages = []
        self.config = sublime.load_settings('')

    def tearDown(self):
        pass

    def test_successful_requests(self):
        c = RequestCommand([
            "get('127.0.0.1:8000/get')",
            "post('127.0.0.1:8000/post')",
            "patch('127.0.0.1:8000/patch')",
            "put('127.0.0.1:8000/put')",
            "delete('127.0.0.1:8000/delete')",
        ])
        c.MAX_WORKERS = 1
        c.run(None)

        activities = c.view._status.get('requester.activity')
        self.assertTrue([a for a in activities if 'Requester [' in a])
        self.assertEqual(activities[-1], '')

        self.assertEqual(len(c._responses), 5)
        self.assertEqual(error_messages, [])

        self.assertEqual(c._responses[0].req.url, 'http://127.0.0.1:8000/get')
        methods = [r.req.method for r in c._responses]
        self.assertEqual(methods, ['GET', 'POST', 'PATCH', 'PUT', 'DELETE'])
        codes = [r.res.status_code for r in c._responses]
        self.assertEqual(codes, [200] * 5)
        errors = [r.err for r in c._responses if r.err != '']
        self.assertEqual(errors, [])

    def test_errors(self):
        c = RequestCommand([
            "get('127.0.0.1:/get')",
            "get('127.0.0.1:8000/get', params=1)",
            "get('127.0.0.1:8000/get', params={'k': v})",
            "get('127.0.0.1:8000/get', timeout=0)",
            "get('127.0.0.1:8000/get', invalid_kwarg=0)",
            "get('127.0.0.1:8000/get', fmt='invalid_fmt')",
            "get('127.0.0.1:8000/get'",
            "s.get('127.0.0.1:8000/get')",
        ])
        c.MAX_WORKERS = 1
        c.run(None)

        errors = [r.err for r in c._responses]
        for error, start in zip(errors, ['Connection', 'Type', 'Other', 'Type', 'Session']):
            self.assertTrue(error.startswith(start))

        for error, contained in zip(error_messages, ['not defined', 'fmt', 'EOF', '']):
            self.assertIn(contained, error)

        self.assertEqual(error_messages[-1].count(' Error:'), 5)

    def test_env(self):
        c = RequestCommand([
            "get('127.0.0.1:8000/get', params={'k': v})",
            "post('127.0.0.1:8000/post', json={'k': w})",
        ], env={'v': 1, 'w': 2})
        c.MAX_WORKERS = 1
        c.run(None)

        r0, r1 = [r.res for r in c._responses]
        self.assertIn('k=1', r0.url)
        self.assertIn('post', r1.url)

if __name__ == '__main__':
    unittest.main()
