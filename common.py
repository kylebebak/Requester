import sublime

import os
import re
import imp
import json
from urllib import parse
from collections import namedtuple
from threading import Thread

from .responses import ResponseThreadPool


Content = namedtuple('Content', 'content, point')
platform = sublime.platform()


class RequestCommandMixin:

    REFRESH_MS = 200 # period of checks on async operations, e.g. requests
    ACTIVITY_SPACES = 9 # number of spaces in activity indicator
    MAX_WORKERS = 10 # default request concurrency

    def get_selections(self):
        """This should be overridden to return a list of request strings.
        """
        return []

    def handle_response(self, response, num_selections):
        """Override this method to handle a response from a single request. This
        method is called as each response is returned.
        """
        pass

    def handle_responses(self, responses):
        """Override this method to handle responses from all requests executed.
        This method is called after all responses have been returned.
        """
        pass

    def handle_error(self, response, num_selections):
        """Override this method to handle an error from a single request. This
        method is called as each response is returned.
        """
        pass

    def handle_errors(self, responses):
        """Override this method to handle errors from all requests executed. This
        method is called after all responses have been returned.
        """
        errors = ['{}\n{}'.format(r.selection, r.error) for r in responses if r.error]
        if errors:
            sublime.error_message('\n\n'.join(errors))

    def run(self, edit):
        self.config = sublime.load_settings('Requester.sublime-settings')
        # `run` runs first, which means `self.config` is available to all methods
        self.reset_env_string()
        self.reset_env_file()
        thread = Thread(target=self._get_env)
        thread.start()
        self._run(thread)

    def _run(self, thread, count=0):
        """Evaluate environment in a separate thread and show an activity
        indicator. Inspect thread at regular intervals until it's finished, at
        which point `make_requests` can be invoked. Return if thread times out.
        """
        REFRESH_MULTIPLIER = 4
        activity = self.get_activity_indicator(count//REFRESH_MULTIPLIER, self.ACTIVITY_SPACES)
        if count > 0: # don't distract user with RequesterEnv status if env can be evaluated quickly
            self.view.set_status('requester.activity', '{} {}'.format( 'RequesterEnv', activity ))

        if thread.is_alive():
            timeout = self.config.get('timeout_env', None)
            if timeout is not None and count * self.REFRESH_MS/REFRESH_MULTIPLIER > timeout * 1000:
                sublime.error_message('Timeout Error: environment took too long to parse')
                self.view.set_status('requester.activity', '')
                return
            sublime.set_timeout(lambda: self._run(thread, count+1), self.REFRESH_MS/REFRESH_MULTIPLIER)

        else:
            selections = self.get_selections()
            self.view.set_status('requester.activity', '')
            self.make_requests(selections, self._env)

    def reset_env_string(self):
        """(Re)sets the `requester.env_string` setting on the view, if appropriate.
        """
        if self.view.settings().get('requester.response_view', False):
            return

        delimeter = '###env'
        in_block = False
        env_lines = []
        for line in self.view.substr( sublime.Region(0, self.view.size()) ).splitlines():
            if in_block:
                if line == delimeter:
                    in_block = False
                    break
                env_lines.append(line)
            else:
                if line == delimeter:
                    in_block = True
        if not len(env_lines) or in_block: # env block must be closed
            self.view.settings().set('requester.env_string', None)
        self.view.settings().set('requester.env_string', '\n'.join(env_lines))

    def reset_env_file(self):
        """(Re)sets the `requester.env_file` setting on the view, if appropriate.
        """
        if self.view.settings().get('requester.response_view', False):
            return

        scope = {}
        p = re.compile('\s*env_file\s*=.*') # `env_file` can be overridden from within requester file
        for line in self.view.substr( sublime.Region(0, self.view.size()) ).splitlines():
            if p.match(line): # matches only at beginning of string
                try:
                    exec(line, scope) # add `env_file` to `scope` dict
                except:
                    pass
                break # stop looking after first match

        env_file = scope.get('env_file')
        if env_file:
            env_file = str(env_file)
            if os.path.isabs(env_file):
                self.view.settings().set('requester.env_file', env_file)
            else:
                file_path = self.view.file_name()
                if file_path:
                    self.view.settings().set('requester.env_file',
                                             os.path.join(os.path.dirname(file_path), env_file))
        else:
            self.view.settings().set('requester.env_file', None)

    def get_env(self):
        """Computes an env from `requester.env_string` setting, and/or from
        `requester.env_file` setting. Returns an env dictionary.

        http://stackoverflow.com/questions/5362771/load-module-from-string-in-python
        http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
        """
        env_dict = {}
        env_string = self.view.settings().get('requester.env_string', None)
        if env_string:
            env = imp.new_module('requester.env')
            try:
                exec(env_string, env.__dict__)
            except Exception as e:
                sublime.error_message('EnvBlock Error:\n{}'.format(e))
            else:
                # return a new intance of this dict, or else its values will be reset to `None` after it's returned
                env_dict = dict(env.__dict__)

        env_file = self.view.settings().get('requester.env_file', None)
        if env_file:
            try:
                env = imp.load_source('requester.env', env_file)
            except Exception as e:
                sublime.error_message('EnvFile Error:\n{}'.format(e))
            else:
                env_dict_ = vars(env)
                env_dict_.update(env_dict) # env computed from `env_string` takes precedence
                return env_dict_
        return env_dict or None

    def _get_env(self):
        """Wrapper calls `get_env` and assigns return value to instance property.
        """
        self._env = self.get_env()

    def make_requests(self, selections, env=None):
        """Make requests concurrently using a `ThreadPool`, which itself runs on
        an alternate thread so as not to block the UI.
        """
        pool = ResponseThreadPool(selections, env, self.MAX_WORKERS) # pass along env vars to thread pool
        self.show_activity_for_pending_requests(selections)
        sublime.set_timeout_async(lambda: pool.run(), 0) # run on an alternate thread
        sublime.set_timeout(lambda: self.gather_responses(pool), self.REFRESH_MS)

    def show_activity_for_pending_requests(self, selections, count=0):
        """Show activity indicator in status bar. Also, if there are already open
        response views waiting to display content from pending requests, show
        activity indicators in views.
        """
        activity = self.get_activity_indicator(count, self.ACTIVITY_SPACES)
        self.view.set_status('requester.activity', '{} {}'.format( 'Requester', activity ))

        for selection in selections:
            for view in self.response_views_with_matching_selection(selection):
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
                    selection, activity
                )})

    def get_activity_indicator(self, count, spaces):
        """Displays an activity indicator in status bar if there are pending
        requests.
        """
        cycle = count // spaces
        if cycle % 2 == 0:
            before = count % spaces
        else:
            before = spaces - (count % spaces)
        after = spaces - before
        return '[{}={}]'.format(' ' * before, ' ' * after)

    def gather_responses(self, pool, count=0, responses=None):
        """Inspect thread pool at regular intervals to remove completed responses
        and handle them, and/or display requests errors.

        Clients can handle responses and errors one at a time as they are
        completed, or as a group when they're all finished. Each response objects
        contains `selection`, `response`, `error`, and `ordering` keys.
        """
        is_done = pool.is_done # cache `is_done` before removing responses from pool

        if responses is None:
            responses = []

        while len(pool.responses): # remove completed responses from thread pool and display them
            r = pool.responses.pop(0)
            responses.append(r)
            self.handle_response(r, num_selections=pool.num_selections())
            self.handle_error(r, num_selections=pool.num_selections())

            for view in self.response_views_with_matching_selection(r.selection):
                self.set_response_view_name(view, r.response)

        if is_done:
            responses.sort(key=lambda response: response.ordering) # parsing order is preserved
            self.handle_responses(responses)
            self.handle_errors(responses)
            self.view.set_status('requester.activity', '') # remove activity indicator from status bar
            return

        count += 1
        self.show_activity_for_pending_requests(pool.pending_selections, count)
        sublime.set_timeout(lambda: self.gather_responses(pool, count, responses), self.REFRESH_MS)

    def get_response_content(self, request, response):
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

    def set_response_view_name(self, view, response):
        """Set name for `view` with content from `response`.
        """
        try: # short but descriptive, to facilitate navigation between response tabs, e.g. using Goto Anything
            name = '{}: {}'.format(response.request.method, parse.urlparse(response.url).path)
        except:
            view.set_name( view.settings().get('requester.name') )
        else:
            view.set_name(name)
            view.settings().set('requester.name', name)

    def set_syntax(self, view, response):
        """Try to set syntax for `view` based on `content-type` response header.
        """
        if not self.config.get('highlighting', False):
            return

        view.set_syntax_file('Packages/Requester/requester-response.sublime-syntax')

    def response_views_with_matching_selection(self, selection):
        """Get all response views whose selection matches `selection`.
        """
        views = []
        for sheet in self.view.window().sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                view_selection = view.settings().get('requester.selection', None)
                if not view_selection:
                    continue
                if selection == view_selection:
                    views.append(view)
        return views

    @staticmethod
    def prepare_selection(s, timeout=None):
        """If selection is not prefixed with "{var_name}.", prefix selection with
        "requests.", because this module is guaranteed to be in the scope under
        which the selection is evaluated.

        Also, ensure request can time out so it doesn't hang indefinitely.
        http://docs.python-requests.org/en/master/user/advanced/#timeouts

        Finally, ensure that selection occupies only one line.
        """
        s = s.strip()
        if not re.match('[\w_][\w\d_]*\.', s):
            s = 'requests.' + s

        if timeout is not None:
            timeout_string = ', timeout={})'.format(timeout)
            s = s[:-1] + timeout_string
        return ' '.join(s.split()) # replace all multiple whitespace with single space
