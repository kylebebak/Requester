import sublime
import sublime_plugin

import webbrowser


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


NEW_REQUESTER_FILE = """# http://docs.python-requests.org/en/master/user/quickstart/

env_file = ''

###env

###env

"""


class RequesterNewRequesterFileCommand(sublime_plugin.TextCommand):
    """Create a new view with a skeleton for a requester file.
    """
    def run(self, edit):
        view = self.view.window().new_file()
        view.insert(edit, 0, NEW_REQUESTER_FILE)
        set_syntax(view, 'Packages/Python/Python.sublime-syntax')
