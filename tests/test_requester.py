import sublime

import sys
from os import path

from unittesting import DeferrableTestCase


####################
# TESTS FOR FUNCTIONS
####################

common = sys.modules['Requester.common']


class TestFunctions(DeferrableTestCase):

    def test_prepare_request(self):
        s = "get('http://httpbin.org/get')"
        s_prepared = common.prepare_request(s, 15)
        self.assertEqual(s_prepared, "requests.get('http://httpbin.org/get', timeout=15)")

    def test_prepare_request_with_prefix(self):
        s = "_s.get('http://httpbin.org/get')"
        s_prepared = common.prepare_request(s, 15)
        self.assertEqual(s_prepared, "_s.get('http://httpbin.org/get', timeout=15)")


####################
# HELPER FUNCTIONS
####################

def select_line_beginnings(view, lines, clear=True):
    if not hasattr(lines, '__iter__'):
        lines = [lines]
    if clear:
        view.sel().clear()
    for line in lines:
        view.sel().add(sublime.Region( view.text_point(line-1, 0) ))


def get_line(view, line):
        return view.substr(view.line( view.text_point(line-1, 0) ))


####################
# TESTS FOR COMMANDS
####################

class TestRequesterMixin:

    WAIT_MS = 2000 # wait in ms for responses to return

    def setUp(self):
        self.config = sublime.load_settings('Requester.sublime-settings')

        self.window = sublime.active_window()
        self.view = self.get_scratch_view_from_resource(self.REQUESTER_FILE)

    def tearDown(self):
        if self.view:
            self.close_view(self.view)
        self.window.run_command('requester_close_response_tabs')

    def close_view(self, view):
        self.window.focus_view(view)
        self.window.run_command('close_file')

    def get_scratch_view_from_resource(self, resource):
        content = sublime.load_resource(resource)
        view = self.window.new_file()
        view.set_name('Requester Tests')
        view.run_command('requester_replace_view_text', {'text': content})
        view.set_scratch(True)
        return view

    def _test_url_in_view(self, view, url):
        self.assertEqual(
            get_line(view, 5),
            url
        )

    def _test_name_in_view(self, view, name):
        self.assertEqual(view.name(), name)

    def _test_string_in_view(self, view, string):
        content = view.substr( sublime.Region(0, view.size()) )
        self.assertTrue(string in content)


class TestRequester(TestRequesterMixin, DeferrableTestCase):

    REQUESTER_FILE = 'Packages/Requester/tests/requester.py'

    def test_single_request(self):
        """Generic.
        """
        select_line_beginnings(self.view, 5)
        self.view.run_command('requester')
        yield self.WAIT_MS # this use of yield CAN'T be moved into a helper, it needs to be part of a test method
        self._test_url_in_view(self.window.active_view(), 'https://jsonplaceholder.typicode.com/albums')
        self._test_name_in_view(self.window.active_view(), 'POST: /albums')

    def test_single_request_no_prefix(self):
        """Without `requests.` prefix.
        """
        select_line_beginnings(self.view, 6)
        self.view.run_command('requester')
        yield self.WAIT_MS
        self._test_url_in_view(self.window.active_view(), 'https://jsonplaceholder.typicode.com/posts')
        self._test_name_in_view(self.window.active_view(), 'GET: /posts')

    def test_single_request_with_env_block(self):
        """From env block.
        """
        select_line_beginnings(self.view, 8)
        self.view.run_command('requester')
        yield self.WAIT_MS
        self._test_url_in_view(self.window.active_view(), 'http://httpbin.org/get?key1=value1')
        self._test_name_in_view(self.window.active_view(), 'GET: /get')

    def test_single_request_with_env_file(self):
        """From env file.
        """
        view = self.window.open_file(
            path.join(sublime.packages_path(), 'Requester', 'tests', 'requester_env_file.py')
        )
        yield 1000 # not waiting here causes a strange bug to happen
        select_line_beginnings(view, 3)
        view.run_command('requester')
        yield self.WAIT_MS
        view.close()
        self._test_url_in_view(self.window.active_view(), 'http://httpbin.org/get')
        self._test_name_in_view(self.window.active_view(), 'GET: /get')

    def test_single_request_focus_change(self):
        """Test that re-executing request in requester file doesn't open response
        tab, but rather reuses already open response tab.
        """
        select_line_beginnings(self.view, 5)
        self.view.run_command('requester')
        yield self.WAIT_MS
        group, index = self.window.get_view_index(self.window.active_view())
        self.window.focus_view(self.view)
        yield 1000
        select_line_beginnings(self.view, 5)
        self.view.run_command('requester')
        yield self.WAIT_MS
        new_group, new_index = self.window.get_view_index(self.window.active_view())
        self.assertEqual(group, new_group)
        self.assertEqual(index, new_index)



class TestRequesterMultiple(TestRequesterMixin, DeferrableTestCase):

    REQUESTER_FILE = 'Packages/Requester/tests/requester.py'

    def test_multiple_requests(self):
        """Tests the following:
            - Blank lines are skipped in requester file
            - 3 response tabs are opened when 3 requests are executed
            - Focus doesn't change to any response tab after it appears
            - Reordering response tabs works correctly
        """
        select_line_beginnings(self.view, [5,6,7,8])
        self.view.run_command('requester')
        yield self.WAIT_MS
        self.assertEqual(self.window.active_view(), self.view)

        self.view.run_command('requester_reorder_response_tabs')
        yield 1000
        self.assertEqual(self.window.active_view(), self.view)

        group, index = self.window.get_view_index(self.view)
        for i, name in enumerate(['POST: /albums', 'GET: /posts', 'GET: /get']):
            self.window.run_command('select_by_index', {'index': index + i + 1})
            yield 1000
            self._test_name_in_view(self.window.active_view(), name)


class TestRequesterSession(TestRequesterMixin, DeferrableTestCase):

    REQUESTER_FILE = 'Packages/Requester/tests/requester_session.py'
    WAIT_MS = 3000

    def test_session(self):
        """Using session.
        """
        select_line_beginnings(self.view, 9)
        self.view.run_command('requester')
        yield self.WAIT_MS
        self._test_url_in_view(self.window.active_view(), 'http://httpbin.org/cookies/set?k1=v1')
        self._test_name_in_view(self.window.active_view(), 'GET: /cookies/set')
        self._test_string_in_view(self.window.active_view(), "'X-Test': 'true'") # header added to session
        self._test_string_in_view(self.window.active_view(), "'Cookie': 'k0=v0'") # cookies added to session
        self._test_string_in_view(self.window.active_view(), "Response Cookies: {'k1': 'v1'}")
