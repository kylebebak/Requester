import sublime
import sublime_plugin

from requests import options

import json
from sys import maxsize
from urllib import parse
from collections import namedtuple

from .graphql import set_graphql_schema_on_view
from ..core import RequestCommandMixin
from ..core.parsers import parse_requests
from ..core.responses import prepare_request
from ..core.helpers import clean_url, truncate


Content = namedtuple('Content', 'content, point')
platform = sublime.platform()


def response_tab_command_bindings():
    """Returns string with special key bindings for response tab commands.
    """
    replay = '[cmd+r]' if platform == 'osx' else '[ctrl+r]'
    nav = '[ctrl+alt+ ←/→]'
    explore = '[cmd+e]' if platform == 'osx' else '[ctrl+e]'
    pin = '[cmd+t]' if platform == 'osx' else '[ctrl+t]'

    return '{} replay request, {} prev/next request, {} pin/unpin tab, {} explore URL'.format(
        replay, nav, pin, explore)


def get_content(res, fmt):
    """Efficiently decides if response content is binary. If this is the case,
    returns before `text` or `json` are invoked on response, because they are VERY
    SLOW when invoked on binary responses. See below:

    https://github.com/requests/requests/issues/2371

    Also makes sure response isn't too large to display. Finally, prettifies JSON
    if response content is JSON.
    """
    config = sublime.load_settings('Requester.sublime-settings')
    max_len = 1000 * int(config.get('max_content_length_kb', 5000))
    if len(res.content) > max_len:
        return "Response is too big. This might be a binary file, or you might need to increase " +\
            "`max_content_length_kb` in Requester's settings."

    if res.encoding is None:
        try:
            res.content.decode('utf-8')
        except UnicodeDecodeError:
            # content is almost certainly binary, and if it's not, requests won't know how to decode it anyway
            return "Response content is binary, so it won't be displayed. Try downloading this file instead."
        else:
            res.encoding = 'utf-8'

    try:
        json_dict = res.json()
    except:
        return res.text
    else:
        if fmt == 'indent_sort':
            return json.dumps(json_dict, sort_keys=True, indent=2, separators=(',', ': '))
        if fmt == 'indent':
            return json.dumps(json_dict, indent=2, separators=(',', ': '))
        return res.text


def get_response_view_content(response):
    """Returns a response string that includes metadata, headers and content,
    and the index of the string at which response content begins.
    """
    req, res, err = response

    read_content = True
    if 'filename' in req.skwargs:
        read_content = False

    redirects = [response.url for response in res.history]  # URLs traversed due to redirects
    redirects.append(res.url)  # final URL

    header = '{} {}\n{}s, {}B\n{}'.format(
        res.status_code, res.reason, res.elapsed.total_seconds(), len(res.content) if read_content else '?',
        ' -> '.join(redirects)
    )
    headers = '\n'.join(
        ['{}: {}'.format(k, v) for k, v in sorted(res.headers.items())]
    )

    content = get_content(res, req.skwargs.get('fmt')) if read_content else 'File download.'
    before_content_items = [
        req.request,
        header,
        'Request Headers: {}'.format(res.request.headers),
        response_tab_command_bindings(),
        headers
    ]
    try:
        body = parse.parse_qs(res.request.body)
        body = {k: v[0] for k, v in body.items()}
    except:
        body = res.request.body

    cookies = res.cookies.get_dict()
    if cookies:
        before_content_items.insert(3, 'Response Cookies: {}'.format(cookies))
    if body:
        before_content_items.insert(3, 'Request Body: {}'.format(truncate(body, 1000)))
    before_content = '\n\n'.join(before_content_items)

    return Content(before_content + '\n\n' + content, len(before_content) + 2)


def set_response_view_name(view, res=None):
    """Set name for `view` with content from `response`.
    """
    try:  # short but descriptive, to facilitate navigation between response tabs, e.g. using Goto Anything
        path = parse.urlparse(res.url).path
        if path and path[-1] == '/':
            path = path[:-1]
        name = '{}: {}'.format(res.request.method, path)
    except:
        name = view.settings().get('requester.name')
    else:
        view.settings().set('requester.name', name)

    pinned = view.settings().get('requester.response_pinned', False)
    view.set_name('{}{}'.format('** ' if pinned else '', name))


