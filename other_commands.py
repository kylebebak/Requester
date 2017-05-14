import sublime, sublime_plugin

import webbrowser


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
