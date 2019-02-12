# flake8: noqa
"""Usage: from repo root, run `python3 -m unittest tests.core -v`

This test module makes sure that the `commands` packages is not imported
"""
import unittest
from unittest.mock import MagicMock

import os
import sys
import json
import tempfile
from collections import defaultdict, OrderedDict

sublime = MagicMock()
sys.modules['sublime'] = sublime


# patch class method before importing `RequestCommandMixin`
from Requester.core.responses import ResponseThreadPool

def handle_special(self, req):
    """Mock this on ResponseThreadPool so it doesn't touch anything in
    `commands` package.
    """
    if 'filename' in req.skwargs or 'streamed' in req.skwargs or 'chunked' in req.skwargs:
        return True
    return False
ResponseThreadPool.handle_special = handle_special

from Requester.core import RequestCommandMixin, persist_requests, helpers, parsers, responses


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

    def test_get_activity_indicator(self):
        self.assertEqual(RequestCommand.get_activity_indicator(0, 7), '[=       ]')
        self.assertEqual(RequestCommand.get_activity_indicator(7, 7), '[       =]')
        self.assertEqual(RequestCommand.get_activity_indicator(15, 7), '[ =      ]')

    def test_get_env_dict_from_string(self):
        env = RequestCommand.get_env_dict_from_string('a = 1\nb = 2')
        self.assertEqual(env['a'], 1)
        self.assertEqual(env['b'], 2)

    def test_parse_env_block(self):
        text = '###env\na=1\n###env\nb=2\n###env'
        block, _, _, _ = RequestCommand.parse_env(text)
        self.assertEqual(block, 'a=1')
        text = '###env\na=1\n'
        block, _, _, _ = RequestCommand.parse_env(text)
        self.assertEqual(block, None)

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
            "get('raisesconnectionerror.com')",
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

    def test_persist_requests(self):
        requests = [
            "requests.get('127.0.0.1:8000/get')",
            "requests.post('127.0.0.1:8000/post')",
            "requests.get('127.0.0.1:8000/get')",
        ]
        c = RequestCommand(requests)
        c.MAX_WORKERS = 1
        c.run(None)

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'history')
            persist_requests(c, c._responses, path)
            with open(path, 'r') as f:
                rh = json.loads(f.read() or '{}', object_pairs_hook=OrderedDict)
                self.assertEqual(len(rh), 2)
                self.assertEqual(list(reversed(requests[:2])), list(rh.keys()))


class TestHelpers(unittest.TestCase):
    def setUp(self):
        self.config = sublime.load_settings('')

    def tearDown(self):
        pass

    def test_truncate(self):
        s = helpers.truncate('hello there', 7, '…')
        self.assertEqual(s, 'hello t…')
        s = helpers.truncate('hello there', 20)
        self.assertEqual(s, 'hello there')

    def test_clean_url(self):
        url = helpers.clean_url('http://google.com/search/?q=stuff')
        self.assertEqual(url, 'http://google.com/search')

    def test_absolute_path(self):
        path = helpers.absolute_path('/absolute/path', View())
        self.assertEqual(path, '/absolute/path')
        path = helpers.absolute_path('relative/path', View())
        self.assertEqual(path, None)

    def test_get_transfer_indicator(self):
        s = helpers.get_transfer_indicator('f', 10, 100)
        self.assertEqual(s, 'f, [·····                                            ] 0kB')

    def test_prepend_scheme(self):
        url = helpers.prepend_scheme('google.com')
        self.assertEqual(url, 'http://google.com')
        url = helpers.prepend_scheme('https://wiki.com')
        self.assertEqual(url, 'https://wiki.com')


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.config = sublime.load_settings('')

    def tearDown(self):
        pass

    def test_parse_requests(self):
        selections = parsers.parse_requests("""
get(
  'https://jsonplaceholder.typicode.com/posts/', # )
  params={'c)': 'E', 'e': "this should work\nok, it's a string with more\nthan one line bro"
  },
  data={'c': 'three\nlines', 'd': 'e'}
)
""")
        self.assertEqual(selections[0], 'get(\n  \'https://jsonplaceholder.typicode.com/posts/\', # )\n  params={\'c)\': \'E\', \'e\': "this should work\nok, it\'s a string with more\nthan one line bro"\n  },\n  data={\'c\': \'three\nlines\', \'d\': \'e\'}\n)')

        with self.assertRaises(IndexError):
            selections = parsers.parse_requests("get(google.com")

    def test_parse_tests(self):
        tests = parsers.parse_tests("""# first request
get(base_url + '/posts')
assert {'status_code': 200, 'encoding': 'utf-8'}

# second request, with no assertion
get(base_url + '/profile')

# third request
get(base_url + '/comments')
assert {'status_code': 500}
""")
        self.assertEqual(len(tests), 2)
        self.assertEqual(tests[0].request, "get(base_url + '/posts')")
        self.assertEqual(tests[1].assertion, "assert {'status_code': 500}")


class TestResponses(unittest.TestCase):
    def setUp(self):
        self.config = sublime.load_settings('')

    def tearDown(self):
        pass

    def test_prepare_request(self):
        req = responses.prepare_request("get('https://google.com', auth=1)", {}, 0)
        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.kwargs['auth'], 1)
        req = responses.prepare_request("get('a.com', auth=1, explore=(\"get('a.com', auth=1)\", 'b.com'))", {}, 0)
        self.assertEqual(req.kwargs['timeout'], 15)
        self.assertEqual(req.kwargs.get('auth'), None)

    def test_prepend_library(self):
        request = responses.prepend_library("get('a.b') ")
        self.assertEqual(request, "requests.get('a.b')")


if __name__ == '__main__':
    unittest.main()
