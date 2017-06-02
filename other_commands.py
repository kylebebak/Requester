import sublime, sublime_plugin

import webbrowser
from sys import maxsize
from collections import namedtuple

from .core import prepare_request
from .parsers import parse_requests


class RequesterReplaceViewTextCommand(sublime_plugin.TextCommand):
    """`TextCommand` to replace all text in view, without selecting text after.
    Optionally leave cursor at `point`.
    """
    def run(self, edit, text, point=None):
        self.view.erase(
            edit, sublime.Region(0, self.view.size())
        )
        self.view.insert(edit, 0, text)
        if point is not None:
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(point))


class RequesterCloseResponseTabsCommand(sublime_plugin.WindowCommand):
    """Iterate over all open tabs and close response tabs.
    """
    def run(self):
        for sheet in self.window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                view.close()


class RequesterShowTutorialCommand(sublime_plugin.WindowCommand):
    """Show a smaller, read-only version of README that can be used to see how
    Requester works.
    """
    def run(self):
        show_read_only_doc_view(self.window.new_file(),
                                sublime.load_resource('Packages/Requester/docs/tutorial.md'),
                                'Requester Tutorial')


class RequesterShowDocumentationCommand(sublime_plugin.WindowCommand):
    """Show read-only version of README.
    """
    def run(self):
        show_read_only_doc_view(self.window.new_file(),
                                sublime.load_resource('Packages/Requester/README.md'),
                                'Requester Documentation')


def show_read_only_doc_view(view, content, name, point=0):
    """Helper for creating read-only scratch view.
    """
    view.run_command('requester_replace_view_text', {'text': content, 'point': point})
    view.set_read_only(True)
    view.set_scratch(True)
    if not set_syntax(view, 'Packages/MarkdownEditing/Markdown.tmLanguage'):
        set_syntax(view, 'Packages/Markdown/Markdown.sublime-syntax')
    view.set_name(name)


def set_syntax(view, syntax):
    """Attempts to set syntax for view without showing error popup.
    """
    try:
        sublime.load_resource(syntax)
    except:
        return False
    else:
        view.set_syntax_file(syntax)
        return True


class RequesterShowSyntaxCommand(sublime_plugin.WindowCommand):
    """Open requests quickstart in web browser.
    """
    def run(self):
        webbrowser.open_new_tab('http://docs.python-requests.org/en/master/user/quickstart/')


class RequesterReorderResponseTabsCommand(sublime_plugin.TextCommand):
    """Reorders open response tabs to match order of requests in current view.
    """
    def run(self, edit):
        window = self.view.window()
        # parse all requests in current view, prepare them, and cache them
        requests = []
        timeout = sublime.load_settings('Requester.sublime-settings').get('timeout', None)
        for request in parse_requests(
            self.view.substr( sublime.Region(0, self.view.size()) )
        ):
            requests.append(prepare_request(request, timeout))
        requests = remove_duplicates(requests)

        # cache all response views in current window
        response_views = []
        for sheet in window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                response_views.append(view)

        View = namedtuple('View', 'view, line')
        views = []
        # add `line` property to cached response views, indicating at which line they appear in current view
        for view in response_views:
            request = view.settings().get('requester.request', None)
            if not request:
                views.append(View(view, maxsize))
            try:
                line = requests.index(request)
            except ValueError:
                views.append(View(view, maxsize))
            else:
                views.append(View(view, line))

        if not len(views):
            return

        # get largest index among open tabs
        group, index = 0, 0
        for sheet in window.sheets():
            view = sheet.view()
            group, index = window.get_view_index(view)

        # sort response views by line property, and reorder response tabs
        views.sort(key=lambda view: view.line)
        # requester tab, then response tabs are moved sequentially to largest index
        window.set_view_index(self.view, group, index)
        for v in views:
            window.set_view_index(v.view, group, index)


def remove_duplicates(seq):
    """Removes duplicates from sequence. Preserves order of sequence.
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
