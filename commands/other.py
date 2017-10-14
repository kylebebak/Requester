import sublime
import sublime_plugin

import webbrowser


class RequesterReplaceTextCommand(sublime_plugin.TextCommand):
    """`TextCommand` to replace region from start index to end index with `text`.
    """
    def run(self, edit, text, start_index, end_index):
        self.view.replace(edit, sublime.Region(start_index, end_index), text)


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
        show_read_only_doc_view(
            self.window.new_file(),
            sublime.load_resource('Packages/Requester/docs/tutorial.pyr'),
            'Requester Tutorial.pyr',
            syntax='Packages/Requester/syntax/requester-source.sublime-syntax'
        )


class RequesterShowDocumentationCommand(sublime_plugin.WindowCommand):
    """Show read-only version of README.
    """
    def run(self, online=False):
        if online:
            webbrowser.open_new_tab('http://requester.org')
            return
        show_read_only_doc_view(self.window.new_file(),
                                sublime.load_resource('Packages/Requester/docs/_content/body.md'),
                                'Requester Documentation')


def show_read_only_doc_view(view, content, name, point=0, syntax=''):
    """Helper for creating read-only scratch view.
    """
    view.run_command('requester_replace_view_text', {'text': content, 'point': point})
    view.set_read_only(True)
    view.set_scratch(True)
    if not syntax:
        if not set_syntax(view, 'Packages/MarkdownEditing/Markdown.tmLanguage'):
            set_syntax(view, 'Packages/Markdown/Markdown.sublime-syntax')
    else:
        set_syntax(view, syntax)
    view.set_name(name)


def set_syntax(view, syntax):
    """Attempts to set syntax for view without showing error pop-up.
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

NEW_REQUESTER_FILE_NAVIGATION = NEW_REQUESTER_FILE + """
## group 1
get('httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

post('httpbin.org/post', json={'key1': 'value1', 'key2': 'value2'})


## group 2
put('httpbin.org/put', json={'key1': 'value1', 'key2': 'value2'})

delete('httpbin.org/delete')

"""


class RequesterNewRequesterFileCommand(sublime_plugin.TextCommand):
    """Create a new view with a skeleton for a requester file.
    """
    def run(self, edit, demo=False):
        view = self.view.window().new_file()
        if demo:
            view.insert(edit, 0, NEW_REQUESTER_FILE_NAVIGATION)
        else:
            view.insert(edit, 0, NEW_REQUESTER_FILE)
        set_syntax(view, 'Packages/Python/Python.sublime-syntax')
        view.set_name('untitled.pyr')
        view.set_syntax_file('Packages/Requester/syntax/requester-source.sublime-syntax')
