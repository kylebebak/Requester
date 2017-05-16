import sublime

import sys
from os import path

from unittesting import DeferrableTestCase


####################
# TESTS FOR FUNCTIONS
####################

common = sys.modules['Requester.common']

class TestFunctions(DeferrableTestCase):

    def test_prepare_selection(self):
        s = "get('http://httpbin.org/get')"
        s_prepared = common.RequestCommandMixin.prepare_selection(s, 30)
        self.assertEqual(s_prepared, "requests.get('http://httpbin.org/get', timeout=30)")


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

class TestRequester(DeferrableTestCase):

    WAIT_MS = 2500 # wait in ms for responses to return

    def setUp(self):
        self.config = sublime.load_settings('Requester.sublime-settings')

        self.window = sublime.active_window()
        self.view = self.get_scratch_view_from_resource('Packages/Requester/tests/requester.py')

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

    def _test_url_and_name_in_view(self, view, url, name):
        self.assertEqual(
            get_line(view, 5),
            url
        )
        self.assertEqual(view.name(), name)

    def test_single_request(self):
        """Vanilla.
        """
        select_line_beginnings(self.view, 5)
        self.view.run_command('requester')
        yield self.WAIT_MS
        self._test_url_and_name_in_view(
            self.window.active_view(), 'https://jsonplaceholder.typicode.com/albums', 'POST: /albums')

    def test_single_request_no_prefix(self):
        """Without `requests.` prefix.
        """
        select_line_beginnings(self.view, 6)
        self.view.run_command('requester')
        yield self.WAIT_MS # this use of yield CAN'T be moved into a helper, it needs to be part of a test method
        self._test_url_and_name_in_view(
            self.window.active_view(), 'https://jsonplaceholder.typicode.com/posts', 'GET: /posts')

    def test_single_request_with_env_block(self):
        """From env block.
        """
        select_line_beginnings(self.view, 8)
        self.view.run_command('requester')
        yield self.WAIT_MS
        self._test_url_and_name_in_view(
            self.window.active_view(), 'http://httpbin.org/get?key1=value1', 'GET: /get')

    def test_single_request_with_env_file(self):
        """From env file.
        """
        view = self.window.open_file(
            path.join(sublime.packages_path(), 'Requester', 'tests', 'requester_env_file.py')
        )
        select_line_beginnings(view, 3)
        view.run_command('requester')
        yield self.WAIT_MS
        self._test_url_and_name_in_view(
            self.window.active_view(), 'http://httpbin.org/get', 'GET: /get')
        self.close_view(view)
