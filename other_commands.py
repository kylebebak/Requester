import sublime, sublime_plugin

import webbrowser
from sys import maxsize
from collections import namedtuple

from .common import RequestCommandMixin


class RequesterReplaceViewTextCommand(sublime_plugin.TextCommand):
    """`TextCommand` to replace all text in view, without highlighting text after.
    Optionally leave cursor at `point`.
    """
    def run(self, edit, text, point=None):
        self.view.erase(
            edit, sublime.Region(0, self.view.size())
        )
        self.view.insert(edit, 0, text)
        if point:
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(point))


class RequesterCloseResponseTabsCommand(sublime_plugin.WindowCommand):
    """`TextCommand` to replace all text in view, without highlighting text after.
    Optionally leave cursor at `point`.
    """
    def run(self):
        for sheet in self.window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                view.close()


class RequesterShowTutorialCommand(sublime_plugin.WindowCommand):
    """Show a modified, read-only version of README that can be used to see how
    Requester works.
    """
    def run(self):
        show_read_only_view(self.window.new_file(),
                            sublime.load_resource('Packages/Requester/docs/tutorial.md'),
                            'Requester Tutorial',
                            sublime.load_resource('Packages/Requester/docs/requester_env.py'),
                            25)


class RequesterShowDocumentationCommand(sublime_plugin.WindowCommand):
    """Show a modified, read-only version of README that can be used to see how
    Requester works.
    """
    def run(self):
        show_read_only_view(self.window.new_file(),
                            sublime.load_resource('Packages/Requester/README.md'),
                            'Requester Documentation',
                            sublime.load_resource('Packages/Requester/docs/requester_env.py'))


def show_read_only_view(view, content, name, env_content='', point=1):
    """Helper for creating read-only scratch view.
    """
    view.run_command('requester_replace_view_text', {'text': content, 'point': point})
    view.settings().set('requester.env_string', env_content)
    view.set_read_only(True)
    view.set_scratch(True)
    if not set_syntax(view, 'Packages/MarkdownEditing/Markdown.tmLanguage'):
        set_syntax(view, 'Packages/Markdown/Markdown.sublime-syntax')
    view.set_name('Requester Tutorial')


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
    """Show a modified, read-only version of README that can be used to see how
    Requester works.
    """
    def run(self):
        webbrowser.open_new_tab('http://docs.python-requests.org/en/master/user/quickstart/')


class RequesterReorderResponseTabsCommand(sublime_plugin.TextCommand):
    """Reads lines in current view one by one, then reorders response tabs to
    match order of requests read from current view. Doesn't work for requests
    defined over multiple lines.
    """
    def run(self, edit):
        window = self.view.window()
        # get all lines in current view, prepare them, and cache them
        lines = []
        timeout = sublime.load_settings('Requester.sublime-settings').get('timeout', None)
        for line in self.view.substr( sublime.Region(0, self.view.size()) ).splitlines():
            lines.append( RequestCommandMixin.prepare_selection(line, timeout) )
        lines = remove_duplicates(lines)

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
            selection = view.settings().get('requester.selection', None)
            if not selection:
                views.append(View(view, maxsize))
            try:
                line = lines.index(selection)
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
