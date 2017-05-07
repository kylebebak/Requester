import sublime, sublime_plugin


class HttpRequestsReplaceViewTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text, point=None):
        self.view.erase(
            edit, sublime.Region(0, self.view.size())
        )
        self.view.insert(edit, 0, text)
        if point:
            self.view.show_at_center(point)
