import sublime
import sublime_plugin

import json
from sys import maxsize
from urllib import parse
from collections import namedtuple

from .core import RequestCommandMixin
from .core.parsers import parse_requests
from .core.helpers import clean_url


Content = namedtuple('Content', 'content, point')
platform = sublime.platform()


def get_content(response):
    """Efficiently decides if response content is binary. If this is the case,
    returns before `text` or `json` are invoked on response, because they are VERY
    SLOW when invoked on binary responses. See below:

    https://github.com/requests/requests/issues/2371

    Also makes sure response isn't too large to display. Finally, prettifies JSON
    if response content is JSON.
    """
    config = sublime.load_settings('Requester.sublime-settings')
    max_len = 1000 * int(config.get('max_content_length_kb', 5000))
    if len(response.content) > max_len:
        return "Response is too big. This might be a binary file, or you might need to increase " +\
            "`max_content_length_kb` in Requester's settings."

    if response.encoding is None:
        try:
            response.content.decode('utf-8')
        except UnicodeDecodeError:
            # content is almost certainly binary, and if it's not, requests won't know how to decode it anyway
            return "Response content is binary, so it can't be displayed. Try downloading this file instead."
        else:
            response.encoding = 'utf-8'

    try:
        json_dict = response.json()
    except:
        return response.text
    else:  # prettify json regardless of what raw response looks like
        return json.dumps(json_dict, sort_keys=True, indent=2, separators=(',', ': '))


def get_response_view_content(request, response):
    """Returns a response string that includes metadata, headers and content,
    and the index of the string at which response content begins.
    """
    r = response
    redirects = [res.url for res in r.history]  # URLs traversed due to redirects
    redirects.append(r.url)  # final URL

    header = '{} {}\n{}s, {}B\n{}'.format(
        r.status_code, r.reason, r.elapsed.total_seconds(), len(r.content),
        ' -> '.join(redirects)
    )
    headers = '\n'.join(
        ['{}: {}'.format(k, v) for k, v in sorted(r.headers.items())]
    )

    content = get_content(r)
    replay_binding = '[cmd+r]' if platform == 'osx' else '[ctrl+r]'
    pin_binding = '[cmd+t]' if platform == 'osx' else '[ctrl+t]'
    before_content_items = [
        request.request,
        header,
        'Request Headers: {}'.format(r.request.headers),
        '{} replay request'.format(replay_binding) + ', ' + '{} pin/unpin tab'.format(pin_binding),
        headers
    ]
    try:
        body = parse.parse_qs(r.request.body)
        body = {k: v[0] for k, v in body.items()}
    except:
        body = r.request.body

    cookies = r.cookies.get_dict()
    if cookies:
        before_content_items.insert(3, 'Response Cookies: {}'.format(cookies))
    if body:
        before_content_items.insert(3, 'Request Body: {}'.format(body))
    before_content = '\n\n'.join(before_content_items)

    return Content(before_content + '\n\n' + content, len(before_content) + 2)


def set_response_view_name(view, response=None):
    """Set name for `view` with content from `response`.
    """
    try:  # short but descriptive, to facilitate navigation between response tabs, e.g. using Goto Anything
        path = parse.urlparse(response.url).path
        if path and path[-1] == '/':
            path = path[:-1]
        name = '{}: {}'.format(response.request.method, path)
    except:
        name = view.settings().get('requester.name')
    else:
        view.settings().set('requester.name', name)

    pinned = view.settings().get('requester.response_pinned', False)
    view.set_name('{}{}'.format('** ' if pinned else '', name))