class RequestsMixin:
    def get_requests(self):
        """Parses requests from multiple selections. If nothing is highlighted,
        cursor's current line is taken as selection.
        """
        view = self.view
        requests = []
        for region in view.sel():
            if not region.empty():
                selection = view.substr(region)
                try:
                    requests_ = parse_requests(selection)
                except Exception as e:
                    sublime.error_message('Parse Error: there may be unbalanced parentheses in calls to requests')
                    print(e)
                    continue
            else:
                selection = view.substr(view.line(region))
                extended_selection = view.substr(sublime.Region(view.line(region).a, view.size()))
                try:
                    requests_ = parse_requests(selection, n=1, es=extended_selection)
                except Exception as e:
                    sublime.error_message('Parse Error: there may be unbalanced parentheses in calls to requests')
                    print(e)
                    continue
            for request in requests_:
                requests.append(request)
        return requests

    def show_activity_for_pending_requests(self, requests, count, activity):
        """If there are already open response views waiting to display content from
        pending requests, show activity indicators in views.
        """
        for req in requests:
            for view in self.response_views_with_matching_request(
                req.method, req.url
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
                    req.request, activity
                )})
                break  # do this for first view only

    def response_views_with_matching_request(self, method, url):
        """Get all response views whose request matches `request`.
        """
        if self.view.settings().get('requester.response_view', False):
            return [self.view]  # don't update other views when replaying a request

        views = []
        for sheet in self.view.window().sheets():
            view = sheet.view()
            if not view:
                continue
            if view.settings().get('requester.response_pinned', False):
                continue

            if view.settings().get('requester.response_view', False):
                view_method = view.settings().get('requester.request_method', None)
                view_url = view.settings().get('requester.request_url', None)
                if not view_method or not view_url:
                    continue
                if method == view_method and clean_url(url) == clean_url(view_url):
                    views.append(view)
        return views

    def handle_response(self, response):
        """Create a response view and insert response content into it. Ensure that
        response tab comes after (to the right of) all other response tabs.

        Don't create new response tab if a response tab matching request is open.
        """
        window = self.view.window()
        req, res, err = response
        if res is None or err:
            return
        method, url = res.request.method, res.url

        requester_sheet = window.active_sheet()

        last_sheet = requester_sheet  # find last sheet (tab) with a response view
        for sheet in window.sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                last_sheet = sheet
        window.focus_sheet(last_sheet)  # make sure new tab is opened after last open response view

        views = self.response_views_with_matching_request(method, url)
        if not len(views):  # if there are no matching response tabs, create a new one
            view = window.new_file()
            pinned = self.config.get('pin_tabs_by_default', False)
            if pinned:
                view.settings().set('requester.response_pinned', True)
        else:
            view = views[0]
        window.focus_sheet(requester_sheet)  # keep focus on requester view

        self._response_view = view  # cache this to change focus after all responses return
        view.set_scratch(True)

        # this setting allows keymap to target response views separately
        view.settings().set('requester.response_view', True)
        self.set_env_on_view(view)

        content, point = get_response_view_content(response)
        view.run_command('requester_replace_view_text', {'text': content, 'point': point})
        view.set_syntax_file('Packages/Requester/syntax/requester-response.sublime-syntax')
        set_request_on_view(view, res)

        # should response tabs be reordered after requests return?
        if self.config.get('reorder_tabs_after_requests', False):
            self.view.run_command('requester_reorder_response_tabs')
        set_response_view_name(view, res)
        set_graphql_schema_on_view(view, req)

    def handle_responses(self, responses):
        """Change focus after request returns? `handle_response` must be called
        before this method.
        """
        if len(responses) != 1:
            return
        if not self.config.get('change_focus_after_request', True):
            return
        if not responses[0].err and responses[0].res is not None:
            if hasattr(self, '_response_view'):
                self.view.window().focus_view(self._response_view)


