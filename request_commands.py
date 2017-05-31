import sublime, sublime_plugin

from .common import RequestCommandMixin
from .parsers import parse_tests


class RequesterCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute requests from requester file concurrently and open multiple
    response views.
    """
    def open_response_view(self, request, response, num_selections):
        """Create a response view and insert response content into it. Ensure that
        response tab comes after (to the right of) all other response tabs.

        Don't create new response tab if a response tab matching request is open.
        """
        window = self.view.window()
        requester_sheet = window.active_sheet()

        last_sheet = requester_sheet # find last sheet (tab) with a response view
        for sheet in window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                last_sheet = sheet
        window.focus_sheet(last_sheet)

        views = self.response_views_with_matching_selection(request)
        if not len(views): # if there are no matching response tabs, create a new one
            views = [window.new_file()]
        else: # move focus to matching view after response is returned if match occurred
            window.focus_view(views[0])

        for view in views:
            view.set_scratch(True)

            # this setting allows keymap to target response views separately
            view.settings().set('requester.response_view', True)
            view.settings().set('requester.env_string',
                                self.view.settings().get('requester.env_string', None))
            view.settings().set('requester.env_file',
                                self.view.settings().get('requester.env_file', None))

            content = self.get_response_content(request, response)
            view.run_command('requester_replace_view_text',
                             {'text': content.content, 'point': content.point})
            self.set_syntax(view, response)
            view.settings().set('requester.selection', request)

        # should response tabs be reordered after requests return?
        if self.config.get('reorder_tabs_after_requests', False):
            self.view.run_command('requester_reorder_response_tabs')

        # will focus change after request(s) return?
        if num_selections > 1:
            if not self.config.get('change_focus_after_requests', False):
                # keep focus on requests view if multiple requests are being executed
                window.focus_sheet(requester_sheet)
        else:
            if not self.config.get('change_focus_after_request', True):
                window.focus_sheet(requester_sheet)


class RequesterReplayRequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Replay a request from a response view.
    """
    def get_selections(self):
        """Returns only one selection, the one on the first line.
        """
        return [self.view.substr( self.view.line(0) )]

    def open_response_view(self, request, response, **kwargs):
        """Overwrites content in current view.
        """
        view = self.view

        content = self.get_response_content(request, response)
        view.run_command('requester_replace_view_text',
                             {'text': content.content, 'point': content.point})
        self.set_syntax(view, response)
        view.settings().set('requester.selection', request)

        self.set_response_view_name(view, response)


class RequesterTestsCommand(sublime_plugin.TextCommand):
    """Execute requests from requester file concurrently. For each request with a
    corresponding assertions dictionary, compare response with assertions and
    display all results in one tab.

    Doesn't work for multiple selections.
    """
    def run(self, edit):
        contents = self.view.substr( sublime.Region(0, self.view.size()) )
        print(parse_tests(contents))