class RequestsMixin:
    FROM_HISTORY = False

    def show_activity_for_pending_requests(self, requests, count, activity):
        """If there are already open response views waiting to display content from
        pending requests, show activity indicators in views.
        """
        for request in requests:

            for view in self.response_views_with_matching_request(
                request.method, request.url
            ):
                # view names set BEFORE view content is set, otherwise
                # activity indicator in view names seems to lag a little
                name = view.settings().get('requester.name')
                if not name:
                    view.set_name(activity)
                else:
                    spaces = min(self.ACTIVITY_SPACES, len(name))
                    activity = self.get_activity_indicator(count, spaces)
                    extra_spaces = 4  # extra spaces because tab names don't use monospace font =/
                    view.set_name(activity.ljust(len(name) + extra_spaces))

                view.run_command('requester_replace_view_text', {'text': '{}\n\n{}\n'.format(
                    request.request, activity
                )})

    def response_views_with_matching_request(self, method, url):
        """Get all response views whose request matches `request`.
        """
        if self.view.settings().get('requester.response_view', False) and not self.FROM_HISTORY:
            return [self.view]  # don't update other views when replaying a request

        views = []
        for sheet in self.view.window().sheets():
            view = sheet.view()
            if not view:
                continue
            if view.settings().get('requester.response_pinned', False):
                continue

            if view.settings().get('requester.response_view', False):
                view_request = view.settings().get('requester.request', None)
                if not view_request or not view_request[0] or not view_request[1]:
                    # don't match only falsy method or url
                    continue
                if view_request[0] == method and clean_url(url) == clean_url(view_request[1]):
                    views.append(view)
        return views

    @staticmethod
    def set_request_setting_on_view(view, response):
        """For reordering requests, showing pending activity for requests, and
        jumping to matching response tabs after requests return.
        """
        url = response.response.url
        view.settings().set('requester.request', [
            response.response.request.method, url.split('?')[0]
        ])


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
            except Exception as e:
                sublime.error_message('Parse Error: there may be unbalanced parentheses in calls to requests')
                print(e)
            else:
                for r in requests_:
                    requests.append(r)
        return requests

    def handle_special_request(self, request):
        """Handle requests which are initially run with `RequesterCommand` but are
        then passed on to other handlers, like downloads.
        """
        if 'filename' in request.kwargs:
            # this is very hacky, but only JSON serializable args can be passed to
            # `run_command`, and `env` isn't JSON serializable...
            from .download_commands import RequesterDownloadCommand as download
            download.REQUEST = request
            sublime.run_command('requester_download')
            return True
        return False

    def handle_response(self, response, num_requests):
        """Create a response view and insert response content into it. Ensure that
        response tab comes after (to the right of) all other response tabs.

        Don't create new response tab if a response tab matching request is open.
        """
        window = self.view.window()
        r = response
        if r.response is None or r.error:  # ignore responses with errors
            self.handle_special_request(response.request)
            return
        method, url = r.response.request.method, r.response.url

        requester_sheet = window.active_sheet()

        last_sheet = requester_sheet  # find last sheet (tab) with a response view
        for sheet in window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                last_sheet = sheet
        window.focus_sheet(last_sheet)

        views = self.response_views_with_matching_request(method, url)
        if not len(views):  # if there are no matching response tabs, create a new one
            view = window.new_file()
            pinned = self.config.get('pin_tabs_by_default', False)
            if pinned:  # is this newly opened view pinned by default?
                view.settings().set('requester.response_pinned', True)
            views = [view]
        else:  # move focus to matching view after response is returned if match occurred
            window.focus_view(views[0])

        for view in views:
            view.set_scratch(True)

            # this setting allows keymap to target response views separately
            view.settings().set('requester.response_view', True)
            self.set_env_settings_on_view(view)

            content = get_response_view_content(r.request, r.response)
            view.run_command('requester_replace_view_text',
                             {'text': content.content, 'point': content.point})
            view.set_syntax_file('Packages/Requester/requester-response.sublime-syntax')
            self.set_request_setting_on_view(view, r)

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
        try:
            requests = parse_requests(self.view.substr(
                sublime.Region(0, self.view.size())
            ), n=1)
        except Exception as e:
            sublime.error_message('Parse Error: there may be unbalanced parentheses in your request')
            print(e)
            return []
        else:
            return requests

    def handle_response(self, response, **kwargs):
        """Overwrites content in current view.
        """
        view = self.view
        r = response

        if r.error:  # ignore responses with errors
            return

        content = get_response_view_content(r.request, r.response)
        view.run_command('requester_replace_view_text',
                         {'text': content.content, 'point': content.point})
        view.set_syntax_file('Packages/Requester/requester-response.sublime-syntax')
        self.set_request_setting_on_view(view, r)

        set_response_view_name(view, r.response)


class RequesterCancelRequestsCommand(sublime_plugin.WindowCommand):
    """Cancel unfinished requests in recently instantiated response pools.
    """
    def run(self):
        pools = RequestCommandMixin.RESPONSE_POOLS
        while not pools.empty():
            pool = pools.get()
            if not pool.is_done:
                pool.is_done = True
                requests = pool.pending_requests
                if len(requests) > 100:
                    print('{} requests cancelled'.format(len(requests)))
                    return
                for request in requests:
                    print('Request cancelled: {}'.format(request.request))


class RequesterResponseTabTogglePinnedCommand(sublime_plugin.WindowCommand):
    """Pin or unpin a response tab. A pinned response tab can't be overwritten.
    """
    def run(self):
        view = self.window.active_view()
        if not view:
            return
        if not view.settings().get('requester.response_view', False):
            return
        pinned = bool(view.settings().get('requester.response_pinned', False))
        pinned = not pinned

        view.settings().set('requester.response_pinned', pinned)
        set_response_view_name(view)


class RequesterReorderResponseTabsCommand(RequestsMixin, RequestCommandMixin, sublime_plugin.TextCommand):
    """Reorders open response tabs to match order of requests in current view.
    """
    def get_requests(self):
        self._requests = []
        try:
            self._requests = parse_requests(self.view.substr(
                sublime.Region(0, self.view.size())
            ))
        except Exception as e:
            sublime.error_message('Parse Error: there may be unbalanced parentheses in calls to requests')
            print(e)
        return []  # these will show up again in `make_requests`, but we're only interested in selections

    def make_requests(self, *args, **kwargs):
        requests = self._requests  # 'selection', 'ordering', 'type' keys

        window = self.view.window()
        # cache all response views in current window
        response_views = []
        for sheet in window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                response_views.append(view)

        View = namedtuple('View', 'view, ordering')
        views = []
        # add `ordering` property to cached response views, indicating at which ordering they appear in current view
        for view in response_views:
            request = view.settings().get('requester.request', None)
            if not request or not request[0] or not request[1]:
                # don't match for falsy method or url
                views.append(View(view, maxsize))
                continue

            match = False
            # iterate over requests parsed from requester file (which are in
            # parsing order), see if request in response view matches any of them
            for r in requests:
                if request[0] == r.method and clean_url(request[1]) == clean_url(r.url):
                    views.append(View(view, r.ordering))
                    match = True
                    break

            if not match:
                views.append(View(view, maxsize))

        if not len(views):
            return

        # get largest index among open tabs
        group, index = 0, 0
        for sheet in window.sheets():
            view = sheet.view()
            group, index = window.get_view_index(view)

        # sort response views by ordering property, and reorder response tabs
        views.sort(key=lambda view: view.ordering)
        # requester tab, then response tabs are moved sequentially to largest index
        window.set_view_index(self.view, group, index)
        for v in views:
            window.set_view_index(v.view, group, index)
