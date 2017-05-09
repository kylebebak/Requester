import sublime, sublime_plugin

import webbrowser
from os.path import join, dirname
from shutil import copyfile


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
        tutorial_file = join(sublime.packages_path(), 'Requester/docs/_tutorial.md')
        tutorial_dir = dirname(tutorial_file)
        tutorial_copy = join(tutorial_dir, 'tutorial.md')

        copyfile(tutorial_file, tutorial_copy)

        view = self.window.open_file(tutorial_copy)
        view.set_read_only(True)


class RequesterShowSyntaxCommand(sublime_plugin.WindowCommand):
    """Show a modified, read-only version of README that can be used to see how
    Requester works.
    """
    def run(self):
        webbrowser.open_new_tab('http://docs.python-requests.org/en/master/user/quickstart/')
