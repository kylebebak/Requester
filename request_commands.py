import sublime, sublime_plugin

from .core import RequestCommandMixin
from .common import set_response_view_syntax, get_response_view_content, prepare_request
from .parsers import parse_requests, parse_tests


class RequesterCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute requests from requester file concurrently and open multiple
    response views.
    """
    def run(self, edit, concurrency=10):
        """Allow user to specify concurrency.
        """
        self.MAX_WORKERS = max(1, concurrency)
        super().run(edit)

    def get_requests(self):
        """Parses requests from multiple selections. If nothing is highlighted,
        cursor's current line is taken as selection.
        """
        view = self.view
        requests = []
        for region in view.sel():
            if not region.empty():
                selection = view.substr(region)
            else:
                selection = view.substr(view.line(region))
            try:
                requests_ = parse_requests(selection)
            except:
                sublime.error_message('Parse Error: unbalanced parentheses in calls to requests')
            else:
                for r in requests_:
                    requests.append(r)
        timeout = self.config.get('timeout', None)
        requests = [prepare_request(r, timeout) for r in requests]
        return requests

    def handle_response(self, response, num_requests):
        """Create a response view and insert response content into it. Ensure that
        response tab comes after (to the right of) all other response tabs.

        Don't create new response tab if a response tab matching request is open.
        """
        if response.error: # ignore responses with errors
            return

        window = self.view.window(); r = response
        requester_sheet = window.active_sheet()

        last_sheet = requester_sheet # find last sheet (tab) with a response view
        for sheet in window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                last_sheet = sheet
        window.focus_sheet(last_sheet)

        views = self.response_views_with_matching_request(r.request)
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

            content = get_response_view_content(r.request, r.response)
            view.run_command('requester_replace_view_text',
                             {'text': content.content, 'point': content.point})
            set_response_view_syntax(self.config, view)
            view.settings().set('requester.request', r.request)

        # should response tabs be reordered after requests return?
        if self.config.get('reorder_tabs_after_requests', False):
            self.view.run_command('requester_reorder_response_tabs')

        # will focus change after request(s) return?
        if num_requests > 1:
            if not self.config.get('change_focus_after_requests', False):
                # keep focus on requests view if multiple requests are being executed
                window.focus_sheet(requester_sheet)
        else:
            if not self.config.get('change_focus_after_request', True):
                window.focus_sheet(requester_sheet)


class RequesterReplayRequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Replay a request from a response view.
    """
    def get_requests(self):
        """Parses requests from first line only.
        """
        return [self.view.substr( self.view.line(0) )]

    def handle_response(self, response, **kwargs):
        """Overwrites content in current view.
        """
        if response.error: # ignore responses with errors
            return

        view = self.view; r = response

        content = get_response_view_content(r.request, r.response)
        view.run_command('requester_replace_view_text',
                             {'text': content.content, 'point': content.point})
        set_response_view_syntax(self.config, view)
        view.settings().set('requester.request', r.request)

        self.set_response_view_name(view, r.response)


class RequesterTestsCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute requests from requester file concurrently. For each request with a
    corresponding assertions dictionary, compare response with assertions and
    display all results in one tab.

    Doesn't work for multiple selections.
    """
    def run(self, edit, concurrency=10):
        """Allow user to specify concurrency.
        """
        self.MAX_WORKERS = max(1, concurrency)
        super().run(edit)

    def get_requests(self):
        """Parses only first highlighted selection.
        """
        view = self.view
        self._tests = []

        for region in view.sel():
            if not region.empty():
                selection = view.substr(region)
            try:
                self._tests = parse_tests(selection)
            except:
                sublime.error_message('Parse Error: unbalanced brackets in tests')
            break # only parse first selection

        timeout = self.config.get('timeout', None)
        requests = []

        for test in self._tests:
            r = prepare_request(test.request, timeout)
            requests.append(r)

        return requests

    def handle_responses(self, responses):
        """Compares response objects with assertions dictionaries and displays a
        test run view that includes all discrepancies.
        """
        assert len(self._tests) == len(responses)
        errors = []
        test_results = []
        for i, response in enumerate(responses):
            try:
                assertion = self.eval_assertion(self._tests[i].assertion)
            except Exception as e:
                errors.append( '{}: {}'.format('Assertion Error', e) )
            else:
                test_results.append(self.get_single_test_results(response, assertion))

        if errors:
            sublime.error_message('\n\n'.join(errors))
        print('\n\n'.join(test_results))

    def eval_assertion(self, s):
        """Includes `env` that was parsed by `RequestCommandMixin`. Raises an
        exception that should be caught by client code if there is assertion can't
        be eval'ed or there's anything wrong with assertion.
        """
        dict_string = s.split('assert', 1)[1]
        try:
            assertion = eval(dict_string, self._env)
        except Exception as e:
            raise Exception('{}, {}'.format(dict_string.strip(), e))

        if not isinstance(assertion, dict):
            raise TypeError('assertion {} is not a dictionary'.format(assertion))
        return assertion

    def get_single_test_results(self, response, assertion):
        print(response, assertion)
        return 'hello'
