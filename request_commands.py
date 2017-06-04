import sublime, sublime_plugin

import json
from urllib import parse
from collections import namedtuple

from .core import RequestCommandMixin
from .core.parsers import parse_requests


Content = namedtuple('Content', 'content, point')
platform = sublime.platform()


def get_response_view_content(request, response):
    """Returns a response string that includes metadata, headers and content,
    and the index of the string at which response content begins.
    """
    r = response
    redirects = [res.url for res in r.history] # URLs traversed due to redirects
    redirects.append(r.url) # final URL

    header = '{} {}\n{}s, {}B\n{}'.format(
        r.status_code, r.reason, r.elapsed.total_seconds(), len(r.content),
        ' -> '.join(redirects)
    )
    headers = '\n'.join(
        [ '{}: {}'.format(k, v) for k, v in sorted(r.headers.items()) ]
    )
    try:
        json_dict = r.json()
    except:
        content = r.text
    else: # prettify json regardless of what raw response looks like
        content = json.dumps(json_dict, sort_keys=True, indent=2, separators=(',', ': '))

    replay_binding = '[cmd+r]' if platform == 'osx' else '[ctrl+r]'
    before_content_items = [
        request,
        header,
        '{}: {}'.format('Request Headers', r.request.headers),
        '{} replay request'.format(replay_binding),
        headers
    ]
    cookies = r.cookies.get_dict()
    if cookies:
        before_content_items.insert(3, '{}: {}'.format('Response Cookies', cookies))
    before_content = '\n\n'.join(before_content_items)

    return Content(before_content + '\n\n' + content, len(before_content) + 2)


def set_response_view_name(view, response):
    """Set name for `view` with content from `response`.
    """
    try: # short but descriptive, to facilitate navigation between response tabs, e.g. using Goto Anything
        name = '{}: {}'.format(response.request.method, parse.urlparse(response.url).path)
    except:
        view.set_name( view.settings().get('requester.name') )
    else:
        view.set_name(name)
        view.settings().set('requester.name', name)


class RequestsMixin:
    def show_activity_for_pending_requests(self, requests, count, activity):
        """If there are already open response views waiting to display content from
        pending requests, show activity indicators in views.
        """
        for request in requests:
            for view in self.response_views_with_matching_request(request):
                # view names set BEFORE view content is set, otherwise
                # activity indicator in view names seems to lag a little
                name = view.settings().get('requester.name')
                if not name:
                    view.set_name(activity)
                else:
                    spaces = min(self.ACTIVITY_SPACES, len(name))
                    activity = self.get_activity_indicator(count, spaces)
                    extra_spaces = 4 # extra spaces because tab names don't use monospace font =/
                    view.set_name(activity.ljust( len(name) + extra_spaces ))

                view.run_command('requester_replace_view_text', {'text': '{}\n\n{}\n'.format(
                    request, activity
                )})

    def response_views_with_matching_request(self, request):
        """Get all response views whose request matches `request`.
        """
        views = []
        for sheet in self.view.window().sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                view_request = view.settings().get('requester.request', None)
                if not view_request:
                    continue
                if request == view_request:
                    views.append(view)
        return views


class RequesterCommand(RequestsMixin, RequestCommandMixin, sublime_plugin.TextCommand):
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
        return requests

    def handle_response(self, response, num_requests):
        """Create a response view and insert response content into it. Ensure that
        response tab comes after (to the right of) all other response tabs.

        Don't create new response tab if a response tab matching request is open.
        """
        window = self.view.window(); r = response

        if r.error: # ignore responses with errors
            for view in self.response_views_with_matching_request(r.request):
                set_response_view_name(view, r.response)
            return

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
            view.set_syntax_file('Packages/Requester/requester-response.sublime-syntax')
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

        for view in views:
            set_response_view_name(view, r.response)


class RequesterReplayRequestCommand(RequestsMixin, RequestCommandMixin, sublime_plugin.TextCommand):
    """Replay a request from a response view.
    """
    def get_requests(self):
        """Parses requests from first line only.
        """
        return [self.view.substr( self.view.line(0) )]

    def handle_response(self, response, **kwargs):
        """Overwrites content in current view.
        """
        view = self.view; r = response

        if r.error: # ignore responses with errors
            return

        content = get_response_view_content(r.request, r.response)
        view.run_command('requester_replace_view_text',
                             {'text': content.content, 'point': content.point})
        view.set_syntax_file('Packages/Requester/requester-response.sublime-syntax')
        view.settings().set('requester.request', r.request)

        set_response_view_name(view, r.response)