class RequesterCommand(RequestsMixin, RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute requests from requester file concurrently and open multiple
    response views.
    """
    def run(self, edit, concurrency=10):
        """Allow user to specify concurrency.
        """
        self.MAX_WORKERS = max(1, concurrency)
        super().run(edit)


class RequesterReplayRequestCommand(RequestsMixin, RequestCommandMixin, sublime_plugin.TextCommand):
    """Replay a request from a response view.
    """
    def get_requests(self):
        """Only parses first request in file.
        """
        try:
            request = self.get_replay_request()
        except:
            return []
        return [request]

    def get_replay_request(self):
        """Only parses first request in file.
        """
        try:
            requests = parse_requests(self.view.substr(sublime.Region(0, self.view.size())), n=1)
        except Exception as e:
            sublime.error_message('Parse Error: there may be unbalanced parentheses in your request')
            print(e)
            raise
        try:
            return requests[0]
        except IndexError:
            sublime.error_message('Replay Error: there is no request in your response review')
            raise

    def handle_response(self, response):
        """Overwrites content in current view.
        """
        view = self.view
        req, res, err = response

        if err:
            return

        content, point = get_response_view_content(response)
        view.run_command('requester_replace_view_text', {'text': content, 'point': point})
        view.set_syntax_file('Packages/Requester/syntax/requester-response.sublime-syntax')
        set_request_on_view(view, res)
        view.settings().erase('requester.request_history_index')
        view.settings().set('requester.history_view', False)
        set_response_view_name(view, res)
        set_graphql_schema_on_view(view, req)


class RequesterExploreUrlCommand(RequesterReplayRequestCommand):
    """Explore a new URL from a response view. If the request doesn't hit the same
    domain, remove the `headers`, `cookies` and `auth` args. This makes it trivial
    for users to explore hyperlinked APIs (HATEOAS).
    """
    def get_requests(self):
        """Parses URL from first selection, and passes it in special `explore` arg
        to call to requests.
        """
        view = self.view
        if not view or not view.settings().get('requester.response_view', False):
            sublime.error_message('Explore Error: you can only explore URLs from response tabs')
            return []

        try:
            url = view.substr(view.sel()[0]).replace('"', '')
        except:
            return []
        if not url:
            return []
        self._explore_url = url

        try:
            request = self.get_replay_request()
        except:
            return []
        return ["{}, explore=({}, {}))".format(request[:-1], repr(request), repr(url))]

    def show_activity_for_pending_requests(self, *args, **kwargs):
        """Don't do this for exploratory requests.
        """

    def handle_response(self, response):
        """Creates new "explore URL" view.
        """
        req, res, err = response

        if err:
            return

        view = self.view.window().new_file()
        self.set_env_on_view(view)
        view.settings().set('requester.response_view', True)
        view.set_scratch(True)

        content, point = get_response_view_content(response)
        view.run_command('requester_replace_view_text', {'text': content, 'point': point})
        view.set_syntax_file('Packages/Requester/syntax/requester-response.sublime-syntax')
        set_request_on_view(view, res)
        set_response_view_name(view, res)
        set_graphql_schema_on_view(view, req)

    def persist_requests(self, responses):
        """Don't do this for exploratory requests.
        """


class RequesterUrlOptionsCommand(sublime_plugin.WindowCommand):
    """Display pop-up with options for request in currently open response tab.
    """
    def run(self):
        view = self.window.active_view()
        url = view.settings().get('requester.request_url', None)
        if url is None:
            return
        sublime.set_timeout_async(lambda: self.show_options(url, view), 0)

    def show_options(self, url, view):
        """Send options request to `url` and display results in pop-up.
        """
        res = options(url, timeout=3)
        if not res.ok:
            return
        names = ['Allow', 'Access-Control-Allow-Methods', 'Access-Control-Max-Age']
        headers = [res.headers.get(name, None) for name in names]
        items = '\n'.join('<li>{}: {}</li>'.format(n, h) for n, h in zip(names, headers) if h)
        content = '<h2>OPTIONS: {}</h2>\n<ul>{}</ul>'.format(url, items)
        try:
            json_dict = res.json()
        except:
            pass
        else:
            content = '{}\n<pre><code>{}</pre></code>'.format(
                content, json.dumps(json_dict, sort_keys=True, indent=2, separators=(',', ': '))
            )

        view.show_popup(content, max_width=700, max_height=500)


class RequesterCancelRequestsCommand(sublime_plugin.WindowCommand):
    """Cancel unfinished requests in recently instantiated response pools.
    """
    def run(self):
        pools = RequestCommandMixin.RESPONSE_POOLS
        while not pools.empty():
            pool = pools.get()
            if not pool.is_done:
                pool.is_done = True
                requests = pool.get_pending_requests()
                if len(requests) > 100:
                    print('{} requests cancelled'.format(len(requests)))
                    return
                for req in requests:
                    print('Request cancelled: {}'.format(req.request))


class RequesterResponseTabTogglePinnedCommand(sublime_plugin.WindowCommand):
    """Pin or unpin a response tab. A pinned response tab can't be overwritten.
    """
    def run(self):
        view = self.window.active_view()
        if not view:
            return
        if not view.settings().get('requester.response_view', False):
            return
        if view.settings().get('requester.history_view', False):
            return
        pinned = bool(view.settings().get('requester.response_pinned', False))
        pinned = not pinned

        view.settings().set('requester.response_pinned', pinned)
        set_response_view_name(view)


class RequesterReorderResponseTabsCommand(RequestsMixin, RequestCommandMixin, sublime_plugin.TextCommand):
    """Reorders open response tabs to match order of requests in current view.
    """
    def get_requests(self):
        try:
            return parse_requests(self.view.substr(
                sublime.Region(0, self.view.size())
            ))
        except Exception as e:
            sublime.error_message('Parse Error: there may be unbalanced parentheses in calls to requests')
            print(e)
            return []

    def make_requests(self, requests, env):
        requests = [prepare_request(request, env, i) for i, request in enumerate(requests)]

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
            method = view.settings().get('requester.request_method', None)
            url = view.settings().get('requester.request_url', None)
            if not method or not url:
                views.append(View(view, maxsize))
                continue

            match = False
            # see if request in response view matches any request parsed from requester file
            for req in requests:
                if not req.method or not req.url:
                    continue
                if method == req.method and clean_url(url) == clean_url(req.url):
                    views.append(View(view, req.ordering))
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


def set_request_on_view(view, res):
    """For reordering requests, showing pending activity for requests, and
    jumping to matching response tabs after requests return.
    """
    view.settings().set('requester.request_method', res.request.method)
    view.settings().set('requester.request_url', res.url.split('?')[0])
