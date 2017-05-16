import sublime
import sys

from unittesting import DeferrableTestCase


common = sys.modules['Requester.common']

class TestFunctions(DeferrableTestCase):

    def test_prepare_selection(self):
        s = "get('http://httpbin.org/get')"
        s_prepared = common.RequestCommandMixin.prepare_selection(s, 30)
        self.assertEqual(s_prepared, "requests.get('http://httpbin.org/get', timeout=30)")


def select_line_beginnings(view, lines, clear=True):
    if not hasattr(lines, '__iter__'):
        lines = [lines]
    if clear:
        view.sel().clear()
    for line in lines:
        view.sel().add(sublime.Region( view.text_point(line-1, 0) ))


def get_line(view, line):
        return view.substr(view.line( view.text_point(line-1, 0) ))


class TestRequester(DeferrableTestCase):

    WAIT_MS = 2000

    def setUp(self):
        self.config = sublime.load_settings('Requester.sublime-settings')

        content = sublime.load_resource('Packages/Requester/tests/requester.py')
        self.window = sublime.active_window()
        self.view = self.window.new_file()
        self.view.set_name('Requester Tests')
        self.view.run_command('requester_replace_view_text', {'text': content})
        self.view.set_scratch(True)

    def tearDown(self):
        if self.view:
            self.window.focus_view(self.view)
            self.window.run_command('close_file')
        self.window.run_command('requester_close_response_tabs')

    def test_request(self):
        select_line_beginnings(self.view, 11)
        self.view.run_command('requester')
        yield self.WAIT_MS # wait ms for responses to return
        self.assertEqual(
            get_line(self.window.active_view(), 5),
            'http://httpbin.org/get?key1=value1&key2=value2'
        )
